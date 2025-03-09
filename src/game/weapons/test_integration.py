"""
武器システムの統合テスト
"""
import unittest
import pygame
import math
from .base_weapon import BaseWeapon
from .negi_rifle import NegiRifle, NEGI_COLOR, DARK_GREEN

class TestWeaponIntegration(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        pygame.init()
        self.screen = pygame.Surface((800, 600))
        self.rifle = NegiRifle()
        
    def tearDown(self):
        """テストの後片付け"""
        pygame.quit()
        
    def test_charge_and_shoot_cycle(self):
        """チャージ→射撃のサイクルテスト"""
        # 初期状態の確認
        self.assertTrue(self.rifle.can_shoot())
        self.assertEqual(self.rifle.charge_level, 0)
        
        # チャージ開始
        self.rifle.start_charge()
        self.assertTrue(self.rifle.is_charging)
        
        # チャージ中の描画を確認
        surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        
        # チャージ進行中の状態を確認
        for i in range(5):  # 5フレーム分のチャージ
            self.rifle.update_charge(0.2)  # 0.2秒ずつ更新
            self.rifle.draw(surface, (100, 100))
            
            # チャージレベルの確認
            expected_charge = min(100, (i + 1) * 10)  # 1フレームあたり10%チャージ
            self.assertAlmostEqual(self.rifle.charge_level, expected_charge, delta=1)
            
            # エフェクトの確認
            visible_pixels = sum(1 for x in range(200) for y in range(200) 
                               if surface.get_at((x, y))[3] > 0)
            self.assertGreater(visible_pixels, 0, "エフェクトが描画されていません")
        
        # チャージ解放
        charge = self.rifle.release_charge()
        self.assertGreater(charge, 0)
        self.assertFalse(self.rifle.is_charging)
        self.assertEqual(self.rifle.charge_level, 0)
        
        # クールダウン中の状態を確認
        self.rifle.last_shot_time = pygame.time.get_ticks()
        self.assertFalse(self.rifle.can_shoot())
        
    def test_weapon_rotation_with_effects(self):
        """回転とエフェクトの組み合わせテスト"""
        angles = [0, 45, 90, 180]
        surface = pygame.Surface((300, 300), pygame.SRCALPHA)
        center = (150, 150)
        
        # 各角度でチャージエフェクト付きの描画をテスト
        self.rifle.start_charge()
        
        for angle in angles:
            # サーフェスをクリア
            surface.fill((0, 0, 0, 0))
            
            # チャージ更新
            self.rifle.update_charge(1.0)  # 50%チャージ
            
            # 複数フレーム描画して、エフェクトを十分に広げる
            for _ in range(10):  # フレーム数を増やす
                self.rifle.draw(surface, center, angle)
            
            # 描画結果の確認
            visible_pixels = sum(1 for x in range(300) for y in range(300) 
                               if surface.get_at((x, y))[3] > 0)
            self.assertGreater(visible_pixels, 0, 
                             f"角度{angle}度で武器とエフェクトが描画されていません")
            
            # エフェクトの位置を確認（中心からの距離）
            effect_positions = []
            for x in range(300):
                for y in range(300):
                    if surface.get_at((x, y))[3] > 0:
                        dx = x - center[0]
                        dy = y - center[1]
                        distance = math.sqrt(dx*dx + dy*dy)
                        effect_positions.append(distance)
            
            # エフェクトが十分に広がっていることを確認
            if effect_positions:
                max_distance = max(effect_positions)
                min_expected_distance = self.rifle.width * 0.5  # 武器サイズの半分まで
                self.assertGreater(max_distance, min_expected_distance,
                                 "エフェクトが十分に広がっていません")
                
    def test_continuous_charge_and_effects(self):
        """連続チャージとエフェクトの持続テスト"""
        surface = pygame.Surface((400, 400), pygame.SRCALPHA)
        center = (200, 200)
        
        # チャージ開始
        self.rifle.start_charge()
        
        # 3段階のチャージレベルでテスト
        charge_levels = [0.2, 0.5, 0.8]  # 20%, 50%, 80%
        previous_effect_area = 0
        
        for charge_level in charge_levels:
            # チャージ更新
            self.rifle.update_charge(charge_level * 2.0)
            
            # 複数フレーム描画
            surface.fill((0, 0, 0, 0))
            for _ in range(5):
                self.rifle.draw(surface, center)
            
            # エフェクト範囲の計算
            effect_area = sum(1 for x in range(400) for y in range(400) 
                            if surface.get_at((x, y))[3] > 0)
            
            # エフェクトが大きくなっていることを確認
            self.assertGreater(effect_area, previous_effect_area,
                             "チャージレベルの上昇に伴いエフェクトが拡大していません")
            previous_effect_area = effect_area
            
            # エフェクトの色の変化を確認
            colors = [surface.get_at((x, y)) for x in range(400) for y in range(400)
                     if surface.get_at((x, y))[3] > 0]
            
            if colors:
                max_r = max(c[0] for c in colors)
                max_g = max(c[1] for c in colors)
                self.assertGreater(max_r, NEGI_COLOR[0], "エフェクトのR値が増加していません")
                self.assertGreaterEqual(max_g, NEGI_COLOR[1], "エフェクトのG値が維持されていません")
        
if __name__ == '__main__':
    unittest.main() 