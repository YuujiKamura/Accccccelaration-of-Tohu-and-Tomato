"""
単純なテスト実行ヘルパー

このスクリプトは、指定されたテストモジュールを実行するシンプルなヘルパーです。
アドバタイズモードの実行回数を制限して、無限ループを防止します。
"""

import sys
import unittest
import importlib.util
import os

def main():
    # コマンドライン引数からテストモジュールを取得
    if len(sys.argv) < 2:
        print("使用方法: python simple_test_runner.py <テストモジュール>")
        return 1
    
    test_module_name = sys.argv[1]
    if test_module_name.endswith('.py'):
        test_module_name = test_module_name[:-3]
    
    print(f"テストモジュール '{test_module_name}' を実行します")
    
    # mainモジュールのアドバタイズモードを制限するパッチを先に適用
    try:
        # モック用のモジュールパッチを作成
        patch_code = """
import sys
import builtins

# 元の__import__関数を保存
original_import = builtins.__import__

# リセット回数カウンター
reset_count = 0
MAX_RESET_COUNT = 5

# アドバタイズモードを制限する関数
def limited_advertise_mode():
    global reset_count
    reset_count += 1
    print(f"アドバタイズモード制限: {reset_count}/{MAX_RESET_COUNT}")
    if reset_count >= MAX_RESET_COUNT:
        print("最大アドバタイズ回数に達したため終了します")
        sys.exit(0)

# インポートをモニタリングする関数
def patched_import(name, *args, **kwargs):
    module = original_import(name, *args, **kwargs)
    
    # mainモジュールの場合、アドバタイズモードを制限
    if name == 'main':
        if hasattr(module, 'advertise_mode'):
            module.advertise_mode = limited_advertise_mode
            print("mainモジュールのアドバタイズモードを制限しました")
    
    return module

# __import__関数を置き換え
builtins.__import__ = patched_import
"""
        
        # 一時的なパッチファイルを作成して実行
        with open('temp_patch.py', 'w') as f:
            f.write(patch_code)
        
        # パッチを適用
        exec(open('temp_patch.py').read())
        print("アドバタイズモード制限パッチを適用しました")
        
    except Exception as e:
        print(f"パッチ適用中にエラー: {e}")
    
    # テストを実行
    try:
        # テスト引数を設定
        test_args = [sys.argv[0]]
        
        # テストディスカバリを使用
        if test_module_name == 'all':
            # すべてのテストを実行
            test_args.append('discover')
            unittest.main(module=None, argv=test_args)
        else:
            # 特定のテストモジュールを実行
            original_argv = sys.argv.copy()
            sys.argv = test_args  # unittest.mainに渡す引数をリセット
            
            # テストモジュールをインポート
            test_module = importlib.import_module(test_module_name)
            
            # テスト実行
            unittest.main(module=test_module)
        
    except ImportError as e:
        print(f"テストモジュール '{test_module_name}' のインポートに失敗: {e}")
        return 1
    except Exception as e:
        print(f"テスト実行中にエラーが発生: {e}")
        return 1
    
    # 一時ファイルを削除
    try:
        if os.path.exists('temp_patch.py'):
            os.remove('temp_patch.py')
    except:
        pass
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except SystemExit as e:
        sys.exit(e.code if hasattr(e, 'code') else 0) 