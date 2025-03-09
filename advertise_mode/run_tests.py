#!/usr/bin/env python
"""
アドバタイズモードテスト実行スクリプト

アドバタイズモードの単体テスト、統合テスト、ベンチマークテストを実行します。
コマンドライン引数を使用して、テスト範囲やオプションを指定できます。
"""

import os
import sys
import time
import argparse
import unittest
import json
import importlib
from datetime import datetime

# 必要なパスをシステムパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests(test_pattern='*', test_type='all', verbose=1, quick=False, benchmark=False):
    """
    指定されたパターンに一致するテストを実行
    
    Args:
        test_pattern: テスト名のパターン（unittest形式）
        test_type: テストの種類（'unit', 'integration', 'all'）
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # テストをパターンに基づいて検索
        if benchmark:
            # ベンチマークテストを実行
            try:
                from advertise_mode.tests.integration_tests.test_advertise_mode_integration import TestComparisonBenchmark
                suite = loader.loadTestsFromTestCase(TestComparisonBenchmark)
            except (ImportError, AttributeError):
                print("ベンチマークテストが見つかりません。")
                return (0, 0, 1)
        elif test_pattern != '*':
            # 特定のテストパターンを実行
            suite = loader.loadTestsFromName(test_pattern)
        else:
            # テストの種類に基づいてディレクトリを選択
            if test_type == 'unit':
                test_dir = os.path.join(base_dir, 'tests', 'unit_tests')
            elif test_type == 'integration':
                test_dir = os.path.join(base_dir, 'tests', 'integration_tests')
            else:  # 'all'
                suite = unittest.TestSuite()
                
                # 単体テスト
                unit_test_dir = os.path.join(base_dir, 'tests', 'unit_tests')
                if os.path.exists(unit_test_dir):
                    unit_suite = loader.discover(unit_test_dir, pattern='test_*.py')
                    suite.addTest(unit_suite)
                
                # 統合テスト
                integration_test_dir = os.path.join(base_dir, 'tests', 'integration_tests')
                if os.path.exists(integration_test_dir):
                    integration_suite = loader.discover(integration_test_dir, pattern='test_*.py')
                    suite.addTest(integration_suite)
                
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
            
            # 特定のディレクトリからテストを検索
            if os.path.exists(test_dir):
                suite = loader.discover(test_dir, pattern='test_*.py')
            else:
                print(f"テストディレクトリが見つかりません: {test_dir}")
                return (0, 0, 1)
        
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
        import traceback
        traceback.print_exc()
        
        # エラー詳細をJSONで保存
        error_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(error_results, f, ensure_ascii=False, indent=2)
        
        return (0, 0, 1)


def run_analysis(frames=1200, headless=True, show_progress=True):
    """
    アドバタイズモードの動作分析を実行
    
    Args:
        frames: 分析するフレーム数
        headless: GUIなしで実行するかどうか
        show_progress: 進捗を表示するかどうか
    
    Returns:
        分析結果の辞書
    """
    try:
        # 分析モジュールをインポート
        from advertise_mode.analyzer.monitor import AdvertiseModeMonitor
        
        # 出力ディレクトリを設定
        output_dir = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 環境変数を設定
        os.environ['ADVERTISE_ANALYSIS_PATH'] = output_dir
        
        # モニターを作成
        monitor = AdvertiseModeMonitor(
            main_module_name="main",
            max_frames=frames,
            headless=headless,
            show_progress=show_progress
        )
        
        # 分析を実行
        print(f"アドバタイズモードの分析を開始します（最大 {frames} フレーム）...")
        monitor.run_analysis()
        
        # 分析結果を返す
        return monitor.analyzer.analysis_results
        
    except Exception as e:
        print(f"分析実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None


def apply_improvements():
    """
    アドバタイズモードの改善パッチを適用
    
    Returns:
        bool: 成功したかどうか
    """
    try:
        # 改善モジュールをインポート
        from advertise_mode.core.improver import AdvertiseModeImprover
        
        # 改善ツールを作成
        improver = AdvertiseModeImprover(main_module_name="main")
        
        # パッチを適用
        print("アドバタイズモードの改善パッチを適用します...")
        improver.apply_patches()
        
        print("改善パッチが正常に適用されました")
        return True
        
    except Exception as e:
        print(f"改善パッチの適用中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='アドバタイズモードのテスト・分析・改善ツール')
    
    # サブコマンドの設定
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # テスト実行コマンド
    test_parser = subparsers.add_parser('test', help='テストを実行')
    test_parser.add_argument('--pattern', type=str, default='*',
                        help='実行するテストのパターン（例: "test_advertise_movement.TestAdvertiseMovement.test_enemy_avoidance"）')
    test_parser.add_argument('--type', type=str, choices=['unit', 'integration', 'all'], default='all',
                        help='実行するテストの種類')
    test_parser.add_argument('--verbose', '-v', type=int, choices=[0, 1, 2, 3], default=2,
                        help='出力の詳細レベル（0: 最小限, 3: 最も詳細）')
    test_parser.add_argument('--quick', '-q', action='store_true',
                        help='高速実行モード（一部のテストをスキップ）')
    test_parser.add_argument('--benchmark', '-b', action='store_true',
                        help='ベンチマークテストを実行')
    test_parser.add_argument('--repeat', '-r', type=int, default=1,
                        help='テストを繰り返す回数')
    
    # 分析実行コマンド
    analyze_parser = subparsers.add_parser('analyze', help='アドバタイズモードの動作を分析')
    analyze_parser.add_argument('--frames', '-f', type=int, default=1200,
                           help='分析するフレーム数')
    analyze_parser.add_argument('--gui', '-g', action='store_true',
                           help='GUIを表示して分析（デフォルトはヘッドレスモード）')
    analyze_parser.add_argument('--quiet', '-q', action='store_true',
                           help='進捗表示を抑制')
    
    # 改善コマンド
    improve_parser = subparsers.add_parser('improve', help='アドバタイズモードの動作を改善')
    
    # 分析・改善・再分析コマンド
    full_parser = subparsers.add_parser('full', help='分析・改善・再分析を一括実行')
    full_parser.add_argument('--frames', '-f', type=int, default=1200,
                         help='分析するフレーム数')
    
    args = parser.parse_args()
    
    # コマンドに基づいて処理を実行
    if args.command == 'test':
        # テスト実行
        total_success = 0
        total_failures = 0
        total_errors = 0
        
        for i in range(args.repeat):
            if args.repeat > 1:
                print(f"\n--- テスト実行 {i+1}/{args.repeat} ---\n")
            
            success, failures, errors = run_tests(
                test_pattern=args.pattern,
                test_type=args.type,
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
        
    elif args.command == 'analyze':
        # 分析実行
        results = run_analysis(
            frames=args.frames,
            headless=not args.gui,
            show_progress=not args.quiet
        )
        
        if results:
            print("\n分析が完了しました。")
            return 0
        else:
            print("\n分析に失敗しました。")
            return 1
            
    elif args.command == 'improve':
        # 改善実行
        success = apply_improvements()
        return 0 if success else 1
        
    elif args.command == 'full':
        # 分析・改善・再分析を一括実行
        print("=== ステップ1: オリジナルの動作を分析 ===")
        original_results = run_analysis(frames=args.frames)
        
        if not original_results:
            print("分析に失敗しました。処理を中止します。")
            return 1
        
        print("\n=== ステップ2: 改善パッチを適用 ===")
        success = apply_improvements()
        
        if not success:
            print("改善パッチの適用に失敗しました。処理を中止します。")
            return 1
        
        print("\n=== ステップ3: 改善後の動作を分析 ===")
        improved_results = run_analysis(frames=args.frames)
        
        if not improved_results:
            print("改善後の分析に失敗しました。")
            return 1
        
        print("\n=== 改善効果の評価 ===")
        # 中央滞在時間比率の改善
        center_improvement = original_results['center_time_ratio'] - improved_results['center_time_ratio']
        print(f"中央滞在時間比率: {original_results['center_time_ratio']:.2%} → {improved_results['center_time_ratio']:.2%} ({center_improvement:.2%}の改善)")
        
        # 振動比率の改善
        vibration_improvement = original_results['vibration_ratio'] - improved_results['vibration_ratio']
        print(f"振動比率: {original_results['vibration_ratio']:.2%} → {improved_results['vibration_ratio']:.2%} ({vibration_improvement:.2%}の改善)")
        
        # 敵回避率の改善
        avoidance_improvement = improved_results['enemy_avoidance_rate'] - original_results['enemy_avoidance_rate']
        print(f"敵回避率: {original_results['enemy_avoidance_rate']:.2%} → {improved_results['enemy_avoidance_rate']:.2%} ({avoidance_improvement:.2%}の改善)")
        
        return 0
        
    else:
        # コマンドが指定されていない場合はヘルプを表示
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main()) 