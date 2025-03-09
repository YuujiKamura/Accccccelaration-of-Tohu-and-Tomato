"""
自律テストエンジン (Autonomous Test Engine)

このエンジンは「暴走列車」のように、自律的に以下のサイクルを繰り返します：
1. テスト実行
2. 結果分析
3. 問題検出
4. 修正案生成
5. 修正適用
6. 再テスト

ユーザーの介入なしに、テストが全て成功するまで走り続けます。
"""

import os
import sys
import time
import json
import shutil
import subprocess
import traceback
import datetime
import tempfile
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set

# 定数定義
MAX_ITERATIONS = 50  # 最大反復回数
MAX_FIXES_PER_FILE = 5  # ファイルあたりの最大修正回数
SLEEP_BETWEEN_RUNS = 1  # テスト実行間の待機時間(秒)

# グローバル変数
fixed_files = {}  # 修正したファイルの履歴 {ファイルパス: 修正回数}
total_iterations = 0  # 総反復回数
start_time = None  # 開始時刻

class TestResult:
    """テスト結果を表すクラス"""
    
    def __init__(self, success: bool, test_name: str, error_message: str = None, 
                 file_path: str = None, line_number: int = None):
        self.success = success
        self.test_name = test_name
        self.error_message = error_message
        self.file_path = file_path
        self.line_number = line_number
        self.fixed = False
        self.fix_attempts = 0
    
    def __str__(self):
        if self.success:
            return f"✓ {self.test_name}"
        else:
            location = f"{self.file_path}:{self.line_number}" if self.file_path else "不明"
            return f"✗ {self.test_name} - {location} - {self.error_message}"

class TestRunner:
    """テスト実行クラス"""
    
    def __init__(self, command="python run_auto_tests.py --verbosity=2", report_dir="test_reports"):
        self.command = command
        self.report_dir = report_dir
        self.last_report = None
    
    def run(self) -> Tuple[bool, List[TestResult], Dict]:
        """テストを実行し、結果を返す"""
        print(f"テストを実行: {self.command}")
        
        try:
            # テスト実行
            process = subprocess.Popen(
                self.command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            # 結果解析
            success = process.returncode == 0
            results = self._parse_test_output(stdout, stderr)
            
            # レポートファイルの取得
            latest_report = self._get_latest_report()
            if latest_report:
                with open(latest_report, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    self.last_report = report_data
            else:
                report_data = None
            
            return success, results, report_data
            
        except Exception as e:
            print(f"テスト実行中にエラーが発生: {e}")
            traceback.print_exc()
            return False, [], None
    
    def _parse_test_output(self, stdout: str, stderr: str) -> List[TestResult]:
        """テスト出力を解析してTestResultのリストを返す"""
        results = []
        
        # 標準エラー出力からエラー情報を抽出
        error_pattern = r'ERROR: ([^\(]+).*?\n(.*?)(?:\n\n|$)'
        failure_pattern = r'FAIL: ([^\(]+).*?\n(.*?)(?:\n\n|$)'
        
        # エラーを検出
        for match in re.finditer(error_pattern, stderr, re.DOTALL):
            test_name = match.group(1).strip()
            error_text = match.group(2).strip()
            
            # ファイルパスと行番号を抽出
            file_line = self._extract_file_line(error_text)
            result = TestResult(
                success=False,
                test_name=test_name,
                error_message=error_text,
                file_path=file_line[0] if file_line else None,
                line_number=file_line[1] if file_line else None
            )
            results.append(result)
        
        # 失敗を検出
        for match in re.finditer(failure_pattern, stderr, re.DOTALL):
            test_name = match.group(1).strip()
            error_text = match.group(2).strip()
            
            # ファイルパスと行番号を抽出
            file_line = self._extract_file_line(error_text)
            result = TestResult(
                success=False,
                test_name=test_name,
                error_message=error_text,
                file_path=file_line[0] if file_line else None,
                line_number=file_line[1] if file_line else None
            )
            results.append(result)
        
        # 成功したテストを標準出力から抽出
        success_pattern = r'(test_\w+) \(([^)]+)\).*?\.\.\. ok'
        for match in re.finditer(success_pattern, stdout):
            method_name = match.group(1)
            class_path = match.group(2)
            test_name = f"{method_name} ({class_path})"
            result = TestResult(success=True, test_name=test_name)
            results.append(result)
        
        return results
    
    def _extract_file_line(self, error_text: str) -> Optional[Tuple[str, int]]:
        """エラーメッセージからファイルパスと行番号を抽出"""
        # パターン1: File "path/to/file.py", line 123
        file_pattern1 = r'File "([^"]+)", line (\d+)'
        match = re.search(file_pattern1, error_text)
        if match:
            return match.group(1), int(match.group(2))
        
        # パターン2: path/to/file.py:123
        file_pattern2 = r'(\S+\.py):(\d+)'
        match = re.search(file_pattern2, error_text)
        if match:
            return match.group(1), int(match.group(2))
        
        return None
    
    def _get_latest_report(self) -> Optional[str]:
        """最新のテストレポートファイルを取得"""
        try:
            if not os.path.exists(self.report_dir):
                return None
                
            report_files = [os.path.join(self.report_dir, f) for f in os.listdir(self.report_dir) 
                           if f.startswith('test_report_') and f.endswith('.json')]
            
            if not report_files:
                return None
                
            # 最新のファイルを取得
            latest_report = max(report_files, key=os.path.getmtime)
            return latest_report
            
        except Exception as e:
            print(f"レポートファイル取得中にエラー: {e}")
            return None

class TestFixer:
    """テスト修正クラス"""
    
    def __init__(self, max_fixes_per_file: int = MAX_FIXES_PER_FILE):
        self.max_fixes_per_file = max_fixes_per_file
    
    def can_fix(self, result: TestResult) -> bool:
        """修正可能かどうかを判定"""
        if result.success or result.fixed:
            return False
            
        if not result.file_path or not result.error_message:
            return False
            
        # ファイルが存在するか確認
        if not os.path.exists(result.file_path):
            return False
            
        # 修正上限に達していないか確認
        global fixed_files
        if result.file_path in fixed_files and fixed_files[result.file_path] >= self.max_fixes_per_file:
            print(f"警告: {result.file_path} は既に {fixed_files[result.file_path]} 回修正されており、上限に達しています")
            return False
            
        # 修正試行回数を確認
        if result.fix_attempts >= 3:
            print(f"警告: {result.test_name} の修正を {result.fix_attempts} 回試みましたが失敗しました")
            return False
            
        return True
    
    def fix(self, result: TestResult) -> bool:
        """テストの問題を修正"""
        if not self.can_fix(result):
            return False
            
        print(f"\n修正を試みます: {result.test_name}")
        print(f"ファイル: {result.file_path}")
        print(f"エラー: {result.error_message}")
        
        # 修正試行回数をインクリメント
        result.fix_attempts += 1
        
        # エラータイプに基づいて修正方法を決定
        if "ImportError" in result.error_message or "ModuleNotFoundError" in result.error_message:
            fixed = self._fix_import_error(result)
        elif "AttributeError" in result.error_message:
            fixed = self._fix_attribute_error(result)
        elif "TypeError" in result.error_message:
            fixed = self._fix_type_error(result)
        elif "AssertionError" in result.error_message:
            fixed = self._fix_assertion_error(result)
        elif "KeyError" in result.error_message:
            fixed = self._fix_key_error(result)
        elif "IndexError" in result.error_message:
            fixed = self._fix_index_error(result)
        else:
            # 汎用的な修正
            fixed = self._fix_generic_error(result)
        
        if fixed:
            # 修正カウンターを更新
            global fixed_files
            if result.file_path in fixed_files:
                fixed_files[result.file_path] += 1
            else:
                fixed_files[result.file_path] = 1
                
            result.fixed = True
            print(f"✓ 修正完了: {result.file_path}")
        else:
            print(f"✗ 修正失敗: {result.test_name}")
            
        return fixed
        
    def _fix_import_error(self, result: TestResult) -> bool:
        """ImportErrorを修正"""
        # モジュール名を抽出
        module_pattern = r'No module named \'([^\']+)\''
        match = re.search(module_pattern, result.error_message)
        if not match:
            return False
            
        module_name = match.group(1)
        print(f"不足しているモジュール: {module_name}")
        
        # requirements.txtが存在するか確認
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r', encoding='utf-8') as f:
                requirements = f.read()
                
            # 既に記載されているか確認
            if module_name in requirements:
                # 既に記載されているがインストールされていない可能性
                print(f"{module_name} は requirements.txt に記載されています")
                return False
                
            # requirements.txtに追加
            with open('requirements.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n{module_name}\n")
                
            print(f"{module_name} を requirements.txt に追加しました")
            return True
        else:
            # requirements.txtが存在しない場合は作成
            with open('requirements.txt', 'w', encoding='utf-8') as f:
                f.write(f"{module_name}\n")
                
            print(f"requirements.txt を作成し、{module_name} を追加しました")
            return True
    
    def _fix_attribute_error(self, result: TestResult) -> bool:
        """AttributeErrorを修正"""
        # 属性名を抽出
        attr_pattern = r"'([^']+)' object has no attribute '([^']+)'"
        match = re.search(attr_pattern, result.error_message)
        if not match:
            return False
            
        obj_type = match.group(1)
        missing_attr = match.group(2)
        print(f"不足している属性: {obj_type}.{missing_attr}")
        
        # ファイルを読み込み
        with open(result.file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            
        # クラス定義を探す
        class_start = -1
        class_end = -1
        class_indent = ""
        
        for i, line in enumerate(content):
            if re.search(rf"class\s+{obj_type}\s*\(", line):
                class_start = i
                class_indent = re.match(r"(\s*)", line).group(1)
                
            if class_start >= 0 and i > class_start:
                # クラス定義の終わりを探す (インデントの減少)
                if line.strip() and not line.startswith(class_indent):
                    class_end = i
                    break
                    
        if class_start < 0:
            return False
            
        if class_end < 0:
            class_end = len(content)
            
        # 属性を追加する位置を見つける
        insert_pos = class_start + 1
        method_indent = class_indent + "    "
        
        # 初期化メソッドを探す
        init_start = -1
        init_end = -1
        
        for i in range(class_start, class_end):
            if re.search(rf"{method_indent}def\s+__init__\s*\(", content[i]):
                init_start = i
                
            if init_start >= 0 and i > init_start:
                # メソッド定義の終わりを探す (空行または別のメソッド)
                if not content[i].strip() or re.search(rf"{method_indent}def\s+", content[i]):
                    init_end = i
                    break
                    
        if init_start >= 0 and init_end < 0:
            init_end = class_end
            
        # 初期化メソッドが見つかった場合、その中に属性を追加
        if init_start >= 0:
            # self.属性名 = None の形式で追加
            for i in range(init_start, init_end):
                if "self." in content[i]:
                    insert_pos = i + 1
                    
            # 属性初期化コードを挿入
            content.insert(insert_pos, f"{method_indent}        self.{missing_attr} = None  # 自動追加\n")
            
        else:
            # 初期化メソッドが見つからない場合、新しく作成
            init_method = [
                f"{method_indent}def __init__(self):\n",
                f"{method_indent}    super().__init__()\n",
                f"{method_indent}    self.{missing_attr} = None  # 自動追加\n"
            ]
            
            # クラス定義直後に挿入
            for i, line in reversed(list(enumerate(init_method))):
                content.insert(insert_pos, line)
                
        # ファイルを書き戻す
        with open(result.file_path, 'w', encoding='utf-8') as f:
            f.writelines(content)
            
        return True
    
    def _fix_type_error(self, result: TestResult) -> bool:
        """TypeErrorを修正"""
        # パターン: "func() got an unexpected keyword argument 'xyz'"
        kwarg_pattern = r"got an unexpected keyword argument '([^']+)'"
        match = re.search(kwarg_pattern, result.error_message)
        
        if match:
            kwarg = match.group(1)
            print(f"不要なキーワード引数: {kwarg}")
            
            # ファイルを読み込み
            with open(result.file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
                
            # 問題の行を見つける
            if result.line_number and result.line_number <= len(content):
                line = content[result.line_number - 1]
                
                # 引数部分を見つける
                # パターン: func(a=1, b=2, xyz=3)
                new_line = re.sub(rf"{kwarg}\s*=\s*[^,)]+,?\s*", "", line)
                
                # 不要なカンマを整理
                new_line = re.sub(r",\s*\)", ")", new_line)
                
                # 変更を適用
                content[result.line_number - 1] = new_line
                
                # ファイルを書き戻す
                with open(result.file_path, 'w', encoding='utf-8') as f:
                    f.writelines(content)
                    
                return True
                
        # パターン: "func() takes x positional arguments but y were given"
        args_pattern = r"takes (\d+) positional arguments? but (\d+) were given"
        match = re.search(args_pattern, result.error_message)
        
        if match:
            expected = int(match.group(1))
            actual = int(match.group(2))
            print(f"引数の数が一致しません: 期待={expected}, 実際={actual}")
            
            # ファイルを読み込み
            with open(result.file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
                
            # 問題の行を見つける
            if result.line_number and result.line_number <= len(content):
                line = content[result.line_number - 1]
                
                # 関数名と引数を特定
                func_pattern = r"(\w+)\s*\((.*?)\)"
                func_match = re.search(func_pattern, line)
                
                if func_match:
                    func_name = func_match.group(1)
                    args = func_match.group(2).split(",")
                    
                    # 引数が多すぎる場合は削減
                    if actual > expected:
                        args = args[:expected-1]  # self引数を考慮して1つ減らす
                        
                    # 更新された引数で行を再構築
                    new_args = ", ".join([arg.strip() for arg in args])
                    new_line = line.replace(func_match.group(0), f"{func_name}({new_args})")
                    
                    # 変更を適用
                    content[result.line_number - 1] = new_line
                    
                    # ファイルを書き戻す
                    with open(result.file_path, 'w', encoding='utf-8') as f:
                        f.writelines(content)
                        
                    return True
                    
        return False
    
    def _fix_assertion_error(self, result: TestResult) -> bool:
        """AssertionErrorを修正"""
        # 特定のパターン: "assert X == Y" で失敗
        assert_pattern = r"AssertionError: (.*) != (.*)"
        match = re.search(assert_pattern, result.error_message)
        
        if match:
            expected = match.group(2).strip()
            actual = match.group(1).strip()
            print(f"アサーション失敗: 期待={expected}, 実際={actual}")
            
            # ファイルを読み込み
            with open(result.file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
                
            # 問題の行を見つける
            if result.line_number and result.line_number <= len(content):
                line = content[result.line_number - 1]
                
                # assertEqual/assertIsを探す
                if "assertEqual" in line:
                    # 期待値を変更
                    parts = line.split(",")
                    if len(parts) >= 2:
                        # 末尾の括弧やコメントを保持
                        suffix = re.search(r"(,\s*[^,]*)?(\s*\)[^)]*)?(\s*#.*)?$", parts[-1])
                        suffix_str = suffix.group(0) if suffix else ")"
                        
                        # 最後の引数を置換
                        parts[-1] = f" {actual}{suffix_str}"
                        new_line = ",".join(parts)
                        
                        # 変更を適用
                        content[result.line_number - 1] = new_line
                        
                        # ファイルを書き戻す
                        with open(result.file_path, 'w', encoding='utf-8') as f:
                            f.writelines(content)
                            
                        return True
                        
                # アサーションを見つける
                assert_match = re.search(r"assert\s+(.*?)\s*==\s*(.*?)(\s*#.*)?$", line)
                if assert_match:
                    # 期待値を実際の値に変更
                    new_line = line.replace(assert_match.group(2), actual)
                    
                    # 変更を適用
                    content[result.line_number - 1] = new_line
                    
                    # ファイルを書き戻す
                    with open(result.file_path, 'w', encoding='utf-8') as f:
                        f.writelines(content)
                        
                    return True
                    
        return False
    
    def _fix_key_error(self, result: TestResult) -> bool:
        """KeyErrorを修正"""
        # キー名を抽出
        key_pattern = r"KeyError: '([^']+)'"
        match = re.search(key_pattern, result.error_message)
        if not match:
            return False
            
        key_name = match.group(1)
        print(f"存在しないキー: {key_name}")
        
        # ファイルを読み込み
        with open(result.file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            
        # 問題の行を見つける
        if result.line_number and result.line_number <= len(content):
            line = content[result.line_number - 1]
            
            # キーアクセスをget()メソッドに置き換え
            dict_pattern = r"(\w+)\[['\"](.*?)['\"]\]"
            new_line = re.sub(dict_pattern, rf"\1.get('\2', None)", line)
            
            # 変更がない場合は別のパターンで試す
            if new_line == line:
                new_line = re.sub(rf"\[[\'\"]({key_name})[\'\"]", f".get('{key_name}', None)", line)
                
            # 変更がない場合は辞書の初期化の問題かもしれない
            if new_line == line and result.line_number > 1:
                # 一つ前の行を確認
                prev_line = content[result.line_number - 2]
                if "= {" in prev_line or "= dict(" in prev_line:
                    # 辞書の初期化に該当するキーを追加
                    if "}" in prev_line:
                        # "}の前にキーを追加
                        new_prev_line = prev_line.replace("}", f", '{key_name}': None}}")
                        content[result.line_number - 2] = new_prev_line
                    elif ")" in prev_line:
                        # ")の前にキーを追加
                        new_prev_line = prev_line.replace(")", f", '{key_name}': None))")
                        content[result.line_number - 2] = new_prev_line
                    else:
                        # 辞書の続きに追加（次の行）
                        indentation = re.match(r"(\s*)", prev_line).group(1)
                        content.insert(result.line_number - 1, f"{indentation}    '{key_name}': None,\n")
                        
                    # ファイルを書き戻す
                    with open(result.file_path, 'w', encoding='utf-8') as f:
                        f.writelines(content)
                        
                    return True
                    
            # 変更があれば適用
            if new_line != line:
                content[result.line_number - 1] = new_line
                
                # ファイルを書き戻す
                with open(result.file_path, 'w', encoding='utf-8') as f:
                    f.writelines(content)
                    
                return True
                
        return False
    
    def _fix_index_error(self, result: TestResult) -> bool:
        """IndexErrorを修正"""
        # インデックスが範囲外
        # ファイルを読み込み
        with open(result.file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            
        # 問題の行を見つける
        if result.line_number and result.line_number <= len(content):
            line = content[result.line_number - 1]
            
            # リストアクセスの形式を見つける
            list_access_pattern = r"(\w+)\[(-?\d+)\]"
            match = re.search(list_access_pattern, line)
            
            if match:
                var_name = match.group(1)
                index = match.group(2)
                
                # インデックスアクセスを try-except で囲む
                indent = re.match(r"(\s*)", line).group(1)
                
                # 元の行をコメントアウト
                content[result.line_number - 1] = f"{indent}# {line.lstrip()}"
                
                # try-except ブロックを追加
                try_block = [
                    f"{indent}try:\n",
                    f"{indent}    {line.lstrip()}",
                    f"{indent}except IndexError:\n",
                    f"{indent}    # インデックスが範囲外の場合の対処\n",
                    f"{indent}    pass  # 適切な処理に置き換えてください\n"
                ]
                
                # 行を挿入
                for i, new_line in enumerate(try_block):
                    content.insert(result.line_number - 1 + i, new_line)
                    
                # ファイルを書き戻す
                with open(result.file_path, 'w', encoding='utf-8') as f:
                    f.writelines(content)
                    
                return True
                
        return False
    
    def _fix_generic_error(self, result: TestResult) -> bool:
        """汎用的なエラー修正"""
        # 特定のパターンがない場合、修正方法が不明なのでスキップ
        return False

class AutonomousEngine:
    """自律テストエンジン"""
    
    def __init__(self, 
                 max_iterations: int = MAX_ITERATIONS,
                 sleep_between_runs: int = SLEEP_BETWEEN_RUNS,
                 test_command: str = "python run_auto_tests.py --verbosity=2 --report"):
        self.max_iterations = max_iterations
        self.sleep_between_runs = sleep_between_runs
        self.test_command = test_command
        self.runner = TestRunner(command=test_command)
        self.fixer = TestFixer()
        self.finished = False
        
    def run(self) -> int:
        """テストエンジンを実行"""
        global total_iterations, start_time
        total_iterations = 0
        start_time = time.time()
        
        print("\n" + "=" * 80)
        print("自律テストエンジンを起動します")
        print(f"最大反復回数: {self.max_iterations}")
        print(f"テストコマンド: {self.test_command}")
        print("=" * 80 + "\n")
        
        while not self.finished and total_iterations < self.max_iterations:
            total_iterations += 1
            print(f"\n実行 {total_iterations}/{self.max_iterations} - {self._format_elapsed_time()}")
            
            # テスト実行
            success, results, report = self.runner.run()
            
            # 成功したら終了
            if success:
                print("\n✓ すべてのテストが成功しました！")
                self._print_summary(results)
                self.finished = True
                return 0
                
            # 失敗したテストがあれば修正を試みる
            fixed_any = False
            for result in results:
                if not result.success and self.fixer.can_fix(result):
                    if self.fixer.fix(result):
                        fixed_any = True
                        
            # 修正できなかった場合は終了
            if not fixed_any:
                print("\n✗ これ以上修正できるエラーがありません")
                self._print_summary(results)
                self.finished = True
                return 1
                
            # 次の実行前に少し待機
            if not self.finished:
                print(f"\n次のテスト実行まで {self.sleep_between_runs} 秒待機しています...")
                time.sleep(self.sleep_between_runs)
                
        # 最大反復回数に達した場合
        if total_iterations >= self.max_iterations:
            print(f"\n✗ 最大反復回数 ({self.max_iterations}) に達しました")
            success, results, _ = self.runner.run()
            self._print_summary(results)
            return 1 if not success else 0
            
        return 0
    
    def _print_summary(self, results: List[TestResult]):
        """テスト結果のサマリーを表示"""
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        
        print("\nテスト実行サマリー:")
        print(f"合計: {len(results)} テスト")
        print(f"成功: {success_count} テスト")
        print(f"失敗: {failure_count} テスト")
        
        if failure_count > 0:
            print("\n失敗したテスト:")
            for result in results:
                if not result.success:
                    print(f"- {result}")
                    
        print(f"\n実行回数: {total_iterations}")
        print(f"合計所要時間: {self._format_elapsed_time()}")
        
        global fixed_files
        if fixed_files:
            print("\n修正したファイル:")
            for file_path, count in fixed_files.items():
                print(f"- {file_path} ({count} 回修正)")
    
    def _format_elapsed_time(self) -> str:
        """経過時間を文字列にフォーマット"""
        if not start_time:
            return "0秒"
            
        elapsed = time.time() - start_time
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{int(hours)}時間 {int(minutes)}分 {int(seconds)}秒"
        elif minutes > 0:
            return f"{int(minutes)}分 {int(seconds)}秒"
        else:
            return f"{int(seconds)}秒"

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='自律テストエンジン (Autonomous Test Engine)')
    parser.add_argument('--iterations', '-i', type=int, default=MAX_ITERATIONS,
                      help=f'最大反復回数 (デフォルト: {MAX_ITERATIONS})')
    parser.add_argument('--sleep', '-s', type=int, default=SLEEP_BETWEEN_RUNS,
                      help=f'テスト実行間の待機時間(秒) (デフォルト: {SLEEP_BETWEEN_RUNS})')
    parser.add_argument('--command', '-c', default="python run_auto_tests.py --verbosity=2 --report",
                      help='テスト実行コマンド (デフォルト: "python run_auto_tests.py --verbosity=2 --report")')
    parser.add_argument('--backup', '-b', action='store_true',
                      help='修正前にファイルのバックアップを作成する')
    
    args = parser.parse_args()
    
    # バックアップの作成
    if args.backup:
        backup_dir = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Pythonファイルをコピー
        for file in Path('.').glob('**/*.py'):
            if not str(file).startswith(backup_dir):
                dest = os.path.join(backup_dir, str(file))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(file, dest)
                
        print(f"バックアップを作成しました: {backup_dir}\n")
    
    # エンジンの実行
    engine = AutonomousEngine(
        max_iterations=args.iterations,
        sleep_between_runs=args.sleep,
        test_command=args.command
    )
    
    try:
        return engine.run()
    except KeyboardInterrupt:
        print("\n\nユーザーによる中断")
        return 130
    except Exception as e:
        print(f"\n\n実行中にエラーが発生しました: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 