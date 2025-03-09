import unittest
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

class BaseTestCase(unittest.TestCase):
    """
    テスト用の基本クラス
    
    機能:
    - テスト実行時間の計測
    - テスト実行情報の記録
    - レポート出力機能
    """
    
    # クラス変数でテスト結果を蓄積
    _test_results = []
    _test_categories = set()
    _start_time = None
    _end_time = None
    
    @classmethod
    def setUpClass(cls):
        """クラス内の全テスト開始前の処理"""
        super().setUpClass()
        cls._test_results = []
        cls._start_time = time.time()
    
    @classmethod
    def tearDownClass(cls):
        """クラス内の全テスト終了後の処理"""
        super().tearDownClass()
        cls._end_time = time.time()
        cls._test_categories.add(cls.__name__)
    
    def setUp(self):
        """各テスト開始前の処理"""
        self._test_start_time = time.time()
        # テスト名からカテゴリを抽出 (例: test_movement_diagonal → movement)
        self._current_test_name = self._testMethodName
        self._current_test_doc = getattr(self, self._testMethodName).__doc__ or ""
        # テスト結果を初期化
        self._test_success = True
        self._test_error_type = None
        self._test_error_message = None
        
    def tearDown(self):
        """各テスト終了後の処理"""
        test_end_time = time.time()
        execution_time = test_end_time - self._test_start_time
        
        # テストメソッド名からカテゴリを抽出
        # 例: test_movement_diagonal → movement
        category = None
        if self._current_test_name.startswith('test_'):
            parts = self._current_test_name[5:].split('_')
            if parts:
                category = parts[0]
                
        # _outcomeオブジェクトから結果を取得（unittestの内部APIを使用）
        test_success = True
        error_type = None
        error_message = None
        
        if hasattr(self, '_outcome') and hasattr(self._outcome, 'errors'):
            # Python 3.4+
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
            if len(result.failures) > 0 or len(result.errors) > 0:
                test_success = False
                if len(result.failures) > 0:
                    error_type = "AssertionError"
                    error_message = result.failures[0][1]
                else:
                    error_type = "Error"
                    error_message = result.errors[0][1]
        
        # テスト結果を記録
        result = {
            'test_name': self._current_test_name,
            'class_name': self.__class__.__name__,
            'category': category,
            'description': self._current_test_doc.strip(),
            'execution_time': execution_time,
            'success': test_success,
            'error_type': error_type,
            'error_message': error_message,
        }
        
        self.__class__._test_results.append(result)
    
    @classmethod
    def generate_report(cls, file_path: Optional[str] = None, print_report: bool = True) -> Dict:
        """
        テスト結果のレポートを生成する
        
        Args:
            file_path: レポートを出力するファイルパス (None の場合は出力しない)
            print_report: 標準出力にレポートを表示するかどうか
            
        Returns:
            レポートのデータ辞書
        """
        # 実行時間の計算
        total_execution_time = cls._end_time - cls._start_time if cls._end_time else 0
        
        # テスト結果の集計
        total_tests = len(cls._test_results)
        successful_tests = sum(1 for r in cls._test_results if r['success'])
        failed_tests = total_tests - successful_tests
        
        # カテゴリごとのテスト数とパス率
        categories = {}
        for result in cls._test_results:
            category = result['category'] or 'unknown'
            if category not in categories:
                categories[category] = {'total': 0, 'passed': 0, 'failed': 0}
            
            categories[category]['total'] += 1
            if result['success']:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
        
        # カテゴリごとのパス率を計算
        for category, stats in categories.items():
            stats['pass_rate'] = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
        
        # テストクラスごとの統計
        class_stats = {}
        for result in cls._test_results:
            class_name = result['class_name']
            if class_name not in class_stats:
                class_stats[class_name] = {'total': 0, 'passed': 0, 'failed': 0}
            
            class_stats[class_name]['total'] += 1
            if result['success']:
                class_stats[class_name]['passed'] += 1
            else:
                class_stats[class_name]['failed'] += 1
        
        # クラスごとのパス率を計算
        for class_name, stats in class_stats.items():
            stats['pass_rate'] = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
        
        # 失敗したテストの詳細
        failed_test_details = [
            {
                'test_name': r['test_name'],
                'class_name': r['class_name'],
                'category': r['category'],
                'description': r['description'],
                'error_type': r['error_type'],
                'error_message': r['error_message'],
            }
            for r in cls._test_results if not r['success']
        ]
        
        # レポートの作成
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_execution_time': total_execution_time,
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'pass_rate': (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            'categories': categories,
            'class_stats': class_stats,
            'failed_test_details': failed_test_details,
            'test_results': cls._test_results,
        }
        
        # レポートの出力
        if print_report:
            cls._print_report(report)
        
        # ファイルへの出力
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    @staticmethod
    def _print_report(report: Dict):
        """レポートを標準出力に表示する"""
        print("\n" + "="*80)
        print(f"テスト実行レポート ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print("="*80)
        
        print(f"\n実行時間: {report['total_execution_time']:.2f}秒")
        print(f"全テスト数: {report['total_tests']}")
        print(f"成功: {report['successful_tests']}")
        print(f"失敗: {report['failed_tests']}")
        print(f"パス率: {report['pass_rate']:.1f}%\n")
        
        # カテゴリごとの結果
        print("カテゴリ別テスト結果:")
        print("-"*60)
        print(f"{'カテゴリ':<20} {'全体':<8} {'成功':<8} {'失敗':<8} {'パス率':<8}")
        print("-"*60)
        for category, stats in sorted(report['categories'].items()):
            print(f"{category:<20} {stats['total']:<8} {stats['passed']:<8} {stats['failed']:<8} {stats['pass_rate']:.1f}%")
        
        # クラスごとの結果
        print("\nクラス別テスト結果:")
        print("-"*60)
        print(f"{'クラス':<30} {'全体':<8} {'成功':<8} {'失敗':<8} {'パス率':<8}")
        print("-"*60)
        for class_name, stats in sorted(report['class_stats'].items()):
            print(f"{class_name:<30} {stats['total']:<8} {stats['passed']:<8} {stats['failed']:<8} {stats['pass_rate']:.1f}%")
        
        # 失敗したテストの詳細
        if report['failed_tests'] > 0:
            print("\n失敗したテスト:")
            print("-"*80)
            for i, test in enumerate(report['failed_test_details'], 1):
                print(f"{i}. {test['class_name']}.{test['test_name']}")
                if test['description']:
                    print(f"   説明: {test['description']}")
                print(f"   エラー: {test['error_type']}: {test['error_message']}")
                print()
        
        print("="*80) 