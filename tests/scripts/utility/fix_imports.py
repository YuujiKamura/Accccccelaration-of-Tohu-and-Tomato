"""
テストファイルのインポートパスを一括で修正するスクリプト

このスクリプトは、テストファイルのインポートパスを修正し、
プロジェクトのモジュール構造に合わせて更新します。
"""

import os
import re
import sys
import glob

def fix_file_imports(file_path, dry_run=False):
    """
    ファイルのインポートパスを修正する
    
    Args:
        file_path (str): 修正するファイルのパス
        dry_run (bool): Trueの場合、変更を実際に適用せずに表示のみ行う
    
    Returns:
        bool: 変更が行われた場合はTrue、変更なしの場合はFalse
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 元のコンテンツを保存
    original_content = content
    
    # インポートパターンを定義
    patterns = [
        # 直接インポート -> 絶対パスインポート
        (r'from test_mock_classes import', 'from tests.unit.test_mock_classes import'),
        (r'from test_base import', 'from tests.unit.test_base import'),
        (r'from dash_spec import', 'from src.game.core.dash_spec import'),
        (r'from player_dash_spec import', 'from src.game.core.player_dash_spec import'),
        (r'from parameterized import', 'from parameterized import'),
        
        # mainモジュール関連のインポート
        (r'import main\b', 'import src.game.core.main as main'),
        (r'from main import', 'from src.game.core.main import'),
        
        # game_logicモジュール関連のインポート
        (r'import game_logic\b', 'import src.game.core.game_logic as game_logic'),
        (r'from game_logic import', 'from src.game.core.game_logic import'),
        
        # src.game.core.mainからの直接インポート
        (r'from src\.game\.core\.main import (.+)(, SCREEN_WIDTH, SCREEN_HEIGHT)', r'from src.game.core.main import \1\2'),
        
        # 日本語コメント中のハイフン修正（SPEC-XXX -> SPEC_XXX）
        (r'\[SPEC-([A-Z0-9]+)-([0-9]+)\]', r'[SPEC_\1_\2]'),
        
        # 日本語のコメントや文字列内の非ASCII文字を修正
        (r'。', '.'),
        (r'、', ','),
        (r'・', '-'),
        
        # モジュールパス修正
        (r'from tests\.unit\.test_mock_classes import', 'from tests.unit.test_mock_classes import'),
    ]
    
    # パターンに基づいて置換
    for old_pattern, new_pattern in patterns:
        content = re.sub(old_pattern, new_pattern, content)
    
    # 特殊なインポート修正 - 不正なimportパスがあるケース
    if "from tests.unit.pygame_mock import install_tests.unit.pygame_mock" in content:
        content = content.replace(
            "from tests.unit.pygame_mock import install_tests.unit.pygame_mock",
            "from tests.unit.pygame_mock import install_pygame_mock"
        )
    
    # 変更があったかどうか
    has_changes = content != original_content
    
    if has_changes:
        print(f"修正: {file_path}")
        
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    else:
        print(f"変更なし: {file_path}")
    
    return has_changes

def process_all_test_files(test_dirs=None, file_pattern="test_*.py", dry_run=False):
    """
    指定したディレクトリ内のすべてのテストファイルを処理する
    
    Args:
        test_dirs (list): 処理するディレクトリのリスト
        file_pattern (str): 処理するファイルパターン
        dry_run (bool): Trueの場合、変更を実際に適用せずに表示のみ行う
    
    Returns:
        tuple: (処理されたファイル数, 変更されたファイル数)
    """
    if test_dirs is None:
        # デフォルトではtestsディレクトリとその下のディレクトリを対象にする
        test_dirs = ['tests', 'tests/unit', 'tests/integration', 'tests/performance', 'advertise_mode']
    
    processed_files = 0
    changed_files = 0
    
    for test_dir in test_dirs:
        if not os.path.exists(test_dir):
            print(f"ディレクトリが見つかりません: {test_dir}")
            continue
        
        pattern = os.path.join(test_dir, file_pattern)
        for file_path in glob.glob(pattern):
            processed_files += 1
            if fix_file_imports(file_path, dry_run):
                changed_files += 1
    
    return processed_files, changed_files

def add_init_files(dirs=None, dry_run=False):
    """
    必要な__init__.pyファイルを追加する
    
    Args:
        dirs (list): 処理するディレクトリのリスト
        dry_run (bool): Trueの場合、変更を実際に適用せずに表示のみ行う
    
    Returns:
        int: 作成された__init__.pyファイルの数
    """
    if dirs is None:
        dirs = [
            'src', 'src/game', 'src/game/core', 'src/game/ui', 'src/game/utils', 'src/common',
            'tests', 'tests/unit', 'tests/integration', 'tests/performance'
        ]
    
    created_files = 0
    
    for directory in dirs:
        if not os.path.exists(directory):
            print(f"ディレクトリが見つかりません: {directory}")
            continue
        
        init_file = os.path.join(directory, '__init__.py')
        if not os.path.exists(init_file):
            print(f"__init__.pyを作成: {init_file}")
            
            if not dry_run:
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write("# Pythonパッケージとして認識させるための空ファイル\n")
            
            created_files += 1
        else:
            print(f"既存の__init__.pyをスキップ: {init_file}")
    
    return created_files

def fix_test_run_script(script_path='scripts/run_tests.py', dry_run=False):
    """
    テスト実行スクリプトを修正する
    
    Args:
        script_path (str): 修正するスクリプトのパス
        dry_run (bool): Trueの場合、変更を実際に適用せずに表示のみ行う
    
    Returns:
        bool: 変更が行われた場合はTrue、変更なしの場合はFalse
    """
    if not os.path.exists(script_path):
        print(f"スクリプトが見つかりません: {script_path}")
        return False
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 元のコンテンツを保存
    original_content = content
    
    # プロジェクトルートのパスをPythonパスに追加するコードを挿入
    python_path_setup = """
# パスの設定 - プロジェクトルートを追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
"""
    
    # パスの設定コードが既に存在するか確認
    if "sys.path.insert(0, project_root)" not in content:
        # import宣言の後にコードを挿入
        content = re.sub(
            r'(from collections import defaultdict\s+)',
            r'\1\n' + python_path_setup + '\n',
            content
        )
    
    # 変更があったかどうか
    has_changes = content != original_content
    
    if has_changes:
        print(f"修正: {script_path}")
        
        if not dry_run:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
    else:
        print(f"変更なし: {script_path}")
    
    return has_changes

def main():
    """
    メイン実行関数
    """
    print("インポートパス修正ツールを実行しています...")
    
    # コマンドライン引数を解析
    import argparse
    parser = argparse.ArgumentParser(description="テストファイルのインポートパスを一括修正します")
    parser.add_argument("--dry-run", action="store_true", help="変更を適用せずに何が行われるかを表示します")
    parser.add_argument("--skip-init", action="store_true", help="__init__.pyファイルの作成をスキップします")
    args = parser.parse_args()
    
    # __init__.pyファイルの追加
    if not args.skip_init:
        created_init_files = add_init_files(dry_run=args.dry_run)
        print(f"{created_init_files}個の__init__.pyファイルを作成しました")
    
    # テスト実行スクリプトの修正
    fix_test_run_script(dry_run=args.dry_run)
    
    # すべてのテストファイルを処理
    processed, changed = process_all_test_files(dry_run=args.dry_run)
    
    print(f"\n処理完了: {processed}個のファイルを処理し、{changed}個のファイルを修正しました")
    
    if args.dry_run:
        print("ドライランモードでした。変更は適用されていません。")
        print("実際に変更を適用するには、--dry-runオプションを外して再実行してください。")

if __name__ == "__main__":
    main() 