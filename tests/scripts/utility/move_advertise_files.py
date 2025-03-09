import os
import shutil
import logging
from datetime import datetime

# ロギングの設定
log_dir = "reorganization_logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"advertise_move_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def create_directory(directory):
    """ディレクトリが存在しない場合は作成する"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"ディレクトリを作成: {directory}")

def move_file(src, dest):
    """ファイルを移動する"""
    try:
        # 移動先ディレクトリの確認
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        # ファイルの移動
        shutil.copy2(src, dest)
        logging.info(f"ファイル移動完了: {src} -> {dest}")
        return True
    except Exception as e:
        logging.error(f"ファイル移動エラー {src} -> {dest}: {str(e)}")
        return False

def main():
    print("=" * 50)
    print("advertise_mode関連ファイルの整理を開始します")
    print("=" * 50)
    
    # 移動対象のadvertise_mode関連ファイル
    advertise_files = [
        {"src": "advertise_mode_analyzer.py", "dest": "advertise_mode/analyzer.py"},
        {"src": "advertise_mode_improver.py", "dest": "advertise_mode/improver.py"},
        {"src": "test_advertise_mode.py", "dest": "advertise_mode/test_advertise_mode.py"},
        {"src": "limit_advertise.py", "dest": "advertise_mode/limit_advertise.py"},
        {"src": "run_advertise_test.bat", "dest": "advertise_mode/run_test.bat"},
    ]
    
    # 追加でtoolsディレクトリに移動するファイル
    tools_files = [
        {"src": "run_specific_test.py", "dest": "tools/development/run_specific_test.py"},
        {"src": "run_simple_test.py", "dest": "tools/development/run_simple_test.py"},
        {"src": "simple_test_runner.py", "dest": "tools/development/simple_test_runner.py"},
        {"src": "simple_main.py", "dest": "tools/development/simple_main.py"},
        {"src": "run_in_cursor.py", "dest": "tools/development/run_in_cursor.py"},
        {"src": "run_no_gui_tests.py", "dest": "tools/development/run_no_gui_tests.py"},
        {"src": "write_python_info.py", "dest": "tools/development/write_python_info.py"},
        {"src": "get_python_info.py", "dest": "tools/development/get_python_info.py"},
        {"src": "check_python_path.py", "dest": "tools/development/check_python_path.py"},
        {"src": "run_autonomous.bat", "dest": "tools/development/run_autonomous.bat"},
        {"src": "convert_tests.py", "dest": "tools/development/convert_tests.py"},
    ]
    
    # 残りのテストファイルをtests/unitに移動
    test_files = [
        {"src": "test_simple_main.py", "dest": "tests/unit/test_simple_main.py"},
        {"src": "test_parameterized.py", "dest": "tests/unit/test_parameterized.py"},
        {"src": "test_main_stub.py", "dest": "tests/unit/test_main_stub.py"},
        {"src": "test_player_dash.py", "dest": "tests/unit/test_player_dash.py"},
        {"src": "coverage_test.py", "dest": "tests/unit/coverage_test.py"},
    ]
    
    # ディレクトリの確認・作成
    create_directory("advertise_mode")
    create_directory("tools/development")
    create_directory("tests/unit")
    
    # advertise_mode関連ファイルの移動
    success_count = 0
    fail_count = 0
    
    print("\nadvertise_mode関連ファイルを移動します...")
    for file_info in advertise_files:
        src = file_info["src"]
        dest = file_info["dest"]
        
        if os.path.exists(src):
            if move_file(src, dest):
                success_count += 1
            else:
                fail_count += 1
        else:
            logging.warning(f"ファイルが見つかりません: {src}")
    
    print("\n追加のツールファイルを移動します...")
    for file_info in tools_files:
        src = file_info["src"]
        dest = file_info["dest"]
        
        if os.path.exists(src):
            if move_file(src, dest):
                success_count += 1
            else:
                fail_count += 1
        else:
            logging.warning(f"ファイルが見つかりません: {src}")
    
    print("\n残りのテストファイルを移動します...")
    for file_info in test_files:
        src = file_info["src"]
        dest = file_info["dest"]
        
        if os.path.exists(src):
            if move_file(src, dest):
                success_count += 1
            else:
                fail_count += 1
        else:
            logging.warning(f"ファイルが見つかりません: {src}")
    
    print("\n" + "=" * 50)
    print(f"処理が完了しました: 成功={success_count}, 失敗={fail_count}")
    print(f"ログファイル: {log_file}")

if __name__ == "__main__":
    main() 