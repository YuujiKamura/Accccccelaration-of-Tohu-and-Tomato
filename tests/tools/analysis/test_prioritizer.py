"""
テスト優先順位付けモジュール

このモジュールは、テストケースの重要度に基づいて優先順位を付け、
効率的なテスト実行を可能にします。
"""

import os
import sys
import json
import time
import datetime
import unittest
import importlib
import inspect
from collections import defaultdict

class TestPrioritizer:
    """テストの優先順位付けを行うクラス"""
    
    def __init__(self, data_dir="test_priority_data"):
        """
        初期化
        
        Args:
            data_dir: 優先順位データを保存するディレクトリ
        """
        self.data_dir = data_dir
        self.history = {}
        self.impact_scores = {}
        self.priorities = {}
        
        # ディレクトリがなければ作成
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 履歴データを読み込む
        self._load_history()
    
    def _load_history(self):
        """履歴データを読み込む"""
        history_file = os.path.join(self.data_dir, 'test_history.json')
        impact_file = os.path.join(self.data_dir, 'test_impact.json')
        
        # テスト実行履歴
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"履歴データの読み込みに失敗しました: {e}")
                self.history = {}
        
        # テスト影響度スコア
        if os.path.exists(impact_file):
            try:
                with open(impact_file, 'r', encoding='utf-8') as f:
                    self.impact_scores = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"影響度データの読み込みに失敗しました: {e}")
                self.impact_scores = {}
    
    def _save_history(self):
        """履歴データを保存する"""
        history_file = os.path.join(self.data_dir, 'test_history.json')
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2)
        except IOError as e:
            print(f"履歴データの保存に失敗しました: {e}")
    
    def _save_impact_scores(self):
        """影響度スコアを保存する"""
        impact_file = os.path.join(self.data_dir, 'test_impact.json')
        try:
            with open(impact_file, 'w', encoding='utf-8') as f:
                json.dump(self.impact_scores, f, indent=2)
        except IOError as e:
            print(f"影響度データの保存に失敗しました: {e}")
    
    def record_test_run(self, test_name, success, duration, timestamp=None):
        """
        テスト実行結果を記録する
        
        Args:
            test_name: テスト名
            success: 成功したかどうか
            duration: 実行時間
            timestamp: タイムスタンプ（Noneの場合は現在時刻）
        """
        if timestamp is None:
            timestamp = time.time()
        
        if test_name not in self.history:
            self.history[test_name] = []
        
        self.history[test_name].append({
            'success': success,
            'duration': duration,
            'timestamp': timestamp
        })
        
        # 履歴を最大100件に制限
        if len(self.history[test_name]) > 100:
            self.history[test_name] = self.history[test_name][-100:]
        
        # 履歴を保存
        self._save_history()
    
    def set_impact_score(self, test_name, score):
        """
        テストの影響度スコアを設定する
        
        Args:
            test_name: テスト名
            score: 影響度スコア（0.0～1.0）
        """
        self.impact_scores[test_name] = max(0.0, min(1.0, score))
        self._save_impact_scores()
    
    def calculate_priorities(self):
        """
        テストの優先順位を計算する
        
        Returns:
            dict: テスト名と優先順位スコアの辞書
        """
        priorities = {}
        
        for test_name, runs in self.history.items():
            # 1. 失敗率（より多く失敗するテストを優先）
            failure_rate = 0
            if runs:
                failures = sum(1 for run in runs if not run['success'])
                failure_rate = failures / len(runs)
            
            # 2. 最近の失敗（最近失敗したテストを優先）
            recent_failure_weight = 0
            if runs:
                # 最新の実行結果を取得
                runs.sort(key=lambda x: x['timestamp'], reverse=True)
                latest_runs = runs[:10]  # 最新10件
                
                # 最近の失敗に重みを付ける
                weighted_failures = 0
                total_weight = 0
                for i, run in enumerate(latest_runs):
                    weight = 1.0 / (i + 1)  # 最新のものほど重み大
                    weighted_failures += (0 if run['success'] else weight)
                    total_weight += weight
                
                if total_weight > 0:
                    recent_failure_weight = weighted_failures / total_weight
            
            # 3. 実行時間（短いテストを優先）
            avg_duration = 0
            if runs:
                durations = [run['duration'] for run in runs]
                avg_duration = sum(durations) / len(durations)
                # 長いテストほど優先度が下がるように正規化（最大で1時間と仮定）
                duration_score = 1.0 - min(1.0, avg_duration / 3600)
            else:
                duration_score = 0.5  # デフォルト値
            
            # 4. 影響度スコア
            impact_score = self.impact_scores.get(test_name, 0.5)  # デフォルトは中程度
            
            # 優先順位スコアの計算（各要素に重みを付ける）
            priority_score = (
                0.4 * failure_rate +            # 失敗率（40%）
                0.3 * recent_failure_weight +   # 最近の失敗（30%）
                0.1 * duration_score +          # 実行時間（10%）
                0.2 * impact_score              # 影響度（20%）
            )
            
            priorities[test_name] = priority_score
        
        # 未実行のテストを追加（デフォルト優先度）
        for test_name in self.impact_scores:
            if test_name not in priorities:
                priorities[test_name] = 0.2 * self.impact_scores[test_name]
        
        self.priorities = priorities
        return priorities
    
    def get_prioritized_tests(self, test_suite=None):
        """
        優先順位付けされたテストリストを取得する
        
        Args:
            test_suite: テストスイート（Noneの場合は履歴データから優先順位を計算）
            
        Returns:
            list: (テスト、優先度スコア) のタプルのリスト（優先度順）
        """
        # 優先順位を計算
        priorities = self.calculate_priorities()
        
        if test_suite is None:
            # 履歴データから優先順位リストを作成
            prioritized_tests = [(name, score) for name, score in priorities.items()]
            prioritized_tests.sort(key=lambda x: x[1], reverse=True)
            return prioritized_tests
        else:
            # テストスイートから優先順位リストを作成
            prioritized_suite = []
            
            # スイートからテストを取得
            for test in get_tests_from_suite(test_suite):
                test_name = get_test_name(test)
                priority = priorities.get(test_name, 0)
                prioritized_suite.append((test, priority))
            
            # 優先度でソート
            prioritized_suite.sort(key=lambda x: x[1], reverse=True)
            return prioritized_suite
    
    def analyze_module(self, module_name):
        """
        モジュール内のテストを分析して影響度スコアを自動設定する
        
        Args:
            module_name: モジュール名
            
        Returns:
            dict: テスト名と影響度スコアの辞書
        """
        try:
            # モジュールをインポート
            module = importlib.import_module(module_name)
            
            # テストクラスを探す
            test_classes = []
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                    test_classes.append(obj)
            
            impact_scores = {}
            
            for test_class in test_classes:
                # テストメソッドを探す
                test_methods = []
                for name, method in inspect.getmembers(test_class, predicate=inspect.isfunction):
                    if name.startswith('test_'):
                        test_methods.append(name)
                
                # デフォルト値を設定
                for method_name in test_methods:
                    test_name = f"{module_name}.{test_class.__name__}.{method_name}"
                    
                    # パフォーマンス関連テスト
                    if 'performance' in test_name.lower() or 'benchmark' in test_name.lower():
                        impact_scores[test_name] = 0.9
                    # UI, コアロジック関連テスト
                    elif 'ui' in test_name.lower() or 'core' in test_name.lower() or 'critical' in test_name.lower():
                        impact_scores[test_name] = 0.8
                    # 通常のテスト
                    else:
                        impact_scores[test_name] = 0.5
            
            # 影響度スコアを更新
            for test_name, score in impact_scores.items():
                self.set_impact_score(test_name, score)
            
            return impact_scores
            
        except ImportError as e:
            print(f"モジュールのインポートに失敗しました: {e}")
            return {}
    
    def generate_report(self, output_file=None):
        """
        優先順位レポートを生成する
        
        Args:
            output_file: 出力ファイル名
            
        Returns:
            str: レポートファイルのパス
        """
        # 優先順位を計算
        priorities = self.calculate_priorities()
        prioritized_tests = [(name, score) for name, score in priorities.items()]
        prioritized_tests.sort(key=lambda x: x[1], reverse=True)
        
        # 出力ファイル名
        if output_file is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.data_dir, f'priority_report_{timestamp}.txt')
        
        # レポートを生成
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("===== テスト優先順位レポート =====\n")
            f.write(f"生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("優先順位の高いテスト（上位20件）:\n")
            for i, (test_name, score) in enumerate(prioritized_tests[:20], 1):
                f.write(f"{i}. {test_name} (スコア: {score:.4f})\n")
            
            f.write("\n失敗率の高いテスト（上位10件）:\n")
            failure_rates = []
            for test_name, runs in self.history.items():
                if runs:
                    failures = sum(1 for run in runs if not run['success'])
                    failure_rate = failures / len(runs)
                    failure_rates.append((test_name, failure_rate))
            
            failure_rates.sort(key=lambda x: x[1], reverse=True)
            for i, (test_name, rate) in enumerate(failure_rates[:10], 1):
                f.write(f"{i}. {test_name} (失敗率: {rate:.2%})\n")
            
            f.write("\n実行時間の長いテスト（上位10件）:\n")
            durations = []
            for test_name, runs in self.history.items():
                if runs:
                    avg_duration = sum(run['duration'] for run in runs) / len(runs)
                    durations.append((test_name, avg_duration))
            
            durations.sort(key=lambda x: x[1], reverse=True)
            for i, (test_name, duration) in enumerate(durations[:10], 1):
                f.write(f"{i}. {test_name} (平均実行時間: {duration:.2f}秒)\n")
            
            f.write("\n影響度の高いテスト（上位10件）:\n")
            impacts = [(name, score) for name, score in self.impact_scores.items()]
            impacts.sort(key=lambda x: x[1], reverse=True)
            for i, (test_name, score) in enumerate(impacts[:10], 1):
                f.write(f"{i}. {test_name} (影響度: {score:.2f})\n")
        
        return output_file


def get_test_name(test):
    """
    テストの完全な名前を取得する
    
    Args:
        test: テストケースまたはテストメソッド
        
    Returns:
        str: テスト名
    """
    if hasattr(test, '_testMethodName'):
        # TestCaseインスタンスの場合
        method_name = test._testMethodName
        cls_name = test.__class__.__name__
        module_name = test.__class__.__module__
        return f"{module_name}.{cls_name}.{method_name}"
    elif isinstance(test, type) and issubclass(test, unittest.TestCase):
        # TestCaseクラスの場合
        return f"{test.__module__}.{test.__name__}"
    else:
        # その他の場合
        return str(test)


def get_tests_from_suite(suite):
    """
    スイートからすべてのテストを取得する
    
    Args:
        suite: テストスイート
        
    Returns:
        list: テストのリスト
    """
    tests = []
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            # サブスイートの場合は再帰的に処理
            tests.extend(get_tests_from_suite(test))
        else:
            # テストケースの場合はリストに追加
            tests.append(test)
    return tests


def prioritize_test_suite(suite, prioritizer=None):
    """
    テストスイートの優先順位を付ける
    
    Args:
        suite: テストスイート
        prioritizer: TestPrioritizer インスタンス
        
    Returns:
        unittest.TestSuite: 優先順位付けされたテストスイート
    """
    if prioritizer is None:
        prioritizer = TestPrioritizer()
    
    # スイートからテストを取得
    tests = get_tests_from_suite(suite)
    
    # 優先順位付け
    prioritized_tests = prioritizer.get_prioritized_tests(tests)
    
    # 新しいスイートを作成
    prioritized_suite = unittest.TestSuite()
    for test, _ in prioritized_tests:
        prioritized_suite.addTest(test)
    
    return prioritized_suite


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='テスト優先順位付けツール')
    parser.add_argument('--analyze', type=str, help='モジュールを分析して影響度スコアを設定する')
    parser.add_argument('--report', action='store_true', help='優先順位レポートを生成する')
    parser.add_argument('--output', type=str, default=None, help='出力ファイル名')
    parser.add_argument('--record', action='store_true', help='テスト実行結果を記録するデモを実行')
    
    args = parser.parse_args()
    
    # 優先順位付けクラスを初期化
    prioritizer = TestPrioritizer()
    
    if args.analyze:
        # モジュールを分析
        impact_scores = prioritizer.analyze_module(args.analyze)
        print(f"\n===== モジュール {args.analyze} の影響度スコア =====")
        for test_name, score in impact_scores.items():
            print(f"{test_name}: {score:.2f}")
    
    elif args.report:
        # レポートを生成
        output_file = prioritizer.generate_report(args.output)
        print(f"優先順位レポートを生成しました: {os.path.abspath(output_file)}")
    
    elif args.record:
        # テスト実行結果を記録するデモ
        import random
        
        print("\n===== テスト実行結果の記録デモ =====")
        test_modules = ['test_game_logic', 'test_player_dash', 'test_performance']
        
        for module in test_modules:
            for i in range(3):
                test_name = f"{module}.TestClass.test_method_{i}"
                success = random.random() > 0.3  # 70%の確率で成功
                duration = random.uniform(0.1, 5.0)  # 0.1〜5秒の実行時間
                
                prioritizer.record_test_run(test_name, success, duration)
                status = "成功" if success else "失敗"
                print(f"{test_name}: {status} ({duration:.2f}秒)")
        
        # 優先順位を計算して表示
        priorities = prioritizer.calculate_priorities()
        print("\n===== 計算された優先順位 =====")
        
        prioritized_tests = [(name, score) for name, score in priorities.items()]
        prioritized_tests.sort(key=lambda x: x[1], reverse=True)
        
        for i, (test_name, score) in enumerate(prioritized_tests, 1):
            print(f"{i}. {test_name} (スコア: {score:.4f})")
    
    else:
        parser.print_help() 