"""
[SPEC-DASH-001] プレイヤーダッシュ機能の仕様とテスト

このファイルはプレイヤーのダッシュ機能に関する仕様と、その仕様を検証するテストを含みます。
仕様の変更は必ずテストの変更を伴い、その逆も同様です。
"""

import unittest
import pygame
import math
from src.game.core.main import Player, SCREEN_WIDTH, SCREEN_HEIGHT

class DashSpec:
    """ダッシュ機能の仕様定義
    
    各仕様項目にはユニークなIDが付与され、テストメソッドと対応しています。
    仕様の変更は、必ずテストの変更を伴う必要があります。
    """
    
    # [SPEC-DASH-101] 基本パラメータ
    NORMAL_SPEED = 5.0
    DASH_SPEED = 8.0  # 通常速度の1.6倍
    ACCELERATION = 0.5
    FRICTION = 0.1
    
    # [SPEC-DASH-102] ヒートゲージパラメータ
    MAX_HEAT = 100
    INITIAL_HEAT = 0
    HEAT_INCREASE_RATE = 1.0  # ダッシュ中の上昇率/フレーム
    HEAT_RECOVERY_RATE = 0.2  # 通常時の回復率/フレーム
    DASH_DISABLE_THRESHOLD = 50  # この値より上ではダッシュ不可
    
    # [SPEC-DASH-103] カーブ移動パラメータ
    MAX_TURN_RATE = 10  # 最大旋回角度/フレーム
    INPUT_WEIGHT = 0.8  # 入力方向の重み
    MOMENTUM_WEIGHT = 0.2  # 現在の移動方向の重み
    NORMAL_GRIP = 1.0
    DASH_GRIP = 0.8

class TestPlayerDash(unittest.TestCase):
    """ダッシュ機能の仕様を検証するテストスイート
    
    各テストメソッドは、対応する仕様のIDをコメントで明記しています。
    テストの追加・変更時は、必ず仕様との対応を確認してください。
    """
    
    def setUp(self):
        pygame.init()
        self.player = Player()
        # キー入力シミュレート用の辞書
        self.mock_keys = {
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LSHIFT: False
        }
    
    def test_dash_basic_parameters(self):
        """[SPEC-DASH-101] 基本パラメータのテスト"""
        self.assertEqual(self.player.max_speed, DashSpec.NORMAL_SPEED)
        self.assertEqual(self.player.dash_speed, DashSpec.DASH_SPEED)
        self.assertEqual(self.player.acceleration, DashSpec.ACCELERATION)
        self.assertEqual(self.player.friction, DashSpec.FRICTION)
    
    def test_heat_parameters(self):
        """[SPEC-DASH-102] ヒートゲージパラメータのテスト"""
        self.assertEqual(self.player.max_heat, DashSpec.MAX_HEAT)
        self.assertEqual(self.player.heat, DashSpec.INITIAL_HEAT)
    
    def test_immediate_dash_activation(self):
        """[SPEC-DASH-201] ダッシュの即時発動テスト
        
        シフトキーを押した瞬間にダッシュが発動することを確認。
        遅延は許容されない。
        """
        self.mock_keys[pygame.K_LSHIFT] = True
        initial_x = self.player.x
        
        # 1フレーム目で即座にダッシュ速度になっていることを確認
        self.player.move(self.mock_keys)
        self.assertTrue(self.player.is_dashing)
        self.assertEqual(self.player.speed_x, DashSpec.DASH_SPEED)
    
    def test_continuous_dash(self):
        """[SPEC-DASH-202] ダッシュの継続テスト
        
        シフトキーを押している間はヒートゲージが上限に達するまでダッシュが継続。
        """
        self.mock_keys[pygame.K_LSHIFT] = True
        self.mock_keys[pygame.K_RIGHT] = True
        
        # ヒートゲージが100%になるまでダッシュが継続することを確認
        while self.player.heat < DashSpec.MAX_HEAT:
            was_dashing = self.player.is_dashing
            self.player.move(self.mock_keys)
            if self.player.heat < DashSpec.MAX_HEAT:
                self.assertTrue(was_dashing)
            else:
                self.assertFalse(self.player.is_dashing)
    
    def test_heat_based_dash_restriction(self):
        """[SPEC-DASH-203] ヒートゲージによるダッシュ制限テスト
        
        ヒートゲージが50%以下に下がるまでダッシュ不可。
        """
        # ヒートゲージを90%に設定
        self.player.heat = 90
        self.mock_keys[pygame.K_LSHIFT] = True
        
        # ダッシュ不可を確認
        self.player.move(self.mock_keys)
        self.assertFalse(self.player.is_dashing)
        
        # ヒートゲージを45%に設定
        self.player.heat = 45
        
        # ダッシュ可能を確認
        self.player.move(self.mock_keys)
        self.assertTrue(self.player.is_dashing)
    
    def test_curve_movement(self):
        """[SPEC-DASH-301] カーブ移動テスト
        
        ダッシュ中の方向キー入力による進行方向の変更を確認。
        """
        # 右方向へのダッシュ開始
        self.mock_keys[pygame.K_RIGHT] = True
        self.mock_keys[pygame.K_LSHIFT] = True
        self.player.move(self.mock_keys)
        
        # 上方向への入力を追加
        self.mock_keys[pygame.K_UP] = True
        initial_angle = self.player.movement_angle
        
        # 1フレームでの旋回角度を確認
        self.player.move(self.mock_keys)
        angle_change = abs(self.player.movement_angle - initial_angle)
        self.assertLessEqual(angle_change, DashSpec.MAX_TURN_RATE)
        
        # 移動方向が入力方向と現在の移動方向の合成になっていることを確認
        expected_angle = initial_angle * DashSpec.MOMENTUM_WEIGHT + 45 * DashSpec.INPUT_WEIGHT
        self.assertAlmostEqual(self.player.movement_angle, expected_angle, delta=1.0)
    
    def test_grip_during_dash(self):
        """[SPEC-DASH-302] ダッシュ中のグリップテスト
        
        ダッシュ中は通常時よりもグリップが低下することを確認。
        """
        self.assertEqual(self.player.grip_level, DashSpec.NORMAL_GRIP)
        
        # ダッシュ開始
        self.mock_keys[pygame.K_LSHIFT] = True
        self.player.move(self.mock_keys)
        
        self.assertEqual(self.player.grip_level, DashSpec.DASH_GRIP)

if __name__ == '__main__':
    unittest.main() 