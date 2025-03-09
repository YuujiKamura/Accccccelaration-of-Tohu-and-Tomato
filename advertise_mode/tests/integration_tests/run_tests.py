#!/usr/bin/env python
"""
アドバタイズモード統合テスト実行スクリプト

統合テストを自動的に実行し、結果をレポートします。
コマンドライン引数を使用して、テスト範囲やオプションを指定できます。
"""

import os
import sys
import time
import argparse
import unittest
import json
from datetime import datetime

# 必要なパスをシステムパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_tests(test_pattern='*', verbose=1, quick=False, benchmark=False):
    """
    指定されたパターンに一致するテストを実行
    
    Args:
        test_pattern: テスト名のパターン（unittest形式）
        verbose: 詳細度（0-3）
        quick: 高速実行モード（一部のテストをスキップ）
        benchmark: ベンチマークテストを実行するかどうか
    
    Returns:
        (成功数, 失敗数, エラー数)
    """
    # テスト開始時間を記録
    start_time = time.time()
    
    # テスト結果を保存するディレクトリを作成
    results_dir = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # テスト結果ファイル
    result_file = os.path.join(results_dir, 'test_results.json')
    
    # テスト環境変数を設定
    if quick:
        os.environ['TEST_QUICK_MODE'] = 'True'
    
    # テストスイートを作成
    loader = unittest.TestLoader()
    
    # テストディレクトリを取得
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # テストをパターンに基づいて検索
        if benchmark:
            suite = loader.loadTestsFromName('test_advertise_mode_integration.TestComparisonBenchmark')
        elif test_pattern == '*':
            suite = loader.discover(test_dir, pattern='test_*.py')
        else:
            suite = loader.loadTestsFromName(test_pattern)
        
        # テスト実行器の作成
        runner = unittest.TextTestRunner(verbosity=verbose)
        
        # テスト実行
        print(f"テスト開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result = runner.run(suite)
        
        # 実行時間を計算
        duration = time.time() - start_time
        
        # 結果の概要を出力
        success = result.wasSuccessful()
        print(f"\nテスト結果の概要:")
        print(f"- 実行テスト数: {result.testsRun}")
        print(f"- 成功: {'すべて' if success else result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"- 失敗: {len(result.failures)}")
        print(f"- エラー: {len(result.errors)}")
        print(f"- 合格率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0:.1f}%")
        print(f"- 実行時間: {duration:.2f}秒")
        
        # 結果をJSONで保存
        test_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful(),
            'duration': duration,
            'failure_details': [
                {
                    'test': str(test),
                    'message': str(err)
                } for test, err in result.failures
            ],
            'error_details': [
                {
                    'test': str(test),
                    'message': str(err)
                } for test, err in result.errors
            ]
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\nテスト結果は {os.path.abspath(result_file)} に保存されました")
        
        return (
            result.testsRun - len(result.failures) - len(result.errors),
            len(result.failures),
            len(result.errors)
        )
        
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        # エラー詳細をJSONで保存
        error_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error': str(e),
            'traceback': sys.exc_info()[2] and "".join(traceback.format_tb(sys.exc_info()[2])) or ""
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(error_results, f, ensure_ascii=False, indent=2)
        
        return (0, 0, 1)


def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='アドバタイズモードの統合テスト実行')
    
    parser.add_argument('--pattern', type=str, default='*',
                        help='実行するテストのパターン（例: "test_advertise_mode_integration.TestAdvertiseModeIntegration.test_original_behavior"）')
    
    parser.add_argument('--verbose', '-v', type=int, choices=[0, 1, 2, 3], default=2,
                        help='出力の詳細レベル（0: 最小限, 3: 最も詳細）')
    
    parser.add_argument('--quick', '-q', action='store_true',
                        help='高速実行モード（一部のテストをスキップ）')
    
    parser.add_argument('--benchmark', '-b', action='store_true',
                        help='ベンチマークテストを実行')
    
    parser.add_argument('--repeat', '-r', type=int, default=1,
                        help='テストを繰り返す回数')
    
    args = parser.parse_args()
    
    # 繰り返し実行
    total_success = 0
    total_failures = 0
    total_errors = 0
    
    for i in range(args.repeat):
        if args.repeat > 1:
            print(f"\n--- テスト実行 {i+1}/{args.repeat} ---\n")
        
        success, failures, errors = run_tests(
            test_pattern=args.pattern,
            verbose=args.verbose,
            quick=args.quick,
            benchmark=args.benchmark
        )
        
        total_success += success
        total_failures += failures
        total_errors += errors
    
    # 複数回実行した場合は合計結果を表示
    if args.repeat > 1:
        print(f"\n=== 合計実行結果（{args.repeat}回） ===")
        print(f"成功: {total_success}")
        print(f"失敗: {total_failures}")
        print(f"エラー: {total_errors}")
        print(f"合格率: {(total_success / (total_success + total_failures + total_errors) * 100):.1f}%")
    
    # 全テスト成功の場合は0、失敗があれば1を返す
    return 0 if total_failures == 0 and total_errors == 0 else 1


if __name__ == "__main__":
    # スクリプトが直接実行された場合はmain関数を実行
    sys.exit(main()) 
"""
アドバタイズモード統合テスト実行スクリプト

統合テストを自動的に実行し、結果をレポートします。
コマンドライン引数を使用して、テスト範囲やオプションを指定できます。
"""

import os
import sys
import time
import argparse
import unittest
import json
from datetime import datetime

# 必要なパスをシステムパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_tests(test_pattern='*', verbose=1, quick=False, benchmark=False):
    """
    指定されたパターンに一致するテストを実行
    
    Args:
        test_pattern: テスト名のパターン（unittest形式）
        verbose: 詳細度（0-3）
        quick: 高速実行モード（一部のテストをスキップ）
        benchmark: ベンチマークテストを実行するかどうか
    
    Returns:
        (成功数, 失敗数, エラー数)
    """
    # テスト開始時間を記録
    start_time = time.time()
    
    # テスト結果を保存するディレクトリを作成
    results_dir = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # テスト結果ファイル
    result_file = os.path.join(results_dir, 'test_results.json')
    
    # テスト環境変数を設定
    if quick:
        os.environ['TEST_QUICK_MODE'] = 'True'
    
    # テストスイートを作成
    loader = unittest.TestLoader()
    
    # テストディレクトリを取得
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # テストをパターンに基づいて検索
        if benchmark:
            suite = loader.loadTestsFromName('test_advertise_mode_integration.TestComparisonBenchmark')
        elif test_pattern == '*':
            suite = loader.discover(test_dir, pattern='test_*.py')
        else:
            suite = loader.loadTestsFromName(test_pattern)
        
        # テスト実行器の作成
        runner = unittest.TextTestRunner(verbosity=verbose)
        
        # テスト実行
        print(f"テスト開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result = runner.run(suite)
        
        # 実行時間を計算
        duration = time.time() - start_time
        
        # 結果の概要を出力
        success = result.wasSuccessful()
        print(f"\nテスト結果の概要:")
        print(f"- 実行テスト数: {result.testsRun}")
        print(f"- 成功: {'すべて' if success else result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"- 失敗: {len(result.failures)}")
        print(f"- エラー: {len(result.errors)}")
        print(f"- 合格率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0:.1f}%")
        print(f"- 実行時間: {duration:.2f}秒")
        
        # 結果をJSONで保存
        test_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful(),
            'duration': duration,
            'failure_details': [
                {
                    'test': str(test),
                    'message': str(err)
                } for test, err in result.failures
            ],
            'error_details': [
                {
                    'test': str(test),
                    'message': str(err)
                } for test, err in result.errors
            ]
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\nテスト結果は {os.path.abspath(result_file)} に保存されました")
        
        return (
            result.testsRun - len(result.failures) - len(result.errors),
            len(result.failures),
            len(result.errors)
        )
        
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        # エラー詳細をJSONで保存
        error_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error': str(e),
            'traceback': sys.exc_info()[2] and "".join(traceback.format_tb(sys.exc_info()[2])) or ""
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(error_results, f, ensure_ascii=False, indent=2)
        
        return (0, 0, 1)


def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='アドバタイズモードの統合テスト実行')
    
    parser.add_argument('--pattern', type=str, default='*',
                        help='実行するテストのパターン（例: "test_advertise_mode_integration.TestAdvertiseModeIntegration.test_original_behavior"）')
    
    parser.add_argument('--verbose', '-v', type=int, choices=[0, 1, 2, 3], default=2,
                        help='出力の詳細レベル（0: 最小限, 3: 最も詳細）')
    
    parser.add_argument('--quick', '-q', action='store_true',
                        help='高速実行モード（一部のテストをスキップ）')
    
    parser.add_argument('--benchmark', '-b', action='store_true',
                        help='ベンチマークテストを実行')
    
    parser.add_argument('--repeat', '-r', type=int, default=1,
                        help='テストを繰り返す回数')
    
    args = parser.parse_args()
    
    # 繰り返し実行
    total_success = 0
    total_failures = 0
    total_errors = 0
    
    for i in range(args.repeat):
        if args.repeat > 1:
            print(f"\n--- テスト実行 {i+1}/{args.repeat} ---\n")
        
        success, failures, errors = run_tests(
            test_pattern=args.pattern,
            verbose=args.verbose,
            quick=args.quick,
            benchmark=args.benchmark
        )
        
        total_success += success
        total_failures += failures
        total_errors += errors
    
    # 複数回実行した場合は合計結果を表示
    if args.repeat > 1:
        print(f"\n=== 合計実行結果（{args.repeat}回） ===")
        print(f"成功: {total_success}")
        print(f"失敗: {total_failures}")
        print(f"エラー: {total_errors}")
        print(f"合格率: {(total_success / (total_success + total_failures + total_errors) * 100):.1f}%")
    
    # 全テスト成功の場合は0、失敗があれば1を返す
    return 0 if total_failures == 0 and total_errors == 0 else 1


if __name__ == "__main__":
    # スクリプトが直接実行された場合はmain関数を実行
    sys.exit(main()) 