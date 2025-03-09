"""
自律テストエンジン V2 - モッククラスを使用したバージョン

ゲームテストを連続的に実行し、結果を監視・分析するエンジン
"""

import unittest
import importlib
import sys
import os
import time
import glob
import re
import json
from datetime import datetime

class TestSummary:
    """テスト実行の概要情報を保持するクラス"""
    
    def __init__(self):
        self.total_runs = 0
        self.passed_runs = 0
        self.failed_runs = 0
        self.error_runs = 0
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.recent_failures = []
        self.start_time = datetime.now()
        self.last_run_time = None
        
    def update_from_result(self, result):
        """テスト結果から概要情報を更新"""
        self.total_runs += 1
        self.last_run_time = datetime.now()
        
        self.total_tests += result.testsRun
        self.passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        self.failed_tests += len(result.failures)
        self.error_tests += len(result.errors)
        
        if len(result.failures) == 0 and len(result.errors) == 0:
            self.passed_runs += 1
        elif len(result.errors) > 0:
            self.error_runs += 1
        else:
            self.failed_runs += 1
        
        # 直近の失敗を記録
        for failure in result.failures:
            test_name = failure[0].id()
            error_message = failure[1]
            self.recent_failures.append({
                'test': test_name,
                'type': 'failure',
                'message': error_message,
                'time': datetime.now().strftime('%H:%M:%S')
            })
            
        for error in result.errors:
            test_name = error[0].id()
            error_message = error[1]
            self.recent_failures.append({
                'test': test_name,
                'type': 'error',
                'message': error_message,
                'time': datetime.now().strftime('%H:%M:%S')
            })
        
        # 直近の失敗は最大10件まで保持
        self.recent_failures = self.recent_failures[-10:]
    
    def get_status_report(self):
        """現在のステータスレポートを取得"""
        duration = datetime.now() - self.start_time
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        report = [
            f"実行時間: {hours}時間{minutes}分{seconds}秒",
            f"総実行回数: {self.total_runs}",
            f"成功実行: {self.passed_runs} ({self.passed_runs/self.total_runs*100:.1f}%)" if self.total_runs > 0 else "成功実行: 0 (0.0%)",
            f"失敗実行: {self.failed_runs} ({self.failed_runs/self.total_runs*100:.1f}%)" if self.total_runs > 0 else "失敗実行: 0 (0.0%)",
            f"エラー実行: {self.error_runs} ({self.error_runs/self.total_runs*100:.1f}%)" if self.total_runs > 0 else "エラー実行: 0 (0.0%)",
            f"総テスト数: {self.total_tests}",
            f"成功テスト: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)" if self.total_tests > 0 else "成功テスト: 0 (0.0%)",
            f"失敗テスト: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)" if self.total_tests > 0 else "失敗テスト: 0 (0.0%)",
            f"エラーテスト: {self.error_tests} ({self.error_tests/self.total_tests*100:.1f}%)" if self.total_tests > 0 else "エラーテスト: 0 (0.0%)",
        ]
        
        if self.recent_failures:
            report.append("\n直近の失敗:")
            for failure in self.recent_failures:
                report.append(f"[{failure['time']}] {failure['test']} - {failure['type']}")
                # エラーメッセージの先頭部分を抽出
                message_lines = failure['message'].split('\n')
                if message_lines:
                    report.append(f"  {message_lines[0][:80]}...")
        
        return '\n'.join(report)
    
    def save_to_file(self, filename="test_summary.json"):
        """概要情報をJSONファイルに保存"""
        data = {
            'total_runs': self.total_runs,
            'passed_runs': self.passed_runs,
            'failed_runs': self.failed_runs,
            'error_runs': self.error_runs,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'error_tests': self.error_tests,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'last_run_time': self.last_run_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_run_time else None,
            'recent_failures': self.recent_failures
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

class TestRunner:
    """テスト実行を管理するクラス"""
    
    def __init__(self, test_pattern="test_*.py", verbosity=1):
        self.test_pattern = test_pattern
        self.verbosity = verbosity
        self.summary = TestSummary()
        self.test_files = []
    
    def discover_tests(self):
        """テストファイルを検索"""
        self.test_files = glob.glob(self.test_pattern)
        print(f"発見されたテストファイル: {len(self.test_files)}")
        for file in self.test_files:
            print(f"  - {file}")
        return self.test_files
    
    def run_single_test(self, test_file):
        """単一のテストファイルを実行"""
        # モジュール名を取得（拡張子を除去）
        module_name = os.path.splitext(test_file)[0]
        
        # モジュールがすでに読み込まれている場合は再読み込み
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        try:
            # モジュールを動的に読み込み
            module = importlib.import_module(module_name)
            
            # テストスイートを作成して実行
            suite = unittest.TestLoader().loadTestsFromModule(module)
            result = unittest.TextTestRunner(verbosity=self.verbosity).run(suite)
            
            # 結果を概要に追加
            self.summary.update_from_result(result)
            
            return result
        except Exception as e:
            print(f"テスト実行中にエラーが発生: {e}")
            # ダミーの失敗結果を作成
            result = unittest.TestResult()
            result.testsRun = 1
            result.errors.append((unittest.FunctionTestCase(lambda: None), str(e)))
            self.summary.update_from_result(result)
            return result
    
    def run_all_tests(self):
        """すべてのテストを実行"""
        self.discover_tests()
        
        for test_file in self.test_files:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {test_file} を実行中...")
            result = self.run_single_test(test_file)
            
            print(f"結果: {result.testsRun} テスト実行、失敗 {len(result.failures)}、エラー {len(result.errors)}")
        
        # 概要を表示
        print("\n===== テスト実行概要 =====")
        print(self.summary.get_status_report())
        
        # 概要をファイルに保存
        self.summary.save_to_file()
    
    def run_test_continuously(self, interval=5.0, max_iterations=None):
        """テストを連続して実行"""
        iteration = 0
        
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            print(f"\n===== 実行 #{iteration} =====")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] テスト実行開始")
            
            self.run_all_tests()
            
            if max_iterations is not None and iteration >= max_iterations:
                break
                
            print(f"\n次の実行まで {interval} 秒待機中...")
            time.sleep(interval)

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自律テストエンジン')
    parser.add_argument('--pattern', default='test_*_v2.py', help='テストファイルのパターン')
    parser.add_argument('--verbosity', type=int, default=2, help='テスト詳細度 (1-2)')
    parser.add_argument('--interval', type=float, default=5.0, help='連続実行の間隔（秒）')
    parser.add_argument('--iterations', type=int, default=None, help='最大実行回数')
    parser.add_argument('--single', action='store_true', help='単一実行モード')
    
    args = parser.parse_args()
    
    runner = TestRunner(test_pattern=args.pattern, verbosity=args.verbosity)
    
    if args.single:
        runner.run_all_tests()
    else:
        runner.run_test_continuously(interval=args.interval, max_iterations=args.iterations)

if __name__ == '__main__':
    main() 
自律テストエンジン V2 - モッククラスを使用したバージョン

ゲームテストを連続的に実行し、結果を監視・分析するエンジン
"""

import unittest
import importlib
import sys
import os
import time
import glob
import re
import json
from datetime import datetime

class TestSummary:
    """テスト実行の概要情報を保持するクラス"""
    
    def __init__(self):
        self.total_runs = 0
        self.passed_runs = 0
        self.failed_runs = 0
        self.error_runs = 0
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.recent_failures = []
        self.start_time = datetime.now()
        self.last_run_time = None
        
    def update_from_result(self, result):
        """テスト結果から概要情報を更新"""
        self.total_runs += 1
        self.last_run_time = datetime.now()
        
        self.total_tests += result.testsRun
        self.passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        self.failed_tests += len(result.failures)
        self.error_tests += len(result.errors)
        
        if len(result.failures) == 0 and len(result.errors) == 0:
            self.passed_runs += 1
        elif len(result.errors) > 0:
            self.error_runs += 1
        else:
            self.failed_runs += 1
        
        # 直近の失敗を記録
        for failure in result.failures:
            test_name = failure[0].id()
            error_message = failure[1]
            self.recent_failures.append({
                'test': test_name,
                'type': 'failure',
                'message': error_message,
                'time': datetime.now().strftime('%H:%M:%S')
            })
            
        for error in result.errors:
            test_name = error[0].id()
            error_message = error[1]
            self.recent_failures.append({
                'test': test_name,
                'type': 'error',
                'message': error_message,
                'time': datetime.now().strftime('%H:%M:%S')
            })
        
        # 直近の失敗は最大10件まで保持
        self.recent_failures = self.recent_failures[-10:]
    
    def get_status_report(self):
        """現在のステータスレポートを取得"""
        duration = datetime.now() - self.start_time
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        report = [
            f"実行時間: {hours}時間{minutes}分{seconds}秒",
            f"総実行回数: {self.total_runs}",
            f"成功実行: {self.passed_runs} ({self.passed_runs/self.total_runs*100:.1f}%)" if self.total_runs > 0 else "成功実行: 0 (0.0%)",
            f"失敗実行: {self.failed_runs} ({self.failed_runs/self.total_runs*100:.1f}%)" if self.total_runs > 0 else "失敗実行: 0 (0.0%)",
            f"エラー実行: {self.error_runs} ({self.error_runs/self.total_runs*100:.1f}%)" if self.total_runs > 0 else "エラー実行: 0 (0.0%)",
            f"総テスト数: {self.total_tests}",
            f"成功テスト: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)" if self.total_tests > 0 else "成功テスト: 0 (0.0%)",
            f"失敗テスト: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)" if self.total_tests > 0 else "失敗テスト: 0 (0.0%)",
            f"エラーテスト: {self.error_tests} ({self.error_tests/self.total_tests*100:.1f}%)" if self.total_tests > 0 else "エラーテスト: 0 (0.0%)",
        ]
        
        if self.recent_failures:
            report.append("\n直近の失敗:")
            for failure in self.recent_failures:
                report.append(f"[{failure['time']}] {failure['test']} - {failure['type']}")
                # エラーメッセージの先頭部分を抽出
                message_lines = failure['message'].split('\n')
                if message_lines:
                    report.append(f"  {message_lines[0][:80]}...")
        
        return '\n'.join(report)
    
    def save_to_file(self, filename="test_summary.json"):
        """概要情報をJSONファイルに保存"""
        data = {
            'total_runs': self.total_runs,
            'passed_runs': self.passed_runs,
            'failed_runs': self.failed_runs,
            'error_runs': self.error_runs,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'error_tests': self.error_tests,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'last_run_time': self.last_run_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_run_time else None,
            'recent_failures': self.recent_failures
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

class TestRunner:
    """テスト実行を管理するクラス"""
    
    def __init__(self, test_pattern="test_*.py", verbosity=1):
        self.test_pattern = test_pattern
        self.verbosity = verbosity
        self.summary = TestSummary()
        self.test_files = []
    
    def discover_tests(self):
        """テストファイルを検索"""
        self.test_files = glob.glob(self.test_pattern)
        print(f"発見されたテストファイル: {len(self.test_files)}")
        for file in self.test_files:
            print(f"  - {file}")
        return self.test_files
    
    def run_single_test(self, test_file):
        """単一のテストファイルを実行"""
        # モジュール名を取得（拡張子を除去）
        module_name = os.path.splitext(test_file)[0]
        
        # モジュールがすでに読み込まれている場合は再読み込み
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        try:
            # モジュールを動的に読み込み
            module = importlib.import_module(module_name)
            
            # テストスイートを作成して実行
            suite = unittest.TestLoader().loadTestsFromModule(module)
            result = unittest.TextTestRunner(verbosity=self.verbosity).run(suite)
            
            # 結果を概要に追加
            self.summary.update_from_result(result)
            
            return result
        except Exception as e:
            print(f"テスト実行中にエラーが発生: {e}")
            # ダミーの失敗結果を作成
            result = unittest.TestResult()
            result.testsRun = 1
            result.errors.append((unittest.FunctionTestCase(lambda: None), str(e)))
            self.summary.update_from_result(result)
            return result
    
    def run_all_tests(self):
        """すべてのテストを実行"""
        self.discover_tests()
        
        for test_file in self.test_files:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {test_file} を実行中...")
            result = self.run_single_test(test_file)
            
            print(f"結果: {result.testsRun} テスト実行、失敗 {len(result.failures)}、エラー {len(result.errors)}")
        
        # 概要を表示
        print("\n===== テスト実行概要 =====")
        print(self.summary.get_status_report())
        
        # 概要をファイルに保存
        self.summary.save_to_file()
    
    def run_test_continuously(self, interval=5.0, max_iterations=None):
        """テストを連続して実行"""
        iteration = 0
        
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            print(f"\n===== 実行 #{iteration} =====")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] テスト実行開始")
            
            self.run_all_tests()
            
            if max_iterations is not None and iteration >= max_iterations:
                break
                
            print(f"\n次の実行まで {interval} 秒待機中...")
            time.sleep(interval)

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自律テストエンジン')
    parser.add_argument('--pattern', default='test_*_v2.py', help='テストファイルのパターン')
    parser.add_argument('--verbosity', type=int, default=2, help='テスト詳細度 (1-2)')
    parser.add_argument('--interval', type=float, default=5.0, help='連続実行の間隔（秒）')
    parser.add_argument('--iterations', type=int, default=None, help='最大実行回数')
    parser.add_argument('--single', action='store_true', help='単一実行モード')
    
    args = parser.parse_args()
    
    runner = TestRunner(test_pattern=args.pattern, verbosity=args.verbosity)
    
    if args.single:
        runner.run_all_tests()
    else:
        runner.run_test_continuously(interval=args.interval, max_iterations=args.iterations)

if __name__ == '__main__':
    main() 