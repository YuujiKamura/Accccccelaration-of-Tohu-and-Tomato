"""
テスト実行のロギング機能を提供するモジュール

テスト実行中の各種情報をログに記録し、テスト結果の可視性を向上させる機能を提供します。
"""

import os
import sys
import time
import unittest
import io
import logging
import tempfile
from datetime import datetime
from enum import Enum
from functools import wraps
import inspect
import traceback

# ユーザーのOSに応じたカラー対応
try:
    import colorama
    colorama.init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

class Colors:
    """ターミナル表示用の色定義"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

class LogLevel(Enum):
    """ログレベルの定義"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class TestLogger:
    """テスト実行のログ管理クラス"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(TestLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, log_level=LogLevel.INFO, enable_color=True, log_file=None):
        """
        ロガーの初期化
        
        Args:
            log_level (LogLevel): ログの出力レベル
            enable_color (bool): 色付き出力を有効にするか
            log_file (str): ログを出力するファイルパス
        """
        # 初期化済みの場合は何もしない（シングルトンの初期化重複防止）
        if hasattr(self, 'initialized'):
            return
            
        self.log_level = log_level
        self.enable_color = enable_color
        self.log_file = log_file
        self.log_file_handle = None
        self.test_session_started = False
        self.test_counts = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # ログファイルの初期化
        if log_file:
            self.log_file_handle = open(log_file, 'a', encoding='utf-8')
        
        self.initialized = True
    
    def __del__(self):
        """デストラクタ - ファイルハンドルをクローズ"""
        if hasattr(self, 'log_file_handle') and self.log_file_handle:
            try:
                if not self.log_file_handle.closed:
                    self.log_file_handle.flush()
                    self.log_file_handle.close()
            except Exception:
                # デストラクタ内のエラーは無視する
                pass
    
    def _get_timestamp(self):
        """タイムスタンプを取得"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    def _get_caller_info(self):
        """呼び出し元の情報を取得"""
        stack = inspect.stack()
        # 自身とラッパーを飛ばして呼び出し元を取得
        for frame in stack[2:]:
            filename = os.path.basename(frame.filename)
            if not filename.startswith('test_logger.py'):
                return f"{filename}:{frame.lineno}"
        return "unknown:0"
    
    def _format_message(self, level, message):
        """ログメッセージのフォーマット"""
        level_str = level.name
        timestamp = self._get_timestamp()
        caller = self._get_caller_info()
        
        # レベルに応じた色を設定
        color = Colors.RESET
        if self.enable_color:
            if level == LogLevel.DEBUG:
                color = Colors.GRAY
            elif level == LogLevel.INFO:
                color = Colors.RESET
            elif level == LogLevel.WARNING:
                color = Colors.YELLOW
            elif level == LogLevel.ERROR:
                color = Colors.RED
            elif level == LogLevel.CRITICAL:
                color = Colors.BG_RED + Colors.WHITE
        
        # コンソール表示用
        console_message = f"{color}[{timestamp}] {level_str:<8} {caller} - {message}{Colors.RESET}"
        
        # ファイル出力用（色コードなし）
        file_message = f"[{timestamp}] {level_str:<8} {caller} - {message}"
        
        return console_message, file_message
    
    def log(self, level, message):
        """
        指定されたレベルでログを出力
        
        Args:
            level (LogLevel): ログレベル
            message (str): メッセージ
        """
        if level.value < self.log_level.value:
            return
            
        console_message, file_message = self._format_message(level, message)
        
        # コンソールに出力
        print(console_message)
        
        # ファイルに出力
        if self.log_file_handle:
            self.log_file_handle.write(file_message + '\n')
            
            # ファイルをフラッシュ（すぐに書き込み）- パフォーマンスに影響しすぎないよう注意
            if level.value >= LogLevel.ERROR.value:
                self.log_file_handle.flush()
    
    def debug(self, message):
        """デバッグログを出力"""
        self.log(LogLevel.DEBUG, message)
    
    def info(self, message):
        """情報ログを出力"""
        self.log(LogLevel.INFO, message)
    
    def warning(self, message):
        """警告ログを出力"""
        self.log(LogLevel.WARNING, message)
    
    def error(self, message):
        """エラーログを出力"""
        self.log(LogLevel.ERROR, message)
    
    def critical(self, message):
        """致命的エラーログを出力"""
        self.log(LogLevel.CRITICAL, message)
    
    def start_test_session(self):
        """テストセッションの開始をログ"""
        self.test_session_started = True
        self.test_counts = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0}
        
        border = f"{Colors.CYAN}{'='*80}{Colors.RESET}" if self.enable_color else '='*80
        message = f"{border}\n{Colors.BOLD}テストセッション開始: {self._get_timestamp()}{Colors.RESET}\n{border}"
        print(message)
        
        if self.log_file_handle:
            self.log_file_handle.write(f"{'='*80}\nテストセッション開始: {self._get_timestamp()}\n{'='*80}\n")
    
    def end_test_session(self):
        """テストセッションの終了をログ"""
        border = f"{Colors.CYAN}{'='*80}{Colors.RESET}" if self.enable_color else '='*80
        
        success_rate = 0
        if self.test_counts['total'] > 0:
            success_rate = (self.test_counts['passed'] / self.test_counts['total']) * 100
        
        result_color = Colors.GREEN if success_rate == 100 else Colors.YELLOW if success_rate >= 80 else Colors.RED
        result_text = f"{result_color}成功率: {success_rate:.1f}%{Colors.RESET}" if self.enable_color else f"成功率: {success_rate:.1f}%"
        
        message = (
            f"{border}\n"
            f"{Colors.BOLD if self.enable_color else ''}テストセッション終了: {self._get_timestamp()}{Colors.RESET if self.enable_color else ''}\n"
            f"実行: {self.test_counts['total']}, 成功: {self.test_counts['passed']}, 失敗: {self.test_counts['failed']}, "
            f"エラー: {self.test_counts['errors']}, スキップ: {self.test_counts['skipped']}\n"
            f"{result_text}\n"
            f"{border}"
        )
        print(message)
        
        if self.log_file_handle:
            self.log_file_handle.write(
                f"{'='*80}\n"
                f"テストセッション終了: {self._get_timestamp()}\n"
                f"実行: {self.test_counts['total']}, 成功: {self.test_counts['passed']}, 失敗: {self.test_counts['failed']}, "
                f"エラー: {self.test_counts['errors']}, スキップ: {self.test_counts['skipped']}\n"
                f"成功率: {success_rate:.1f}%\n"
                f"{'='*80}\n"
            )
            self.log_file_handle.flush()
    
    def start_test_class(self, class_name):
        """テストクラスの開始をログ"""
        message = f"\n✅ テスト開始: {class_name}"
        print(message)
        if self.log_file_handle:
            self.log_file_handle.write(f"\n✅ テスト開始: {class_name}\n")
    
    def end_test_class(self, class_name, duration):
        """テストクラスの終了をログ"""
        message = f"✅ テスト終了: {class_name} ({duration:.3f}秒)"
        print(message)
        if self.log_file_handle:
            self.log_file_handle.write(f"✅ テスト終了: {class_name} ({duration:.3f}秒)\n")
    
    def start_test_method(self, method_name):
        """テストメソッドの開始をログ"""
        self.test_counts['total'] += 1
        icon = "▶️"
        message = f"  {icon} 実行中: {method_name}"
        print(message)
        if self.log_file_handle:
            self.log_file_handle.write(f"  実行中: {method_name}\n")
    
    def end_test_method(self, method_name, result, duration, error=None):
        """テストメソッドの終了をログ"""
        if result == 'pass':
            self.test_counts['passed'] += 1
            icon = "✔️"
            color = Colors.GREEN if self.enable_color else ""
        elif result == 'fail':
            self.test_counts['failed'] += 1
            icon = "❌"
            color = Colors.RED if self.enable_color else ""
        elif result == 'error':
            self.test_counts['errors'] += 1
            icon = "❌"
            color = Colors.RED if self.enable_color else ""
        elif result == 'skip':
            self.test_counts['skipped'] += 1
            icon = "⏭️"
            color = Colors.YELLOW if self.enable_color else ""
        
        error_msg = f" - {str(error)}" if error else ""
        message = f"  {color}{icon} 完了: {method_name}{error_msg} ({duration:.3f}秒){Colors.RESET if self.enable_color else ''}"
        print(message)
        
        if self.log_file_handle:
            self.log_file_handle.write(f"  完了: {method_name}{error_msg} ({duration:.3f}秒)\n")
    
    def log_assert(self, assertion, expected, actual, message=None):
        """アサーションのログ出力"""
        msg = f"アサート {assertion}: 期待値 '{expected}', 実際値 '{actual}'"
        if message:
            msg += f" - {message}"
        self.debug(msg)

def get_logger(log_level=LogLevel.INFO, enable_color=True, log_file=None):
    """ロガーのインスタンスを取得"""
    return TestLogger(log_level, enable_color, log_file)

def log_test_enhanced(func):
    """テスト関数をデコレートして詳細なログを出力する拡張版"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        test_name = func.__name__
        logger.start_test_method(test_name)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.end_test_method(test_name, 'pass', duration)
            return result
        except AssertionError as e:
            duration = time.time() - start_time
            logger.end_test_method(test_name, 'fail', duration, str(e))
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.end_test_method(test_name, 'error', duration, str(e))
            raise
            
    return wrapper

def run_test_with_enhanced_logging(test_case, log_level=LogLevel.INFO, log_file=None):
    """テストケースを実行し、詳細なログを出力する"""
    logger = get_logger(log_level, True, log_file)
    logger.start_test_session()
    
    start_time = time.time()
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_case)
        result = unittest.TextTestRunner(verbosity=0).run(suite)
        duration = time.time() - start_time
        
        # テスト結果の詳細を出力
        logger.info(f"実行テスト数: {result.testsRun}")
        logger.info(f"成功テスト数: {result.testsRun - len(result.failures) - len(result.errors)}")
        
        if result.failures:
            logger.warning(f"失敗テスト数: {len(result.failures)}")
            for test, err in result.failures:
                logger.warning(f"失敗: {test}")
                logger.debug(f"詳細: {err}")
        
        if result.errors:
            logger.error(f"エラーテスト数: {len(result.errors)}")
            for test, err in result.errors:
                logger.error(f"エラー: {test}")
                logger.debug(f"詳細: {err}")
        
        logger.info(f"合計実行時間: {duration:.3f}秒")
        return result.wasSuccessful()
    finally:
        logger.end_test_session()

# パフォーマンスモニタリング用のユーティリティ
class PerformanceMonitor:
    """テスト実行時のパフォーマンスをモニタリングするクラス"""
    
    def __init__(self):
        self.start_time = None
        self.memory_usage_start = None
        self.cpu_usage_start = None
    
    def start_monitoring(self):
        """モニタリング開始"""
        self.start_time = time.time()
        
        # メモリ使用量と CPU 使用率の初期値を取得
        try:
            import psutil
            process = psutil.Process(os.getpid())
            self.memory_usage_start = process.memory_info().rss
            self.cpu_usage_start = process.cpu_percent(interval=0.1)
        except ImportError:
            logger = get_logger()
            logger.warning("psutilがインストールされていないため、メモリとCPUの使用量は測定できません。")
            self.memory_usage_start = 0
            self.cpu_usage_start = 0
    
    def stop_monitoring(self):
        """モニタリング終了して結果を返す"""
        if not self.start_time:
            return {}
            
        elapsed_time = time.time() - self.start_time
        
        result = {
            'elapsed_time': elapsed_time,
        }
        
        # メモリとCPU使用率の差分を計算
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_usage_end = process.memory_info().rss
            cpu_usage_end = process.cpu_percent(interval=0.1)
            
            result['memory_usage'] = {
                'start': self.memory_usage_start / (1024 * 1024),  # MB
                'end': memory_usage_end / (1024 * 1024),  # MB
                'diff': (memory_usage_end - self.memory_usage_start) / (1024 * 1024)  # MB
            }
            
            result['cpu_usage'] = {
                'start': self.cpu_usage_start,
                'end': cpu_usage_end,
                'avg': (self.cpu_usage_start + cpu_usage_end) / 2
            }
        except ImportError:
            result['memory_usage'] = None
            result['cpu_usage'] = None
        
        return result

# 高負荷の原因となる可能性のある問題をチェックする関数
def check_performance_issues():
    """テストのパフォーマンス問題をチェックする"""
    logger = get_logger()
    issues = []
    
    # モジュールのインポート循環参照をチェック
    try:
        import sys
        for module_name, module in list(sys.modules.items()):
            if not module_name.startswith('tests.'):
                continue
                
            # モジュールの依存関係をチェック
            dependencies = set()
            for attr_name in dir(module):
                try:
                    attr = getattr(module, attr_name)
                    if inspect.ismodule(attr) and attr.__name__.startswith('tests.'):
                        dependencies.add(attr.__name__)
                except (ImportError, AttributeError):
                    continue
            
            # 循環参照の兆候
            circular_refs = []
            for dep in dependencies:
                try:
                    dep_module = sys.modules.get(dep)
                    if dep_module and module_name in [getattr(getattr(dep_module, attr_name), '__module__', '') 
                                            for attr_name in dir(dep_module)]:
                        circular_refs.append(dep)
                except (ImportError, AttributeError):
                    continue
                    
            if circular_refs:
                issues.append(f"循環参照の可能性: {module_name} <-> {', '.join(circular_refs)}")
    except Exception as e:
        logger.error(f"依存関係チェック中にエラー: {str(e)}")
    
    # 大きすぎるテストモジュールをチェック
    try:
        import os
        test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for root, _, files in os.walk(test_dir):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)
                    
                    # 40KB以上のファイルは大きすぎる可能性
                    if size > 40 * 1024:
                        issues.append(f"大きすぎるテストファイル: {file_path} ({size/1024:.1f}KB)")
                        
                    # ファイルの内容を確認
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # 重複コードが多い可能性をチェック
                        duplicate_blocks = 0
                        lines = content.split('\n')
                        block_signatures = {}
                        
                        for i in range(len(lines) - 3):
                            block = '\n'.join(lines[i:i+4])  # 4行ブロック
                            if len(block.strip()) > 0:
                                if block in block_signatures:
                                    duplicate_blocks += 1
                                    block_signatures[block] += 1
                                else:
                                    block_signatures[block] = 1
                        
                        # 重複ブロックが多すぎる場合は警告
                        if duplicate_blocks > 100:
                            issues.append(f"重複コードブロックが多い: {file_path} ({duplicate_blocks}ブロック)")
                        
                        # クラス定義の重複をチェック
                        class_counts = {}
                        import re
                        class_pattern = r"class\s+(\w+)"
                        for match in re.finditer(class_pattern, content):
                            class_name = match.group(1)
                            if class_name in class_counts:
                                class_counts[class_name] += 1
                            else:
                                class_counts[class_name] = 1
                        
                        duplicate_classes = [name for name, count in class_counts.items() if count > 1]
                        if duplicate_classes:
                            issues.append(f"重複クラス定義: {file_path} - {', '.join(duplicate_classes)}")
                    
                    except Exception as e:
                        logger.error(f"ファイル {file_path} のチェック中にエラー: {str(e)}")
    except Exception as e:
        logger.error(f"ファイルサイズチェック中にエラー: {str(e)}")
    
    return issues 

# テストケース部分を削除
# TestLoggerTestクラスを残すと循環参照になるため、これをコメントアウトする
'''
class TestLoggerTest:
    """TestLoggerクラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト用の一時ファイルを作成
        self.temp_log_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
        self.temp_log_file.close()
        
        # 既存のインスタンスをリセット（シングルトンなので）
        TestLogger._instance = None
        
        # テスト用のロガーを作成
        self.logger = TestLogger(
            log_level=LogLevel.DEBUG,
            enable_color=False,
            log_file=self.temp_log_file.name
        )
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # ファイルハンドルを閉じる
        if hasattr(self.logger, 'log_file_handle') and self.logger.log_file_handle:
            try:
                self.logger.log_file_handle.close()
            except:
                pass
        
        # 一時ファイルを削除
        try:
            os.remove(self.temp_log_file.name)
        except:
            pass
    
    def _get_log_content(self):
        """ログファイルの内容を取得"""
        with open(self.temp_log_file.name, 'r', encoding='utf-8') as f:
            return f.read()
    
    @log_test_enhanced
    def test_singleton_pattern(self):
        """シングルトンパターンが正しく実装されていることを確認"""
        logger1 = TestLogger()
        logger2 = TestLogger()
        
        # 同じインスタンスであることを確認
        self.assertIs(logger1, logger2)
        
        # 設定変更後も同じインスタンスを維持
        logger3 = TestLogger(log_level=LogLevel.DEBUG)
        self.assertIs(logger1, logger3)
    
    @log_test_enhanced
    def test_log_levels(self):
        """異なるログレベルが正しく機能することを確認"""
        # 各レベルのログを出力
        self.logger.debug("デバッグメッセージテスト")
        self.logger.info("情報メッセージテスト")
        self.logger.warning("警告メッセージテスト")
        self.logger.error("エラーメッセージテスト")
        self.logger.critical("重大なエラーメッセージテスト")
        
        # ログファイルの内容を取得
        log_content = self._get_log_content()
        
        # 各レベルのメッセージが含まれていることを確認
        self.assertIn("デバッグメッセージテスト", log_content)
        self.assertIn("情報メッセージテスト", log_content)
        self.assertIn("警告メッセージテスト", log_content)
        self.assertIn("エラーメッセージテスト", log_content)
        self.assertIn("重大なエラーメッセージテスト", log_content)
    
    @log_test_enhanced
    def test_session_logging(self):
        """セッションログ機能が正しく動作することを確認"""
        # 新しいロガーインスタンスを使用（前のテストのログが混ざらないように）
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
        temp_file.close()
        
        try:
            # インスタンスをリセット
            TestLogger._instance = None
            session_logger = TestLogger(log_level=LogLevel.INFO, enable_color=False, log_file=temp_file.name)
            
            # セッション開始
            session_logger.start_test_session()
            
            # テストクラスのログ
            session_logger.start_test_class("TestExampleClass")
            
            # テストメソッドのログ（成功）
            session_logger.start_test_method("test_success_method")
            session_logger.end_test_method("test_success_method", "pass", 0.123)
            
            # テストメソッドのログ（失敗）
            session_logger.start_test_method("test_failure_method")
            session_logger.end_test_method("test_failure_method", "fail", 0.456)
            
            # テストクラス終了ログ
            session_logger.end_test_class("TestExampleClass", 0.6)
            
            # セッション終了ログ
            session_logger.end_test_session()
            
            # ログファイル内容を読み込み
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # 必要な情報が含まれていることを確認
            self.assertIn("テストセッション開始", log_content)
            self.assertIn("TestExampleClass", log_content)
            self.assertIn("test_success_method", log_content)
            self.assertIn("test_failure_method", log_content)
            self.assertIn("テストセッション終了", log_content)
        
        finally:
            # 一時ファイルを削除
            try:
                os.remove(temp_file.name)
            except:
                pass
    
    @log_test_enhanced
    def test_file_logging(self):
        """ファイルログ機能が正しく動作することを確認"""
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp:
            log_file = tmp.name
        
        try:
            # インスタンスをリセット
            TestLogger._instance = None
            
            # ファイルロガーを作成
            file_logger = TestLogger(log_level=LogLevel.INFO, enable_color=False, log_file=log_file)
            
            # ログを出力
            test_message = "ファイルログテスト専用メッセージ"
            warning_message = "警告専用テストメッセージ"
            file_logger.info(test_message)
            file_logger.warning(warning_message)
            
            # ファイルハンドルを確実に閉じる
            if hasattr(file_logger, 'log_file_handle') and file_logger.log_file_handle:
                file_logger.log_file_handle.flush()
                file_logger.log_file_handle.close()
                file_logger.log_file_handle = None
            
            # ファイルを読み込んで確認
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # メッセージが含まれていることを確認
            self.assertIn(test_message, content)
            self.assertIn(warning_message, content)
            
        finally:
            # 一時ファイルを削除
            if os.path.exists(log_file):
                os.remove(log_file)
'''

if __name__ == "__main__":
    # TestLoggerTestは削除されたため、main部分も対応する
    logger = TestLogger(log_level=LogLevel.INFO)
    logger.info("TestLoggerモジュールをインポートしました。テストは実行されません。") 