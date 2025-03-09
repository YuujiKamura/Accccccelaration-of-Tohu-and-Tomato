#!/usr/bin/env python
"""
メモリ使用量を監視しながらテストを実行するスクリプト

各テストファイルを実行し、メモリ使用量をモニタリングして
高メモリ消費のテストを特定します。
"""

import os
import sys
import time
import psutil
import importlib.util
import unittest
import tracemalloc
from run_single_test import color_print, load_test_module

# カラー表示用コード
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"
BOLD = "\033[1m"

# メモリ使用量計測クラス
class MemoryProfiler:
    """メモリ使用量を計測するクラス"""
    
    def __init__(self, threshold_mb=100):
        """初期化"""
        self.process = psutil.Process(os.getpid())
        self.threshold_mb = threshold_mb
        self.baseline_memory = 0
        self.peak_memory = 0
        self.current_memory = 0
    
    def start(self):
        """計測開始"""
        # トレースマロックを開始
        tracemalloc.start()
        # ベースラインメモリを計測
        self.baseline_memory = self.process.memory_info().rss / (1024 * 1024)  # MB単位
        return self.baseline_memory
    
    def check_memory(self):
        """現在のメモリ使用量をチェック"""
        self.current_memory = self.process.memory_info().rss / (1024 * 1024)
        if self.current_memory > self.peak_memory:
            self.peak_memory = self.current_memory
        
        # しきい値を超えた場合は警告
        if self.current_memory - self.baseline_memory > self.threshold_mb:
            color_print(f"警告: メモリ使用量が閾値を超えました: {self.current_memory:.2f}MB (基準値からの増加: {self.current_memory - self.baseline_memory:.2f}MB)", 
                       RED)
            # トレースマロックのスナップショットを取得して大きなメモリ割り当てを表示
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            print("[ メモリ割り当てトップ10 ]")
            for stat in top_stats[:10]:
                print(f"{stat.size / (1024 * 1024):.2f}MB: {stat.traceback.format()[0]}")
        
        return self.current_memory
    
    def stop(self):
        """計測終了"""
        final_memory = self.process.memory_info().rss / (1024 * 1024)
        memory_increase = final_memory - self.baseline_memory
        # トレースマロックを停止
        tracemalloc.stop()
        return {
            'baseline': self.baseline_memory,
            'peak': self.peak_memory,
            'final': final_memory,
            'increase': memory_increase
        }

# テスト実行しながらメモリ監視
def run_test_with_memory_profile(file_path, interval=0.5, threshold_mb=50, timeout=60):
    """
    テストを実行しながらメモリ使用量を監視
    
    Args:
        file_path: テストファイルのパス
        interval: メモリチェックの間隔(秒)
        threshold_mb: 警告を発する閾値(MB)
        timeout: タイムアウト時間(秒)
    
    Returns:
        テスト結果とメモリ使用状況
    """
    # テストモジュールのロード
    color_print(f"テストファイル '{file_path}' のメモリプロファイリングを開始...", BLUE)
    module = load_test_module(file_path)
    if not module:
        return None, None
    
    # テストスイートの作成
    suite = unittest.TestLoader().loadTestsFromModule(module)
    test_count = suite.countTestCases()
    color_print(f"テスト数: {test_count}", BLUE)
    
    # メモリプロファイラー初期化
    profiler = MemoryProfiler(threshold_mb=threshold_mb)
    baseline = profiler.start()
    color_print(f"ベースラインメモリ: {baseline:.2f}MB", BLUE)
    
    # テスト実行用スレッドの作成
    import threading
    
    # 結果格納用の変数
    test_result = None
    is_completed = False
    has_error = False
    error_msg = ""
    
    # テスト実行関数
    def run_tests():
        nonlocal test_result, is_completed, has_error, error_msg
        try:
            test_result = unittest.TextTestRunner(verbosity=0).run(suite)
            is_completed = True
        except Exception as e:
            has_error = True
            error_msg = str(e)
            traceback.print_exc()
    
    # テスト実行スレッドの開始
    thread = threading.Thread(target=run_tests)
    thread.daemon = True  # メインスレッドが終了したら強制終了
    thread.start()
    
    # メモリ監視ループ
    start_time = time.time()
    memory_samples = []
    
    try:
        while thread.is_alive() and time.time() - start_time < timeout:
            # メモリチェック
            current_memory = profiler.check_memory()
            elapsed = time.time() - start_time
            memory_samples.append((elapsed, current_memory))
            
            # メモリ使用状況の表示（1秒ごと）
            if len(memory_samples) % int(1/interval) == 0:
                color_print(f"実行時間: {elapsed:.1f}秒, メモリ使用量: {current_memory:.2f}MB (増加量: {current_memory - baseline:.2f}MB)", 
                           YELLOW if current_memory - baseline > threshold_mb else BLUE)
            
            # スレッドが終了するまで待機
            time.sleep(interval)
    except KeyboardInterrupt:
        color_print("ユーザーによる中断", RED)
    finally:
        # タイムアウトまたは完了
        if not is_completed and not has_error:
            if time.time() - start_time >= timeout:
                color_print(f"タイムアウト: {timeout}秒を超えました", RED)
                has_error = True
                error_msg = f"タイムアウト({timeout}秒)"
            else:
                color_print("不明な理由で終了", RED)
                has_error = True
                error_msg = "不明な終了理由"
    
    # メモリ使用状況のサマリー
    memory_stats = profiler.stop()
    
    # 結果の表示
    color_print("\nメモリ使用状況:", BLUE, bold=True)
    color_print(f"ベースライン: {memory_stats['baseline']:.2f}MB", BLUE)
    color_print(f"ピーク時: {memory_stats['peak']:.2f}MB (増加: {memory_stats['peak'] - memory_stats['baseline']:.2f}MB)", 
               RED if memory_stats['peak'] - memory_stats['baseline'] > threshold_mb else GREEN)
    color_print(f"終了時: {memory_stats['final']:.2f}MB (増加: {memory_stats['increase']:.2f}MB)", 
               RED if memory_stats['increase'] > threshold_mb else GREEN)
    
    if has_error:
        color_print(f"エラー発生: {error_msg}", RED)
    elif is_completed:
        status = "成功" if test_result.wasSuccessful() else "失敗"
        color = GREEN if test_result.wasSuccessful() else RED
        color_print(f"テスト結果: {status} (成功: {test_result.testsRun - len(test_result.errors) - len(test_result.failures)}/{test_result.testsRun})", color)
    
    return test_result, memory_stats, memory_samples

def analyze_all_test_files(test_dir=None, pattern="test_*.py", exclude=None, threshold_mb=50):
    """
    すべてのテストファイルを分析
    
    Args:
        test_dir: テストディレクトリ
        pattern: テストファイルのパターン
        exclude: 除外するファイル名のリスト
        threshold_mb: メモリ使用量の閾値(MB)
    """
    import glob
    
    # テストディレクトリの設定
    if test_dir is None:
        test_dir = os.path.join(os.getcwd(), "tests")
    
    # テストファイルの検出
    pattern_path = os.path.join(test_dir, "**", pattern)
    test_files = glob.glob(pattern_path, recursive=True)
    
    # 除外パターンを適用
    if exclude:
        filtered_files = []
        for file in test_files:
            if not any(excl in file for excl in exclude):
                filtered_files.append(file)
        test_files = filtered_files
    
    # 相対パスに変換
    test_files = [os.path.relpath(file) for file in test_files]
    
    if not test_files:
        color_print(f"テストファイルが見つかりません: {pattern_path}", RED)
        return
    
    # ファイル数の表示
    color_print(f"\n検出されたテストファイル: {len(test_files)}件", GREEN)
    for i, file in enumerate(test_files, 1):
        print(f"  {i}. {file}")
    
    # 結果の格納
    results = []
    
    # 各ファイルを分析
    for i, file in enumerate(test_files, 1):
        color_print(f"\n[{i}/{len(test_files)}] テストファイル: {file}", GREEN, bold=True)
        try:
            result, memory_stats, _ = run_test_with_memory_profile(file, threshold_mb=threshold_mb)
            
            if result and memory_stats:
                # 結果を格納
                results.append({
                    'file': file,
                    'success': result.wasSuccessful() if result else False,
                    'memory': memory_stats
                })
        except Exception as e:
            color_print(f"分析中にエラーが発生: {str(e)}", RED)
            traceback.print_exc()
    
    # 結果の集計
    if results:
        # メモリ使用量でソート
        results.sort(key=lambda x: x['memory']['peak'] - x['memory']['baseline'], reverse=True)
        
        color_print("\n=== メモリ使用量ランキング ===", BLUE, bold=True)
        for i, result in enumerate(results, 1):
            status = "成功" if result['success'] else "失敗"
            color = GREEN if result['success'] else RED
            memory_increase = result['memory']['peak'] - result['memory']['baseline']
            color_print(f"{i}. {result['file']} - 増加量: {memory_increase:.2f}MB, テスト結果: {color}{status}{RESET}", 
                       RED if memory_increase > threshold_mb else BLUE)
    else:
        color_print("分析結果がありません", YELLOW)

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="テストファイルのメモリプロファイリング")
    parser.add_argument('--file', help='単一のテストファイルを分析')
    parser.add_argument('--dir', help='テストディレクトリ', default=None)
    parser.add_argument('--pattern', help='テストファイルのパターン', default='test_*.py')
    parser.add_argument('--exclude', nargs='*', help='除外するファイルパターン', default=[])
    parser.add_argument('--threshold', type=int, help='メモリ使用量の閾値(MB)', default=50)
    args = parser.parse_args()
    
    # 単一ファイルまたはすべてのファイルを分析
    if args.file:
        run_test_with_memory_profile(args.file, threshold_mb=args.threshold)
    else:
        analyze_all_test_files(args.dir, args.pattern, args.exclude, args.threshold)

if __name__ == '__main__':
    main() 