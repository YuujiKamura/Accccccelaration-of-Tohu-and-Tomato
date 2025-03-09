#!/usr/bin/env python
"""
テストファイルをBaseTestCaseを継承するように変換するスクリプト

すべてのテストファイルを処理し、unittest.TestCaseからBaseTestCaseに変更し、
@log_testデコレータをテストメソッドに追加します。
"""

import os
import re
import glob
import argparse

def process_file(file_path, dry_run=False):
    """テストファイルを処理してBaseTestCaseを継承するように変換する"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # すでに変換されているかチェック
    if 'from tests.unit.test_base import BaseTestCase' in content:
        print(f"[スキップ] {file_path} は既に変換済みです")
        return False
    
    # インポート文を追加
    if 'import unittest' in content:
        content = content.replace(
            'import unittest',
            'import unittest\nfrom tests.unit.test_base import BaseTestCase, log_test'
        )
    else:
        content = 'import unittest\nfrom tests.unit.test_base import BaseTestCase, log_test\n' + content
    
    # TestCaseの継承を変更
    content = re.sub(
        r'class\s+(\w+)\s*\(\s*unittest\.TestCase\s*\)',
        r'class \1(BaseTestCase)',
        content
    )
    
    # setUpメソッドを検索して親クラスの呼び出しを追加
    setup_pattern = re.compile(r'def\s+setUp\s*\(\s*self\s*\):.*?:(\s+)(?=\w)', re.DOTALL)
    
    def setup_replacement(match):
        indent = match.group(1)
        return f'def setUp(self):{indent}super().setUp()  # 親クラスのsetUp()を呼び出す{indent}'
    
    content = setup_pattern.sub(setup_replacement, content)
    
    # テストメソッドを検索してデコレータを追加
    test_method_pattern = re.compile(r'(\s+)def\s+(test_\w+)')
    
    def test_method_replacement(match):
        indent = match.group(1)
        method_name = match.group(2)
        return f'{indent}@log_test\n{indent}def {method_name}'
    
    content = test_method_pattern.sub(test_method_replacement, content)
    
    if dry_run:
        print(f"[ドライラン] {file_path} を変換しました")
        print("-" * 40)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 40)
        return True
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[変換完了] {file_path}")
        return True

def process_all_test_files(test_dirs=None, pattern='test_*.py', dry_run=False):
    """すべてのテストファイルを処理する"""
    if test_dirs is None:
        # プロジェクトルートからの相対パス
        test_dirs = ['tests/unit', 'tests/integration_tests', 'tests/performance']
    
    modified_files = 0
    total_files = 0
    
    for test_dir in test_dirs:
        if not os.path.exists(test_dir):
            print(f"[警告] ディレクトリが見つかりません: {test_dir}")
            continue
        
        for test_file in glob.glob(os.path.join(test_dir, pattern)):
            total_files += 1
            if process_file(test_file, dry_run):
                modified_files += 1
    
    print(f"\n処理完了: {total_files} ファイル中 {modified_files} ファイルを変換しました")
    return modified_files

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='テストファイルをBaseTestCaseを継承するように変換するスクリプト')
    parser.add_argument('--dry-run', action='store_true', help='変更を適用せずに結果を表示する')
    parser.add_argument('--dirs', nargs='+', help='処理するディレクトリのリスト')
    parser.add_argument('--pattern', default='test_*.py', help='処理するファイルのパターン')
    args = parser.parse_args()
    
    print("テストファイル変換ツールを実行中...")
    process_all_test_files(
        test_dirs=args.dirs,
        pattern=args.pattern,
        dry_run=args.dry_run
    )

if __name__ == '__main__':
    main() 