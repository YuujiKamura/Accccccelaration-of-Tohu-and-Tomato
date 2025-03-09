import unittest
from test_mock_classes import Enemy

class EnemyTest(unittest.TestCase):
    """敵クラスの機能テスト"""

    def setUp(self):
        """各テスト前の準備"""
        # 基本的な敵を初期化
        self.enemy = Enemy(x=100, y=50, enemy_type="mob", speed_factor=1.0)

    def test_initial_state(self):
        """敵の初期状態が正しいことを確認"""
        self.assertEqual(self.enemy.x, 100)
        self.assertEqual(self.enemy.y, 50)
        self.assertEqual(self.enemy.enemy_type, "mob")
        self.assertEqual(self.enemy.health, 50)
        self.assertEqual(self.enemy.max_health, 50)
        self.assertEqual(self.enemy.speed, 2.0)
        self.assertFalse(self.enemy.is_defeated)
        self.assertFalse(self.enemy.is_exploding)

    def test_speed_factor(self):
        """速度係数が正しく適用されるか確認"""
        fast_enemy = Enemy(x=100, y=50, speed_factor=2.0)
        self.assertEqual(fast_enemy.speed, 4.0)  # 2.0 * 2.0
        
        slow_enemy = Enemy(x=100, y=50, speed_factor=0.5)
        self.assertEqual(slow_enemy.speed, 1.0)  # 2.0 * 0.5

    def test_take_damage(self):
        """ダメージを受けた時の処理が正しく機能するか確認"""
        initial_health = self.enemy.health
        damage = 20
        
        self.enemy.take_damage(damage)
        
        # ヘルスが減少していることを確認
        self.assertEqual(self.enemy.health, initial_health - damage)
        
        # まだ倒されていないことを確認
        self.assertFalse(self.enemy.is_defeated)
        self.assertFalse(self.enemy.is_exploding)

    def test_defeat(self):
        """敵が倒される時の処理が正しく機能するか確認"""
        # 敵の体力以上のダメージを与える
        self.enemy.take_damage(self.enemy.health + 10)
        
        # 倒されたことを確認
        self.assertTrue(self.enemy.is_defeated)
        self.assertTrue(self.enemy.is_exploding)
        self.assertEqual(self.enemy.health, -10)

    def test_explosion_animation(self):
        """爆発アニメーションが正しく機能するか確認"""
        # 敵を倒す
        self.enemy.take_damage(self.enemy.health)
        
        # 爆発中であることを確認
        self.assertTrue(self.enemy.is_exploding)
        self.assertEqual(self.enemy.explosion_frame, 0)
        
        # 爆発アニメーションの更新
        self.enemy.update()
        
        # フレームが進んだことを確認
        self.assertEqual(self.enemy.explosion_frame, 1)
        
        # アニメーション終了まで更新
        for _ in range(9):
            self.enemy.update()
        
        # 爆発アニメーションが終了したことを確認
        self.assertFalse(self.enemy.is_exploding)
        self.assertEqual(self.enemy.explosion_frame, 10)

    def test_movement(self):
        """敵の移動処理が正しく機能するか確認"""
        # 初期位置を記録
        initial_x = self.enemy.x
        initial_y = self.enemy.y
        
        # 移動方向を設定
        self.enemy.direction_x = 1
        self.enemy.direction_y = 0
        
        # 1フレーム更新
        self.enemy.update()
        
        # X方向に移動したことを確認
        self.assertEqual(self.enemy.x, initial_x + self.enemy.speed)
        self.assertEqual(self.enemy.y, initial_y)
        
        # 別の方向で再テスト
        self.enemy.direction_x = 0
        self.enemy.direction_y = 1
        
        # 更新前の位置を記録
        prev_x = self.enemy.x
        prev_y = self.enemy.y
        
        # 1フレーム更新
        self.enemy.update()
        
        # Y方向に移動したことを確認
        self.assertEqual(self.enemy.x, prev_x)
        self.assertEqual(self.enemy.y, prev_y + self.enemy.speed)

    def test_defeated_enemy_no_movement(self):
        """倒された敵が移動しないことを確認"""
        # 敵を倒す
        self.enemy.take_damage(self.enemy.health)
        
        # 位置を記録
        initial_x = self.enemy.x
        initial_y = self.enemy.y
        
        # 移動方向を設定
        self.enemy.direction_x = 1
        self.enemy.direction_y = 1
        
        # 1フレーム更新
        self.enemy.update()
        
        # 位置が変わらないことを確認（爆発アニメーションのみ進行）
        self.assertEqual(self.enemy.x, initial_x)
        self.assertEqual(self.enemy.y, initial_y)
        self.assertEqual(self.enemy.explosion_frame, 1)

    def test_enemy_types(self):
        """異なる敵タイプが設定されることを確認"""
        boss_enemy = Enemy(enemy_type="boss")
        self.assertEqual(boss_enemy.enemy_type, "boss")
        
        drone_enemy = Enemy(enemy_type="drone")
        self.assertEqual(drone_enemy.enemy_type, "drone")

if __name__ == '__main__':
    unittest.main() 