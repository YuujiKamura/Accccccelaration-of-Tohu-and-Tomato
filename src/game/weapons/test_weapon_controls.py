import unittest
import pygame
import math
from src.game.weapons.negi_rifle import NegiRifle
from src.game.core.player import Player
from src.game.core.bullet import Bullet

class TestWeaponControls(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        pygame.init()
        self.screen = pygame.Surface((800, 600))
        self.bullets = []
        self.player = Player()
        self.rifle = self.player.weapon
        self.player.bullets = self.bullets  # bulletsリストを設定
        self.rifle.bullets = self.bullets  # 武器にもbulletsリストを設定
        
    def tearDown(self):
        """テストの後片付け"""
        pygame.quit()
        
    def create_mock_keys(self, **kwargs):
        """キー入力の辞書を作成"""
        keys = {
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LSHIFT: False,
            pygame.K_z: False,
            pygame.K_x: False,
            pygame.K_TAB: False
        }
        # キーの値を更新
        for key, value in kwargs.items():
            if key.startswith('K_'):
                keys[getattr(pygame, key)] = value
        return keys
        
    def test_normal_shot(self):
        """通常射撃（Zキー）のテスト"""
        # キー入力を模擬
        keys = self.create_mock_keys(K_z=True)
        
        # 射撃前の状態確認
        initial_bullet_count = len(self.bullets)
        
        # プレイヤーの更新（射撃）
        self.player.update(keys, [], self.bullets)
        
        # 弾が生成されたことを確認
        self.assertEqual(len(self.bullets), initial_bullet_count + 1)
        
        # 生成された弾の属性を確認
        bullet = self.bullets[-1]
        self.assertIsInstance(bullet, Bullet)
        self.assertEqual(bullet.bullet_type, "beam_rifle")
        self.assertEqual(bullet.charge_level, 0)  # 通常射撃は非チャージ
        
    def test_charge_shot(self):
        """チャージ射撃（Xキー）のテスト"""
        # チャージ開始
        keys = self.create_mock_keys(K_x=True)
        
        # チャージ中の状態を確認
        self.player.update(keys, [], self.bullets)
        self.assertTrue(self.rifle.is_charging)
        
        # チャージを継続（100%まで）
        for _ in range(60):  # 60フレーム（約1秒）
            self.player.update(keys, [], self.bullets)
            
        # チャージレベルが上昇していることを確認
        self.assertGreater(self.rifle.charge_level, 50)
        
        # チャージ解放
        keys = self.create_mock_keys()  # すべてのキーをFalseに
        initial_bullet_count = len(self.bullets)
        self.player.update(keys, [], self.bullets)
        
        # 弾が生成されたことを確認
        self.assertEqual(len(self.bullets), initial_bullet_count + 1)
        
        # 生成された弾の属性を確認
        bullet = self.bullets[-1]
        self.assertIsInstance(bullet, Bullet)
        self.assertEqual(bullet.bullet_type, "beam_rifle")
        self.assertEqual(bullet.charge_level, 1)  # フルチャージ
        
    def test_lock_on_shot(self):
        """ロックオン射撃のテスト"""
        # 模擬的な敵を作成
        class MockEnemy:
            def __init__(self):
                self.x = 400
                self.y = 300
                self.width = 32
                self.height = 32
                
        enemy = MockEnemy()
        self.player.locked_enemy = enemy
        
        # 通常射撃
        keys = self.create_mock_keys(K_z=True)
        self.player.update(keys, [enemy], self.bullets)
        
        # 弾が生成されたことを確認
        self.assertEqual(len(self.bullets), 1)
        
        # 弾が敵の方向を向いていることを確認
        bullet = self.bullets[-1]
        self.assertIsNotNone(bullet.target)
        self.assertEqual(bullet.target, enemy)
        
    def test_weapon_direction(self):
        """武器の向きのテスト"""
        # 模擬的な敵を作成
        class MockEnemy:
            def __init__(self, x, y):
                self.x = x
                self.y = y
                self.width = 32
                self.height = 32
                
        # プレイヤーの位置を設定
        self.player.x = 300
        self.player.y = 300
        
        # 右向きの場合のテスト
        self.player.facing_right = True
        self.player.update(self.create_mock_keys(), [], self.bullets)
        self.assertEqual(self.player.weapon.angle, 0)  # 右向き
        
        # 左向きの場合のテスト
        self.player.facing_right = False
        self.player.update(self.create_mock_keys(), [], self.bullets)
        self.assertEqual(self.player.weapon.angle, 180)  # 左向き
        
        # ロックオン時の向きテスト
        # 右上の敵
        enemy1 = MockEnemy(400, 200)
        self.player.locked_enemy = enemy1
        self.player.update(self.create_mock_keys(), [enemy1], self.bullets)
        expected_angle1 = math.degrees(math.atan2(enemy1.y - self.player.y, enemy1.x - self.player.x))
        self.assertAlmostEqual(self.player.weapon.angle, expected_angle1, places=1)
        
        # 左下の敵
        enemy2 = MockEnemy(200, 400)
        self.player.locked_enemy = enemy2
        self.player.update(self.create_mock_keys(), [enemy2], self.bullets)
        expected_angle2 = math.degrees(math.atan2(enemy2.y - self.player.y, enemy2.x - self.player.x))
        self.assertAlmostEqual(self.player.weapon.angle, expected_angle2, places=1)

if __name__ == '__main__':
    unittest.main() 