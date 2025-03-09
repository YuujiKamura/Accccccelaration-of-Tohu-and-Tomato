import sys
import os
import platform

# パス情報をファイルに書き込む
with open("python_info.txt", "w") as f:
    f.write("="*50 + "\n")
    f.write("Pythonパス情報\n")
    f.write("="*50 + "\n\n")
    
    # Pythonの実行ファイルパス
    f.write(f"Pythonの実行ファイル: {sys.executable}\n")
    
    # Pythonのバージョン
    f.write(f"Pythonバージョン: {platform.python_version()}\n")
    
    # システムのパス
    f.write("\nシステムPATH環境変数:\n")
    paths = os.environ.get('PATH', '').split(os.pathsep)
    for i, path in enumerate(paths, 1):
        f.write(f"{i}. {path}\n")
    
    # モジュール検索パス
    f.write("\nPythonモジュール検索パス:\n")
    for i, path in enumerate(sys.path, 1):
        f.write(f"{i}. {path}\n")

print("パス情報を python_info.txt に書き込みました。")
print("このファイルをテキストエディタで開いて確認してください。")

# スクリプト終了しないようにする
if __name__ == "__main__":
    input("\nEnterキーを押して終了...") 