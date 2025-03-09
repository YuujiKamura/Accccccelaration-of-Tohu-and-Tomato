import unittest
import pygame
import sys
import os

# テスト対象のモジュールをインポートできるようにパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.game.core.player import Player
from src.game.core.controls import Controls

class TestPlayerMovement(unittest.TestCase):
    """プレイヤーの移動に関するテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # Pygameの初期化
        pygame.init()
        
        # テスト用のプレイヤーとコントロールを作成
        self.player = Player()
        self.controls = Controls()
        
        # シミュレーションモードを有効化
        self.controls.set_simulation_mode(True)
        
        # 初期位置を保存
        self.initial_x = self.player.x
        self.initial_y = self.player.y
    
    def tearDown(self):
        """テスト後の後片付け"""
        pygame.quit()
    
    def test_no_movement(self):
        """何も押されていない場合は動かない"""
        # キー入力なし
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新
        self.player.move(keys_dict)
        
        # 位置が変わっていないことを確認
        self.assertAlmostEqual(self.player.x, self.initial_x, delta=0.1)
        self.assertAlmostEqual(self.player.y, self.initial_y, delta=0.1)
    
    def test_move_right(self):
        """右キーで右に移動"""
        # 右キーを押す
        self.controls.simulate_key_press('right', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 右に移動していることを確認
        self.assertGreater(self.player.x, self.initial_x)
        self.assertAlmostEqual(self.player.y, self.initial_y, delta=0.1)
        
        # 向きが右になっていること
        self.assertTrue(self.player.facing_right)
    
    def test_move_left(self):
        """左キーで左に移動"""
        # 左キーを押す
        self.controls.simulate_key_press('left', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 左に移動していることを確認
        self.assertLess(self.player.x, self.initial_x)
        self.assertAlmostEqual(self.player.y, self.initial_y, delta=0.1)
        
        # 向きが左になっていること
        self.assertFalse(self.player.facing_right)
    
    def test_move_up(self):
        """上キーで上に移動"""
        # 上キーを押す
        self.controls.simulate_key_press('up', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 上に移動していることを確認
        self.assertAlmostEqual(self.player.x, self.initial_x, delta=0.1)
        self.assertLess(self.player.y, self.initial_y)
    
    def test_move_down(self):
        """下キーで下に移動"""
        # 下キーを押す
        self.controls.simulate_key_press('down', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 下に移動していることを確認
        self.assertAlmostEqual(self.player.x, self.initial_x, delta=0.1)
        self.assertGreater(self.player.y, self.initial_y)
    
    def test_diagonal_movement(self):
        """斜め移動のテスト（正規化されているか）"""
        # 右下キーを押す
        self.controls.simulate_key_press('right', True)
        self.controls.simulate_key_press('down', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 右下に移動していることを確認
        self.assertGreater(self.player.x, self.initial_x)
        self.assertGreater(self.player.y, self.initial_y)
        
        # 移動距離を計算
        dx = self.player.x - self.initial_x
        dy = self.player.y - self.initial_y
        
        # 斜め移動時の速度が適切に正規化されているか確認
        # 許容誤差を考慮して、両方の移動量がほぼ同じであることを確認
        self.assertAlmostEqual(dx / dy, 1.0, delta=0.1)
    
    def test_dash_movement(self):
        """ダッシュ移動のテスト"""
        # 右キーとシフトキーを押す
        self.controls.simulate_key_press('right', True)
        self.controls.simulate_key_press('dash', True)
        keys_dict = self.controls.create_keys_dict()
        
        # ヒートゲージを0に設定
        self.player.heat = 0
        
        # プレイヤーの更新（1フレーム）
        self.player.move(keys_dict)
        
        # ダッシュが開始されていることを確認
        self.assertTrue(self.player.is_dashing)
        
        # 通常の移動より速く移動していることを確認するため、通常移動の距離を計算
        normal_player = Player()
        normal_player.x = self.initial_x
        normal_player.y = self.initial_y
        
        # 通常の右移動
        normal_controls = Controls()
        normal_controls.set_simulation_mode(True)
        normal_controls.simulate_key_press('right', True)
        normal_keys_dict = normal_controls.create_keys_dict()
        
        # 通常プレイヤーの更新
        normal_player.move(normal_keys_dict)
        
        # ダッシュ中の方が速いことを確認
        self.assertGreater(self.player.speed_x, normal_player.speed_x)
    
    def test_dash_heat_limit(self):
        """ダッシュのヒート制限テスト"""
        # ヒートゲージを最大に設定
        self.player.heat = self.player.max_heat
        
        # 右キーとシフトキーを押す
        self.controls.simulate_key_press('right', True)
        self.controls.simulate_key_press('dash', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新
        self.player.move(keys_dict)
        
        # ヒートが最大のためダッシュが開始されないことを確認
        self.assertFalse(self.player.is_dashing)
    
    def test_dash_cooldown(self):
        """ダッシュのクールダウンテスト"""
        # 右キーとシフトキーを押す
        self.controls.simulate_key_press('right', True)
        self.controls.simulate_key_press('dash', True)
        keys_dict = self.controls.create_keys_dict()
        
        # ヒートゲージを0に設定
        self.player.heat = 0
        
        # プレイヤーの更新（ダッシュ開始）
        self.player.move(keys_dict)
        
        # ダッシュが開始されていることを確認
        self.assertTrue(self.player.is_dashing)
        
        # ダッシュ中の更新（ダッシュ終了まで）
        for _ in range(self.player.dash_duration):
            self.player.move(keys_dict)
        
        # ダッシュが終了していることを確認
        self.assertFalse(self.player.is_dashing)
        
        # クールダウンが設定されていることを確認
        # 厳密な値ではなく、クールダウンが一定以上あることを確認
        self.assertGreater(self.player.dash_cooldown, 0)
        self.assertLessEqual(self.player.dash_cooldown, self.player.dash_cooldown_time)
        
        # クールダウン中は再度ダッシュできないことを確認
        self.player.move(keys_dict)
        self.assertFalse(self.player.is_dashing)
    
    def test_screen_boundaries(self):
        """画面外に出ないことを確認するテスト"""
        # 左上端に移動
        self.player.x = 0
        self.player.y = 0
        
        # さらに左上に移動しようとする
        self.controls.simulate_key_press('left', True)
        self.controls.simulate_key_press('up', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 画面外に出ていないことを確認
        self.assertGreaterEqual(self.player.x, 0)
        self.assertGreaterEqual(self.player.y, 0)
        
        # 右下端に移動
        self.player.x = 800 - self.player.width
        self.player.y = 600 - self.player.height
        
        # さらに右下に移動しようとする
        self.controls.simulate_key_press('left', False)
        self.controls.simulate_key_press('up', False)
        self.controls.simulate_key_press('right', True)
        self.controls.simulate_key_press('down', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 画面外に出ていないことを確認
        self.assertLessEqual(self.player.x, 800 - self.player.width)
        self.assertLessEqual(self.player.y, 600 - self.player.height)
    
    def test_movement_inertia(self):
        """移動の慣性テスト"""
        # 右に移動
        self.controls.simulate_key_press('right', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（加速）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 現在の速度を保存
        speed_x_before = self.player.speed_x
        
        # キーを離す
        self.controls.simulate_key_press('right', False)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（減速）
        self.player.move(keys_dict)
        
        # 慣性で移動が続いていることを確認（速度が急に0になっていない）
        self.assertGreater(self.player.speed_x, 0)
        self.assertLess(self.player.speed_x, speed_x_before)
        
        # 完全に停止するまで更新
        while self.player.speed_x > 0:
            self.player.move(keys_dict)
            
        # 最終的に停止することを確認
        self.assertAlmostEqual(self.player.speed_x, 0, delta=0.1)

if __name__ == "__main__":
    unittest.main() 