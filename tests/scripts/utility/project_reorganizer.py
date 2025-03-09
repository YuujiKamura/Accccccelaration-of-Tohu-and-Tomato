import os
import sys
import shutil
import re
import ast
import logging
import subprocess
import time
import tempfile
from pathlib import Path
from datetime import datetime
import importlib.util
import argparse

# コマンドライン引数の処理
parser = argparse.ArgumentParser(description="プロジェクト再構成ツール")
parser.add_argument("--auto", action="store_true", help="自動モードで実行（確認なし）")
parser.add_argument("--keep-originals", action="store_true", help="元のファイルを保持する")
parser.add_argument("--dry-run", action="store_true", help="変更を実際に適用せずに実行計画を表示")
args = parser.parse_args()

# ロギングの設定
log_dir = "reorganization_logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"reorganization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Gitの存在を確認
GIT_AVAILABLE = False
try:
    result = subprocess.run(['git', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        GIT_AVAILABLE = True
        logging.info("Git検出: 変更の追跡に使用します")
except:
    logging.warning("Gitが見つかりません。バックアップに頼ります")

# バックアップから除外するディレクトリやファイル
EXCLUDE_FROM_BACKUP = [
    ".venv",
    "__pycache__",
    ".git",
    "backup_",
    "node_modules",
    ".pytest_cache"
]

# 新しいディレクトリ構造
NEW_DIRECTORY_STRUCTURE = {
    "src": {
        "game": {
            "core": {},
            "ui": {},
            "utils": {}
        },
        "common": {},
    },
    "tests": {
        "unit": {},
        "integration": {},
        "performance": {}
    },
    "docs": {
        "specs": {},
        "user_guides": {}
    },
    "scripts": {},
    "tools": {
        "analysis": {},
        "development": {}
    }
}

# 既存のadvertise_modeディレクトリは維持
if os.path.exists("advertise_mode"):
    NEW_DIRECTORY_STRUCTURE["advertise_mode"] = {}

# ファイル移動計画
FILE_MOVE_PLAN = [
    # ゲームのメインファイル
    {"src": "main.py", "dest": "src/game/core/main.py"},
    
    # ゲーム関連ファイル
    {"src": "game_logic.py", "dest": "src/game/core/game_logic.py"},
    {"src": "enemy_v2.py", "dest": "src/game/core/enemy.py", "alternatives": ["enemy.py"]},
    {"src": "player_v2.py", "dest": "src/game/core/player.py", "alternatives": ["player.py"]},
    {"src": "bullet_v2.py", "dest": "src/game/core/bullet.py", "alternatives": ["bullet.py"]},
    {"src": "dash_spec.py", "dest": "src/game/core/dash_spec.py"},
    {"src": "player_dash_spec.py", "dest": "src/game/core/player_dash_spec.py"},
    
    # UI関連
    {"src": "ui_components.py", "dest": "src/game/ui/ui_components.py"},
    {"src": "game_screens.py", "dest": "src/game/ui/game_screens.py"},
    
    # ユーティリティ
    {"src": "utils.py", "dest": "src/common/utils.py", "alternatives": []},
    {"src": "config.py", "dest": "src/common/config.py", "alternatives": []},
    {"src": "constants.py", "dest": "src/common/constants.py", "alternatives": []},
    
    # テスト
    {"src": "test_base.py", "dest": "tests/unit/test_base.py"},
    {"src": "test_basic.py", "dest": "tests/unit/test_basic.py"},
    {"src": "test_basic_new.py", "dest": "tests/unit/test_basic_new.py"},
    {"src": "test_dash.py", "dest": "tests/unit/test_dash.py"},
    {"src": "test_dash_new.py", "dest": "tests/unit/test_dash_new.py"},
    {"src": "test_dash_new_v2.py", "dest": "tests/unit/test_dash_new_v2.py"},
    {"src": "test_enemy_v2.py", "dest": "tests/unit/test_enemy.py", "alternatives": ["test_enemy.py"]},
    {"src": "test_player_v2.py", "dest": "tests/unit/test_player.py", "alternatives": ["test_player.py"]},
    {"src": "test_bullet_v2.py", "dest": "tests/unit/test_bullet.py", "alternatives": ["test_bullet.py"]},
    {"src": "test_game_logic.py", "dest": "tests/unit/test_game_logic.py"},
    {"src": "test_game_logic_advanced.py", "dest": "tests/unit/test_game_logic_advanced.py"},
    {"src": "test_performance.py", "dest": "tests/performance/test_performance.py"},
    
    # テストユーティリティ
    {"src": "pygame_mock.py", "dest": "tests/unit/pygame_mock.py"},
    {"src": "test_dependency.py", "dest": "tests/unit/test_dependency.py"},
    {"src": "test_mock_classes.py", "dest": "tests/unit/test_mock_classes.py"},
    
    # スクリプト
    {"src": "run_tests.py", "dest": "scripts/run_tests.py"},
    {"src": "run_tests.bat", "dest": "scripts/run_tests.bat"},
    {"src": "run_auto_tests.py", "dest": "scripts/run_auto_tests.py"},
    {"src": "run_auto_tests.bat", "dest": "scripts/run_auto_tests.bat"},
    {"src": "run_game.bat", "dest": "scripts/run_game.bat", "alternatives": []},
    {"src": "watch_tests.py", "dest": "scripts/watch_tests.py"},
    {"src": "watch_tests.bat", "dest": "scripts/watch_tests.bat"},
    {"src": "run_single_test.py", "dest": "scripts/run_single_test.py"},
    {"src": "run_single_test.bat", "dest": "scripts/run_single_test.bat"},
    
    # ツール
    {"src": "autonomous_test_engine.py", "dest": "tools/development/autonomous_test_engine.py"},
    {"src": "autonomous_test_engine_v2.py", "dest": "tools/development/autonomous_test_engine_v2.py"},
    {"src": "performance_analyzer.py", "dest": "tools/analysis/performance_analyzer.py"},
    {"src": "test_report.py", "dest": "tools/analysis/test_report.py"},
    {"src": "test_prioritizer.py", "dest": "tools/analysis/test_prioritizer.py"},
    {"src": "test_scheduler.py", "dest": "tools/analysis/test_scheduler.py"},
    
    # ドキュメント
    {"src": "TESTING_README.md", "dest": "docs/TESTING_README.md"},
]

class ImportUpdater:
    """インポートパスの更新を処理するクラス"""
    
    def __init__(self, moved_files):
        self.moved_files = moved_files
        self.updated_files = 0
        self.failed_files = 0
    
    def _get_module_name(self, file_path):
        """ファイルパスからモジュール名を取得"""
        rel_path = os.path.relpath(file_path)
        module_path = rel_path.replace(os.path.sep, '.').replace('.py', '')
        
        # src/game/core/main.py → src.game.core.main
        return module_path
    
    def _convert_file_path_to_module(self, filepath):
        """ファイルパスをインポート可能なモジュールパスに変換"""
        if filepath.endswith(".py"):
            return filepath[:-3].replace("/", ".").replace("\\", ".")
        return filepath.replace("/", ".").replace("\\", ".")
    
    def _get_original_module(self, src_file):
        """元のソースファイルのモジュール名を取得"""
        if src_file.endswith(".py"):
            return src_file[:-3]
        return src_file
    
    def _create_import_mapping(self):
        """移動されたファイルの古い→新しいインポートパスのマッピングを作成"""
        mapping = {}
        
        for file_info in self.moved_files:
            src = file_info["src"]
            dest = file_info["dest"]
            
            src_module = self._get_original_module(src)
            dest_module = self._convert_file_path_to_module(dest)
            
            mapping[src_module] = dest_module
            
            # 代替名も追加
            if "alternatives" in file_info and file_info["alternatives"]:
                for alt in file_info["alternatives"]:
                    alt_module = self._get_original_module(alt)
                    mapping[alt_module] = dest_module
        
        return mapping
    
    def update_imports(self):
        """プロジェクト内のすべてのPythonファイルのインポートを更新"""
        import_mapping = self._create_import_mapping()
        
        # インポートのパターン
        # from X import Y
        # import X as Y
        # import X.Y.Z
        from_import_pattern = re.compile(r'from\s+([\w.]+)\s+import')
        import_pattern = re.compile(r'import\s+([\w.]+)(?:\s+as\s+[\w]+)?')
        
        # 処理するファイルを収集
        python_files = []
        for root, _, files in os.walk("."):
            if any(exclude in root for exclude in EXCLUDE_FROM_BACKUP):
                continue
                
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
        
        # 各ファイルのインポートを更新
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # ファイルが空または読み取れない場合はスキップ
                if not content.strip():
                    continue
                
                modified = False
                lines = content.split('\n')
                updated_lines = []
                
                for line in lines:
                    updated_line = line
                    
                    # from X import Y の形式
                    for match in from_import_pattern.finditer(line):
                        module = match.group(1)
                        
                        # モジュールが更新対象かチェック
                        if module in import_mapping:
                            new_module = import_mapping[module]
                            updated_line = line.replace(f"from {module} import", f"from {new_module} import")
                            modified = True
                            
                    # import X, import X.Y.Z, import X as Y の形式
                    for match in import_pattern.finditer(line):
                        module = match.group(1)
                        
                        # 完全一致または先頭部分一致をチェック
                        for old_module, new_module in import_mapping.items():
                            if module == old_module or module.startswith(old_module + "."):
                                suffix = module[len(old_module):] if module.startswith(old_module + ".") else ""
                                updated_line = line.replace(f"import {module}", f"import {new_module}{suffix}")
                                modified = True
                                break
                    
                    updated_lines.append(updated_line)
                
                # 変更があれば保存
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(updated_lines))
                    
                    self.updated_files += 1
                    
            except Exception as e:
                logging.error(f"インポート更新中にエラー ({file_path}): {str(e)}")
                self.failed_files += 1
        
        logging.info(f"{self.updated_files}個の残りのファイルのインポートパスを更新しました")
        if self.failed_files > 0:
            logging.warning(f"{self.failed_files}個のファイルの更新に失敗しました")

class ProjectReorganizer:
    """プロジェクト再構成を管理するクラス"""
    
    def __init__(self):
        self.backup_dir = self._create_backup_dir()
        self.moved_files = []
        self.success_count = 0
        self.fail_count = 0
        self.errors = []
    
    def _create_backup_dir(self):
        """バックアップディレクトリを作成"""
        backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logging.info(f"バックアップディレクトリを作成: {backup_dir}")
        
        if args.dry_run:
            logging.info("ドライラン: バックアップはスキップされます")
            return backup_dir
            
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            # 重要なファイルをバックアップ
            self._backup_files(backup_dir)
            logging.info("バックアップが完了しました")
        except Exception as e:
            logging.error(f"バックアップエラー: {str(e)}")
            
        return backup_dir
    
    def _backup_files(self, backup_dir):
        """プロジェクトファイルをバックアップ"""
        for root, dirs, files in os.walk(".", topdown=True):
            # 除外ディレクトリのフィルタリング
            dirs[:] = [d for d in dirs if not any(exclude in d for exclude in EXCLUDE_FROM_BACKUP)]
            
            if any(exclude in root for exclude in EXCLUDE_FROM_BACKUP):
                continue
                
            # 相対パスを作成
            rel_path = os.path.relpath(root, ".")
            if rel_path == ".":
                rel_path = ""
                
            # バックアップディレクトリ内の対応するパスを作成
            backup_path = os.path.join(backup_dir, rel_path) if rel_path else backup_dir
            os.makedirs(backup_path, exist_ok=True)
            
            # ファイルをコピー
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(backup_path, file)
                
                try:
                    shutil.copy2(src_file, dest_file)
                except Exception as e:
                    logging.warning(f"ファイルのバックアップに失敗: {src_file} - {str(e)}")
    
    def _create_directory_structure(self):
        """新しいディレクトリ構造を作成"""
        def create_directories(parent_path, structure):
            for dir_name, sub_dirs in structure.items():
                dir_path = os.path.join(parent_path, dir_name)
                
                if args.dry_run:
                    logging.info(f"ドライラン: ディレクトリ作成: {dir_path}")
                    continue
                    
                os.makedirs(dir_path, exist_ok=True)
                logging.info(f"ディレクトリ作成: {dir_path}")
                
                # __init__.py ファイルを作成（Pythonパッケージとして認識されるため）
                if dir_name not in ["docs", "scripts"] and dir_path.endswith(os.path.sep) is False:
                    init_file = os.path.join(dir_path, "__init__.py")
                    if not os.path.exists(init_file):
                        with open(init_file, 'w', encoding='utf-8') as f:
                            f.write("# このディレクトリはPythonパッケージです\n")
                
                # サブディレクトリを再帰的に作成
                create_directories(dir_path, sub_dirs)
        
        create_directories(".", NEW_DIRECTORY_STRUCTURE)
        logging.info("ディレクトリ構造の作成完了")
    
    def _move_files(self):
        """ファイルを移動計画に従って移動"""
        # 実際に存在するファイルを特定
        existing_files = []
        
        for file_info in FILE_MOVE_PLAN:
            src = file_info["src"]
            dest = file_info["dest"]
            
            # 元ファイルの存在チェック
            if os.path.exists(src):
                existing_files.append(file_info)
                continue
                
            # 代替ファイルの存在チェック
            if "alternatives" in file_info:
                found = False
                for alt in file_info["alternatives"]:
                    if os.path.exists(alt):
                        # 代替ファイルが見つかった場合、情報を更新
                        existing_files.append({"src": alt, "dest": dest})
                        found = True
                        break
                        
                if found:
                    continue
            
            logging.warning(f"ファイルが見つかりません: {src}")
        
        logging.info(f"{len(existing_files)}個のファイルが移動対象として特定されました")
        
        # ドライランモードの場合
        if args.dry_run:
            for file_info in existing_files:
                src = file_info["src"]
                dest = file_info["dest"]
                logging.info(f"ドライラン: ファイル移動: {src} → {dest}")
            return existing_files
        
        # ファイルの移動実行
        for file_info in existing_files:
            src = file_info["src"]
            dest = file_info["dest"]
            
            try:
                # 移動先ディレクトリの存在確認
                dest_dir = os.path.dirname(dest)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)
                
                # ファイルコピー
                shutil.copy2(src, dest)
                
                # 構文チェック（.pyファイルの場合）
                if dest.endswith(".py"):
                    try:
                        with open(dest, 'r', encoding='utf-8') as f:
                            content = f.read()
                            ast.parse(content)
                    except SyntaxError:
                        logging.error(f"構文エラー: {dest}")
                        os.remove(dest)
                        self.fail_count += 1
                        continue
                        
                self.moved_files.append(file_info)
                self.success_count += 1
                logging.info(f"ファイル移動完了: {src} -> {dest}")
                
            except Exception as e:
                logging.error(f"ファイル移動エラー {src} -> {dest}: {str(e)}")
                self.fail_count += 1
                self.errors.append(f"{src}: {str(e)}")
        
        logging.info(f"{self.success_count}個のファイルが正常に移動されました")
        if self.fail_count > 0:
            logging.warning(f"{self.fail_count}個のファイルの移動に失敗しました")
            
        return self.moved_files
    
    def _update_imports(self, moved_files):
        """移動したファイルの参照を更新"""
        if args.dry_run:
            logging.info("ドライラン: インポートパス更新はスキップされます")
            return
            
        updater = ImportUpdater(moved_files)
        updater.update_imports()
    
    def _create_execution_scripts(self):
        """実行スクリプトを作成/更新"""
        if args.dry_run:
            logging.info("ドライラン: 実行スクリプト作成はスキップされます")
            return
            
        # ゲーム実行スクリプト
        run_game_bat = os.path.join("scripts", "run_game.bat")
        if not os.path.exists(run_game_bat):
            with open(run_game_bat, 'w') as f:
                f.write('@echo off\n')
                f.write('cd %~dp0..\n')
                f.write('python -m src.game.core.main\n')
                f.write('pause\n')
            logging.info(f"実行スクリプトを作成: {run_game_bat}")
        
        # テスト実行スクリプト
        run_tests_bat = os.path.join("scripts", "run_tests.bat")
        if not os.path.exists(run_tests_bat):
            with open(run_tests_bat, 'w') as f:
                f.write('@echo off\n')
                f.write('cd %~dp0..\n')
                f.write('python -m scripts.run_tests\n')
                f.write('pause\n')
            logging.info(f"実行スクリプトを作成: {run_tests_bat}")
    
    def cleanup_old_files(self, confirmed=False):
        """移動が完了した元ファイルを削除"""
        if args.dry_run:
            logging.info("ドライラン: 元ファイル削除はスキップされます")
            return
            
        if not confirmed and not args.auto:
            return
            
        removed_count = 0
        
        for file_info in self.moved_files:
            src = file_info["src"]
            if os.path.exists(src):
                try:
                    os.remove(src)
                    removed_count += 1
                    logging.info(f"元ファイルを削除: {src}")
                except Exception as e:
                    logging.error(f"ファイル削除エラー {src}: {str(e)}")
        
        logging.info(f"{removed_count}個の元ファイルを削除しました")
    
    def run(self):
        """再構成処理の実行"""
        try:
            logging.info("プロジェクト自動再構成を開始")
            
            # 1. ディレクトリ構造の作成
            self._create_directory_structure()
            
            # 2. ファイルの移動
            moved_files = self._move_files()
            
            # 3. インポートパスの更新
            self._update_imports(moved_files)
            
            # 4. 実行スクリプトの作成/更新
            self._create_execution_scripts()
            
            # 5. 元ファイルの削除（自動モードまたは確認済みの場合）
            if args.auto and not args.keep_originals and not args.dry_run:
                self.cleanup_old_files(confirmed=True)
            
            logging.info("プロジェクト自動再構成が完了しました")
            return True
            
        except Exception as e:
            logging.error(f"再構成中に重大なエラーが発生: {str(e)}")
            return False

def interactive_restore(backup_dir):
    """バックアップからの対話的復元"""
    print("\n" + "="*50)
    print("エラーが発生しました。バックアップから復元しますか？")
    choice = input("復元する? (y/n): ").strip().lower()
    
    if choice == 'y':
        try:
            # バックアップから復元（実装省略）
            print("復元処理は実装されていません。手動でバックアップから復元してください。")
            print(f"バックアップディレクトリ: {backup_dir}")
        except Exception as e:
            logging.error(f"復元中にエラー: {str(e)}")
            print("復元に失敗しました。手動で復元してください。")

def main():
    """メイン実行関数"""
    if args.dry_run:
        print("="*50)
        print("プロジェクト再構成ドライラン")
        print("="*50)
        print("注意: これはシミュレーションモードです。実際の変更は行われません。")
        
        reorganizer = ProjectReorganizer()
        reorganizer.run()
        
        print("\n"+"="*50)
        print("ドライランが完了しました。")
        print(f"ログファイル: {log_file}")
        print("実際に適用するには --dry-run オプションを外して再実行してください。")
        
    elif args.auto:
        print("="*50)
        print("完全自動プロジェクト再構成ツール実行中...")
        print("="*50)
        
        # 確認不要で実行
        reorganizer = ProjectReorganizer()
        success = reorganizer.run()
        
        if success:
            print("\n"+"="*50)
            print("プロジェクト再構成が完了しました。")
            print(f"ログファイル: {log_file}")
            print(f"バックアップ: {reorganizer.backup_dir}")
        else:
            print("\n"+"="*50)
            print("エラーが発生しました。ログを確認してください。")
            print(f"ログファイル: {log_file}")
            print(f"バックアップ: {reorganizer.backup_dir}")
    
    else:
        print("="*50)
        print("プロジェクト再構成ツール")
        print("="*50)
        print("注意: このツールはプロジェクトの構造を変更します。")
        print("進める前に作業中のファイルを保存してください。")
        print("\n処理内容:")
        print("1. バックアップを作成")
        print("2. 新しいディレクトリ構造を作成")
        print("3. ファイルを解析")
        print("4. ファイルを移動し、インポートパスを自動更新")
        print("5. 実行スクリプトを更新")
        
        confirm = input("\n続行しますか？ (y/n): ").strip().lower()
        if confirm == 'y':
            reorganizer = ProjectReorganizer()
            success = reorganizer.run()
            
            if success:
                print("\n"+"="*50)
                print("プロジェクト再構成が完了しました。")
                print(f"ログファイル: {log_file}")
                
                if not args.keep_originals:
                    delete_confirm = input("\n元のファイルを削除しますか？ (y/n): ").strip().lower()
                    if delete_confirm == 'y':
                        reorganizer.cleanup_old_files(confirmed=True)
                        print("元のファイルを削除しました。")
                    else:
                        print("元のファイルは保持されています。")
            else:
                print("\n"+"="*50)
                print("エラーが発生しました。ログを確認してください。")
                print(f"ログファイル: {log_file}")
                print("\nバックアップは次の場所にあります: " + reorganizer.backup_dir)
                
                # 重大なエラーの場合、復元オプションを提供
                if reorganizer.errors:
                    interactive_restore(reorganizer.backup_dir)
        else:
            print("操作がキャンセルされました。")

if __name__ == "__main__":
    main() 