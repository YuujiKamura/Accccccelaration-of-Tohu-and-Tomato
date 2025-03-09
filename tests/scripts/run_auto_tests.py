"""
自動テスト実行スクリプト

このスクリプトは、GUIなしでゲームのすべてのテストを自動的に実行します。
テスト結果を収集し、レポートを生成します。
CI/CD環境での実行に最適化されています。
"""

import os
import sys
import unittest
import importlib
import time
import argparse
import datetime
import json
from unittest.mock import patch

def setup_test_environment():
    """テスト環境をセットアップする"""
    print("テスト環境をセットアップしています...")
    
    # テスト基底クラスがあるかどうか確認
    try:
        from tests.unit.test_base import GameTestBase
        print("テスト基底クラスを使用します")
    except ImportError:
        print("警告: test_base.pyが見つかりません。環境構築が不完全です。")
        return False
    
    return True

def discover_tests(test_pattern=None):
    """テストを検出する"""
    if test_pattern:
        # 特定のパターンに一致するテストのみ実行
        print(f"パターン '{test_pattern}' に一致するテストを検出しています...")
        return unittest.defaultTestLoader.discover('.', pattern=test_pattern)
    else:
        # すべてのテストファイルを検出
        print("すべてのテストを検出しています...")
        return unittest.defaultTestLoader.discover('.', pattern='test_*.py')

def run_tests(test_suite, verbosity=1, output_file=None):
    """テストを実行し、結果を収集する"""
    # テストランナーを設定
    if output_file:
        # 結果をファイルに出力
        with open(output_file, 'w') as f:
            runner = unittest.TextTestRunner(stream=f, verbosity=verbosity)
            result = runner.run(test_suite)
    else:
        # 結果を標準出力に表示
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(test_suite)
    
    # 実行結果の概要
    summary = {
        'total': result.testsRun,
        'passed': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
        'failed': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0
    }
    
    return summary, result

def generate_report(summary, result, test_duration, output_dir='test_reports'):
    """テスト結果のレポートを生成する"""
    # 出力ディレクトリが存在しなければ作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # タイムスタンプを含むファイル名
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(output_dir, f'test_report_{timestamp}.json')
    
    # 詳細な結果を収集
    failures = [{'test': str(test), 'message': err} for test, err in result.failures]
    errors = [{'test': str(test), 'message': err} for test, err in result.errors]
    
    # レポートデータ
    report_data = {
        'timestamp': timestamp,
        'summary': summary,
        'duration': test_duration,
        'failures': failures,
        'errors': errors
    }
    
    # JSONファイルに出力
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"テストレポートを生成しました: {report_file}")
    return report_file

def format_duration(seconds):
    """秒数を読みやすい形式にフォーマットする"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{int(hours)}時間 {int(minutes)}分 {seconds:.2f}秒"
    elif minutes > 0:
        return f"{int(minutes)}分 {seconds:.2f}秒"
    else:
        return f"{seconds:.2f}秒"

def main():
    """メイン実行関数"""
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='ゲーム自動テスト実行システム')
    parser.add_argument('--pattern', dest='pattern', default=None,
                      help='テストファイルの検出パターン (例: test_basic*.py)')
    parser.add_argument('--verbosity', dest='verbosity', type=int, default=1,
                      help='テスト出力の詳細レベル (1-3)')
    parser.add_argument('--output', dest='output', default=None,
                      help='テスト出力を保存するファイル')
    parser.add_argument('--report', dest='report', action='store_true',
                      help='テストレポートを生成する')
    parser.add_argument('--report-dir', dest='report_dir', default='test_reports',
                      help='テストレポートの出力ディレクトリ')
    
    args = parser.parse_args()
    
    # テスト環境のセットアップ
    if not setup_test_environment():
        print("テスト環境のセットアップに失敗しました。終了します。")
        return 1
    
    # テストの検出
    test_suite = discover_tests(args.pattern)
    
    # テストの実行時間計測
    start_time = time.time()
    
    # テストの実行
    summary, result = run_tests(test_suite, args.verbosity, args.output)
    
    # 経過時間計算
    end_time = time.time()
    duration = end_time - start_time
    
    # 結果の表示
    print("\nテスト実行結果:")
    print(f"合計テスト数: {summary['total']}")
    print(f"成功: {summary['passed']}")
    print(f"失敗: {summary['failed']}")
    print(f"エラー: {summary['errors']}")
    print(f"スキップ: {summary['skipped']}")
    print(f"成功率: {summary['success_rate'] * 100:.2f}%")
    print(f"実行時間: {format_duration(duration)}")
    
    # レポートの生成
    if args.report:
        report_file = generate_report(summary, result, duration, args.report_dir)
    
    # 終了コードの設定（失敗またはエラーがあれば非ゼロ）
    if summary['failed'] > 0 or summary['errors'] > 0:
        return 1
    else:
        return 0

if __name__ == "__main__":
    # import時にPygameのGUIが表示されるのを防ぐためにpygameをモック化
    sys.modules['pygame'] = unittest.mock.MagicMock()
    
    # プログラム実行
    exit_code = main()
    sys.exit(exit_code) 