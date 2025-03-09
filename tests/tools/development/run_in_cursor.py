"""
Cursor用ランチャースクリプト
VSコード/Cursor内から直接実行できます
"""
import os
import sys
import subprocess
import platform

def run_game():
    """ゲームを実行する関数"""
    print("="*50)
    print("デスクトップ版ゲームを起動します")
    print("="*50)
    
    # 現在のOS確認
    os_name = platform.system()
    print(f"オペレーティングシステム: {os_name}")
    
    # Pythonバージョン確認
    print(f"Pythonバージョン: {sys.version}")
    
    # 必要なモジュールの確認
    try:
        import pygame
        print(f"Pygame バージョン: {pygame.version.ver}")
    except ImportError:
        print("Pygameがインストールされていません。インストールします...")
        subprocess.call([sys.executable, "-m", "pip", "install", "pygame==2.5.2"])
        try:
            import pygame
            print(f"Pygame インストール成功: {pygame.version.ver}")
        except ImportError:
            print("Pygameのインストールに失敗しました。")
            return
    
    try:
        import numpy
        print(f"NumPy バージョン: {numpy.__version__}")
    except ImportError:
        print("NumPyがインストールされていません。インストールします...")
        subprocess.call([sys.executable, "-m", "pip", "install", "numpy==1.24.3"])
    
    # main.pyを実行
    print("\nゲームを起動しています...")
    try:
        # このスクリプトと同じディレクトリにあるmain.pyを実行
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_path = os.path.join(script_dir, "main.py")
        
        if os.path.exists(main_path):
            print(f"ゲームファイルが見つかりました: {main_path}")
            # 直接Pythonプロセスを実行（subprocess.callがブロッキング）
            subprocess.call([sys.executable, main_path])
        else:
            print(f"エラー: main.pyが見つかりません: {main_path}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    
    print("\n"+"="*50)
    print("ゲームを終了しました")
    print("="*50)
    input("Enterキーを押して終了...")

if __name__ == "__main__":
    run_game() 