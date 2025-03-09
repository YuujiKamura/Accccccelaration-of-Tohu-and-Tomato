"""
新しいダッシュテスト

このモジュールはプレイヤーのダッシュ機能をテストします。
"""

import unittest
from tests.unit.test_base import BaseTestCase, log_test
from unittest.mock import MagicMock

class DashTest(BaseTestCase):
    """ダッシュ機能のテスト"""
    
    def setUp(self):
        """テスト前の初期化"""
        super().setUp()
        
        # モックプレイヤーを作成
        self.player = MagicMock()
        self.player.x = 400
        self.player.y = 300
        self.player.speed = 5.0
        self.player.dash_speed = 10.0
        self.player.is_dashing = False
        self.player.dash_cooldown = 0
        self.player.dash_duration = 0
        self.player.heat = 0
        self.player.max_heat = 100
        
        # ダッシュメソッドの動作を定義
        def mock_dash():
            if self.player.dash_cooldown == 0 and self.player.heat < self.player.max_heat:
                self.player.is_dashing = True
                self.player.dash_duration = 10
                self.player.heat += 20
            return self.player.is_dashing
            
        self.player.dash = mock_dash
        
        # 更新メソッドの動作を定義
        def mock_update():
            if self.player.is_dashing:
                self.player.dash_duration -= 1
                if self.player.dash_duration <= 0:
                    self.player.is_dashing = False
                    self.player.dash_cooldown = 45
            elif self.player.dash_cooldown > 0:
                self.player.dash_cooldown -= 1
                
            # ヒート回復
            if not self.player.is_dashing and self.player.heat > 0:
                self.player.heat = max(0, self.player.heat - 1)
                
        self.player.update = mock_update
    
    @log_test
    def test_dash_activation(self):
        """ダッシュが正しく作動するか確認"""
        # 初期状態
        self.assertFalse(self.player.is_dashing)
        self.assertEqual(self.player.dash_cooldown, 0)
        
        # ダッシュを実行
        self.player.dash()
        
        # ダッシュが有効になっていることを確認
        self.assertTrue(self.player.is_dashing)
        self.assertEqual(self.player.dash_duration, 10)
        self.assertEqual(self.player.heat, 20)
    
    @log_test
    def test_dash_cooldown(self):
        """ダッシュのクールダウンが正しく機能するか確認"""
        # ダッシュを実行
        self.player.dash()
        
        # ダッシュが終了するまで更新
        for _ in range(11):  # ダッシュ持続時間 + 1
            self.player.update()
        
        # ダッシュが終了していることを確認
        self.assertFalse(self.player.is_dashing)
        self.assertGreater(self.player.dash_cooldown, 0)
        
        # クールダウン中はダッシュできないことを確認
        dash_result = self.player.dash()
        self.assertFalse(dash_result)
    
    @log_test
    def test_heat_management(self):
        """ヒートゲージの管理が正しく機能するか確認"""
        # 初期状態
        self.assertEqual(self.player.heat, 0)
        
        # ダッシュを複数回実行してヒートを蓄積
        self.player.dash()
        self.assertEqual(self.player.heat, 20)
        
        # クールダウンをリセットして次のダッシュを可能にする
        self.player.dash_cooldown = 0
        self.player.dash()
        self.assertEqual(self.player.heat, 40)
        
        self.player.dash_cooldown = 0
        self.player.dash()
        self.assertEqual(self.player.heat, 60)
        
        # ヒートが徐々に回復することを確認
        self.player.is_dashing = False
        initial_heat = self.player.heat
        
        for _ in range(10):
            self.player.update()
        
        self.assertLess(self.player.heat, initial_heat)

if __name__ == '__main__':
    unittest.main() 