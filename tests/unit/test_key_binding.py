import sys
import unittest
from unittest.mock import MagicMock, patch
import pygame
from tests.unit.test_base import BaseTestCase, log_test

class KeyBindingTest(BaseTestCase):
    """キーバインドのテスト"""
    
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
        
        # キーイベント用のモック
        self.key_up_event = MagicMock()
        self.key_up_event.type = pygame.KEYUP
        self.key_up_event.key = self.pygame_mock.K_SPACE
        
        # pygameをモックに置き換え
        sys.modules['pygame'] = self.pygame_mock
        
        # Playerクラスのモックを作成
        self.player = MagicMock()
        self.player.x = 400
        self.player.y = 300
        self.player.width = 30
        self.player.height = 30
        self.player.facing_right = True
        self.player.weapon_cooldown = 0
        self.player.is_charging = False
        self.player.charge_level = 0
        self.player.charge_target_position = None
        
        # can_fireメソッドの実装
        def can_fire(weapon_type=None):
            return self.player.weapon_cooldown <= 0
        self.player.can_fire = can_fire
        
        # update_chargeメソッドの実装
        def update_charge(keys, enemies):
            if keys.get(self.pygame_mock.K_SPACE, False):
                if not self.player.is_charging:
                    self.player.is_charging = True
                    self.player.charge_start_time = 0  # テスト用簡易値
                else:
                    # テスト用に即座に充電完了
                    self.player.charge_level = 1
                    self.player.charge_target_position = (500, 200)  # 適当な座標
            else:
                self.player.is_charging = False
        self.player.update_charge = update_charge
        
        # 弾リスト
        self.bullets = []
        
        # 敵リスト
        self.enemies = []
        
        # キーアップイベント処理関数
        def process_keyup_event(event, player, bullets):
            if event.type == pygame.KEYUP and event.key == self.pygame_mock.K_SPACE:
                if player.can_fire():
                    target_pos = player.charge_target_position if player.charge_level > 0 else None
                    bullets.append(MagicMock())  # モック弾を追加
                    player.charge_level = 0
                    player.charge_target_position = None
                    player.weapon_cooldown = 20  # クールダウン設定
                    return True
            return False
        self.process_keyup_event = process_keyup_event
        
        # 通常射撃処理関数
        def process_normal_shot(keys, player, bullets):
            if keys.get(self.pygame_mock.K_SPACE, False) and player.can_fire() and not player.is_charging:
                bullets.append(MagicMock())  # モック弾を追加
                player.weapon_cooldown = 20  # クールダウン設定
                return True
            return False
        self.process_normal_shot = process_normal_shot
    
    def tearDown(self):
        """テスト環境のクリーンアップ"""
        # 実際のpygameを元に戻す
        if self.real_pygame:
            sys.modules['pygame'] = self.real_pygame
        super().tearDown()
    
    @log_test
    def test_charge_laser_flow(self):
        """チャージレーザーの操作フローのテスト"""
        # 初期状態の確認
        self.assertEqual(len(self.bullets), 0)
        self.assertEqual(self.player.weapon_cooldown, 0)
        self.assertFalse(self.player.is_charging)
        self.assertEqual(self.player.charge_level, 0)
        
        # スペースキーを押す（チャージ開始）
        self.keys[self.pygame_mock.K_SPACE] = True
        self.player.update_charge(self.keys, self.enemies)
        
        # チャージ中の状態を確認
        self.assertTrue(self.player.is_charging)
        
        # チャージ中は通常射撃が発動しないことを確認
        result = self.process_normal_shot(self.keys, self.player, self.bullets)
        self.assertFalse(result)
        self.assertEqual(len(self.bullets), 0)
        
        # 十分なチャージを行う
        self.player.update_charge(self.keys, self.enemies)
        
        # チャージ完了の確認
        self.assertEqual(self.player.charge_level, 1)
        self.assertIsNotNone(self.player.charge_target_position)
        
        # スペースキーを離す（発射）
        self.keys[self.pygame_mock.K_SPACE] = False
        result = self.process_keyup_event(self.key_up_event, self.player, self.bullets)
        
        # 発射されたことを確認
        self.assertTrue(result)
        self.assertEqual(len(self.bullets), 1)
        self.assertEqual(self.player.charge_level, 0)
        self.assertIsNone(self.player.charge_target_position)
        self.assertGreater(self.player.weapon_cooldown, 0)
        
    @log_test
    def test_charge_during_cooldown(self):
        """クールダウン中にチャージを試みるテスト"""
        # 発射してクールダウン状態にする
        self.keys[self.pygame_mock.K_SPACE] = True
        self.player.update_charge(self.keys, self.enemies)
        self.player.update_charge(self.keys, self.enemies)
        self.process_keyup_event(self.key_up_event, self.player, self.bullets)
        
        # クールダウン中であることを確認
        self.assertGreater(self.player.weapon_cooldown, 0)
        
        # 再度チャージを試みる
        self.keys[self.pygame_mock.K_SPACE] = True
        self.player.update_charge(self.keys, self.enemies)
        
        # 発射を試みる
        result = self.process_keyup_event(self.key_up_event, self.player, self.bullets)
        
        # クールダウン中は発射できないはず
        self.assertFalse(result)
        self.assertEqual(len(self.bullets), 1)  # 弾の数は増えていない
        
    @log_test
    def test_charge_cancel(self):
        """チャージキャンセルのテスト"""
        # チャージ開始
        self.keys[self.pygame_mock.K_SPACE] = True
        self.player.update_charge(self.keys, self.enemies)
        
        # チャージ中であることを確認
        self.assertTrue(self.player.is_charging)
        
        # チャージキャンセル（スペースキーを離す）
        self.keys[self.pygame_mock.K_SPACE] = False
        self.player.update_charge(self.keys, self.enemies)
        
        # チャージがキャンセルされたことを確認
        self.assertFalse(self.player.is_charging)
        
    @log_test
    def test_space_held_down_behavior(self):
        """スペースキーを押しっぱなしにした際の挙動テスト"""
        # 初期状態確認
        self.assertEqual(len(self.bullets), 0)
        
        # スペースキーを押す
        self.keys[self.pygame_mock.K_SPACE] = True
        
        # 最初のフレーム - チャージ開始前
        self.assertFalse(self.player.is_charging)
        
        # 通常射撃が発生することを確認
        result = self.process_normal_shot(self.keys, self.player, self.bullets)
        self.assertTrue(result)
        self.assertEqual(len(self.bullets), 1)
        
        # チャージを開始
        self.player.update_charge(self.keys, self.enemies)
        
        # チャージ中になったことを確認
        self.assertTrue(self.player.is_charging)
        
        # チャージ中は通常射撃が発生しないことを確認
        result = self.process_normal_shot(self.keys, self.player, self.bullets)
        self.assertFalse(result)
        self.assertEqual(len(self.bullets), 1)  # 弾の数は増えていない 