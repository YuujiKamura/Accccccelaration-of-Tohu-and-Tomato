#!/usr/bin/env python
"""
テストバッチ実行スクリプト

指定されたディレクトリ内のすべてのテストファイルを検出し、
順次実行して結果を表示します。
進捗状況を分かりやすく表示します。
"""

import os
import sys
import time
import glob
import argparse
import unittest
import importlib.util
from contextlib import contextmanager
import io
from run_single_test import color_print, ProgressTestRunner, load_test_module

# カラー表示用コード
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
RESET = "\033[0m"
BOLD = "\033[1m"

class TestBatch:
    """テストバッチクラス"""
    
    def __init__(self, test_dir=None, pattern="test_*.py", exclude=None):
        """初期化"""
        self.test_dir = test_dir or os.path.join(os.getcwd(), "tests")
        self.pattern = pattern
        self.exclude = exclude or []
        self.test_files = []
        self.results = {}
        self.start_time = None
        self.total_tests = 0
        self.successes = 0
        self.failures = 0
        self.errors = 0
        self.skipped = 0
    
    def discover_tests(self):
        """テストファイルを検出"""
        if not os.path.exists(self.test_dir):
            color_print(f"エラー: テストディレクトリが見つかりません: {self.test_dir}", RED)
            return False
        
        # テストファイルを検出
        pattern_path = os.path.join(self.test_dir, "**", self.pattern)
        test_files = glob.glob(pattern_path, recursive=True)
        
        # 除外パターンを適用
        if self.exclude:
            filtered_files = []
            for file in test_files:
                if not any(excl in file for excl in self.exclude):
                    filtered_files.append(file)
            test_files = filtered_files
        
        if not test_files:
            color_print(f"警告: テストファイルが見つかりません: {pattern_path}", YELLOW)
            return False
        
        # 相対パスに変換
        self.test_files = [os.path.relpath(file) for file in test_files]
        
        # 検出結果を表示
        color_print(f"\n検出されたテストファイル: {len(self.test_files)}件", GREEN)
        for i, file in enumerate(self.test_files, 1):
            print(f"  {i}. {file}")
        
        return True
    
    def count_total_tests(self):
        """テスト総数をカウント"""
        total = 0
        for file in self.test_files:
            try:
                module = load_test_module(file)
                if module:
                    suite = unittest.TestLoader().loadTestsFromModule(module)
                    total += suite.countTestCases()
            except Exception as e:
                color_print(f"警告: {file} のテスト数カウント中にエラー: {e}", YELLOW)
        
        self.total_tests = total
        return total
    
    def run_all_tests(self):
        """すべてのテストを実行"""
        if not self.test_files:
            if not self.discover_tests():
                return False
        
        # テスト総数をカウント
        total_tests = self.count_total_tests()
        
        color_print("\n" + "=" * 70, GREEN)
        color_print(f"テストバッチ実行開始: {len(self.test_files)}ファイル, 合計{total_tests}テスト", GREEN, bold=True)
        color_print("=" * 70, GREEN)
        
        self.start_time = time.time()
        total_files = len(self.test_files)
        
        for i, file in enumerate(self.test_files, 1):
            # ファイルヘッダー
            color_print(f"\n[{i}/{total_files}] テストファイル: {file}", CYAN, bold=True)
            
            try:
                # テストモジュールのロード
                module = load_test_module(file)
                if not module:
                    self.results[file] = {
                        'success': False,
                        'error': 'モジュールのロードに失敗',
                        'tests': 0
                    }
                    continue
                
                # テストスイートの作成と実行
                suite = unittest.TestLoader().loadTestsFromModule(module)
                test_count = suite.countTestCases()
                
                # 時間計測
                file_start_time = time.time()
                
                # テスト実行
                runner = ProgressTestRunner()
                result = runner.run(suite)
                
                # 経過時間
                duration = time.time() - file_start_time
                
                # 結果の保存
                success = len(result.successes)
                failures = len(result.failures)
                errors = len(result.errors)
                skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
                
                self.successes += success
                self.failures += failures
                self.errors += errors
                self.skipped += skipped
                
                # ファイル単位の結果を保存
                self.results[file] = {
                    'success': result.wasSuccessful(),
                    'tests': test_count,
                    'passed': success,
                    'failures': failures,
                    'errors': errors,
                    'skipped': skipped,
                    'duration': duration
                }
                
                # ファイル単位の結果サマリー
                if result.wasSuccessful():
                    status = f"{GREEN}成功{RESET}"
                else:
                    status = f"{RED}失敗{RESET}"
                
                # 総合進捗
                elapsed = time.time() - self.start_time
                completed_tests = self.successes + self.failures + self.errors + self.skipped
                percent = (completed_tests / total_tests * 100) if total_tests > 0 else 0
                
                color_print(f"\n●  ファイル結果: {status} ({success}/{test_count}) - {duration:.2f}秒", 
                           GREEN if result.wasSuccessful() else RED)
                
                color_print("\n" + "-" * 50, BLUE)
                color_print(f"全体進捗: {percent:.1f}% ({completed_tests}/{total_tests}) - 経過時間: {elapsed:.2f}秒", BLUE)
                color_print("-" * 50, BLUE)
                
            except Exception as e:
                color_print(f"エラー: {file} の実行中に例外が発生しました: {e}", RED)
                self.results[file] = {
                    'success': False,
                    'error': str(e),
                    'tests': 0
                }
                self.errors += 1
        
        # すべての結果を表示
        self.show_summary()
        
        return self.failures == 0 and self.errors == 0
    
    def show_summary(self):
        """結果サマリーを表示"""
        if not self.results:
            color_print("警告: テスト結果がありません", YELLOW)
            return
        
        total_duration = time.time() - self.start_time
        
        color_print("\n" + "=" * 70, GREEN)
        color_print("テストバッチ実行完了", GREEN, bold=True)
        color_print("=" * 70, GREEN)
        
        color_print(f"\n実行時間: {total_duration:.2f}秒", BLUE)
        color_print(f"テストファイル: {len(self.test_files)}件", BLUE)
        
        # 成功率の計算
        total_tests = self.total_tests
        if total_tests > 0:
            success_rate = (self.successes / total_tests) * 100
            color_print(f"全テスト: {total_tests}件", BLUE)
            color_print(f"成功: {self.successes}件 ({success_rate:.1f}%)", 
                       GREEN if success_rate == 100 else YELLOW)
        else:
            color_print("テストが実行されていません", YELLOW)
        
        # 失敗とエラーがあれば表示
        if self.failures > 0:
            color_print(f"失敗: {self.failures}件", RED)
            # 失敗したファイルを表示
            for file, result in self.results.items():
                if result.get('failures', 0) > 0:
                    color_print(f"  - {file}: {result['failures']}件の失敗", RED)
        
        if self.errors > 0:
            color_print(f"エラー: {self.errors}件", RED)
            # エラーのあったファイルを表示
            for file, result in self.results.items():
                if result.get('errors', 0) > 0 or 'error' in result:
                    error_msg = result.get('error', f"{result.get('errors', 0)}件のエラー")
                    color_print(f"  - {file}: {error_msg}", RED)
        
        if self.skipped > 0:
            color_print(f"スキップ: {self.skipped}件", YELLOW)
        
        # 総合結果
        if self.failures == 0 and self.errors == 0:
            color_print("\n総合結果: すべてのテストが成功しました！", GREEN, bold=True)
        else:
            color_print("\n総合結果: テストに問題があります", RED, bold=True)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='テストバッチ実行スクリプト')
    parser.add_argument('--dir', help='テストディレクトリ', default=None)
    parser.add_argument('--pattern', help='テストファイルのパターン', default='test_*.py')
    parser.add_argument('--exclude', nargs='*', help='除外するファイルパターン', default=[])
    args = parser.parse_args()
    
    batch = TestBatch(args.dir, args.pattern, args.exclude)
    success = batch.run_all_tests()
    
    # 終了コードの設定
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 