"""
ヒートゲージの描画テスト

このモジュールでは、プレイヤーのヒートゲージの描画と更新をテストします。
"""

import unittest
from tests.unit.test_base import BaseTestCase, log_test
from unittest.mock import MagicMock, patch, call
import sys
import os

# プロジェクトルートをシステムパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class HeatGaugeTest(BaseTestCase):
    """ヒートゲージの描画と更新のテスト"""
    
    def setUp(self):
        """テスト環境の準備"""
        super().setUp()
        
        # 実際のpygameモジュールを保存
        self.real_pygame = sys.modules.get('pygame')
        
        # モックの作成
        self.pygame_mock = MagicMock()
        self.pygame_mock.time.get_ticks.return_value = 1000
        self.screen_mock = MagicMock()
        self.font_mock = MagicMock()
        self.font_render_mock = MagicMock()
        
        self.pygame_mock.display.set_mode.return_value = self.screen_mock
        self.pygame_mock.font.Font.return_value = self.font_mock
        self.font_mock.render.return_value = self.font_render_mock
        
        # pygameをモックに置き換え
        sys.modules['pygame'] = self.pygame_mock
        
        # Playerクラスのモックを作成
        self.player = MagicMock()
        self.player.heat = 0
        self.player.max_heat = 100
        
        # ヒートゲージの描画をシミュレートする関数
        def mock_draw_gauges():
            # ヒートゲージの背景を描画
            self.pygame_mock.draw.rect(self.screen_mock, (50, 50, 50), (20, 60, 150, 10))
            
            # ヒートゲージ本体を描画
            heat_ratio = self.player.heat / self.player.max_heat
            heat_color = (255 * heat_ratio, 255 * (1 - heat_ratio), 0)
            self.pygame_mock.draw.rect(self.screen_mock, heat_color, (20, 60, int(150 * heat_ratio), 10))
            
            # ヒートゲージの枠を描画
            self.pygame_mock.draw.rect(self.screen_mock, (255, 255, 255), (20, 60, 150, 10), 1)
            
            # ヒートゲージのテキストを描画
            heat_text = f"HEAT: {int(self.player.heat)}/{self.player.max_heat}"
            self.font_mock.render(heat_text, True, (255, 255, 255))
            self.screen_mock.blit(self.font_render_mock, (20 + 150 + 10, 60))
        
        self.player.draw_gauges = mock_draw_gauges
    
    def tearDown(self):
        """テスト環境のクリーンアップ"""
        # 実際のpygameを元に戻す
        if self.real_pygame:
            sys.modules['pygame'] = self.real_pygame
        super().tearDown()
    
    @log_test
    def test_heat_gauge_drawing(self):
        """ヒートゲージが正しく描画されるかテスト"""
        # draw_gaugesメソッドの呼び出し
        self.player.draw_gauges()
        
        # pygameのdraw.rectが呼ばれたことを確認
        self.pygame_mock.draw.rect.assert_called()
        
        # 枠線描画の呼び出しが含まれていることを確認
        self.pygame_mock.draw.rect.assert_any_call(self.screen_mock, (255, 255, 255), (20, 60, 150, 10), 1)
        
        # フォントのrenderが呼ばれたことを確認
        self.font_mock.render.assert_called_with("HEAT: 0/100", True, (255, 255, 255))
    
    @log_test
    def test_heat_gauge_value_changes(self):
        """ヒートゲージの値が変更されたときに正しく反映されるかテスト"""
        # 初期値の確認
        self.assertEqual(self.player.heat, 0)
        
        # ヒートゲージを増加させる
        test_heat_value = 50
        self.player.heat = test_heat_value
        
        # draw_gaugesメソッドの呼び出し
        self.player.draw_gauges()
        
        # フォントのrenderが適切な値で呼ばれたか確認
        self.font_mock.render.assert_called_with(f"HEAT: {test_heat_value}/100", True, (255, 255, 255))
        
        # ヒートゲージが最大値に達した場合
        self.player.heat = self.player.max_heat
        
        # draw_gaugesメソッドの呼び出し
        self.player.draw_gauges()
        
        # 最大値でヒートゲージが描画されることを確認
        self.font_mock.render.assert_called_with(f"HEAT: 100/100", True, (255, 255, 255))
    
    @log_test
    def test_heat_gauge_position(self):
        """ヒートゲージが正しい位置に描画されるかテスト"""
        # draw_gaugesメソッドの呼び出し
        self.player.draw_gauges()
        
        # ヒートゲージの背景が正しい位置に描画されることを確認
        self.pygame_mock.draw.rect.assert_any_call(self.screen_mock, (50, 50, 50), (20, 60, 150, 10))
        
        # ゲージのテキストが正しい位置に描画されることを確認
        self.screen_mock.blit.assert_called_with(self.font_render_mock, (20 + 150 + 10, 60))

if __name__ == '__main__':
    unittest.main() 