#!/usr/bin/env python
"""
特定のファイル内の重複クラスや重複コードブロックを検出するスクリプト
"""

import re
import sys
import os
from collections import Counter

def count_duplicates(file_path):
    """ファイル内の重複クラスを検出して数える"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # クラス定義を検出
        class_pattern = re.compile(r'^\s*class\s+([A-Za-z0-9_]+)', re.MULTILINE)
        classes = []
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            classes.append(class_name)
        
        # 重複を計数
        counter = Counter(classes)
        duplicates = {name: count for name, count in counter.items() if count > 1}
        
        # 結果表示
        if duplicates:
            print(f"ファイル: {file_path}で重複クラスが見つかりました:")
            for name, count in duplicates.items():
                print(f"  {name}: {count}回")
            
            # 各クラスの最初の位置
            for name in duplicates:
                pattern = re.compile(f'^\s*class\s+{name}\s*\(', re.MULTILINE)
                positions = [m.start() for m in pattern.finditer(content)]
                
                # 各出現位置の前後数行を表示
                for pos in positions:
                    # 位置から行番号を計算
                    line_num = content[:pos].count('\n') + 1
                    print(f"\n{name}の定義 #{positions.index(pos)+1} (行 {line_num}):")
                    
                    # 定義の前後を表示
                    lines = content.split('\n')
                    start = max(0, line_num - 3)
                    end = min(len(lines), line_num + 5)
                    for i in range(start, end):
                        prefix = ">" if i == line_num - 1 else " "
                        print(f"{prefix} {i+1}: {lines[i]}")
                    print()
        else:
            print(f"ファイル: {file_path}に重複クラスはありません")
        
        # 重複コードブロックを数える
        min_lines = 5  # 最小行数
        block_size = min_lines
        
        lines = content.split('\n')
        blocks = {}
        for i in range(len(lines) - block_size + 1):
            block = '\n'.join(lines[i:i + block_size])
            if block not in blocks:
                blocks[block] = []
            blocks[block].append(i + 1)  # 1-indexedの行番号
        
        # 重複ブロックのみ抽出
        duplicate_blocks = {block: positions for block, positions in blocks.items() if len(positions) > 1}
        
        if duplicate_blocks:
            print(f"\n重複コードブロック: {len(duplicate_blocks)}件")
            # 最も多く重複しているブロックを表示
            top_blocks = sorted(duplicate_blocks.items(), key=lambda x: len(x[1]), reverse=True)[:3]
            for block, positions in top_blocks:
                print(f"\n{len(positions)}回出現するブロック:")
                print(f"最初の出現: 行 {positions[0]}")
                print("コードブロック:")
                print(block[:200] + "..." if len(block) > 200 else block)
                print("\n出現位置:", positions)
        
        return duplicates, duplicate_blocks
    
    except Exception as e:
        print(f"エラー: {file_path} の解析中に例外が発生しました: {e}")
        return {}, {}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法: python count_duplicates.py <ファイルパス>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが見つかりません: {file_path}")
        sys.exit(1)
    
    count_duplicates(file_path) 