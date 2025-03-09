"""
特定のテストファイルのみを実行するシンプルなスクリプト
"""

import sys
import unittest
import importlib

# リセット回数制限を設定
MAX_RESET_COUNT = 5
reset_count = 0

def reset_game():
    """リセット関数のモック"""
    global reset_count
    reset_count += 1
    print(f"リセット実行 ({reset_count}/{MAX_RESET_COUNT})")
    
    if reset_count >= MAX_RESET_COUNT:
        print(f"最大リセット回数 ({MAX_RESET_COUNT}) に達したため終了します")
        sys.exit(0)

def main():
    """メイン関数"""
    print("特定のテストを実行します")
    
    # 引数から実行するテストファイルを取得
    if len(sys.argv) < 2:
        print("使用方法: python run_specific_test.py <テストファイル名> [テストメソッド名]")
        return 1
    
    test_file = sys.argv[1]
    if test_file.endswith('.py'):
        test_file = test_file[:-3]  # .py拡張子を削除
    
    # テストの選択パターン
    test_pattern = None
    if len(sys.argv) >= 3:
        test_pattern = sys.argv[2]
    
    try:
        # テストモジュールをインポート
        test_module = importlib.import_module(test_file)
        
        # クラス内のreset_game関数をオーバーライド
        # これにより、リセット回数を制限する
        for attr_name in dir(test_module):
            try:
                attr = getattr(test_module, attr_name)
                if hasattr(attr, 'reset_game'):
                    setattr(attr, 'reset_game', reset_game)
            except:
                pass
        
        # テストを実行
        if test_pattern:
            unittest.main(module=test_module, argv=[sys.argv[0], test_pattern])
        else:
            unittest.main(module=test_module)
        
        return 0
    except ImportError as e:
        print(f"エラー: テストモジュール '{test_file}' をインポートできません: {e}")
        return 1
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    # 本来のコマンドライン引数を保存
    original_argv = sys.argv.copy()
    
    try:
        exit_code = main()
        sys.exit(exit_code)
    except SystemExit as e:
        # unittestからのsys.exitをキャッチ
        if hasattr(e, 'code') and e.code is not None:
            sys.exit(e.code)
        sys.exit(0)
    except KeyboardInterrupt:
        print("\nテストが中断されました")
        sys.exit(1) 