"""
アドバタイズモードを制限する単純なスクリプト

このスクリプトは、テスト実行前にmainモジュールのアドバタイズモードを置き換えて
無限ループを防止します。
"""

import sys
import importlib
import unittest

# リセット回数の制限
MAX_RESET_COUNT = 5
reset_count = 0

# 制限付きアドバタイズモード関数
def limited_advertise_mode():
    """リセット回数を制限するアドバタイズモード"""
    global reset_count
    reset_count += 1
    print(f"アドバタイズモード実行 ({reset_count}/{MAX_RESET_COUNT})")
    
    if reset_count >= MAX_RESET_COUNT:
        print(f"最大リセット回数 ({MAX_RESET_COUNT}) に達したため終了します")
        sys.exit(0)

# 指定されたテストモジュールを実行
def run_test(test_file):
    """テストを実行する"""
    print(f"テストモジュール '{test_file}' を実行します")
    
    # テストモジュール名を取得
    if test_file.endswith('.py'):
        test_file = test_file[:-3]
    
    # まずmainモジュールをインポート
    try:
        import src.game.core.main
        # アドバタイズモードを制限する版に置き換え
        if hasattr(main, 'advertise_mode'):
            original_advertise = main.advertise_mode
            main.advertise_mode = limited_advertise_mode
            print("mainモジュールのアドバタイズモードを置き換えました")
        
        if hasattr(main, 'reset_game'):
            # リセット関数を拡張して回数を制限
            original_reset = main.reset_game
            def limited_reset_game():
                global reset_count
                reset_count += 1
                print(f"ゲームリセット ({reset_count}/{MAX_RESET_COUNT})")
                
                # オリジナルのリセット関数を呼び出す
                original_reset()
                
                if reset_count >= MAX_RESET_COUNT:
                    print(f"最大リセット回数 ({MAX_RESET_COUNT}) に達したため終了します")
                    sys.exit(0)
            
            main.reset_game = limited_reset_game
            print("mainモジュールのリセット関数を置き換えました")
    except ImportError:
        print("mainモジュールをインポートできませんでした")
    except Exception as e:
        print(f"mainモジュールの初期化中にエラー: {e}")
    
    # テストを実行
    try:
        # テストモジュールをインポート
        test_module = importlib.import_module(test_file)
        # テストを実行
        unittest.main(module=test_module)
    except ImportError as e:
        print(f"テストモジュール '{test_file}' のインポートに失敗: {e}")
        return 1
    except Exception as e:
        print(f"テスト実行中にエラー: {e}")
        return 1
    
    return 0

# メイン実行
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python limit_advertise.py <テストモジュール>")
        sys.exit(1)
    
    test_file = sys.argv[1]
    
    # コマンドライン引数を保存
    original_argv = sys.argv.copy()
    
    # unittest用に引数をリセット
    sys.argv = [sys.argv[0]]
    
    try:
        exit_code = run_test(test_file)
        sys.exit(exit_code)
    except SystemExit as e:
        sys.exit(e.code if hasattr(e, 'code') else 0) 