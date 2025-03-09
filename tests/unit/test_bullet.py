import unittest
from tests.unit.test_mock_classes import Bullet, Enemy
from tests.unit.test_base import BaseTestCase, log_test

class BulletTest(BaseTestCase):
    """弾クラスの機能テスト"""

    def setUp(self):
        """各テスト前の準備"""
        super().setUp()  # 親クラスのsetUp()を呼ぶ
        # 基本的な弾を初期化
        self.bullet = Bullet(x=100, y=50, facing_right=True, bullet_type="beam_rifle")

    @log_test
    def test_initial_state(self):
        """弾の初期状態が正しいことを確認"""
        self.assertEqual(self.bullet.x, 100)
        self.assertEqual(self.bullet.y, 50)
        self.assertEqual(self.bullet.bullet_type, "beam_rifle")
        self.assertTrue(self.bullet.facing_right)
        self.assertTrue(self.bullet.is_active)
        self.assertTrue(self.bullet.is_player_bullet)
        self.assertEqual(self.bullet.lifetime, 60)

    @log_test
    def test_movement_right(self):
        """右向きの弾の移動が正しいことを確認"""
        initial_x = self.bullet.x
        
        # 移動処理
        self.bullet.move()
        
        # 右方向に移動したことを確認
        self.assertGreater(self.bullet.x, initial_x)
        # 速度分だけ移動したことを確認
        self.assertEqual(self.bullet.x, initial_x + self.bullet.speed)

    @log_test
    def test_movement_left(self):
        """左向きの弾の移動が正しいことを確認"""
        self.bullet = Bullet(x=100, y=50, facing_right=False)
        initial_x = self.bullet.x
        
        # 移動処理
        self.bullet.move()
        
        # 左方向に移動したことを確認
        self.assertLess(self.bullet.x, initial_x)
        # 速度分だけ移動したことを確認
        self.assertEqual(self.bullet.x, initial_x - self.bullet.speed)

    @log_test
    def test_lifetime_decrease(self):
        """弾の寿命が正しく減少することを確認"""
        initial_lifetime = self.bullet.lifetime
        
        # 移動処理
        self.bullet.move()
        
        # 寿命が減少したことを確認
        self.assertEqual(self.bullet.lifetime, initial_lifetime - 1)

    @log_test
    def test_lifetime_expiration(self):
        """寿命切れで弾が非アクティブになることを確認"""
        # 寿命をほぼ0に設定
        self.bullet.lifetime = 1
        self.assertTrue(self.bullet.is_active)
        
        # 移動処理
        self.bullet.move()
        
        # 寿命切れで非アクティブになったことを確認
        self.assertEqual(self.bullet.lifetime, 0)
        self.assertFalse(self.bullet.is_active)

    @log_test
    def test_bullet_types(self):
        """異なる弾タイプが設定されることを確認"""
        shotgun_bullet = Bullet(bullet_type="shotgun")
        self.assertEqual(shotgun_bullet.bullet_type, "shotgun")
        
        missile_bullet = Bullet(bullet_type="missile")
        self.assertEqual(missile_bullet.bullet_type, "missile")

    @log_test
    def test_charge_level(self):
        """チャージレベルが正しく設定されることを確認"""
        charged_bullet = Bullet(charge_level=2)
        self.assertEqual(charged_bullet.charge_level, 2)

    @log_test
    def test_update_method(self):
        """updateメソッドが正しく機能することを確認"""
        initial_x = self.bullet.x
        initial_lifetime = self.bullet.lifetime
        
        # 更新処理
        self.bullet.update()
        
        # 位置が更新されたことを確認
        self.assertGreater(self.bullet.x, initial_x)
        # 寿命が減少したことを確認
        self.assertLess(self.bullet.lifetime, initial_lifetime)

    @log_test
    def test_target_tracking(self):
        """ターゲット指定された場合のテスト（基本実装では使用されない）"""
        target = Enemy(x=200, y=50)
        
        # ターゲットを指定した弾
        tracking_bullet = Bullet(x=100, y=50, target=target)
        
        # ターゲットが設定されていることを確認
        self.assertEqual(tracking_bullet.target, target)

if __name__ == '__main__':
    unittest.main() 