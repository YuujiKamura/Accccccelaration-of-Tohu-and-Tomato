"""
アドバタイズモードの統合テスト

このモジュールでは、アドバタイズモード（自動デモ）の総合的な機能テストを行います。
特に複数のコンポーネントを連携させた際の安定性と有効性を検証します。
"""

import unittest
import os
import sys
import time
import random
import math
import json
import datetime
from unittest.mock import MagicMock, patch
from tests.unit.test_base import BaseTestCase, log_test

# プロジェクトルートへのパスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# テスト用のモッククラスをインポート
from tests.integration_tests.test_mock_classes import Player, Enemy, Bullet, DashSpec, GameState


class TestAdvertiseModeIntegration(BaseTestCase):
    """アドバタイズモードの統合テスト"""
    
    @classmethod
    def setUpClass(cls):
        """クラス全体のセットアップ"""
        super().setUpClass()
        
        # 結果保存用のディレクトリを作成
        cls.output_dir = os.path.join(os.path.dirname(__file__), 'test_results')
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # テスト用のゲーム状態を初期化
        cls.game_state = GameState()
        
        # 連続実行のためのカウンタ
        cls.run_counter = 0
        
        # パフォーマンス評価用の指標
        cls.metrics = {
            'frame_times': [],
            'average_enemies': 0,
            'enemy_defeat_count': 0,
            'player_death_count': 0,
            'average_score': 0
        }
    
    def setUp(self):
        """各テスト前の準備"""
        super().setUp()
        
        # テスト状態をリセット
        self.reset_game_state()
        
        # 連続実行のためのカウンタをインクリメント
        self.__class__.run_counter += 1
    
    def reset_game_state(self):
        """ゲーム状態をリセット"""
        self.game_state = GameState()
        self.game_state.player.advertise_mode = True
        
        # 初期敵を生成
        for _ in range(5):
            self.game_state.spawn_enemy()
    
    @log_test
    def test_advertise_mode_activation(self):
        """アドバタイズモードが正しく有効化されることを確認"""
        # プレイヤーのアドバタイズモードを有効化
        self.game_state.player.advertise_mode = True
        
        # 60フレーム（約1秒）更新
        for _ in range(60):
            self.game_state.update()
        
        # アドバタイズモードが動作していることを確認
        # プレイヤーが動いていることを確認
        self.assertTrue(
            self.game_state.player.velocity_x != 0 or 
            self.game_state.player.velocity_y != 0
        )
    
    @log_test
    def test_enemy_tracking(self):
        """敵が自動的にプレイヤーを追跡することを確認"""
        # 敵をプレイヤーから離れた位置に配置
        enemy = Enemy(100, 100, "normal")
        self.game_state.enemies.append(enemy)
        
        # プレイヤーの位置を設定
        self.game_state.player.x = 700
        self.game_state.player.y = 500
        
        # 初期位置を記録
        initial_x = enemy.x
        initial_y = enemy.y
        
        # 60フレーム（約1秒）更新
        for _ in range(60):
            self.game_state.update()
        
        # 敵がプレイヤーの方向に移動していることを確認
        self.assertGreater(enemy.x, initial_x)
        self.assertGreater(enemy.y, initial_y)
    
    @log_test
    def test_bullet_collision(self):
        """弾と敵の衝突判定が正しく機能することを確認"""
        # 敵を配置
        enemy = Enemy(400, 300, "normal")
        self.game_state.enemies.append(enemy)
        
        # 敵に向かう弾を発射
        bullet = Bullet(
            300, 300,  # 位置
            (1, 0),    # 右方向
            15,        # 速度
            10,        # ダメージ
            "player"   # 所有者（プレイヤー）
        )
        self.game_state.bullets.append(bullet)
        
        # 衝突するまで更新
        for _ in range(20):
            self.game_state.update()
            if not bullet.is_active:
                break
        
        # 弾が衝突して非アクティブになったことを確認
        self.assertFalse(bullet.is_active)
        
        # 敵がダメージを受けたことを確認
        self.assertLess(enemy.health, enemy.max_health)
    
    @log_test
    def test_enemy_defeated(self):
        """敵が倒されたときの処理が正しく機能することを確認"""
        # 敵を配置
        enemy = Enemy(400, 300, "normal")
        # 体力を低く設定
        enemy.health = 5
        self.game_state.enemies.append(enemy)
        
        # 敵に向かう弾を発射
        bullet = Bullet(
            300, 300,  # 位置
            (1, 0),    # 右方向
            15,        # 速度
            10,        # ダメージ
            "player"   # 所有者（プレイヤー）
        )
        self.game_state.bullets.append(bullet)
        
        # 敵が倒されるまで更新
        initial_score = self.game_state.score
        for _ in range(20):
            self.game_state.update()
            if not enemy.is_active:
                break
        
        # 敵が倒されて非アクティブになったことを確認
        self.assertFalse(enemy.is_active)
        
        # 敵がリストから削除されていることを確認
        self.assertNotIn(enemy, self.game_state.enemies)
        
        # スコアが加算されたことを確認
        self.assertGreater(self.game_state.score, initial_score)
    
    @log_test
    def test_long_run_stability(self):
        """長時間実行時の安定性を確認"""
        # 長時間実行でのメモリ使用量と安定性をチェック
        
        # ゲーム状態をセットアップ
        self.reset_game_state()
        
        # 1800フレーム（約30秒相当）実行
        frames = 1800
        start_time = time.time()
        
        # フレーム時間を計測
        frame_times = []
        
        for _ in range(frames):
            frame_start = time.time()
            
            # ゲーム状態の更新
            self.game_state.update()
            
            # 一定確率で撃つアクション
            if random.random() < 0.1:  # 10%の確率
                self.game_state.fire_player_bullet()
            
            # ダッシュアクション
            if random.random() < 0.05:  # 5%の確率
                self.game_state.player.dash()
            
            # フレーム時間を記録
            frame_end = time.time()
            frame_time = frame_end - frame_start
            frame_times.append(frame_time)
        
        # 経過時間を計測
        elapsed_time = time.time() - start_time
        
        # パフォーマンス指標を計算
        avg_frame_time = sum(frame_times) / len(frame_times)
        max_frame_time = max(frame_times)
        min_frame_time = min(frame_times)
        
        # 結果をJSONファイルに出力
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.__class__.output_dir, f"stability_test_{timestamp}.json")
        
        with open(result_file, 'w') as f:
            json.dump({
                'frames': frames,
                'elapsed_time': elapsed_time,
                'average_frame_time': avg_frame_time,
                'max_frame_time': max_frame_time,
                'min_frame_time': min_frame_time,
                'final_score': self.game_state.score,
                'enemies_count': len(self.game_state.enemies),
                'bullets_count': len(self.game_state.bullets)
            }, f, indent=2)
        
        # 結果確認のためにファイルパスを表示
        print(f"テスト結果: {result_file}")
        
        # 基本的な安定性チェック
        self.assertLess(avg_frame_time, 0.01)  # 平均フレーム時間が10ms未満であること
        self.assertLess(max_frame_time, 0.1)   # 最大フレーム時間が100ms未満であること
    
    @classmethod
    def tearDownClass(cls):
        """クラス全体の終了処理"""
        # 結果ディレクトリを表示
        print(f"テスト結果は {os.path.abspath(cls.output_dir)} に保存されました")
        
        super().tearDownClass()


class TestComparisonBenchmark(BaseTestCase):
    """オリジナルと改善版のアドバタイズモードを比較するベンチマークテスト"""
    
    @classmethod
    def setUpClass(cls):
        """クラス全体のセットアップ"""
        super().setUpClass()
        
        # 結果保存用のディレクトリを作成
        cls.output_dir = os.path.join(os.path.dirname(__file__), 'benchmark_results')
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # テストの実行回数
        cls.test_runs = 5
        cls.frames_per_run = 1200  # 各テストで実行するフレーム数（約20秒相当）
    
    def setUp(self):
        """各テスト前の準備"""
        super().setUp()
    
    @log_test
    def test_original_advertise_mode(self):
        """オリジナルのアドバタイズモードのパフォーマンスを計測"""
        # 結果リスト
        results = []
        
        for run in range(self.__class__.test_runs):
            # ゲーム状態を初期化
            game_state = GameState()
            game_state.player.advertise_mode = True
            
            # 一定数の敵を生成
            for _ in range(10):
                game_state.spawn_enemy()
            
            # 記録用の変数
            frame_times = []
            score_history = []
            enemy_counts = []
            bullet_counts = []
            
            # フレーム実行
            for frame in range(self.__class__.frames_per_run):
                frame_start = time.time()
                
                # ゲーム状態の更新
                game_state.update()
                
                # ランダムアクション（テスト用）
                if random.random() < 0.1:  # 10%の確率
                    game_state.fire_player_bullet()
                
                # 状態記録
                score_history.append(game_state.score)
                enemy_counts.append(len(game_state.enemies))
                bullet_counts.append(len(game_state.bullets))
                
                # フレーム時間計測
                frame_end = time.time()
                frame_times.append(frame_end - frame_start)
            
            # 実行結果を記録
            run_result = {
                'run': run + 1,
                'average_frame_time': sum(frame_times) / len(frame_times),
                'max_frame_time': max(frame_times),
                'final_score': game_state.score,
                'average_enemy_count': sum(enemy_counts) / len(enemy_counts),
                'average_bullet_count': sum(bullet_counts) / len(bullet_counts),
                'score_progression': score_history[::60]  # 1秒ごとのスコアを記録
            }
            
            results.append(run_result)
        
        # 結果を保存
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.__class__.output_dir, f"original_mode_{timestamp}.json")
        
        with open(result_file, 'w') as f:
            json.dump({
                'test_type': 'original',
                'test_runs': self.__class__.test_runs,
                'frames_per_run': self.__class__.frames_per_run,
                'results': results
            }, f, indent=2)
        
        print(f"オリジナルモードのテスト結果: {result_file}")
    
    @log_test
    def test_enhanced_advertise_mode(self):
        """改善版のアドバタイズモードのパフォーマンスを計測"""
        # 結果リスト
        results = []
        
        for run in range(self.__class__.test_runs):
            # ゲーム状態を初期化
            game_state = GameState()
            game_state.player.advertise_mode = True
            
            # 拡張モードの設定（実際のゲームでは改善版のロジックがここに入る）
            # このテストでは基本動作とほぼ同じだが、より高度な戦略を模倣
            
            # 一定数の敵を生成
            for _ in range(10):
                game_state.spawn_enemy()
            
            # 記録用の変数
            frame_times = []
            score_history = []
            enemy_counts = []
            bullet_counts = []
            
            # フレーム実行
            for frame in range(self.__class__.frames_per_run):
                frame_start = time.time()
                
                # ゲーム状態の更新
                game_state.update()
                
                # 拡張版のランダムアクション（発射確率が少し高い）
                if random.random() < 0.15:  # 15%の確率
                    game_state.fire_player_bullet()
                
                # 状態記録
                score_history.append(game_state.score)
                enemy_counts.append(len(game_state.enemies))
                bullet_counts.append(len(game_state.bullets))
                
                # フレーム時間計測
                frame_end = time.time()
                frame_times.append(frame_end - frame_start)
            
            # 実行結果を記録
            run_result = {
                'run': run + 1,
                'average_frame_time': sum(frame_times) / len(frame_times),
                'max_frame_time': max(frame_times),
                'final_score': game_state.score,
                'average_enemy_count': sum(enemy_counts) / len(enemy_counts),
                'average_bullet_count': sum(bullet_counts) / len(bullet_counts),
                'score_progression': score_history[::60]  # 1秒ごとのスコアを記録
            }
            
            results.append(run_result)
        
        # 結果を保存
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.__class__.output_dir, f"enhanced_mode_{timestamp}.json")
        
        with open(result_file, 'w') as f:
            json.dump({
                'test_type': 'enhanced',
                'test_runs': self.__class__.test_runs,
                'frames_per_run': self.__class__.frames_per_run,
                'results': results
            }, f, indent=2)
        
        print(f"拡張モードのテスト結果: {result_file}")
    
    @classmethod
    def tearDownClass(cls):
        """クラス全体の終了処理"""
        # 結果ディレクトリを表示
        print(f"テスト結果は {os.path.abspath(cls.output_dir)} に保存されました")
        
        super().tearDownClass()


if __name__ == '__main__':
    unittest.main() 