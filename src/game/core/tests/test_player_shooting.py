"""
プレイヤーの射撃機能テスト

このモジュールでは、Playerクラスの射撃機能をテストします。
以下の機能を検証します：
- 通常射撃（ビームライフル）
- チャージショット
- ロックオン射撃
- 射撃クールダウン
"""

import unittest
import sys
import os
import pygame
import math

# システムパスに上位ディレクトリを追加（相対インポート用）
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# テスト対象のモジュールをインポート
from src.game.core.player import Player
from src.game.core.enemy import Enemy
from src.game.core.bullet import Bullet, BULLET_TYPES
from src.game.core.controls import Controls

class TestPlayerShooting(unittest.TestCase):
    """プレイヤーの射撃機能に関するテスト"""
    
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
        
        # 敵のリスト
        self.enemies = []
    
    def tearDown(self):
        """テスト後の後片付け"""
        pygame.quit()
    
    def test_normal_shot(self):
        """通常射撃のテスト
        
        Zキーを押すと、弾が発射されるか検証します。
        """
        # 射撃ボタンを押す
        self.controls.simulate_key_press('shoot', True)
        keys_dict = self.controls.create_keys_dict()
        
        # クールダウンをリセット
        self.player.beam_rifle_cooldown = 0
        
        # プレイヤーの更新
        self.player.update(keys_dict, self.enemies, self.bullets)
        
        # 弾が発射されたことを確認（bulletsリストに追加されているか）
        self.assertEqual(len(self.bullets), 1, "弾が発射されていません")
        
        # 発射された弾の確認
        bullet = self.bullets[0]
        
        # プレイヤーの向いている方向に弾が発射されていることを確認
        if self.player.facing_right:
            self.assertGreater(bullet.dx, 0, "右向きなのに弾が右に進んでいません")
        else:
            self.assertLess(bullet.dx, 0, "左向きなのに弾が左に進んでいません")
            
        # 弾の種類が正しいことを確認
        self.assertEqual(bullet.damage, BULLET_TYPES["beam_rifle"]["damage"], "弾のダメージが通常射撃と異なります")
        
        # クールダウンが設定されていることを確認
        self.assertEqual(self.player.beam_rifle_cooldown, self.player.beam_rifle_cooldown_time)
    
    def test_shot_cooldown(self):
        """射撃クールダウンのテスト
        
        クールダウン中は弾が発射されないことを検証します。
        """
        # クールダウンを設定
        self.player.beam_rifle_cooldown = self.player.beam_rifle_cooldown_time
        
        # 射撃ボタンを押す
        self.controls.simulate_key_press('shoot', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新
        self.player.update(keys_dict, self.enemies, self.bullets)
        
        # クールダウン中なので弾は発射されないはず
        self.assertEqual(len(self.bullets), 0, "クールダウン中なのに弾が発射されています")
        
        # クールダウンを消費
        for _ in range(self.player.beam_rifle_cooldown_time):
            self.player.update_weapon_cooldown()
        
        # クールダウンが終わったことを確認
        self.assertEqual(self.player.beam_rifle_cooldown, 0)
        
        # 再度プレイヤーの更新
        self.player.update(keys_dict, self.enemies, self.bullets)
        
        # 弾が発射されたことを確認
        self.assertEqual(len(self.bullets), 1, "クールダウン後も弾が発射されていません")
    
    def test_charge_shot(self):
        """チャージショットのテスト
        
        チャージボタンを押し続け、離した時にチャージショットが発射されるか検証します。
        """
        # チャージボタンを押す
        self.controls.simulate_key_press('charge', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（チャージ開始）
        self.player.update(keys_dict, self.enemies, self.bullets)
        
        # チャージが開始されていることを確認
        self.assertTrue(self.player.is_charging, "チャージが開始されていません")
        
        # チャージが最大になるまで更新
        initial_charge = self.player.charge_level
        
        # チャージが最大になるまで更新を繰り返す
        for _ in range(100):  # 十分な回数繰り返す
            self.player.update(keys_dict, self.enemies, self.bullets)
            if self.player.charge_level >= self.player.max_charge_level:
                break
                
        # チャージが上昇していることを確認
        self.assertGreater(self.player.charge_level, initial_charge, "チャージレベルが上昇していません")
        
        # チャージボタンを離す
        self.controls.simulate_key_press('charge', False)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（チャージショット発射）
        self.player.update(keys_dict, self.enemies, self.bullets)
        
        # チャージショットが発射されたことを確認
        self.assertEqual(len(self.bullets), 1, "チャージショットが発射されていません")
        
        # チャージショットの性質を確認
        bullet = self.bullets[0]
        
        # チャージショットは貫通するはず
        self.assertTrue(bullet.penetrate, "チャージショットが貫通属性を持っていません")
        
        # チャージショットは通常弾より威力が高いはず
        self.assertGreater(bullet.damage, BULLET_TYPES["beam_rifle"]["damage"], "チャージショットのダメージが不足しています")
        
        # チャージ状態がリセットされていることを確認
        self.assertFalse(self.player.is_charging, "チャージ状態がリセットされていません")
        self.assertEqual(self.player.charge_level, 0, "チャージレベルがリセットされていません")
    
    def test_lock_on_shot(self):
        """ロックオン射撃のテスト
        
        敵をロックオンして射撃すると、その方向に弾が発射されるか検証します。
        """
        # 敵を作成（プレイヤーの右側）
        enemy = Enemy()
        enemy.x = self.player.x + 200  # プレイヤーの右側に配置
        enemy.y = self.player.y
        self.enemies.append(enemy)
        
        # 敵をロックオン
        self.player.locked_enemy = enemy
        
        # 射撃ボタンを押す
        self.controls.simulate_key_press('shoot', True)
        keys_dict = self.controls.create_keys_dict()
        
        # クールダウンをリセット
        self.player.beam_rifle_cooldown = 0
        
        # プレイヤーの更新
        self.player.update(keys_dict, self.enemies, self.bullets)
        
        # 弾が発射されたことを確認
        self.assertEqual(len(self.bullets), 1, "弾が発射されていません")
        
        # 発射された弾がロックオンした敵の方向に向かっていることを確認
        bullet = self.bullets[0]
        
        # ターゲットの設定を確認
        self.assertEqual(bullet.target, enemy, "弾のターゲットが正しく設定されていません")
        
        # 弾の方向が敵に向かっていることを確認
        # 敵は右側にいるので、弾のdxは正の値のはず
        self.assertGreater(bullet.dx, 0, "弾が敵の方向に向かっていません")
    
    def test_cannot_shoot_without_input(self):
        """入力なしでは射撃されないテスト
        
        射撃ボタンを押さなければ弾は発射されないことを検証します。
        """
        # 射撃ボタンを押さない
        keys_dict = self.controls.create_keys_dict()
        
        # クールダウンをリセット
        self.player.beam_rifle_cooldown = 0
        
        # プレイヤーの更新
        self.player.update(keys_dict, self.enemies, self.bullets)
        
        # 弾が発射されていないことを確認
        self.assertEqual(len(self.bullets), 0, "入力がないのに弾が発射されています")
    
    def test_shoot_direction(self):
        """射撃方向のテスト
        
        プレイヤーの向きに応じて弾の方向が変わることを検証します。
        """
        # プレイヤーを右向きにする
        self.player.facing_right = True
        
        # 射撃ボタンを押す
        self.controls.simulate_key_press('shoot', True)
        keys_dict = self.controls.create_keys_dict()
        
        # クールダウンをリセット
        self.player.beam_rifle_cooldown = 0
        
        # プレイヤーの更新（右向きで射撃）
        self.player.update(keys_dict, self.enemies, self.bullets)
        
        # 弾が発射されたことを確認
        self.assertEqual(len(self.bullets), 1, "弾が発射されていません")
        
        # 右向きの弾を保存
        right_bullet = self.bullets[0]
        
        # 弾リストをクリア
        self.bullets.clear()
        
        # プレイヤーを左向きにする
        self.player.facing_right = False
        
        # クールダウンをリセット
        self.player.beam_rifle_cooldown = 0
        
        # プレイヤーの更新（左向きで射撃）
        self.player.update(keys_dict, self.enemies, self.bullets)
        
        # 弾が発射されたことを確認
        self.assertEqual(len(self.bullets), 1, "弾が発射されていません")
        
        # 左向きの弾を取得
        left_bullet = self.bullets[0]
        
        # 弾の方向が異なることを確認
        self.assertGreater(right_bullet.dx, 0, "右向きの弾が右に進んでいません")
        self.assertLess(left_bullet.dx, 0, "左向きの弾が左に進んでいません")
    
    def test_rapid_fire_with_cooldown(self):
        """連射とクールダウンのテスト
        
        連射時にクールダウンが正しく機能することを検証します。
        """
        # 射撃ボタンを押す
        self.controls.simulate_key_press('shoot', True)
        keys_dict = self.controls.create_keys_dict()
        
        # 発射回数をカウントする変数
        shot_count = 0
        
        # 最初は必ずクールダウンをリセットしておく
        self.player.beam_rifle_cooldown = 0
        
        # 複数回更新を行い、クールダウンがちゃんと機能しているか確認
        for i in range(10):
            # プレイヤーを更新（射撃を試みる）
            self.player.update(keys_dict, self.enemies, self.bullets)
            
            # 弾が発射されたかを確認し、カウント
            current_count = len(self.bullets)
            if current_count > shot_count:
                # 弾が増えた場合
                self.assertEqual(current_count, shot_count + 1, "一度に複数の弾が発射されました")
                shot_count = current_count
                
                # 発射直後はクールダウンが設定されているはず
                self.assertEqual(
                    self.player.beam_rifle_cooldown,
                    self.player.beam_rifle_cooldown_time,
                    "弾の発射後にクールダウンが正しく設定されていません"
                )
                
                # クールダウン中は発射できないことを確認
                self.assertFalse(
                    self.player.can_fire("beam_rifle"),
                    "クールダウン中なのにcan_fireがTrueを返しています"
                )
            
            # クールダウンを少し減らす（完全には消費しない）
            self.player.update_weapon_cooldown()
        
        # 10回の更新でも、クールダウンのため発射回数は限られるはず
        self.assertLess(shot_count, 10, "クールダウンが機能していないようです")
        self.assertGreater(shot_count, 0, "一度も射撃されていません")

if __name__ == "__main__":
    # テストを実行
    unittest.main() 