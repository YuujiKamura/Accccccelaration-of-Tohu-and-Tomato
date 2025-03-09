"""
武器クラスのテストコード
"""
import unittest
import pygame
import time
import math
from .base_weapon import BaseWeapon
from .negi_rifle import NegiRifle, NEGI_COLOR, DARK_GREEN

class TestBaseWeapon(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        pygame.init()
        self.weapon = BaseWeapon("テスト武器", 10, 1.0)
        
    def tearDown(self):
        """テストの後片付け"""
        pygame.quit()
        
    def test_init(self):
        """初期化のテスト"""
        self.assertEqual(self.weapon.name, "テスト武器")
        self.assertEqual(self.weapon.damage, 10)
        self.assertEqual(self.weapon.cooldown, 1.0)
        self.assertEqual(self.weapon.last_shot_time, 0)
        
    def test_can_shoot(self):
        """射撃可能判定のテスト"""
        # 初期状態では射撃可能
        current_time = pygame.time.get_ticks()
        self.weapon.last_shot_time = current_time - 2000  # 2秒前に発射したとする
        self.assertTrue(self.weapon.can_shoot())
        
        # 射撃後はクールダウン中
        self.weapon.last_shot_time = current_time
        self.assertFalse(self.weapon.can_shoot())
        
class TestNegiRifle(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        pygame.init()
        self.screen = pygame.Surface((800, 600))
        self.rifle = NegiRifle()
        
    def tearDown(self):
        """テストの後片付け"""
        pygame.quit()
        
    def test_init(self):
        """初期化のテスト"""
        self.assertEqual(self.rifle.name, "ネギライフル")
        self.assertEqual(self.rifle.damage, 10)
        self.assertEqual(self.rifle.cooldown, 0.5)
        self.assertEqual(self.rifle.charge_level, 0)
        self.assertEqual(self.rifle.max_charge, 100)
        self.assertFalse(self.rifle.is_charging)
        
    def test_charge(self):
        """チャージ機能のテスト"""
        # チャージ開始
        self.rifle.start_charge()
        self.assertTrue(self.rifle.is_charging)
        self.assertEqual(self.rifle.charge_level, 0)
        
        # チャージ更新
        self.rifle.update_charge(1.0)  # 1秒経過
        self.assertEqual(self.rifle.charge_level, 50)  # 50%チャージ
        
        # チャージ解放
        charge = self.rifle.release_charge()
        self.assertEqual(charge, 50)
        self.assertFalse(self.rifle.is_charging)
        self.assertEqual(self.rifle.charge_level, 0)
        
    def test_max_charge(self):
        """最大チャージのテスト"""
        self.rifle.start_charge()
        self.rifle.update_charge(3.0)  # 十分な時間経過
        self.assertEqual(self.rifle.charge_level, self.rifle.max_charge)
        
    def test_draw(self):
        """描画のテスト"""
        # 通常状態の描画
        self.rifle.draw(self.screen, (400, 300))
        
        # チャージ状態の描画
        self.rifle.start_charge()
        self.rifle.update_charge(1.0)
        self.rifle.draw(self.screen, (400, 300), 45)  # 45度回転
        
    def test_colors(self):
        """色の設定のテスト"""
        # 基本色の確認
        self.assertEqual(NEGI_COLOR, (200, 255, 200))  # 薄緑色
        self.assertEqual(DARK_GREEN, (0, 100, 0))      # 深緑色
        
        # チャージ時の色変化をテスト
        self.rifle.start_charge()
        self.rifle.update_charge(1.0)  # チャージレベル50
        
        # 描画用のサーフェスを作成
        surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        self.rifle.draw(surface, (50, 50))
        
        # チャージ時の色が正しく変化しているか確認
        color_at_center = surface.get_at((50, 50))
        self.assertGreater(color_at_center[0], NEGI_COLOR[0])  # R値が増加
        self.assertGreaterEqual(color_at_center[1], NEGI_COLOR[1])  # G値は維持または増加
        self.assertEqual(color_at_center[2], NEGI_COLOR[2])    # B値は変化なし
        
    def test_rotation_angles(self):
        """回転角度のテスト"""
        # 様々な角度でテスト
        test_angles = [0, 45, 90, 180, 270, 359]
        
        for angle in test_angles:
            # 描画用のサーフェスを作成
            surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            self.rifle.draw(surface, (50, 50), angle)
            
            # 回転後も武器が描画されているか確認
            # 完全な透明でない画素が存在することを確認
            has_visible_pixels = False
            for x in range(100):
                for y in range(100):
                    if surface.get_at((x, y))[3] > 0:  # アルファ値が0より大きい
                        has_visible_pixels = True
                        break
                if has_visible_pixels:
                    break
            
            self.assertTrue(has_visible_pixels, f"角度{angle}度で武器が描画されていません")
            
    def test_target_direction(self):
        """目標方向への回転テスト"""
        # 様々な目標位置でテスト
        test_positions = [
            ((50, 0), -90),    # 上
            ((100, 50), 0),    # 右
            ((50, 100), 90),   # 下
            ((0, 50), 180),    # 左
            ((100, 100), 45),  # 右下
            ((0, 0), -135),    # 左上
        ]
        
        center_pos = (50, 50)
        for target_pos, expected_angle in test_positions:
            # 目標位置から角度を計算
            dx = target_pos[0] - center_pos[0]
            dy = target_pos[1] - center_pos[1]
            angle = math.degrees(math.atan2(dy, dx))
                
            # 期待される角度と近いか確認（浮動小数点の誤差を考慮）
            self.assertAlmostEqual(angle, expected_angle, delta=1.0,
                                 msg=f"目標位置{target_pos}での角度が不正: {angle} != {expected_angle}")
            
            # 実際に描画してみる
            surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            self.rifle.draw(surface, center_pos, angle)
        
    def test_charge_effect(self):
        """チャージ時のエフェクトテスト"""
        # 描画用のサーフェスを作成
        surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        
        # チャージなしの状態を確認
        self.rifle.draw(surface, (100, 100))
        base_pixels = sum(1 for x in range(200) for y in range(200) 
                         if surface.get_at((x, y))[3] > 0)
        
        # チャージ開始
        self.rifle.start_charge()
        self.rifle.update_charge(1.0)  # 50%チャージ
        
        # 新しいサーフェスで描画（複数フレーム）
        charge_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        for _ in range(10):  # 10フレーム分描画
            self.rifle.draw(charge_surface, (100, 100))
        
        # チャージ時のピクセル数を確認（エフェクトにより増加しているはず）
        charge_pixels = sum(1 for x in range(200) for y in range(200) 
                          if charge_surface.get_at((x, y))[3] > 0)
        
        self.assertGreater(charge_pixels, base_pixels, 
                          "チャージ時にエフェクトが追加されていません")
        
        # エフェクトの色を確認
        center_color = charge_surface.get_at((100, 100))
        self.assertGreater(center_color[0], NEGI_COLOR[0])  # R値が増加
        self.assertGreaterEqual(center_color[1], NEGI_COLOR[1])  # G値は維持または増加
        
    def test_effect_animation(self):
        """エフェクトのアニメーションテスト"""
        # 描画用のサーフェスを作成
        surface1 = pygame.Surface((200, 200), pygame.SRCALPHA)
        surface2 = pygame.Surface((200, 200), pygame.SRCALPHA)
        
        # チャージ開始
        self.rifle.start_charge()
        self.rifle.update_charge(0.5)  # 25%チャージ
        
        # 1フレーム目を描画（複数回更新）
        for _ in range(5):
            self.rifle.draw(surface1, (100, 100))
        
        # チャージを進める
        self.rifle.update_charge(0.5)  # さらに25%チャージ
        
        # 2フレーム目を描画（複数回更新）
        for _ in range(5):
            self.rifle.draw(surface2, (100, 100))
        
        # フレーム間で変化があることを確認
        def get_effect_area(surface):
            return sum(1 for x in range(200) for y in range(200) 
                      if surface.get_at((x, y))[3] > 0)
        
        area1 = get_effect_area(surface1)
        area2 = get_effect_area(surface2)
        
        self.assertNotEqual(area1, area2, 
                          "エフェクトがアニメーションしていません")
        
if __name__ == '__main__':
    unittest.main() 