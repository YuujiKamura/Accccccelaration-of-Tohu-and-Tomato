import unittest
from test_mock_classes import Player, Enemy, Bullet

class PlayerTest(unittest.TestCase):
    """プレイヤー機能のテスト"""

    def setUp(self):
        """各テスト前の準備"""
        # プレイヤーオブジェクトを初期化
        self.player = Player()
        
        # 必要なキー入力の準備
        self.keys = {'left': False, 'right': False, 'up': False, 'down': False, 'shift': False, 'z': False}
        
        # 敵とバレットの配列を初期化
        self.enemies = []
        self.bullets = []

    def test_initial_state(self):
        """プレイヤーの初期状態が正しいことを確認"""
        self.assertEqual(self.player.health, 100)
        self.assertEqual(self.player.score, 0)
        self.assertFalse(self.player.is_dashing)
        self.assertEqual(self.player.heat, 0)
        self.assertEqual(self.player.dash_cooldown, 0)

    def test_movement_right(self):
        """右移動が正しく機能するか確認"""
        initial_x = self.player.x
        self.keys['right'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        self.assertGreater(self.player.x, initial_x)

    def test_movement_left(self):
        """左移動が正しく機能するか確認"""
        initial_x = self.player.x
        self.keys['left'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        self.assertLess(self.player.x, initial_x)

    def test_movement_up(self):
        """上移動が正しく機能するか確認"""
        initial_y = self.player.y
        self.keys['up'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        self.assertLess(self.player.y, initial_y)

    def test_movement_down(self):
        """下移動が正しく機能するか確認"""
        initial_y = self.player.y
        self.keys['down'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        self.assertGreater(self.player.y, initial_y)

    def test_diagonal_movement(self):
        """斜め移動が正しく機能するか確認"""
        initial_x = self.player.x
        initial_y = self.player.y
        self.keys['right'] = True
        self.keys['down'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        self.assertGreater(self.player.x, initial_x)
        self.assertGreater(self.player.y, initial_y)

    def test_fire_weapon(self):
        """武器発射が正しく機能するか確認"""
        self.keys['z'] = True
        # 武器クールダウンが0であることを確認
        self.assertEqual(self.player.weapon_cooldown, 0)
        
        # 発射処理
        fire_result = self.player.fire()
        
        # 発射が成功したことを確認
        self.assertTrue(fire_result)
        
        # クールダウンが設定されたことを確認
        self.assertGreater(self.player.weapon_cooldown, 0)

    def test_weapon_cooldown(self):
        """武器クールダウンが正しく機能するか確認"""
        # 最初の発射
        self.player.fire()
        initial_cooldown = self.player.weapon_cooldown
        
        # クールダウン中は発射できないことを確認
        fire_result = self.player.fire()
        self.assertFalse(fire_result)
        
        # 1フレーム経過
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # クールダウンが減少したことを確認
        self.assertLess(self.player.weapon_cooldown, initial_cooldown)

if __name__ == '__main__':
    unittest.main() 