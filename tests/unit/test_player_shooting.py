import unittest
import pygame
import sys
import os

# テスト対象のモジュールをインポートできるようにパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.game.core.player import Player
from src.game.core.controls import Controls
from src.game.core.bullet import Bullet

class TestPlayerShooting(unittest.TestCase):
    """プレイヤーの射撃に関するテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # Pygameの初期化
        pygame.init()
        
        # テスト用のプレイヤーとコントロールを作成
        self.player = Player()
        self.controls = Controls()
        
        # シミュレーションモードを有効化
        self.controls.set_simulation_mode(True)
        
        # 弾のリスト
        self.bullets = []
    
    def tearDown(self):
        """テスト後の後片付け"""
        pygame.quit()
    
    def test_normal_shot(self):
        """通常ショットのテスト"""
        # ショットボタンを押す
        self.controls.simulate_key_press('shoot', True)
        keys_dict = self.controls.create_keys_dict()
        
        # クールダウンをリセット
        self.player.beam_rifle_cooldown = 0
        
        # 弾のリストを用意
        bullets = []
        
        # シミュレート: プレイヤーがショットボタンを押して弾を発射
        if self.player.can_fire("beam_rifle"):
            # ビームを発射する位置（プレイヤーの前方）
            bullet_x = self.player.x + self.player.width
            bullet_y = self.player.y + self.player.height / 2
            
            # 新しい弾を作成
            bullet = Bullet(bullet_x, bullet_y, None, True, "beam_rifle")
            bullets.append(bullet)
            
            # クールダウンを設定
            self.player.beam_rifle_cooldown = self.player.beam_rifle_cooldown_time
        
        # 弾が発射されたことを確認
        self.assertEqual(len(bullets), 1)
        
        # 弾のパラメータを確認
        bullet = bullets[0]
        self.assertEqual(bullet.x, self.player.x + self.player.width)
        self.assertEqual(bullet.y, self.player.y + self.player.height / 2)
        self.assertFalse(bullet.penetrate)  # 通常弾は貫通しない
        
        # クールダウンが設定されていることを確認
        self.assertEqual(self.player.beam_rifle_cooldown, self.player.beam_rifle_cooldown_time)
    
    def test_shot_cooldown(self):
        """ショットのクールダウンテスト"""
        # クールダウンを設定
        self.player.beam_rifle_cooldown = self.player.beam_rifle_cooldown_time
        
        # can_fireメソッドが適切に動作することを確認
        self.assertFalse(self.player.can_fire("beam_rifle"))
        
        # クールダウンを減らす
        self.player.update_weapon_cooldown()
        
        # クールダウンが減っていることを確認
        self.assertEqual(self.player.beam_rifle_cooldown, self.player.beam_rifle_cooldown_time - 1)
        
        # クールダウンをすべて減らす
        for _ in range(self.player.beam_rifle_cooldown_time):
            self.player.update_weapon_cooldown()
        
        # クールダウンが0になったことを確認
        self.assertEqual(self.player.beam_rifle_cooldown, 0)
        
        # 再度発射可能になったことを確認
        self.assertTrue(self.player.can_fire("beam_rifle"))
    
    def test_invincibility(self):
        """無敵状態のテスト"""
        # 初期状態では無敵ではない
        self.assertFalse(self.player.is_invincible())
        
        # ダメージを受ける
        damage_applied = self.player.take_damage(10)
        
        # ダメージが適用されたことを確認
        self.assertTrue(damage_applied)
        
        # HPが減ったことを確認
        self.assertEqual(self.player.hp, 90)
        
        # 無敵状態になったことを確認
        self.assertTrue(self.player.is_invincible())
        
        # 無敵状態中のダメージは無視される
        damage_applied = self.player.take_damage(10)
        self.assertFalse(damage_applied)
        
        # HPが変わっていないことを確認
        self.assertEqual(self.player.hp, 90)
        
        # 無敵時間を減らす
        for _ in range(self.player.invincible_time):
            if self.player.invincible_time > 0:
                self.player.invincible_time -= 1
        
        # 無敵状態が終了したことを確認
        self.assertFalse(self.player.is_invincible())
        
        # 再びダメージを受けることができる
        damage_applied = self.player.take_damage(10)
        self.assertTrue(damage_applied)
        self.assertEqual(self.player.hp, 80)

if __name__ == "__main__":
    unittest.main() 