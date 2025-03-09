"""
シンプルでGUIなしのテスト実行スクリプト

このスクリプトは、まず単純化されたmainモジュールをインポートして
リセット回数を制限してから、テストを実行します。
"""

import sys
import os
import unittest
import importlib

def setup_simple_main():
    """
    test_simple_mainモジュールをセットアップします。
    これにより、テストがメインモジュールをインポートしても無限ループに陥りません。
    """
    try:
        # test_simple_mainを先にインポート
        import test_simple_main
        print("リセット回数制限版のmainモジュールを使用します")
        return True
    except ImportError as e:
        print(f"警告: test_simple_mainモジュールが見つかりません: {e}")
        return False
    except Exception as e:
        print(f"test_simple_mainモジュールのセットアップ中にエラー: {e}")
        return False

def main():
    # 1. まず修正版mainをインポート（メイン処理の前にセットアップ）
    if not setup_simple_main():
        print("警告: 制限付きメインモジュールが設定できませんでした。テストが無限ループする可能性があります。")
    
    # 2. テストを実行
    if len(sys.argv) > 1:
        # 指定されたテストモジュールを実行
        test_file = sys.argv[1]
        if test_file.endswith('.py'):
            # .py拡張子を取り除く
            test_module = test_file[:-3]
        else:
            test_module = test_file
            
        print(f"テストモジュール '{test_module}' を実行します")
        
        try:
            # モジュールをインポート
            module = importlib.import_module(test_module)
            # テストを実行
            unittest.main(module=module)
        except ImportError as e:
            print(f"エラー: モジュール '{test_module}' をインポートできません: {e}")
            return 1
        except Exception as e:
            print(f"テスト実行中にエラーが発生しました: {e}")
            return 1
    else:
        # デフォルトではすべてのテストを実行
        print("すべてのテストを実行します")
        unittest.main(module=None, argv=['run_simple_test.py', 'discover'])
    
    return 0

if __name__ == "__main__":
    # コマンドライン引数の修正: unittest.mainに直接渡さないようにする
    real_argv = sys.argv.copy()
    sys.argv = [sys.argv[0]]  # 最初の引数(スクリプト名)だけ残す
    
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nテストが中断されました")
        sys.exit(1)
    except SystemExit as e:
        # unittestからのsys.exitをキャッチ
        if e.code is not None and e.code != 0:
            print(f"テストが失敗しました (終了コード: {e.code})")
        sys.exit(e.code if e.code is not None else 0) 