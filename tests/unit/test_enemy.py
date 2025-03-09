import unittest
from tests.unit.test_base import BaseTestCase, log_test
from tests.unit.test_mock_classes import Enemy

class EnemyTest(BaseTestCase):
    """敵クラスの機能テスト"""

    def setUp(self):
        """テスト前の準備"""
        super().setUp()  # 親クラスのsetUp()を呼び出す
        
        # 基本的な敵を初期化
        self.enemy = Enemy(x=100, y=50, enemy_type="mob")
        
        # 敵の初期状態を確認
        self.assertEqual(self.enemy.x, 100)
        self.assertEqual(self.enemy.y, 50)
        self.assertEqual(self.enemy.enemy_type, "mob")
        self.assertFalse(self.enemy.is_defeated)
        self.assertFalse(self.enemy.is_exploding)

    @log_test
    def test_movement(self):
        """敵の移動処理が正しく機能するか確認"""
        initial_x = self.enemy.x
        initial_y = self.enemy.y
        
        # 方向を設定
        self.enemy.direction_x = 1
        self.enemy.direction_y = 0.5
        
        # 移動処理
        self.enemy.update()
        
        # 位置が更新されたことを確認
        self.assertEqual(self.enemy.x, initial_x + self.enemy.speed * self.enemy.direction_x)
        self.assertEqual(self.enemy.y, initial_y + self.enemy.speed * self.enemy.direction_y)
        
        # 複数フレームの移動
        frames = 5
        for _ in range(frames):
            self.enemy.update()
        
        # 正確な位置の確認
        expected_x = initial_x + self.enemy.speed * self.enemy.direction_x * (frames + 1)
        expected_y = initial_y + self.enemy.speed * self.enemy.direction_y * (frames + 1)
        self.assertEqual(self.enemy.x, expected_x)
        self.assertEqual(self.enemy.y, expected_y)

    @log_test
    def test_defeated_enemy_no_movement(self):
        """倒された敵が動かないことを確認"""
        initial_x = self.enemy.x
        initial_y = self.enemy.y
        
        # 方向を設定
        self.enemy.direction_x = 1
        self.enemy.direction_y = 1
        
        # 敵を倒す
        self.enemy.take_damage(100)
        self.assertTrue(self.enemy.is_defeated)
        self.assertTrue(self.enemy.is_exploding)
        
        # 爆発中の敵は動かないことを確認
        self.enemy.update()
        self.assertEqual(self.enemy.x, initial_x)
        self.assertEqual(self.enemy.y, initial_y)
        
        # 爆発アニメーションを完了させる
        for _ in range(10):
            self.enemy.update()
        
        # 爆発アニメーションが終了したことを確認
        self.assertFalse(self.enemy.is_exploding)
        self.assertEqual(self.enemy.explosion_frame, 10)

    @log_test
    def test_enemy_types(self):
        """異なる敵タイプが正しく設定されることを確認"""
        # 基本的な敵
        basic_enemy = Enemy(enemy_type="mob")
        self.assertEqual(basic_enemy.enemy_type, "mob")
        
        # ボス敵
        boss_enemy = Enemy(enemy_type="boss")
        self.assertEqual(boss_enemy.enemy_type, "boss")
        
        # 速度係数の確認
        fast_enemy = Enemy(speed_factor=2.0)
        slow_enemy = Enemy(speed_factor=0.5)
        
        self.assertEqual(fast_enemy.speed, 2.0 * 2.0)  # 基本速度 * 係数
        self.assertEqual(slow_enemy.speed, 2.0 * 0.5)  # 基本速度 * 係数

if __name__ == '__main__':
    unittest.main() 