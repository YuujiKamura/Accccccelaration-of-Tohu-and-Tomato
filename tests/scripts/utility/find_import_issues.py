#!/usr/bin/env python
"""
インポートの問題や重複コードを検出するスクリプト

このスクリプトは、テストファイル内のインポート文や重複コードを検出します。
循環参照や重複したクラス定義などを特定し、問題の解決に役立てます。
"""

import os
import sys
import re
import glob
from collections import defaultdict

# カラー表示用コード
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"
BOLD = "\033[1m"

def color_print(text, color=RESET, bold=False):
    """カラー付きで文字列を出力"""
    prefix = BOLD if bold else ""
    print(f"{prefix}{color}{text}{RESET}")

def find_imports(file_path):
    """ファイル内のインポート文を検出"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # importとfrom import文を検出
        import_pattern = re.compile(r'^\s*import\s+(.+?)(?:\s+as\s+.+?)?$', re.MULTILINE)
        from_import_pattern = re.compile(r'^\s*from\s+(.+?)\s+import\s+(.+?)(?:\s+as\s+.+?)?$', re.MULTILINE)
        
        # 通常のimport文
        for match in import_pattern.finditer(content):
            modules = match.group(1).split(',')
            for module in modules:
                imports.append(module.strip())
        
        # from import文
        for match in from_import_pattern.finditer(content):
            module = match.group(1).strip()
            imports.append(module)
        
        return imports
    except Exception as e:
        color_print(f"エラー: {file_path} の解析中に例外が発生しました: {e}", RED)
        return []

def find_duplicate_classes(file_path):
    """ファイル内の重複したクラス定義を検出"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # クラス定義を検出
        class_pattern = re.compile(r'^\s*class\s+([A-Za-z0-9_]+)', re.MULTILINE)
        classes = []
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            classes.append(class_name)
        
        # 重複を検出
        duplicates = []
        seen = set()
        for cls in classes:
            if cls in seen:
                duplicates.append(cls)
            else:
                seen.add(cls)
        
        return duplicates
    except Exception as e:
        color_print(f"エラー: {file_path} の解析中に例外が発生しました: {e}", RED)
        return []

def find_duplicate_code_blocks(file_path, min_lines=5):
    """ファイル内の重複したコードブロックを検出"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # コードブロックを収集
        blocks = {}
        for i in range(len(lines) - min_lines + 1):
            block = ''.join(lines[i:i + min_lines])
            if block not in blocks:
                blocks[block] = []
            blocks[block].append(i + 1)  # 1-indexedの行番号
        
        # 重複ブロックのみ抽出
        duplicates = {block: positions for block, positions in blocks.items() if len(positions) > 1}
        
        return duplicates
    except Exception as e:
        color_print(f"エラー: {file_path} の解析中に例外が発生しました: {e}", RED)
        return {}

def detect_circular_imports(files):
    """循環インポートを検出"""
    imports_map = {}
    
    # 各ファイルのインポートを記録
    for file in files:
        imports = find_imports(file)
        file_module = os.path.splitext(os.path.basename(file))[0]
        imports_map[file_module] = imports
    
    # 循環参照を検出
    circular_refs = []
    for module, imports in imports_map.items():
        for imported in imports:
            if imported in imports_map and module in imports_map.get(imported, []):
                circular_refs.append((module, imported))
    
    return circular_refs

def get_file_size(file_path):
    """ファイルサイズを取得"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def calculate_avg_line_length(file_path):
    """平均行長を計算"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if not lines:
            return 0
        total_length = sum(len(line) for line in lines)
        return total_length / len(lines)
    except:
        return 0

def find_unusual_files(test_dir=None, pattern="*.py"):
    """
    異常なファイルを検出
    
    Args:
        test_dir: テストディレクトリ
        pattern: ファイルパターン
    """
    if test_dir is None:
        test_dir = os.path.join(os.getcwd(), "tests")
    
    pattern_path = os.path.join(test_dir, "**", pattern)
    files = glob.glob(pattern_path, recursive=True)
    
    if not files:
        color_print(f"ファイルが見つかりません: {pattern_path}", RED)
        return
    
    # 結果を格納するデータ構造
    results = {
        'circular_imports': [],
        'duplicate_classes': defaultdict(list),
        'large_files': [],
        'duplicate_code': defaultdict(list),
        'anomalies': []
    }
    
    # 各ファイルの解析
    color_print(f"\n{len(files)}個のファイルを解析中...", BLUE)
    
    # ファイルサイズの統計
    file_sizes = [get_file_size(file) for file in files]
    if file_sizes:
        avg_size = sum(file_sizes) / len(file_sizes)
        std_dev = (sum((size - avg_size) ** 2 for size in file_sizes) / len(file_sizes)) ** 0.5
        size_threshold = avg_size + 2 * std_dev
    else:
        size_threshold = 10000  # デフォルト値
    
    # 循環インポートの検出
    color_print("\n循環インポートを検出中...", BLUE)
    circular_refs = detect_circular_imports(files)
    if circular_refs:
        color_print(f"🔄 循環インポートが検出されました: {len(circular_refs)}件", RED, bold=True)
        for module1, module2 in circular_refs:
            print(f"   {module1} ⟷ {module2}")
            results['circular_imports'].append((module1, module2))
    else:
        color_print("✅ 循環インポートはありません", GREEN)
    
    # 個々のファイルの問題を検出
    color_print("\n各ファイルの問題を検出中...", BLUE)
    for file in files:
        rel_path = os.path.relpath(file)
        file_size = get_file_size(file)
        
        # 大きなファイルを検出
        if file_size > size_threshold:
            color_print(f"📁 特大ファイル: {rel_path} ({file_size / 1024:.1f}KB)", YELLOW)
            results['large_files'].append((rel_path, file_size))
        
        # 重複クラスを検出
        duplicate_classes = find_duplicate_classes(file)
        if duplicate_classes:
            color_print(f"🔍 重複クラス in {rel_path}: {', '.join(duplicate_classes)}", RED)
            results['duplicate_classes'][rel_path].extend(duplicate_classes)
        
        # 重複コードブロックを検出
        duplicate_blocks = find_duplicate_code_blocks(file)
        if duplicate_blocks:
            color_print(f"🔍 重複コードブロック in {rel_path}: {len(duplicate_blocks)}件", RED)
            for block, positions in duplicate_blocks.items():
                snippet = block.split('\n')[0].strip()[:40] + "..."
                results['duplicate_code'][rel_path].append((snippet, positions))
        
        # 平均行長を計算し、異常に長い行を検出
        avg_line_length = calculate_avg_line_length(file)
        if avg_line_length > 100:  # 平均行長が100文字を超える場合
            color_print(f"📏 異常に長い行: {rel_path} (平均 {avg_line_length:.1f}文字)", YELLOW)
            results['anomalies'].append((rel_path, f"平均行長: {avg_line_length:.1f}文字"))
    
    # 結果のサマリー
    color_print("\n解析結果のサマリー", BLUE, bold=True)
    
    if results['circular_imports']:
        color_print(f"🔄 循環インポート: {len(results['circular_imports'])}件", RED)
    
    if results['duplicate_classes']:
        color_print(f"🔄 重複クラス: {sum(len(classes) for classes in results['duplicate_classes'].values())}件", RED)
    
    if results['large_files']:
        color_print(f"📁 特大ファイル: {len(results['large_files'])}件", YELLOW)
    
    if results['duplicate_code']:
        total_blocks = sum(len(blocks) for blocks in results['duplicate_code'].values())
        color_print(f"🔍 重複コードブロック: {total_blocks}件", RED)
    
    if results['anomalies']:
        color_print(f"⚠️ その他の異常: {len(results['anomalies'])}件", YELLOW)
    
    if not any(results.values()):
        color_print("✅ 重大な問題は検出されませんでした", GREEN)
    
    return results

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="インポートの問題や重複コードを検出するスクリプト")
    parser.add_argument('--dir', help='テストディレクトリ', default=None)
    parser.add_argument('--pattern', help='ファイルパターン', default="*.py")
    args = parser.parse_args()
    
    find_unusual_files(args.dir, args.pattern)

if __name__ == '__main__':
    main() 