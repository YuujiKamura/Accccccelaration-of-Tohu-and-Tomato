import sys
import os
import platform

print("="*50)
print("Pythonパス情報")
print("="*50)

# Pythonの実行ファイルパス
print(f"Pythonの実行ファイル: {sys.executable}")

# Pythonのバージョン
print(f"Pythonバージョン: {platform.python_version()}")

# システムのパス
print("\nシステムPATH環境変数:")
paths = os.environ.get('PATH', '').split(os.pathsep)
for i, path in enumerate(paths, 1):
    print(f"{i}. {path}")

# モジュール検索パス
print("\nPythonモジュール検索パス:")
for i, path in enumerate(sys.path, 1):
    print(f"{i}. {path}")

print("\n"+"="*50)
input("Enterキーを押して終了...") 