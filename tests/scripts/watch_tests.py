"""
テスト監視自動実行スクリプト

ファイルの変更を監視し、変更があった場合に自動的にテストを実行します。
REPループ（Read-Eval-Print）を高速化し、迅速なフィードバックを提供します。
"""

import os
import sys
import time
import datetime
import subprocess
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 監視対象の拡張子
WATCHED_EXTENSIONS = ['.py']

# 最小実行間隔（秒）- 連続した変更イベントによる頻繁なテスト実行を防ぐ
MIN_EXECUTION_INTERVAL = 2.0

# 最後のテスト実行時刻
last_execution_time = 0

class TestEventHandler(FileSystemEventHandler):
    """ファイル変更イベントを処理するハンドラー"""
    
    def __init__(self, test_command, include_patterns=None, exclude_patterns=None):
        self.test_command = test_command
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        
    def on_modified(self, event):
        """ファイル変更イベントを処理"""
        global last_execution_time
        
        # ディレクトリの場合は無視
        if event.is_directory:
            return
            
        # ファイルパスの取得
        file_path = event.src_path
        _, file_ext = os.path.splitext(file_path)
        
        # 拡張子のチェック
        if file_ext.lower() not in WATCHED_EXTENSIONS:
            return
            
        # 監視対象パターンのチェック
        if self.include_patterns and not any(pattern in file_path for pattern in self.include_patterns):
            return
            
        # 除外パターンのチェック
        if any(pattern in file_path for pattern in self.exclude_patterns):
            return
            
        # 最小実行間隔のチェック
        current_time = time.time()
        if current_time - last_execution_time < MIN_EXECUTION_INTERVAL:
            return
        
        # テスト実行
        last_execution_time = current_time
        self._run_tests(file_path)
        
    def _run_tests(self, changed_file):
        """テストを実行"""
        print("\n" + "=" * 80)
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 変更を検知: {os.path.basename(changed_file)}")
        print("テストを実行します...")
        print("=" * 80)
        
        # テストコマンドの実行
        try:
            # テストコマンドに変更ファイルのパターンを追加
            test_file_pattern = self._get_test_pattern(changed_file)
            cmd = self.test_command
            
            if test_file_pattern:
                cmd = f"{cmd} {test_file_pattern}"
            
            print(f"実行コマンド: {cmd}")
            process = subprocess.Popen(cmd, shell=True)
            process.wait()
            
            # 結果の表示
            if process.returncode == 0:
                print("\n✓ テスト成功!")
            else:
                print(f"\n✗ テスト失敗 (終了コード: {process.returncode})")
                
        except Exception as e:
            print(f"テスト実行中にエラーが発生しました: {e}")
    
    def _get_test_pattern(self, file_path):
        """変更ファイルに対応するテストパターンを取得"""
        filename = os.path.basename(file_path)
        
        # テストファイルが変更された場合
        if filename.startswith('test_'):
            return filename
            
        # 実装ファイルが変更された場合、対応するテストファイルを探す
        module_name = os.path.splitext(filename)[0]
        test_file = f'test_{module_name}.py'
        
        # 対応するテストファイルが存在するかチェック
        if os.path.exists(test_file):
            return test_file
            
        # 新しい命名規則のテストファイルをチェック
        test_file_new = f'test_{module_name}_new.py'
        if os.path.exists(test_file_new):
            return test_file_new
            
        # 対応するテストが見つからない場合、None を返す
        return None

def start_watching(args):
    """ファイル監視を開始"""
    print("ファイル変更の監視を開始します...")
    print(f"監視対象ディレクトリ: {args.directory}")
    
    if args.include:
        print(f"監視対象パターン: {', '.join(args.include)}")
    if args.exclude:
        print(f"除外パターン: {', '.join(args.exclude)}")
        
    print(f"テストコマンド: {args.command}")
    print("(Ctrl+C で終了)")
    print("\n変更を待機中...")
    
    # イベントハンドラーの設定
    event_handler = TestEventHandler(
        args.command,
        args.include,
        args.exclude
    )
    
    # 監視の開始
    observer = Observer()
    observer.schedule(event_handler, args.directory, recursive=True)
    observer.start()
    
    try:
        # 監視状態を維持
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n監視を終了します...")
        observer.stop()
        
    observer.join()
    return 0

def main():
    """メイン関数"""
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='テスト自動実行ウォッチャー')
    parser.add_argument('--dir', '-d', dest='directory', default='.',
                      help='監視対象ディレクトリ (デフォルト: カレントディレクトリ)')
    parser.add_argument('--include', '-i', dest='include', action='append',
                      help='監視対象に含めるパターン (複数指定可)')
    parser.add_argument('--exclude', '-e', dest='exclude', action='append',
                      help='監視対象から除外するパターン (複数指定可)')
    parser.add_argument('--command', '-c', dest='command', default='python -m unittest discover',
                      help='テスト実行コマンド (デフォルト: "python -m unittest discover")')
    parser.add_argument('--fast', '-f', dest='fast_mode', action='store_true',
                      help='高速モード (変更されたファイルに関連するテストのみ実行)')
    
    args = parser.parse_args()
    
    # 高速モードの場合、デフォルトコマンドを変更
    if args.fast_mode and args.command == 'python -m unittest discover':
        args.command = 'python run_auto_tests.py --pattern'
    
    try:
        # 必要なパッケージの確認
        try:
            import watchdog
        except ImportError:
            print("watchdogパッケージがインストールされていません。")
            print("以下のコマンドでインストールしてください:")
            print("  pip install watchdog")
            return 1
        
        # 監視の開始
        return start_watching(args)
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 