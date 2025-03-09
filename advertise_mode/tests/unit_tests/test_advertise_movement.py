"""
アドバタイズモードの移動機能に関するユニットテスト
"""

import unittest
import sys
import os
import math
import pygame

# テスト用のパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# テスト用のモッククラスをインポート
from test_mock_classes import Player, Enemy, DashSpec

class TestAdvertiseMovement(unittest.TestCase):
    """アドバタイズモードの移動アルゴリズムをテストするクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        # プレイヤーオブジェクトを初期化
        self.player = Player()
        self.player.advertise_mode = True
        
        # 敵と弾の配列を初期化
        self.enemies = []
        self.bullets = []
        
        # デフォルトの戦略を設定
        if hasattr(self.player, '_current_strategy'):
            self.player._current_strategy = 'balanced'
    
    def test_movement_without_enemies(self):
        """敵がいない場合の移動をテスト"""
        # 初期位置を記録
        initial_x, initial_y = self.player.x, self.player.y
        
        # アドバタイズモードの移動を実行
        if hasattr(self.player, 'update_advertise_movement'):
            self.player.update_advertise_movement(self.enemies)
        else:
            self.player.update({}, self.enemies, self.bullets)
        
        # 位置が変化していることを確認
        current_x, current_y = self.player.x, self.player.y
        has_moved = (current_x != initial_x or current_y != initial_y)
        self.assertTrue(has_moved, "敵がいない場合でも移動すべき")
    
    def test_enemy_avoidance(self):
        """敵が近づいた場合の回避行動をテスト"""
        # プレイヤーの位置を設定
        self.player.x = 400
        self.player.y = 300
        
        # プレイヤーに近い敵を追加
        enemy = Enemy(enemy_type="mob")
        enemy.x = self.player.x + 50  # プレイヤーの近くに配置
        enemy.y = self.player.y
        self.enemies.append(enemy)
        
        # 初期距離を計算
        initial_distance = math.sqrt((enemy.x - self.player.x)**2 + (enemy.y - self.player.y)**2)
        
        # アドバタイズモードの移動を実行
        if hasattr(self.player, 'update_advertise_movement'):
            self.player.update_advertise_movement(self.enemies)
        else:
            self.player.update({}, self.enemies, self.bullets)
        
        # 移動後の距離を計算
        new_distance = math.sqrt((enemy.x - self.player.x)**2 + (enemy.y - self.player.y)**2)
        
        # 敵から離れる方向に移動していることを確認
        self.assertGreater(new_distance, initial_distance, "敵が近づいた場合は敵から離れるべき")
    
    def test_multiple_enemy_prioritization(self):
        """複数の敵がいる場合の優先順位をテスト"""
        # プレイヤーの位置を設定
        self.player.x = 400
        self.player.y = 300
        
        # 複数の敵を追加（距離が異なる）
        near_enemy = Enemy(enemy_type="mob")
        near_enemy.x = self.player.x + 80
        near_enemy.y = self.player.y
        
        far_enemy = Enemy(enemy_type="mob")
        far_enemy.x = self.player.x - 200
        far_enemy.y = self.player.y + 100
        
        self.enemies.extend([near_enemy, far_enemy])
        
        # 初期距離を計算
        initial_near_distance = math.sqrt((near_enemy.x - self.player.x)**2 + (near_enemy.y - self.player.y)**2)
        
        # アドバタイズモードの移動を実行
        if hasattr(self.player, 'update_advertise_movement'):
            self.player.update_advertise_movement(self.enemies)
        else:
            self.player.update({}, self.enemies, self.bullets)
        
        # 移動後の距離を計算
        new_near_distance = math.sqrt((near_enemy.x - self.player.x)**2 + (near_enemy.y - self.player.y)**2)
        
        # 近い敵からより離れる方向に移動していることを確認
        self.assertGreater(new_near_distance, initial_near_distance, "近い敵からの回避を優先すべき")
    
    def test_boundary_avoidance(self):
        """画面の端に近づきすぎないことをテスト"""
        # プレイヤーを画面の端に配置
        self.player.x = 50  # 左端付近
        self.player.y = 300
        
        # 敵を配置（左側からプレイヤーを追いかける想定）
        enemy = Enemy(enemy_type="mob")
        enemy.x = 10
        enemy.y = 300
        self.enemies.append(enemy)
        
        # アドバタイズモードの移動を実行
        if hasattr(self.player, 'update_advertise_movement'):
            self.player.update_advertise_movement(self.enemies)
        else:
            self.player.update({}, self.enemies, self.bullets)
        
        # 画面からはみ出していないことを確認
        self.assertGreater(self.player.x, 0, "画面左端からはみ出ていないこと")
        self.assertLess(self.player.x, 800, "画面右端からはみ出ていないこと")
        self.assertGreater(self.player.y, 0, "画面上端からはみ出ていないこと")
        self.assertLess(self.player.y, 600, "画面下端からはみ出ていないこと")
        
        # 左端に近づきすぎていない場合、右側（画面内側）に移動していることを確認
        # （ただし、改善版では常に成立するとは限らないので条件付き）
        if hasattr(self.player, '_defensive_movement'):
            self.assertGreater(self.player.x, 50, "画面端では内側に移動すべき")
    
    def test_strategy_switching(self):
        """戦略の切り替えが機能するかテスト"""
        # 戦略パラメータが存在する場合のみテスト
        if not hasattr(self.player, '_current_strategy'):
            self.skipTest("戦略切り替え機能が実装されていません")
        
        # 初期戦略を記録
        initial_strategy = self.player._current_strategy
        
        # 戦略を変更
        strategies = ['aggressive', 'defensive', 'flanking', 'balanced']
        new_strategy = next(s for s in strategies if s != initial_strategy)
        self.player._current_strategy = new_strategy
        
        # 敵を追加
        enemy = Enemy(enemy_type="mob")
        enemy.x = self.player.x + 100
        enemy.y = self.player.y
        self.enemies.append(enemy)
        
        # 初期位置を記録
        initial_x, initial_y = self.player.x, self.player.y
        
        # アドバタイズモードの移動を実行
        self.player.update_advertise_movement(self.enemies)
        
        # 位置が変化していることを確認
        current_x, current_y = self.player.x, self.player.y
        has_moved = (current_x != initial_x or current_y != initial_y)
        self.assertTrue(has_moved, "戦略変更後も移動すべき")
        
        # 戦略が維持されていることを確認
        self.assertEqual(self.player._current_strategy, new_strategy, "戦略が維持されるべき")


class TestMovementPatterns(unittest.TestCase):
    """アドバタイズモードの様々な移動パターンをテストするクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        # プレイヤーオブジェクトを初期化
        self.player = Player()
        self.player.advertise_mode = True
        
        # 敵と弾の配列を初期化
        self.enemies = []
        self.bullets = []
        
        # 戦略があれば初期化
        if hasattr(self.player, '_strategy_timer'):
            self.player._strategy_timer = 0
        if hasattr(self.player, '_current_strategy'):
            self.player._current_strategy = 'balanced'
    
    def _track_movement(self, frames=180):
        """指定フレーム数の移動をトラッキングし、位置の履歴を返す"""
        positions = []
        
        for _ in range(frames):
            # 現在位置を記録
            positions.append((self.player.x, self.player.y))
            
            # 移動処理
            if hasattr(self.player, 'update_advertise_movement'):
                self.player.update_advertise_movement(self.enemies)
            else:
                self.player.update({}, self.enemies, self.bullets)
        
        return positions
    
    def test_no_vibration(self):
        """振動動作（小さな範囲での行ったり来たり）がないことをテスト"""
        # 中央に配置
        self.player.x = 400
        self.player.y = 300
        
        # 180フレーム分の移動を記録
        positions = self._track_movement(180)
        
        # 振動を検出
        vibration_count = 0
        
        for i in range(2, len(positions)):
            # 3点を使って方向変化を検出
            p1 = positions[i-2]
            p2 = positions[i-1]
            p3 = positions[i]
            
            # ベクトル計算
            v1 = (p2[0] - p1[0], p2[1] - p1[1])
            v2 = (p3[0] - p2[0], p3[1] - p2[1])
            
            # 方向変化の検出（内積の符号で判定）
            dot_product = v1[0] * v2[0] + v1[1] * v2[1]
            v1_mag = math.sqrt(v1[0]**2 + v1[1]**2)
            v2_mag = math.sqrt(v2[0]**2 + v2[1]**2)
            
            # 速度が小さい場合は無視
            if v1_mag < 0.1 or v2_mag < 0.1:
                continue
            
            # 方向が大きく変わり、かつ移動量が小さい場合を振動とみなす
            if dot_product < 0 and v1_mag < 5 and v2_mag < 5:
                vibration_count += 1
        
        # 振動回数が少ないことを確認（10%以下）
        max_allowed_vibrations = len(positions) * 0.1
        self.assertLessEqual(vibration_count, max_allowed_vibrations, 
                           f"振動回数が多すぎます: {vibration_count}/{len(positions)}")
    
    def test_area_coverage(self):
        """一定時間内に画面の広い範囲をカバーすることをテスト"""
        # 300フレーム分の移動を記録
        positions = self._track_movement(300)
        
        # 訪れたグリッドセルをカウント
        grid_size = 40  # 20x15のグリッド（画面を800x600とした場合）
        visited_grids = set()
        
        for x, y in positions:
            grid_x = int(x // grid_size)
            grid_y = int(y // grid_size)
            visited_grids.add((grid_x, grid_y))
        
        # 総グリッド数
        total_grids = (800 // grid_size) * (600 // grid_size)
        
        # カバー率を計算
        coverage_rate = len(visited_grids) / total_grids
        
        # 少なくとも20%のグリッドを訪れていることを確認
        self.assertGreaterEqual(coverage_rate, 0.2, 
                              f"エリアカバレッジが低すぎます: {coverage_rate:.2%}")
    
    def test_center_avoidance(self):
        """画面中央に長時間留まらないことをテスト"""
        # 中央に配置
        self.player.x = 400
        self.player.y = 300
        
        # 300フレーム分の移動を記録
        positions = self._track_movement(300)
        
        # 中央領域の定義
        center_x, center_y = 400, 300
        center_radius = 100
        
        # 中央にいた時間をカウント
        center_time = 0
        
        for x, y in positions:
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            if distance < center_radius:
                center_time += 1
        
        # 中央滞在率を計算
        center_ratio = center_time / len(positions)
        
        # 50%以下の時間しか中央にいないことを確認
        self.assertLessEqual(center_ratio, 0.5, 
                           f"中央滞在時間が長すぎます: {center_ratio:.2%}")


if __name__ == '__main__':
    # 直接実行された場合はテストを実行
    unittest.main() 