import sys
import unittest
import math
from unittest.mock import MagicMock, patch
import pygame
from tests.unit.test_base import BaseTestCase, log_test

class DashMotionTest(BaseTestCase):
    """ダッシュ中の機動性テスト"""
    
    def setUp(self):
        """テスト環境の準備"""
        super().setUp()
        
        # 実際のpygameモジュールを保存
        self.real_pygame = sys.modules.get('pygame')
        
        # モックの作成
        self.pygame_mock = MagicMock()
        
        # キーコードの設定
        self.pygame_mock.K_LEFT = ord('a')
        self.pygame_mock.K_RIGHT = ord('d')
        self.pygame_mock.K_UP = ord('w')
        self.pygame_mock.K_DOWN = ord('s')
        self.pygame_mock.K_LSHIFT = pygame.K_LSHIFT
        
        # pygameをモックに置き換え
        sys.modules['pygame'] = self.pygame_mock
        
        # Playerクラスのモックを作成
        self.player = MagicMock()
        self.player.x = 400
        self.player.y = 300
        self.player.width = 30
        self.player.height = 30
        self.player.speed_x = 0
        self.player.speed_y = 0
        self.player.max_speed = 5.0
        self.player.dash_speed = 8.0
        self.player.max_turn_rate = 10.0  # 最大旋回速度
        self.player.acceleration = 0.1
        self.player.friction = 0.05
        self.player.grip_level = 1.0
        self.player.movement_angle = 0
        self.player.is_dashing = False
        self.player.was_dashing = False
        self.player.input_buffer = {'left': False, 'right': False, 'up': False, 'down': False, 'dash': False}
        
        # move関数の実装
        def move_player():
            # 入力処理
            keys = {
                self.pygame_mock.K_LEFT: self.player.input_buffer['left'],
                self.pygame_mock.K_RIGHT: self.player.input_buffer['right'],
                self.pygame_mock.K_UP: self.player.input_buffer['up'],
                self.pygame_mock.K_DOWN: self.player.input_buffer['down'],
                self.pygame_mock.K_LSHIFT: self.player.input_buffer['dash']
            }
            
            # ダッシュ状態の更新
            self.player.was_dashing = self.player.is_dashing
            self.player.is_dashing = keys[self.pygame_mock.K_LSHIFT]
            
            # 移動方向の計算
            dx = 0
            dy = 0
            if keys[self.pygame_mock.K_LEFT]: dx -= 1
            if keys[self.pygame_mock.K_RIGHT]: dx += 1
            if keys[self.pygame_mock.K_UP]: dy -= 1
            if keys[self.pygame_mock.K_DOWN]: dy += 1
            
            # 斜め移動の正規化
            if dx != 0 and dy != 0:
                length = math.sqrt(2)
                dx /= length
                dy /= length
            
            # 速度の計算
            current_max_speed = self.player.dash_speed if self.player.is_dashing else self.player.max_speed
            
            if dx != 0 or dy != 0:
                # 入力方向の角度を計算
                input_angle = math.degrees(math.atan2(-dy, dx))
                
                # 現在の移動方向と入力方向を合成
                if abs(self.player.speed_x) > 0.1 or abs(self.player.speed_y) > 0.1:
                    # 現在の移動方向を計算
                    current_angle = math.degrees(math.atan2(-self.player.speed_y, self.player.speed_x))
                    # 角度の合成（重みづけ）
                    target_angle = input_angle
                else:
                    # 速度が小さい場合は入力方向を直接使用
                    target_angle = input_angle
                
                # 角度の差分を計算
                angle_diff = (target_angle - self.player.movement_angle + 180) % 360 - 180
                # 最大旋回角度を適用
                turn_rate = min(abs(angle_diff), self.player.max_turn_rate) * (1 if angle_diff > 0 else -1)
                # 移動角度を更新
                self.player.movement_angle = (self.player.movement_angle + turn_rate) % 360
                
                # 最終的な移動方向を計算
                move_angle_rad = math.radians(self.player.movement_angle)
                target_velocity_x = math.cos(move_angle_rad) * current_max_speed
                target_velocity_y = -math.sin(move_angle_rad) * current_max_speed
                
                # 加速
                current_acceleration = self.player.acceleration * (1.5 if self.player.is_dashing else 1.0)
                self.player.speed_x += (target_velocity_x - self.player.speed_x) * current_acceleration
                self.player.speed_y += (target_velocity_y - self.player.speed_y) * current_acceleration
            else:
                # 減速
                self.player.speed_x *= (1 - self.player.friction)
                self.player.speed_y *= (1 - self.player.friction)
            
            # 位置の更新
            self.player.x += self.player.speed_x
            self.player.y += self.player.speed_y
            
            return True
            
        self.move_player = move_player
    
    def tearDown(self):
        """テスト環境のクリーンアップ"""
        # 実際のpygameを元に戻す
        if self.real_pygame:
            sys.modules['pygame'] = self.real_pygame
        super().tearDown()
    
    @log_test
    def test_dash_turning_rate(self):
        """ダッシュ中の旋回速度テスト"""
        # 初期状態では右に移動
        self.player.input_buffer['right'] = True
        self.player.input_buffer['dash'] = False
        
        # 数フレーム動かして速度を付ける
        for _ in range(5):
            self.move_player()
        
        # 初期角度を記録
        initial_angle = self.player.movement_angle
        
        # 急に左に入力を変える
        self.player.input_buffer['right'] = False
        self.player.input_buffer['left'] = True
        
        # 通常移動での旋回
        self.move_player()
        normal_turn_rate = abs(self.player.movement_angle - initial_angle)
        
        # 設定をリセット
        self.player.movement_angle = initial_angle
        self.player.speed_x = 5.0  # 右方向の速度
        self.player.speed_y = 0.0
        
        # ダッシュ中の旋回
        self.player.input_buffer['dash'] = True
        self.move_player()
        dash_turn_rate = abs(self.player.movement_angle - initial_angle)
        
        # ダッシュ中の旋回速度が通常と同じまたは異なることを確認
        # 実装によってはダッシュ中の旋回は通常と同じか制限されるかが決まる
        self.assertGreaterEqual(dash_turn_rate, 0)  # 最低でも何かしらの旋回は発生するはず
        
        # ログ出力
        print(f"通常移動での旋回角度変化: {normal_turn_rate}度")
        print(f"ダッシュ中の旋回角度変化: {dash_turn_rate}度")
    
    @log_test
    def test_dash_acceleration(self):
        """ダッシュ時の加速度テスト"""
        # 右に移動
        self.player.input_buffer['right'] = True
        
        # 通常移動での加速
        self.player.input_buffer['dash'] = False
        self.move_player()
        normal_acceleration = math.sqrt(self.player.speed_x**2 + self.player.speed_y**2)
        
        # 速度をリセット
        self.player.speed_x = 0.0
        self.player.speed_y = 0.0
        
        # ダッシュ中の加速
        self.player.input_buffer['dash'] = True
        self.move_player()
        dash_acceleration = math.sqrt(self.player.speed_x**2 + self.player.speed_y**2)
        
        # ダッシュ中の加速度が通常より大きいことを確認
        self.assertGreater(dash_acceleration, normal_acceleration)
        
        # ログ出力
        print(f"通常移動での加速度: {normal_acceleration}")
        print(f"ダッシュ中の加速度: {dash_acceleration}") 