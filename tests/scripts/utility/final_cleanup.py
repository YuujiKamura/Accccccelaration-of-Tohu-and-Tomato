import os
import shutil
import logging
from datetime import datetime

# ロギングの設定
log_dir = "reorganization_logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"final_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def ensure_directory(directory):
    """ディレクトリが存在しない場合は作成する"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logging.info(f"ディレクトリを作成: {directory}")

def move_file(src, dest):
    """ファイルを移動する"""
    try:
        # 移動先ディレクトリの確認
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
            
        # ファイルコピー
        shutil.copy2(src, dest)
        
        # 元ファイル削除
        os.remove(src)
        
        logging.info(f"ファイル移動完了: {src} -> {dest}")
        return True
    except Exception as e:
        logging.error(f"ファイル移動エラー {src} -> {dest}: {str(e)}")
        return False

def main():
    print("=" * 50)
    print("最終クリーンアップを開始します")
    print("=" * 50)
    
    # 残りのファイル移動計画
    move_plan = [
        # advertise関連
        {"src": "advertise_mode_analyzer.py", "dest": "advertise_mode/analyzer.py"},
        {"src": "advertise_mode_improver.py", "dest": "advertise_mode/improver.py"},
        {"src": "test_advertise_mode.py", "dest": "advertise_mode/test_advertise_mode.py"},
        {"src": "limit_advertise.py", "dest": "advertise_mode/limit_advertise.py"},
        
        # テスト関連
        {"src": "test_base.py", "dest": "tests/unit/test_base.py"},
        {"src": "test_basic.py", "dest": "tests/unit/test_basic.py"},
        {"src": "test_basic_new.py", "dest": "tests/unit/test_basic_new.py"},
        {"src": "test_bullet_v2.py", "dest": "tests/unit/test_bullet.py"},
        {"src": "test_dash_new.py", "dest": "tests/unit/test_dash_new.py"},
        {"src": "test_dash_new_v2.py", "dest": "tests/unit/test_dash_new_v2.py"},
        {"src": "test_enemy_v2.py", "dest": "tests/unit/test_enemy.py"},
        {"src": "test_game_logic_advanced.py", "dest": "tests/unit/test_game_logic_advanced.py"},
        {"src": "test_main_stub.py", "dest": "tests/unit/test_main_stub.py"},
        {"src": "test_mock_classes.py", "dest": "tests/unit/test_mock_classes.py"},
        {"src": "test_parameterized.py", "dest": "tests/unit/test_parameterized.py"},
        {"src": "test_performance.py", "dest": "tests/performance/test_performance.py"},
        {"src": "test_player_dash.py", "dest": "tests/unit/test_player_dash.py"},
        {"src": "test_player_v2.py", "dest": "tests/unit/test_player.py"},
        {"src": "test_simple_main.py", "dest": "tests/unit/test_simple_main.py"},
        {"src": "coverage_test.py", "dest": "tests/unit/coverage_test.py"},
        
        # スクリプト関連
        {"src": "run_tests.py", "dest": "scripts/run_tests.py"},
        {"src": "run_auto_tests.py", "dest": "scripts/run_auto_tests.py"},
        {"src": "run_single_test.py", "dest": "scripts/run_single_test.py"},
        {"src": "watch_tests.py", "dest": "scripts/watch_tests.py"},
        
        # 開発ツール
        {"src": "autonomous_test_engine.py", "dest": "tools/development/autonomous_test_engine.py"},
        {"src": "autonomous_test_engine_v2.py", "dest": "tools/development/autonomous_test_engine_v2.py"},
        {"src": "convert_tests.py", "dest": "tools/development/convert_tests.py"},
        {"src": "run_in_cursor.py", "dest": "tools/development/run_in_cursor.py"},
        {"src": "run_no_gui_tests.py", "dest": "tools/development/run_no_gui_tests.py"},
        {"src": "run_simple_test.py", "dest": "tools/development/run_simple_test.py"},
        {"src": "run_specific_test.py", "dest": "tools/development/run_specific_test.py"},
        {"src": "simple_main.py", "dest": "tools/development/simple_main.py"},
        {"src": "simple_test_runner.py", "dest": "tools/development/simple_test_runner.py"},
        {"src": "check_python_path.py", "dest": "tools/development/check_python_path.py"},
        {"src": "get_python_info.py", "dest": "tools/development/get_python_info.py"},
        {"src": "write_python_info.py", "dest": "tools/development/write_python_info.py"},
        
        # 分析ツール
        {"src": "test_prioritizer.py", "dest": "tools/analysis/test_prioritizer.py"},
        {"src": "test_report.py", "dest": "tools/analysis/test_report.py"},
        {"src": "test_scheduler.py", "dest": "tools/analysis/test_scheduler.py"},
        
        # 一時ファイル→toolsへ
        {"src": "temp_patch.py", "dest": "tools/development/temp_patch.py"},
    ]
    
    # 残しておくスクリプト
    keep_files = [
        "project_reorganizer.py", 
        "move_advertise_files.py",
        "cleanup_old_files.py",
        "final_cleanup.py"
    ]
    
    # ディレクトリを確認
    ensure_directory("advertise_mode")
    ensure_directory("tests/unit")
    ensure_directory("tests/performance")
    ensure_directory("scripts")
    ensure_directory("tools/development")
    ensure_directory("tools/analysis")
    
    # ファイル移動
    moved_count = 0
    failed_count = 0
    skipped_count = 0
    
    for file_info in move_plan:
        src = file_info["src"]
        dest = file_info["dest"]
        
        if src in keep_files:
            logging.info(f"ファイルをスキップ: {src}")
            skipped_count += 1
            continue
            
        if os.path.exists(src):
            if move_file(src, dest):
                moved_count += 1
            else:
                failed_count += 1
        else:
            logging.info(f"ファイルが見つかりません: {src}")
            skipped_count += 1
    
    print("\n" + "=" * 50)
    print(f"クリーンアップが完了しました: 移動={moved_count}, 失敗={failed_count}, スキップ={skipped_count}")
    print(f"ログファイル: {log_file}")

if __name__ == "__main__":
    main() 