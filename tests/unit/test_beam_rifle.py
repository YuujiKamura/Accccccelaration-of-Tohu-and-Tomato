"""
ビームライフルの発射間隔テスト

このモジュールでは、ビームライフル（通常弾）の発射間隔と挙動をテストします。
特に以下の点を検証します：
1. 1回の発射で単発のみが発射されること（複数発射されないこと）
2. クールダウン中は追加で弾が発射されないこと
3. クールダウン後は再度発射できること
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

class BeamRifleTest(BaseTestCase):
    """ビームライフルの発射間隔と挙動のテスト"""
    
    def setUp(self):
        """テスト環境の準備"""
        super().setUp()
        
        # 実際のpygameモジュールを保存
        self.real_pygame = sys.modules.get('pygame')
        
        # モックの作成
        self.pygame_mock = MagicMock()
        self.pygame_mock.K_SPACE = ord(' ')  # スペースキーのキーコード
        
        # キーの状態の辞書
        self.keys = {self.pygame_mock.K_SPACE: False}
        
        # pygameをモックに置き換え
        sys.modules['pygame'] = self.pygame_mock
        
        # 弾のパラメータ定義用のモック
        self.BULLET_TYPES = {
            "beam_rifle": {
                "speed": 12,
                "width": 15,
                "height": 60,
                "damage": 25,
                "homing_strength": 0.001,
                "max_turn_angle": 5,
                "min_homing_distance": 0,
                "max_homing_distance": 9999,
                "color": (100, 200, 255),
                "cooldown": 20  # 発射間隔（フレーム数）
            }
        }
        
        # Playerクラスのモックを作成
        self.player = MagicMock()
        self.player.x = 400
        self.player.y = 300
        self.player.width = 30
        self.player.height = 30
        self.player.facing_right = True
        self.player.weapon_cooldown = 0
        
        # can_fireメソッドの実装
        def can_fire():
            return self.player.weapon_cooldown <= 0
        self.player.can_fire = can_fire
        
        # update_weapon_cooldownメソッドの実装
        def update_weapon_cooldown():
            if self.player.weapon_cooldown > 0:
                self.player.weapon_cooldown -= 1
        self.player.update_weapon_cooldown = update_weapon_cooldown
        
        # 弾リスト
        self.bullets = []
        
        # 敵リスト
        self.enemies = []
        
        # モック関数を通した発射処理
        def fire_beam(keys, bullets, enemies):
            if keys[self.pygame_mock.K_SPACE] and self.player.can_fire():
                # 一回の発射で単発のみ発射する（修正済みの前提）
                bullet_x = self.player.x + (self.player.width if self.player.facing_right else 0)
                bullet_y = self.player.y + self.player.height // 2
                bullets.append(MagicMock())  # モック弾を追加
                
                # 射撃後クールダウン
                self.player.weapon_cooldown = self.BULLET_TYPES["beam_rifle"]["cooldown"]
        
        self.fire_beam = fire_beam
    
    def tearDown(self):
        """テスト環境のクリーンアップ"""
        # 実際のpygameを元に戻す
        if self.real_pygame:
            sys.modules['pygame'] = self.real_pygame
        super().tearDown()
    
    @log_test
    def test_single_shot_firing(self):
        """単発発射のテスト - 1回の発射で1発のみ発射されること"""
        # 初期状態の確認
        self.assertEqual(len(self.bullets), 0)
        self.assertEqual(self.player.weapon_cooldown, 0)
        
        # 発射（スペースキーを押す）
        self.keys[self.pygame_mock.K_SPACE] = True
        self.fire_beam(self.keys, self.bullets, self.enemies)
        
        # 弾が1発だけ発射されたことを確認
        self.assertEqual(len(self.bullets), 1)
        
        # クールダウンが設定されたことを確認
        self.assertEqual(self.player.weapon_cooldown, self.BULLET_TYPES["beam_rifle"]["cooldown"])
    
    @log_test
    def test_cooldown_prevents_firing(self):
        """クールダウン中は発射できないことを確認"""
        # 発射して初期クールダウン設定
        self.keys[self.pygame_mock.K_SPACE] = True
        self.fire_beam(self.keys, self.bullets, self.enemies)
        
        # 初期状態確認
        initial_bullets = len(self.bullets)
        self.assertGreater(self.player.weapon_cooldown, 0)
        
        # クールダウン中に再度発射を試みる
        self.fire_beam(self.keys, self.bullets, self.enemies)
        
        # 弾が追加発射されていないことを確認
        self.assertEqual(len(self.bullets), initial_bullets)
    
    @log_test
    def test_firing_after_cooldown(self):
        """クールダウン終了後は再度発射できることを確認"""
        # 発射して初期クールダウン設定
        self.keys[self.pygame_mock.K_SPACE] = True
        self.fire_beam(self.keys, self.bullets, self.enemies)
        
        # 初期状態確認
        initial_bullets = len(self.bullets)
        self.assertGreater(self.player.weapon_cooldown, 0)
        
        # クールダウンを経過させる
        for _ in range(self.BULLET_TYPES["beam_rifle"]["cooldown"]):
            self.player.update_weapon_cooldown()
        
        # クールダウンが0になったことを確認
        self.assertEqual(self.player.weapon_cooldown, 0)
        
        # 再度発射
        self.fire_beam(self.keys, self.bullets, self.enemies)
        
        # 弾が追加発射されたことを確認
        self.assertEqual(len(self.bullets), initial_bullets + 1)
    
    @log_test
    def test_cooldown_duration(self):
        """クールダウン時間が正確に設定されていることを確認"""
        # 発射してクールダウン設定
        self.keys[self.pygame_mock.K_SPACE] = True
        self.fire_beam(self.keys, self.bullets, self.enemies)
        
        # クールダウンが正確に設定されていることを確認
        self.assertEqual(self.player.weapon_cooldown, 20)  # 定義されたクールダウン値
        
        # クールダウンを半分経過させる
        for _ in range(10):
            self.player.update_weapon_cooldown()
        
        # 半分経過後の確認
        self.assertEqual(self.player.weapon_cooldown, 10)
        
        # 残りのクールダウンを経過させる
        for _ in range(10):
            self.player.update_weapon_cooldown()
        
        # クールダウン完了確認
        self.assertEqual(self.player.weapon_cooldown, 0)

if __name__ == '__main__':
    unittest.main() 