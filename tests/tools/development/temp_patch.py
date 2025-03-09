
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
