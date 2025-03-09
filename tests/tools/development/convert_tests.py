"""
既存テスト変換スクリプト

このスクリプトは、既存のテストファイルを新しいGameTestBase基底クラスを
継承する形式に変換します。これにより、テスト環境の一貫性が保たれます。
"""

import os
import sys
import re
import argparse
import shutil

def find_test_files(directory='.'):
    """テストファイルを検索"""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith('test_') and file.endswith('.py') and not file.endswith('_new.py'):
                test_files.append(os.path.join(root, file))
    return test_files

def convert_test_file(file_path, backup=True):
    """テストファイルを新しい構造に変換"""
    print(f"変換中: {file_path}")
    
    # ファイルの内容を読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # バックアップを作成
    if backup:
        backup_path = f"{file_path}.bak"
        shutil.copy2(file_path, backup_path)
        print(f"バックアップ作成: {backup_path}")
    
    # 既存のインポート行を検出
    import_pattern = r'(import\s+[^\n]+)|(\s*from\s+[^\n]+)'
    imports = re.findall(import_pattern, content)
    imports = [imp[0] if imp[0] else imp[1] for imp in imports]
    
    # 既存のテストクラスを検出
    class_pattern = r'class\s+(\w+)\s*\(\s*(?:unittest\.)?TestCase\s*\):'
    class_matches = re.findall(class_pattern, content)
    
    if not class_matches:
        print(f"警告: テストクラスが見つかりません: {file_path}")
        return False
    
    # 変換済みか確認
    if 'from tests.unit.test_base import GameTestBase' in content:
        print(f"既に変換済み: {file_path}")
        return False
    
    # ファイル名からモジュール名を取得
    module_name = os.path.basename(file_path)
    module_name = os.path.splitext(module_name)[0]
    
    # docstringを抽出
    docstring_pattern = r'"""(.*?)"""'
    docstring_match = re.search(docstring_pattern, content, re.DOTALL)
    docstring = docstring_match.group(1).strip() if docstring_match else f"{module_name} のテスト"
    
    # 新しいファイル名を生成
    new_file_path = os.path.join(os.path.dirname(file_path), f"{module_name}_new.py")
    
    # 新しい内容を生成
    new_content = [
        f'"""',
        f'{docstring}',
        f'',
        f'GameTestBase基底クラスを継承した新しい構造のテストです。',
        f'"""',
        f'',
        f'import unittest',
        f'import sys',
        f'from tests.unit.test_base import GameTestBase',
        f'',
    ]
    
    # 元のimportを追加（unittest, sysを除く）
    for imp in imports:
        if 'unittest' not in imp and 'sys' not in imp:
            new_content.append(imp)
    
    # 元のクラスを基底クラスを使用するように変更
    for class_name in class_matches:
        # クラスの定義を基底クラスを継承するように変更
        class_pattern = f'class\\s+{class_name}\\s*\\(\\s*(?:unittest\\.)?TestCase\\s*\\):'
        content = re.sub(class_pattern, f'class {class_name}(GameTestBase):', content)
    
    # クラス以降の内容を追加
    class_start = re.search(f'class\\s+{class_matches[0]}', content).start()
    new_content.append(content[class_start:])
    
    # __main__セクションがなければ追加
    if '__name__' not in content:
        new_content.append('\n')
        new_content.append('if __name__ == "__main__":')
        new_content.append('    unittest.main()')
    
    # 新しいファイルを作成
    with open(new_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_content))
    
    print(f"変換完了: {new_file_path}")
    return True

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='既存のテストを新しい構造に変換')
    parser.add_argument('--dir', '-d', dest='directory', default='.',
                      help='テストファイルがあるディレクトリ (デフォルト: カレントディレクトリ)')
    parser.add_argument('--file', '-f', dest='file', default=None,
                      help='変換する特定のテストファイル')
    parser.add_argument('--no-backup', dest='no_backup', action='store_true',
                      help='バックアップを作成しない')
    
    args = parser.parse_args()
    
    # 特定のファイルのみを変換
    if args.file:
        if not os.path.exists(args.file):
            print(f"エラー: ファイルが見つかりません: {args.file}")
            return 1
        
        convert_test_file(args.file, not args.no_backup)
        return 0
    
    # すべてのテストファイルを検索して変換
    test_files = find_test_files(args.directory)
    if not test_files:
        print(f"テストファイルが見つかりませんでした: {args.directory}")
        return 1
    
    print(f"{len(test_files)}個のテストファイルが見つかりました")
    
    # 変換の実行
    converted = 0
    for file_path in test_files:
        if convert_test_file(file_path, not args.no_backup):
            converted += 1
    
    print(f"変換完了: {converted}/{len(test_files)} ファイルを変換しました")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 