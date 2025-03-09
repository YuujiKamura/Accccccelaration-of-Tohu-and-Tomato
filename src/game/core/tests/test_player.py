"""
プレイヤークラスのテスト

このモジュールでは、Playerクラスの機能をテストします。
特に以下の機能に注目してテストします：
- 8方向移動
- ダッシュ機能（カーブダッシュを含む）
- ヒート管理
- 衝突判定
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
from src.game.core.controls import Controls

# テスト用の相対インポート
# from ..player import Player
# from ..controls import Controls

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
    
    # 8方向移動テスト
    
    def test_movement_8way_right(self):
        """8方向移動: 右"""
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
    
    def test_movement_8way_left(self):
        """8方向移動: 左"""
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
    
    def test_movement_8way_up(self):
        """8方向移動: 上"""
        self.controls.simulate_key_press('up', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 上に移動していることを確認
        self.assertAlmostEqual(self.player.x, self.initial_x, delta=0.1)
        self.assertLess(self.player.y, self.initial_y)
    
    def test_movement_8way_down(self):
        """8方向移動: 下"""
        self.controls.simulate_key_press('down', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 下に移動していることを確認
        self.assertAlmostEqual(self.player.x, self.initial_x, delta=0.1)
        self.assertGreater(self.player.y, self.initial_y)
    
    def test_movement_8way_up_right(self):
        """8方向移動: 右上"""
        self.controls.simulate_key_press('up', True)
        self.controls.simulate_key_press('right', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 右上に移動していることを確認
        self.assertGreater(self.player.x, self.initial_x)
        self.assertLess(self.player.y, self.initial_y)
        
        # 斜め移動の場合、速度が正規化されていることを確認
        dx = self.player.x - self.initial_x
        dy = self.initial_y - self.player.y  # yは上が負なので反転
        
        # 方向ベクトルの正規化を確認
        ratio = dx / dy if dy != 0 else float('inf')
        self.assertAlmostEqual(ratio, 1.0, delta=0.2)
    
    def test_movement_8way_up_left(self):
        """8方向移動: 左上"""
        self.controls.simulate_key_press('up', True)
        self.controls.simulate_key_press('left', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 左上に移動していることを確認
        self.assertLess(self.player.x, self.initial_x)
        self.assertLess(self.player.y, self.initial_y)
        
        # 斜め移動の場合、速度が正規化されていることを確認
        dx = self.initial_x - self.player.x
        dy = self.initial_y - self.player.y  # yは上が負なので反転
        
        # 方向ベクトルの正規化を確認
        ratio = dx / dy if dy != 0 else float('inf')
        self.assertAlmostEqual(ratio, 1.0, delta=0.2)
    
    def test_movement_8way_down_right(self):
        """8方向移動: 右下"""
        self.controls.simulate_key_press('down', True)
        self.controls.simulate_key_press('right', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 右下に移動していることを確認
        self.assertGreater(self.player.x, self.initial_x)
        self.assertGreater(self.player.y, self.initial_y)
        
        # 斜め移動の場合、速度が正規化されていることを確認
        dx = self.player.x - self.initial_x
        dy = self.player.y - self.initial_y
        
        # 方向ベクトルの正規化を確認
        ratio = dx / dy if dy != 0 else float('inf')
        self.assertAlmostEqual(ratio, 1.0, delta=0.2)
    
    def test_movement_8way_down_left(self):
        """8方向移動: 左下"""
        self.controls.simulate_key_press('down', True)
        self.controls.simulate_key_press('left', True)
        keys_dict = self.controls.create_keys_dict()
        
        # プレイヤーの更新（複数フレーム）
        for _ in range(10):
            self.player.move(keys_dict)
        
        # 左下に移動していることを確認
        self.assertLess(self.player.x, self.initial_x)
        self.assertGreater(self.player.y, self.initial_y)
        
        # 斜め移動の場合、速度が正規化されていることを確認
        dx = self.initial_x - self.player.x
        dy = self.player.y - self.initial_y
        
        # 方向ベクトルの正規化を確認
        ratio = dx / dy if dy != 0 else float('inf')
        self.assertAlmostEqual(ratio, 1.0, delta=0.2)
    
    # ダッシュテスト
    
    def test_dash_basic(self):
        """基本的なダッシュ機能"""
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
        
        # ダッシュ中は通常より速いことを確認
        normal_player = Player()
        normal_player.x = self.initial_x
        normal_player.y = self.initial_y
        
        # 通常の右移動
        normal_controls = Controls()
        normal_controls.set_simulation_mode(True)
        normal_controls.simulate_key_press('right', True)
        normal_keys_dict = normal_controls.create_keys_dict()
        
        # 両方のプレイヤーを更新
        self.player.move(keys_dict)
        normal_player.move(normal_keys_dict)
        
        # ダッシュ中の方が速いことを確認
        self.assertGreater(self.player.speed_x, normal_player.speed_x)
    
    def test_dash_heat_limit(self):
        """ダッシュのヒート制限"""
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
        """ダッシュのクールダウン"""
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
        
        # ダッシュ持続時間分更新（ダッシュ終了まで）
        for _ in range(self.player.dash_duration):
            self.player.move(keys_dict)
        
        # ダッシュが終了していることを確認
        self.assertFalse(self.player.is_dashing)
        
        # クールダウンが設定されていることを確認
        self.assertGreater(self.player.dash_cooldown, 0)
        
        # クールダウン中は再度ダッシュできないことを確認
        self.player.move(keys_dict)
        self.assertFalse(self.player.is_dashing)
    
    def test_dash_curve_movement(self):
        """ダッシュ中のカーブ移動
        
        仕様: ダッシュ中に別の方向を入力するとカーブする
        """
        # まず右にダッシュする
        self.controls.simulate_key_press('right', True)
        self.controls.simulate_key_press('dash', True)
        keys_dict = self.controls.create_keys_dict()
        
        # ヒートゲージを0に設定
        self.player.heat = 0
        
        # プレイヤーの更新（ダッシュ開始）
        self.player.move(keys_dict)
        
        # ダッシュが開始されていることを確認
        self.assertTrue(self.player.is_dashing)
        
        # いくつかのフレームでダッシュを続ける
        for _ in range(5):
            self.player.move(keys_dict)
        
        # 現在位置を記録
        x_after_horizontal_dash = self.player.x
        y_after_horizontal_dash = self.player.y
        
        # ダッシュ中に方向を変更（右下に）
        self.controls.simulate_key_press('down', True)
        keys_dict = self.controls.create_keys_dict()
        
        # 方向変更後に複数フレーム実行
        for _ in range(10):
            self.player.move(keys_dict)
        
        # カーブしているかを確認
        # 仕様では、ダッシュ中に別の方向を入力するとカーブすることになっているので、
        # プレイヤーが右下方向に移動しているはず
        
        # 右方向への移動が継続していることを確認
        self.assertGreater(self.player.x, x_after_horizontal_dash)
        
        # 下方向にも移動していることを確認 (カーブ機能の検証)
        # この行は仕様が実装されていれば成功するはず
        self.assertGreater(self.player.y, y_after_horizontal_dash)
        
        # ダッシュ中であることを確認
        self.assertTrue(self.player.is_dashing)

# ここに実装すべき修正案も提示する
class SuggestedPlayerImplementation:
    """
    ダッシュ中のカーブ移動を実現するための修正案
    
    Playerクラスの一部実装例として、ダッシュ中に方向を変更できるようにします。
    """
    
    def move_with_curve_dash(self, keys):
        """
        カーブダッシュを実装した移動メソッド
        
        このメソッドは、Playerクラスのmoveメソッドを修正した例です。
        ダッシュ中でも入力に応じて方向を変更できるようにしています。
        """
        # 入力バッファの更新
        self.input_buffer['left'] = keys[pygame.K_LEFT]
        self.input_buffer['right'] = keys[pygame.K_RIGHT]
        self.input_buffer['up'] = keys[pygame.K_UP]
        self.input_buffer['down'] = keys[pygame.K_DOWN]
        self.input_buffer['shift'] = keys[pygame.K_LSHIFT]
        
        # 移動方向の決定
        dx = 0
        dy = 0
        
        if self.input_buffer['left']:
            dx -= 1
            self.facing_right = False
        if self.input_buffer['right']:
            dx += 1
            self.facing_right = True
        if self.input_buffer['up']:
            dy -= 1
        if self.input_buffer['down']:
            dy += 1
            
        # 斜め移動の場合は速度を正規化
        if dx != 0 and dy != 0:
            normalize_factor = 0.7071  # √2分の1の近似値
            dx *= normalize_factor
            dy *= normalize_factor
        
        # ダッシュ処理
        dash_requested = self.input_buffer['shift']
        
        # 即時発動: シフトキーが押され、ダッシュ中でなく、クールダウンもない場合
        if dash_requested and not self.is_dashing and self.dash_cooldown <= 0:
            # ヒートが一定以下ならダッシュ発動
            if self.heat < self.max_heat * 0.8:  # ヒート制限
                self.is_dashing = True
                self.dash_duration = 120  # ダッシュ持続時間をリセット
                
                # ダッシュ方向を記録
                if dx != 0 or dy != 0:
                    self.last_direction = (dx, dy)
        
        # ダッシュ中の処理
        if self.is_dashing:
            # ヒートゲージの上昇
            self.heat += 0.5
            
            # ヒートが上限に達したらダッシュ終了
            if self.heat >= self.max_heat:
                self.is_dashing = False
                self.dash_cooldown = self.dash_cooldown_time
            
            # ダッシュ持続時間の消費
            self.dash_duration -= 1
            if self.dash_duration <= 0:
                self.is_dashing = False
                self.dash_cooldown = self.dash_cooldown_time
            
            # ダッシュ中もカーブできるように、新しい入力があれば方向を更新
            if dx != 0 or dy != 0:
                self.last_direction = (dx, dy)
            
            # ダッシュ方向を使用
            if self.last_direction:
                dx, dy = self.last_direction
                
            # ダッシュ中は速度上昇
            current_speed = self.dash_speed
        else:
            # 通常移動
            current_speed = self.max_speed
            
            # ヒートの冷却
            if self.heat > 0:
                self.heat -= 0.2
                if self.heat < 0:
                    self.heat = 0
        
        # ダッシュクールダウンの更新
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        
        # 目標速度の設定と現在の速度の更新
        # (以下略、元の実装と同じ)
        
        # この修正のポイント:
        # 1. ダッシュ中も新しい入力があれば last_direction を更新
        # 2. これにより、ダッシュ中に方向キーを変えるとカーブする


if __name__ == "__main__":
    # テストを実行
    unittest.main() 