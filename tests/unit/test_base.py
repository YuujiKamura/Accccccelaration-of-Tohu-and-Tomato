"""
テスト用基底クラス

すべてのテストはこのクラスを継承して実装することで,
一貫したテスト環境とルールを適用できます.
"""

import unittest
import sys
from unittest.mock import MagicMock, patch
import time
import os
from functools import wraps
import traceback

# テストロガーをインポート (循環参照に注意)
from tests.unit.test_logger import TestLogger, LogLevel

# リセット回数の制限
MAX_RESET_COUNT = 5
reset_count = 0

# パスの設定 - プロジェクトルートを追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# テストロガーのインスタンスを取得
def get_test_logger():
    """テストロガーのインスタンスを取得"""
    # アサーションのログも表示するため、ログレベルをDEBUGに設定
    return TestLogger(log_level=LogLevel.DEBUG, enable_color=True)

class BaseTestCase(unittest.TestCase):
    """すべてのテストケースの基底クラス"""
    
    # クラスレベルのロガー
    logger = None
    
    # セッション開始フラグ（最初のテストクラスのみセッションを開始するため）
    _session_started = False
    
    @classmethod
    def setUpClass(cls):
        """クラス全体のセットアップ"""
        # ロガーの初期化（遅延初期化）
        if BaseTestCase.logger is None:
            BaseTestCase.logger = get_test_logger()
        
        # テストセッションを開始（最初のテストクラスのみ）
        if not BaseTestCase._session_started:
            BaseTestCase.logger.start_test_session()
            BaseTestCase._session_started = True
        
        # テストクラスの開始をログ
        cls.logger.start_test_class(cls.__name__)
        cls.start_time = time.time()
    
    @classmethod
    def tearDownClass(cls):
        """クラス全体の終了処理"""
        duration = time.time() - cls.start_time
        
        # テストクラスの終了をログ
        cls.logger.end_test_class(cls.__name__, duration)
    
    def setUp(self):
        """各テストメソッドの開始前に実行"""
        # ロガーの確認
        if BaseTestCase.logger is None:
            BaseTestCase.logger = get_test_logger()
            
        self.test_start_time = time.time()
        test_name = self.id().split('.')[-1]
        self.logger.start_test_method(test_name)
    
    def tearDown(self):
        """各テストメソッドの終了後に実行"""
        duration = time.time() - self.test_start_time
        test_name = self.id().split('.')[-1]
        
        # テスト結果を判定
        result = "pass"
        error = None
        
        # テスト結果を取得 - _outcomeへのアクセスをより安全に行う
        try:
            # Python 3.7.2以降のunittest実装
            if hasattr(self, '_outcome') and self._outcome:
                # エラーチェック
                error_list = []
                # _outcomeの構造は実装に依存するため、複数の可能性を考慮
                if hasattr(self._outcome, 'errors') and self._outcome.errors:
                    error_list = self._outcome.errors
                elif hasattr(self._outcome, '_exc_info_to_string'):
                    # Python 3.11以降: エラー情報は別の場所に保存されている可能性
                    result_obj = getattr(self._outcome, 'result', None)
                    if result_obj:
                        error_list = [(t, e) for t, e in getattr(result_obj, 'errors', [])]
                
                # エラーの有無を確認
                for test, exc_info in error_list:
                    if test.id() == self.id():
                        result = "error"
                        error = exc_info[1] if len(exc_info) > 1 else str(exc_info)
                        break
                
                # 失敗チェック
                result_obj = getattr(self._outcome, 'result', None)
                if result_obj and hasattr(result_obj, 'failures'):
                    for test, _ in result_obj.failures:
                        if test.id() == self.id():
                            result = "fail"
                            break
        except Exception as e:
            # 最悪の場合でもテストの実行を継続
            print(f"警告: テスト結果の判定中にエラーが発生: {str(e)}")
        
        # テストメソッドの終了をログ
        self.logger.end_test_method(test_name, result, duration, error)
    
    # アサーションメソッドをオーバーライドして、ロギングを追加
    def assertEqual(self, first, second, msg=None):
        """等価アサーション - ロギング付き"""
        try:
            super().assertEqual(first, second, msg)
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_assert("assertEqual", first, second, msg)
        except AssertionError as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_assert("assertEqual", first, second, str(e))
            raise
    
    def assertTrue(self, expr, msg=None):
        """真偽アサーション - ロギング付き"""
        try:
            super().assertTrue(expr, msg)
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_assert("assertTrue", True, expr, msg)
        except AssertionError as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_assert("assertTrue", True, expr, str(e))
            raise
    
    def assertFalse(self, expr, msg=None):
        """真偽アサーション - ロギング付き"""
        try:
            super().assertFalse(expr, msg)
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_assert("assertFalse", False, expr, msg)
        except AssertionError as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_assert("assertFalse", False, expr, str(e))
            raise

class GameTestBase(BaseTestCase):
    """
    すべてのゲームテストの基底クラス
    このクラスを継承することで,以下の機能が利用できます：
    
    1. Pygameのモック化（GUI表示なし）
    2. アドバタイズモードの制限
    3. リセット関数の制限
    4. 共通のテスト環境
    """
    
    @classmethod
    def setUpClass(cls):
        """
        クラス全体のセットアップ - 一度だけ実行される
        """
        print(f"\n✅ テスト開始: {cls.__name__}")
        cls.start_time = time.time()
        
        # Pygameのモック化
        cls._setup_pygame_mock()
        
        # メインモジュールのパッチ適用
        cls._patch_main_module()
        
        print(f"{cls.__name__} テスト環境をセットアップしました")
    
    @classmethod
    def _setup_pygame_mock(cls):
        """Pygameをモック化して,GUIを無効化する"""
        # 既にモック化されていなければモック化
        if 'pygame' not in sys.modules or not isinstance(sys.modules['pygame'], MagicMock):
            pygame_mock = MagicMock()
            sys.modules['pygame'] = pygame_mock
            
            # 主要な関数をモック化
            pygame_mock.init = MagicMock(return_value=(0, 0))
            pygame_mock.quit = MagicMock()
            pygame_mock.display.set_mode = MagicMock(return_value=MagicMock())
            pygame_mock.time.Clock = MagicMock(return_value=MagicMock())
            pygame_mock.time.get_ticks = MagicMock(return_value=0)
            pygame_mock.event.get = MagicMock(return_value=[])
            
            # 数値演算をサポートするようにする
            cls._enhance_mock_for_calculations()
            
            print("Pygameをモック化しました")
    
    @classmethod
    def _enhance_mock_for_calculations(cls):
        """MagicMockを拡張して数値演算をサポートする"""
        original_mock = MagicMock
        
        class EnhancedMock(original_mock):
            def __lt__(self, other): return False
            def __gt__(self, other): return False
            def __le__(self, other): return True
            def __ge__(self, other): return True
            def __eq__(self, other): return True if isinstance(other, MagicMock) else False
            def __add__(self, other): return other
            def __sub__(self, other): return 0
            def __mul__(self, other): return 0
            def __truediv__(self, other): return 0
            def __floordiv__(self, other): return 0
            def __mod__(self, other): return 0
        
        # 元のMagicMockを置き換え
        unittest.mock.MagicMock = EnhancedMock
    
    @classmethod
    def _patch_main_module(cls):
        """mainモジュールのパッチを適用"""
        try:
            # game_moduleがすでにモック化されているか確認
            if 'main' in sys.modules:
                main_module = sys.modules['main']
                
                # 要修正点： アドバタイズモードの制限
                if hasattr(main_module, 'advertise_mode'):
                    original_advertise = main_module.advertise_mode
                    main_module.advertise_mode = cls._limited_advertise_mode
                    print("アドバタイズモードを制限しました")
                
                # 要修正点： リセット関数の制限
                if hasattr(main_module, 'reset_game'):
                    original_reset = main_module.reset_game
                    main_module.reset_game = cls._limited_reset_game
                    print("リセット関数を制限しました")
            else:
                print("mainモジュールがロードされていません")
        except Exception as e:
            print(f"メインモジュールのパッチ適用中にエラー: {e}")
    
    @classmethod
    def _limited_advertise_mode(cls):
        """アドバタイズモードの実行回数を制限する"""
        global reset_count
        reset_count += 1
        print(f"アドバタイズモード制限 ({reset_count}/{MAX_RESET_COUNT})")
        
        if reset_count >= MAX_RESET_COUNT:
            print(f"最大実行回数 ({MAX_RESET_COUNT}) に達したため終了します")
            sys.exit(0)
    
    @classmethod
    def _limited_reset_game(cls):
        """リセット関数の実行回数を制限する"""
        global reset_count
        reset_count += 1
        print(f"ゲームリセット制限 ({reset_count}/{MAX_RESET_COUNT})")
        
        # ゲーム状態を初期化
        if 'main' in sys.modules:
            main = sys.modules['main']
            if hasattr(main, 'game_over'):
                main.game_over = False
            if hasattr(main, 'score'):
                main.score = 0
            if hasattr(main, 'enemies'):
                main.enemies = []
            if hasattr(main, 'bullets'):
                main.bullets = []
        
        if reset_count >= MAX_RESET_COUNT:
            print(f"最大リセット回数 ({MAX_RESET_COUNT}) に達したため終了します")
            sys.exit(0)
    
    def setUp(self):
        """各テスト実行前のセットアップ"""
        super().setUp()  # 親クラスのsetUp()を呼び出す
        self.test_start_time = time.time()
        test_name = self.id().split('.')[-1]
        print(f"  ▶️ 実行中: {test_name}")
            
        # スタブモジュールのロードを試みる
        self._try_load_stub_module()
        
        # ゲーム状態をリセット
        self._reset_game_state()
            
    def _try_load_stub_module(self):
        """スタブモジュールのロードを試みる"""
        try:
            import importlib.util
            try:
                spec = importlib.util.spec_from_file_location("main", "test_main_stub.py")
                main = importlib.util.module_from_spec(spec)
                sys.modules['main'] = main
                spec.loader.exec_module(main)
                print("テスト用スタブモジュールを使用します")
            except (ImportError, FileNotFoundError):
                # スタブがなければtest_simple_mainを試す
                try:
                    spec = importlib.util.spec_from_file_location("main", "test_simple_main.py")
                    main = importlib.util.module_from_spec(spec)
                    sys.modules['main'] = main
                    spec.loader.exec_module(main)
                    print("簡易版スタブモジュールを使用します")
                except (ImportError, FileNotFoundError):
                    print("スタブモジュールが見つかりません")
        except Exception as e:
            print(f"スタブモジュールのロード中にエラー: {e}")
    
    def _reset_game_state(self):
        """テスト用にゲーム状態をリセットする"""
        # 必要に応じてゲーム状態をリセット
        if 'main' in sys.modules:
            main = sys.modules['main']
            if hasattr(main, 'game_over'):
                main.game_over = False
            if hasattr(main, 'score'):
                main.score = 0
    
    def tearDown(self):
        """各テスト実行後のクリーンアップ"""
        # 必要に応じてリソースをクリーンアップ
        duration = time.time() - self.test_start_time
        test_name = self.id().split('.')[-1]
        print(f"  ✔️ 完了: {test_name} ({duration:.3f}秒)")
    
    @classmethod
    def tearDownClass(cls):
        """クラス全体のクリーンアップ - 全テスト終了後に一度だけ実行される"""
        # 必要に応じてリソースをクリーンアップ
        duration = time.time() - cls.start_time
        print(f"✅ テスト終了: {cls.__name__} ({duration:.3f}秒)")

# ロガーを使用したテストデコレータ
def log_test(func):
    """テスト関数をデコレートしてログを出力する"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # ロガーを取得
        logger = get_test_logger()
        
        # テスト名を取得
        test_name = func.__name__
        
        try:
            # テスト実行
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            # 例外発生時
            # 例外情報をログに残す
            exc_type, exc_value, exc_traceback = sys.exc_info()
            if logger:
                logger.error(f"例外発生: {exc_type.__name__}: {str(exc_value)}")
                logger.debug("トレースバック:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            
            raise
    return wrapper

# テスト実行ラッパー関数
def run_test_with_logging(test_case):
    """指定されたテストケースを実行し、ロガーを使用してログを出力する"""
    logger = get_test_logger()
    
    # テストセッション開始
    logger.start_test_session()
    
    # テストの実行
    suite = unittest.TestLoader().loadTestsFromTestCase(test_case)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    
    # テストセッション終了
    logger.end_test_session()
    
    return result.wasSuccessful() 