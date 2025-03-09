import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from tests.unit.test_base import BaseTestCase, log_test

class MainRootTest(BaseTestCase):
    """ルートにあるmain.pyのテスト"""

    @classmethod
    def setUpClass(cls):
        """クラス全体のセットアップ"""
        super().setUpClass()
        
        # main.pyのあるディレクトリをパスに追加
        cls.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        if cls.root_dir not in sys.path:
            sys.path.append(cls.root_dir)

    def setUp(self):
        """テストの前準備"""
        super().setUp()
        
        # main.pyを直接実行（モジュールとして読み込み）するときに必要な他のモジュールをモック化
        # Pygameのモックをさらに詳細に設定
        self.pygame_mock = MagicMock()
        self.clock_mock = MagicMock()
        self.clock_mock.tick = MagicMock(return_value=30)
        self.pygame_mock.time.Clock.return_value = self.clock_mock
        self.surface_mock = MagicMock()
        self.surface_mock.blit = MagicMock()
        self.surface_mock.fill = MagicMock()
        self.pygame_mock.display.set_mode.return_value = self.surface_mock
        self.pygame_mock.display.update = MagicMock()
        self.pygame_mock.display.flip = MagicMock()
        self.pygame_mock.event.get.return_value = []
        
        # キー押下状態をモック
        self.key_pressed_dict = {}
        self.pygame_mock.key.get_pressed.return_value = self.key_pressed_dict
        
        # 定数
        self.pygame_mock.QUIT = 12
        self.pygame_mock.KEYDOWN = 2
        self.pygame_mock.K_ESCAPE = 27
        self.pygame_mock.K_SPACE = 32
        self.pygame_mock.K_LEFT = 276
        self.pygame_mock.K_RIGHT = 275
        self.pygame_mock.K_UP = 273
        self.pygame_mock.K_DOWN = 274
        self.pygame_mock.K_F1 = 282
        self.pygame_mock.K_F2 = 283
        self.pygame_mock.K_v = 118
        
        # numpy, randomなどのモジュールもモック化
        self.numpy_mock = MagicMock()
        self.random_mock = MagicMock()
        self.random_mock.randint.return_value = 5
        self.random_mock.random.return_value = 0.5
        
        # pygame.fontやpygame.mixerのモック
        self.font_mock = MagicMock()
        self.font_mock.render.return_value = self.surface_mock
        self.pygame_mock.font.Font.return_value = self.font_mock
        self.pygame_mock.font.init = MagicMock()
        self.pygame_mock.mixer = MagicMock()
        self.pygame_mock.mixer.Sound = MagicMock()
        
        # パッチを適用
        self.patches = [
            patch.dict('sys.modules', {'pygame': self.pygame_mock}),
            patch.dict('sys.modules', {'numpy': self.numpy_mock}),
            patch.dict('sys.modules', {'random': self.random_mock}),
            # __main__をモック化して直接実行を防止
            patch.dict('sys.modules', {'__main__': MagicMock()})
        ]
        
        # すべてのパッチを開始
        for p in self.patches:
            p.start()

    def tearDown(self):
        """テストの後片付け"""
        # すべてのパッチを停止
        for p in self.patches:
            p.stop()
            
        # キャッシュからモジュールを削除
        if 'main' in sys.modules:
            del sys.modules['main']
            
        super().tearDown()

    @log_test
    def test_main_constants_exist(self):
        """main.pyに必要な定数が存在するかチェック"""
        # main.pyをファイルとして読み取り、内容を解析
        try:
            with open(os.path.join(self.root_dir, 'main.py'), 'r', encoding='utf-8') as f:
                main_content = f.read()
            
            # 定数定義をチェック
            expected_constants = {
                'SCREEN_WIDTH': 800,
                'SCREEN_HEIGHT': 600,
                'WHITE': '(255, 255, 255)',
                'BLACK': '(0, 0, 0)',
                'RED': '(255, 0, 0)'
            }
            
            for const_name, expected_value in expected_constants.items():
                # 定数名が存在するか確認
                pattern = f"{const_name} = "
                self.assertIn(pattern, main_content, f"定数 {const_name} が見つかりません")
                
                # 値が正しいかも簡易チェック（文字列として含まれるかだけ）
                value_str = str(expected_value)
                self.assertIn(value_str, main_content, f"定数 {const_name} の値が期待値と異なります")
                
        except Exception as e:
            self.fail(f"予期しないエラーが発生: {e}")

    @log_test
    def test_main_functions_exist(self):
        """main.pyに必要な関数やクラスがあるか確認"""
        try:
            with open(os.path.join(self.root_dir, 'main.py'), 'r', encoding='utf-8') as f:
                main_content = f.read()
            
            # 関数やクラスの存在をチェック
            expected_functions = [
                'reset_game', 'calculate_difficulty_factor', 'get_difficulty_name'
            ]
            
            expected_classes = [
                'Player', 'Bullet', 'Enemy', 'RingEffect'
            ]
            
            for func in expected_functions:
                pattern = f"def {func}"
                self.assertIn(pattern, main_content, f"関数 {func} が見つかりません")
                
            for cls in expected_classes:
                pattern = f"class {cls}"
                self.assertIn(pattern, main_content, f"クラス {cls} が見つかりません")
                
        except Exception as e:
            self.fail(f"予期しないエラーが発生: {e}")

if __name__ == "__main__":
    unittest.main() 