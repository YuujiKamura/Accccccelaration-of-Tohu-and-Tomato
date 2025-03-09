#!/usr/bin/env python
"""
アドバタイズモード統合テスト実行スクリプト

統合テストを自動的に実行し、結果をレポートします。
コマンドライン引数を使用して、テスト範囲やオプションを指定できます。
メモリ使用量を最適化し、テスト実行時のパフォーマンスを改善しています。
"""

import os
import sys
import time
import argparse
import unittest
import json
import gc
from datetime import datetime

# 必要なパスをシステムパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# psutilがインストールされているか確認
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("警告: psutilがインストールされていません。メモリ使用量を監視できません。")

# メモリ使用量を監視する関数
def get_memory_usage():
    """現在のプロセスのメモリ使用量をMB単位で返す"""
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)  # MB単位
    return 0

def run_single_test_case(test_case, verbosity=1):
    """
    単一のテストケースクラスを実行
    
    Args:
        test_case: 実行するテストケースクラス
        verbosity: 詳細度
    
    Returns:
        (実行数, 成功数, 失敗数, エラー数)
    """
    # テストスイートを作成
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_case)
    
    # テスト実行
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    
    # 結果を返す
    successful = result.testsRun - len(result.failures) - len(result.errors)
    return (result.testsRun, successful, len(result.failures), len(result.errors))

def run_tests(test_pattern='*', verbose=1, quick=False, benchmark=False, memory_limit=500):
    """
    指定されたパターンに一致するテストを実行
    
    Args:
        test_pattern: テスト名のパターン（unittest形式）
        verbose: 詳細度（0-3）
        quick: 高速実行モード（一部のテストをスキップ）
        benchmark: ベンチマークテストを実行するかどうか
        memory_limit: メモリ使用量の上限(MB)
    
    Returns:
        (成功数, 失敗数, エラー数)
    """
    # テスト開始時間を記録
    start_time = time.time()
    initial_memory = get_memory_usage()
    
    if verbose >= 1:
        print(f"初期メモリ使用量: {initial_memory:.2f}MB")
    
    # テスト結果を保存するディレクトリを作成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = f"test_results_{timestamp}"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # テスト結果ファイル
    result_file = os.path.join(results_dir, 'test_results.json')
    
    # テスト環境変数を設定
    if quick:
        os.environ['TEST_QUICK_MODE'] = 'True'
    
    # テストモジュールを見つける
    test_files = []
    for root, _, files in os.walk(os.path.dirname(__file__)):
        for file in files:
            if file.startswith(f'test_{test_pattern.replace("*", "")}') and file.endswith('.py'):
                module_path = os.path.join(root, file)
                # ベンチマークテストのフィルタリング
                if not benchmark and 'benchmark' in file.lower():
                    continue
                test_files.append(module_path)
    
    # テスト結果の集計
    total_run = 0
    total_success = 0
    total_failures = 0
    total_errors = 0
    failure_details = []
    error_details = []
    
    # 各テストファイルを個別に処理
    for test_file in test_files:
        if verbose >= 1:
            rel_path = os.path.relpath(test_file, project_root)
            print(f"\n実行中: {rel_path}")
        
        # メモリ使用量をチェック
        current_memory = get_memory_usage()
        if current_memory > memory_limit:
            print(f"警告: メモリ使用量が上限を超えています ({current_memory:.2f}MB > {memory_limit}MB)")
            print("メモリを解放するためにガベージコレクションを実行します...")
            gc.collect()
            current_memory = get_memory_usage()
            if current_memory > memory_limit:
                print(f"メモリ使用量がまだ高いです ({current_memory:.2f}MB). テスト続行が困難な場合があります。")
        
        try:
            # ファイルパスからモジュールパスを取得
            rel_path = os.path.relpath(test_file, project_root)
            module_name = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
            
            # 動的にモジュールをインポート
            import importlib
            test_module = importlib.import_module(module_name)
            
            # テストケースクラスを見つける
            test_cases = []
            for item_name in dir(test_module):
                item = getattr(test_module, item_name)
                if isinstance(item, type) and issubclass(item, unittest.TestCase) and item is not unittest.TestCase:
                    # ベンチマークフィルタリング
                    if not benchmark and 'Benchmark' in item_name:
                        continue
                    test_cases.append(item)
            
            # 各テストケースを個別に実行
            for test_case in test_cases:
                if verbose >= 1:
                    print(f"  テストケース: {test_case.__name__}")
                
                tests_run, success, failures, errors = run_single_test_case(test_case, verbose)
                
                # 結果を集計
                total_run += tests_run
                total_success += success
                total_failures += failures
                total_errors += errors
                
                # メモリを解放
                gc.collect()
                
                # 現在のメモリ使用量を表示
                if verbose >= 2 and HAS_PSUTIL:
                    current_memory = get_memory_usage()
                    print(f"  現在のメモリ使用量: {current_memory:.2f}MB")
            
            # 使用済みモジュールの参照を削除してメモリを解放
            if 'test_module' in locals():
                del test_module
                gc.collect()
                
        except Exception as e:
            import traceback
            print(f"テストファイル {test_file} の実行中にエラーが発生しました:")
            print(traceback.format_exc())
            total_errors += 1
            error_details.append({
                'test': os.path.basename(test_file),
                'message': str(e)
            })
            
            # エラー後のメモリ使用量をチェック
            if verbose >= 1 and HAS_PSUTIL:
                current_memory = get_memory_usage()
                print(f"エラー後のメモリ使用量: {current_memory:.2f}MB")
                
            # メモリを解放
            gc.collect()
    
    # テスト時間を計算
    end_time = time.time()
    elapsed_time = end_time - start_time
    final_memory = get_memory_usage()
    
    # 結果の概要を表示
    print(f"\nテスト完了: {elapsed_time:.2f}秒")
    print(f"実行: {total_run}, 成功: {total_success}, 失敗: {total_failures}, エラー: {total_errors}")
    
    if HAS_PSUTIL:
        print(f"メモリ使用量: {initial_memory:.2f}MB -> {final_memory:.2f}MB (差分: {final_memory - initial_memory:.2f}MB)")
    
    # 詳細な結果をJSONファイルに保存
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'elapsed_time': elapsed_time,
        'tests_run': total_run,
        'success': total_success,
        'failures': total_failures,
        'errors': total_errors,
        'memory_initial': initial_memory,
        'memory_final': final_memory,
        'memory_diff': final_memory - initial_memory,
        'failure_details': failure_details,
        'error_details': error_details,
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"詳細な結果は {os.path.abspath(result_file)} に保存されました")
    
    return (total_success, total_failures, total_errors)


def main():
    """
    メイン実行関数
    
    コマンドライン引数を解析し、適切なテストを実行します。
    """
    parser = argparse.ArgumentParser(description='アドバタイズモード統合テスト実行スクリプト')
    parser.add_argument('-p', '--pattern', default='*', help='テスト名のパターン（例: dash, bullet など）')
    parser.add_argument('-v', '--verbose', type=int, choices=[0, 1, 2, 3], default=1, help='出力の詳細レベル')
    parser.add_argument('-q', '--quick', action='store_true', help='クイックモード（一部のテストをスキップ）')
    parser.add_argument('-b', '--benchmark', action='store_true', help='ベンチマークテストを含める')
    parser.add_argument('-a', '--all', action='store_true', help='すべてのテストを実行（デフォルト）')
    parser.add_argument('-m', '--memory-limit', type=int, default=500, help='メモリ使用量の上限(MB)')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--unit', action='store_true', help='ユニットテストのみ実行')
    group.add_argument('--integration', action='store_true', help='統合テストのみ実行')
    
    args = parser.parse_args()
    
    # パターンの検証
    pattern = args.pattern.replace('*', '')  # アスタリスクを削除
    if pattern and not pattern.isalnum() and not all(c.isalnum() or c == '_' for c in pattern):
        print(f"エラー: パターンには英数字またはアンダースコアのみ使用できます: {args.pattern}")
        sys.exit(1)
    
    # テスト開始前のメモリ使用量を表示
    initial_memory = get_memory_usage()
    if HAS_PSUTIL:
        print(f"テスト開始前のメモリ使用量: {initial_memory:.2f}MB")
    
    # カレントディレクトリを保存
    original_dir = os.getcwd()
    
    try:
        # テスト種別の選択
        if args.unit:
            # ユニットテストのみ実行
            print("ユニットテストを実行します...")
            os.chdir(os.path.join(project_root, 'tests', 'unit'))
            success, failures, errors = run_tests(args.pattern, args.verbose, args.quick, args.benchmark, args.memory_limit)
        elif args.integration:
            # 統合テストのみ実行
            print("統合テストを実行します...")
            os.chdir(os.path.join(project_root, 'tests', 'integration_tests'))
            success, failures, errors = run_tests(args.pattern, args.verbose, args.quick, args.benchmark, args.memory_limit)
        else:
            # すべてのテストを実行
            print("すべてのテストを実行します...")
            
            # ユニットテスト
            print("\n--- ユニットテスト ---")
            os.chdir(os.path.join(project_root, 'tests', 'unit'))
            success1, failures1, errors1 = run_tests(args.pattern, args.verbose, args.quick, args.benchmark, args.memory_limit)
            
            # メモリを解放
            gc.collect()
            if HAS_PSUTIL:
                memory_after_unit = get_memory_usage()
                print(f"ユニットテスト後のメモリ使用量: {memory_after_unit:.2f}MB")
            
            # 統合テスト
            print("\n--- 統合テスト ---")
            os.chdir(os.path.join(project_root, 'tests', 'integration_tests'))
            success2, failures2, errors2 = run_tests(args.pattern, args.verbose, args.quick, args.benchmark, args.memory_limit)
            
            success = success1 + success2
            failures = failures1 + failures2
            errors = errors1 + errors2
    
    finally:
        # カレントディレクトリを元に戻す
        os.chdir(original_dir)
    
    # 最終的なメモリ使用量を表示
    if HAS_PSUTIL:
        final_memory = get_memory_usage()
        print(f"\nテスト終了後のメモリ使用量: {final_memory:.2f}MB (差分: {final_memory - initial_memory:.2f}MB)")
    
    # 終了コードを設定（エラーがあれば非ゼロ）
    if failures > 0 or errors > 0:
        sys.exit(1)


if __name__ == '__main__':
    main() 