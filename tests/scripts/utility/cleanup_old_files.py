import os
import logging
from datetime import datetime
import glob

# ロギングの設定
log_dir = "reorganization_logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_files_to_cleanup():
    """クリーンアップ対象のファイルを取得"""
    # 移動済みのテストファイル
    test_files = [
        "test_base.py", "test_basic.py", "test_basic_new.py", "test_dash_new.py", 
        "test_dash_new_v2.py", "test_enemy_v2.py", "test_player_v2.py", "test_bullet_v2.py",
        "test_game_logic_advanced.py", "test_performance.py", "test_mock_classes.py",
        "test_advertise_mode.py", "test_simple_main.py", "test_parameterized.py",
        "test_main_stub.py", "test_player_dash.py", "coverage_test.py"
    ]
    
    # 移動済みのスクリプトファイル
    script_files = [
        "run_tests.py", "run_tests.bat", "run_auto_tests.py", "watch_tests.py", 
        "watch_tests.bat", "run_single_test.py", "run_single_test.bat",
        "run_advertise_test.bat"
    ]
    
    # 移動済みのツールファイル
    tool_files = [
        "autonomous_test_engine.py", "autonomous_test_engine_v2.py", "test_report.py",
        "test_prioritizer.py", "test_scheduler.py", "run_specific_test.py",
        "run_simple_test.py", "simple_test_runner.py", "simple_main.py", "run_in_cursor.py",
        "run_no_gui_tests.py", "write_python_info.py", "get_python_info.py",
        "check_python_path.py", "run_autonomous.bat", "convert_tests.py"
    ]
    
    # 移動済みのadvertiseファイル
    advertise_files = [
        "advertise_mode_analyzer.py", "advertise_mode_improver.py", "test_advertise_mode.py",
        "limit_advertise.py"
    ]
    
    # 移動済みのドキュメントファイル
    doc_files = [
        "TESTING_README.md"
    ]
    
    # 不要な一時ファイルやログファイル
    temp_files = [
        "temp_patch.py", 
        "advertise_analysis_*.log"
    ]
    
    # 古い整理スクリプト（バックアップ済み）
    old_scripts = [
        "auto_reorganize.py", "auto_reorganize.bat",
        "smart_reorganize.py", "smart_reorganize.bat", 
        "organize_project_safe.py", "organize_project_safe.bat"
    ]
    
    return test_files + script_files + tool_files + advertise_files + doc_files + old_scripts


def main():
    print("=" * 50)
    print("不要なファイルのクリーンアップを開始します")
    print("=" * 50)
    
    # 移動済みのファイルのリスト取得
    files_to_cleanup = get_files_to_cleanup()
    
    # 削除前の確認
    print("\n以下のファイルを削除します（既に移動済み）:")
    for file in files_to_cleanup:
        if "*" in file:
            matching_files = glob.glob(file)
            for matching_file in matching_files:
                if os.path.exists(matching_file):
                    print(f" - {matching_file}")
        elif os.path.exists(file):
            print(f" - {file}")
    
    confirm = input("\n続行しますか？ (y/n): ").strip().lower()
    if confirm != 'y':
        print("クリーンアップをキャンセルしました。")
        return
    
    # ファイルの削除
    deleted_count = 0
    skipped_count = 0
    
    for file in files_to_cleanup:
        if "*" in file:
            # ワイルドカードを含むパターンの処理
            matching_files = glob.glob(file)
            for matching_file in matching_files:
                if os.path.exists(matching_file):
                    try:
                        os.remove(matching_file)
                        logging.info(f"ファイルを削除: {matching_file}")
                        deleted_count += 1
                    except Exception as e:
                        logging.error(f"ファイル削除エラー {matching_file}: {str(e)}")
                        skipped_count += 1
        elif os.path.exists(file):
            try:
                os.remove(file)
                logging.info(f"ファイルを削除: {file}")
                deleted_count += 1
            except Exception as e:
                logging.error(f"ファイル削除エラー {file}: {str(e)}")
                skipped_count += 1
        else:
            # logging.debug(f"ファイルが見つかりません: {file}")
            skipped_count += 1
    
    print("\n" + "=" * 50)
    print(f"クリーンアップが完了しました: 削除={deleted_count}, スキップ={skipped_count}")
    print(f"ログファイル: {log_file}")

if __name__ == "__main__":
    main() 