"""
scripts/run_tests.pyファイルのインデントエラーを修正するスクリプト
"""

# ファイルを読み込む
with open('scripts/run_tests.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 問題の行番号（168-172行目）のインデントを修正
for i in range(168, 173):
    if i < len(lines):
        # 行の内容を取得
        line = lines[i].rstrip('\n')
        # インデントを削除した内容
        content = line.lstrip()
        # 正しいインデント（12スペース）を追加
        lines[i] = ' ' * 12 + content + '\n'

# 修正したファイルを書き込む
with open('scripts/run_tests.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("scripts/run_tests.pyのインデントを修正しました。") 