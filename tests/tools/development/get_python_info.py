import sys
import platform

# パス情報を出力
print(f"Python実行ファイル: {sys.executable}")
print(f"Pythonバージョン: {platform.python_version()}")
print(f"プラットフォーム: {platform.platform()}")

# スクリプト終了しないようにする
if __name__ == "__main__":
    input("\nEnterキーを押して終了...") 