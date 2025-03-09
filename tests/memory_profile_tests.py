#!/usr/bin/env python
"""
テスト実行時のメモリ使用量プロファイリングツール

テストファイルごとのメモリ使用量を測定し、高負荷の原因となるテストを特定します。
"""

import os
import sys
import glob
import time
import argparse
import unittest
import importlib
import traceback
import gc

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_root)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# psutilがインストールされているか確認
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("警告: psutilがインストールされていません。正確なメモリ使用量を測定できません。")
    print("インストールするには: pip install psutil")

class TestMemoryProfiler:
    """テストのメモリ使用量をプロファイリングするクラス"""
    
    def __init__(self, test_dir='tests', patterns=None, verbose=1):
        """
        初期化
        
        Args:
            test_dir: テストディレクトリ
            patterns: テストファイルのパターン（例: ['test_dash*.py']）
            verbose: 詳細度（0-2）
        """
        self.test_dir = test_dir
        self.patterns = patterns or ['test_*.py']
        self.verbose = verbose
        self.results = []
    
    def get_memory_usage(self):
        """現在のプロセスのメモリ使用量を取得"""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            # RSS (Resident Set Size) - 実際に使用されている物理メモリ
            return process.memory_info().rss / (1024 * 1024)  # MB単位
        return 0
    
    def find_test_files(self):
        """テストファイルを検索"""
        test_files = []
        
        for pattern in self.patterns:
            search_path = os.path.join(self.test_dir, '**', pattern)
            test_files.extend(glob.glob(search_path, recursive=True))
        
        return test_files
    
    def _import_test_module(self, test_file):
        """テストモジュールをインポート"""
        # ファイルパスからモジュールパスを作成
        rel_path = os.path.relpath(test_file, os.path.dirname(project_root))
        module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
        
        try:
            # 明示的にGCを実行してメモリを解放
            gc.collect()
            
            # モジュールをインポート
            module = importlib.import_module(module_path)
            return module
        except Exception as e:
            if self.verbose >= 1:
                print(f"エラー: モジュール '{module_path}' のインポートに失敗しました:")
                print(f"  {type(e).__name__}: {str(e)}")
                if self.verbose >= 2:
                    traceback.print_exc()
            return None
    
    def _find_test_cases(self, module):
        """モジュール内のテストケースクラスを検索"""
        test_cases = []
        
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj is not unittest.TestCase:
                test_cases.append(obj)
        
        return test_cases
    
    def profile_test_file(self, test_file):
        """テストファイルのメモリ使用量をプロファイリング"""
        if self.verbose >= 1:
            print(f"プロファイリング: {test_file}")
        
        # テストモジュールを取得
        module = self._import_test_module(test_file)
        if not module:
            return {
                'file': test_file,
                'success': False,
                'error': 'インポートエラー',
                'memory_before': 0,
                'memory_after': 0,
                'memory_diff': 0
            }
        
        # テストケースを取得
        test_cases = self._find_test_cases(module)
        if not test_cases:
            if self.verbose >= 1:
                print(f"  警告: テストケースが見つかりませんでした")
            return {
                'file': test_file,
                'success': False,
                'error': 'テストケースなし',
                'memory_before': 0,
                'memory_after': 0,
                'memory_diff': 0
            }
        
        # 初期メモリ使用量を測定
        gc.collect()  # 正確な測定のためにGCを実行
        memory_before = self.get_memory_usage()
        
        # テストを実行
        total_tests = 0
        success_tests = 0
        try:
            for test_case in test_cases:
                if self.verbose >= 2:
                    print(f"  テストケース実行: {test_case.__name__}")
                
                suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_case)
                result = unittest.TextTestRunner(verbosity=0).run(suite)
                
                total_tests += result.testsRun
                success_tests += result.testsRun - len(result.errors) - len(result.failures)
        except Exception as e:
            if self.verbose >= 1:
                print(f"  エラー: テスト実行中に例外が発生しました:")
                print(f"    {type(e).__name__}: {str(e)}")
                if self.verbose >= 2:
                    traceback.print_exc()
            return {
                'file': test_file,
                'success': False,
                'error': f'{type(e).__name__}: {str(e)}',
                'memory_before': memory_before,
                'memory_after': 0,
                'memory_diff': 0
            }
        
        # 実行後のメモリ使用量を測定
        memory_after = self.get_memory_usage()
        memory_diff = memory_after - memory_before
        
        if self.verbose >= 1:
            print(f"  メモリ使用量: {memory_before:.2f}MB -> {memory_after:.2f}MB (差分: {memory_diff:.2f}MB)")
            print(f"  テスト実行: {success_tests}/{total_tests} 成功")
            
        return {
            'file': test_file,
            'success': True,
            'total_tests': total_tests,
            'success_tests': success_tests,
            'memory_before': memory_before,
            'memory_after': memory_after,
            'memory_diff': memory_diff
        }
    
    def run_profiling(self):
        """すべてのテストファイルのプロファイリングを実行"""
        print(f"=" * 80)
        print(f"テスト実行のメモリプロファイリングを開始")
        print(f"テストディレクトリ: {self.test_dir}")
        print(f"パターン: {', '.join(self.patterns)}")
        print(f"=" * 80)
        
        # テストファイルを検索
        test_files = self.find_test_files()
        print(f"{len(test_files)}個のテストファイルが見つかりました\n")
        
        if not test_files:
            print("プロファイリングを終了します。")
            return []
        
        # 各ファイルのプロファイリングを実行
        for test_file in test_files:
            result = self.profile_test_file(test_file)
            self.results.append(result)
            print("")  # ファイル間の区切り
        
        return self.results
    
    def print_summary(self):
        """結果のサマリーを表示"""
        if not self.results:
            print("結果がありません。")
            return
        
        print(f"=" * 80)
        print(f"メモリプロファイリング結果のサマリー")
        print(f"=" * 80)
        
        # 結果を記憶分析の多い順に並び替え
        sorted_results = sorted([r for r in self.results if r['success']], 
                               key=lambda x: x['memory_diff'], reverse=True)
        
        failed_results = [r for r in self.results if not r['success']]
        
        # 結果を表示 - メモリ使用量の多い順
        print("\nメモリ使用量の多いテスト（降順）:")
        print("-" * 80)
        print(f"{'ファイル':<40} {'メモリ増加(MB)':<15} {'テスト数':<10} {'成功率':<10}")
        print("-" * 80)
        
        for result in sorted_results:
            success_rate = 100.0 * result['success_tests'] / result['total_tests'] if result['total_tests'] > 0 else 0
            filename = os.path.basename(result['file'])
            print(f"{filename:<40} {result['memory_diff']:<15.2f} {result['total_tests']:<10} {success_rate:<10.1f}%")
        
        # 失敗したテスト
        if failed_results:
            print("\n失敗したテスト:")
            print("-" * 80)
            for result in failed_results:
                print(f"{os.path.basename(result['file'])}: {result.get('error', '不明なエラー')}")
        
        # 総括
        total_memory = sum(r['memory_diff'] for r in self.results if r['success'])
        total_tests = sum(r['total_tests'] for r in self.results if r['success'])
        successful_tests = sum(r['success_tests'] for r in self.results if r['success'])
        
        print("\n総括:")
        print(f"合計テストファイル数: {len(self.results)}（成功: {len(sorted_results)}, 失敗: {len(failed_results)}）")
        print(f"合計テストケース数: {total_tests}（成功: {successful_tests}, 失敗: {total_tests - successful_tests}）")
        print(f"合計メモリ増加: {total_memory:.2f}MB")
        
        print("\n推奨アクション:")
        if sorted_results and sorted_results[0]['memory_diff'] > 50:
            print(f"1. {os.path.basename(sorted_results[0]['file'])}のメモリ使用量が特に多いです。最適化を検討してください。")
        
        if any(r['memory_diff'] > 20 for r in sorted_results):
            print("2. メモリリークの可能性があるテストがあります。リソースの適切な解放を確認してください。")
            
        print("3. テスト間での状態の分離が不十分な可能性があります。クラスレベルの変数や初期化を確認してください。")
        
        print(f"=" * 80)

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='テスト実行のメモリプロファイリング')
    parser.add_argument('-d', '--directory', default='tests', help='テストディレクトリ（デフォルト: tests）')
    parser.add_argument('-p', '--patterns', nargs='+', default=['test_*.py'], help='テストファイルのパターン（デフォルト: test_*.py）')
    parser.add_argument('-v', '--verbose', type=int, choices=[0, 1, 2], default=1, help='詳細度（0: 最小, 1: 通常, 2: 詳細）')
    
    args = parser.parse_args()
    
    profiler = TestMemoryProfiler(
        test_dir=args.directory,
        patterns=args.patterns,
        verbose=args.verbose
    )
    
    profiler.run_profiling()
    profiler.print_summary()

if __name__ == "__main__":
    main() 