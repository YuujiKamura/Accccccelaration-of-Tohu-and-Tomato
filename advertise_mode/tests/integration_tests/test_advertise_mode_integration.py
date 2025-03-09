"""
アドバタイズモードの統合テスト

複数のコンポーネントを連携させて、アドバタイズモード全体の動作をテストします。
"""

import unittest
import sys
import os
import time
import math
import pygame
import json
from datetime import datetime

# テスト用のパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 必要なモジュールをインポート
try:
    from advertise_mode_analyzer import AdvertiseModeAnalyzer, AdvertiseModeMonitor
    from advertise_mode_improver import AdvertiseModeImprover
except ImportError:
    print("アドバタイズモード分析/改善モジュールがインポートできません。パスが正しいか確認してください。")
    sys.exit(1)

# テスト用のモッククラスをインポート
from test_mock_classes import Player, Enemy, Bullet, DashSpec


class TestAdvertiseModeIntegration(unittest.TestCase):
    """アドバタイズモードの統合テスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の前処理"""
        # テスト結果保存用のディレクトリを作成
        cls.output_dir = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not os.path.exists(cls.output_dir):
            os.makedirs(cls.output_dir)
        
        # テスト実行時間を記録
        cls.test_start_time = time.time()
    
    def setUp(self):
        """各テスト前の準備"""
        # Pygameの初期化
        pygame.init()
        
        # ゲーム環境の初期化
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.Surface((self.screen_width, self.screen_height))
        
        # モニターとアナライザーの初期化
        self.analyzer = AdvertiseModeAnalyzer(verbose=False)
        
        # プレイヤーと敵の初期化
        self.player = Player()
        self.player.advertise_mode = True
        self.enemies = []
        self.bullets = []
        
        # 分析結果
        self.analysis_results = None
    
    def _run_simulation(self, frames=300, enemy_count=5):
        """指定フレーム数のシミュレーションを実行"""
        # 敵を生成
        self.enemies = []
        for _ in range(enemy_count):
            enemy = Enemy()
            enemy.x = 100 + (self.screen_width - 200) * (0.1 + 0.8 * (len(self.enemies) / max(1, enemy_count - 1)))
            enemy.y = 100 + (self.screen_height - 300) * (0.2 + 0.6 * (len(self.enemies) % 3) / 2)
            self.enemies.append(enemy)
        
        # シミュレーションを実行
        for frame in range(frames):
            # プレイヤー更新
            if hasattr(self.player, 'update_advertise_movement'):
                # 改善版があればそれを使用
                self.player.update_advertise_movement(self.enemies)
                if hasattr(self.player, 'perform_advertise_action'):
                    self.player.perform_advertise_action(self.enemies, self.bullets)
            else:
                # 通常の更新
                self.player.update({}, self.enemies, self.bullets)
            
            # 敵更新
            for enemy in self.enemies:
                enemy.update()
                
                # 画面の端で反射させる
                if enemy.x < 0 or enemy.x > self.screen_width:
                    enemy.direction_x = -enemy.direction_x
                if enemy.y < 0 or enemy.y > self.screen_height:
                    enemy.direction_y = -enemy.direction_y
            
            # 弾更新
            for bullet in self.bullets[:]:
                bullet.update()
                if not bullet.is_active:
                    self.bullets.remove(bullet)
            
            # 分析データを更新
            self.analyzer.update(self.player.x, self.player.y, self.enemies, frame)
        
        # 分析結果を生成
        self.analyzer.analyze_session(frames)
        self.analysis_results = self.analyzer.analysis_results
        
        # 分析結果をファイルに保存
        result_file = os.path.join(self.output_dir, f"analysis_{len(self.enemies)}enemies_{frames}frames.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
            
        return self.analysis_results
    
    def test_original_behavior(self):
        """オリジナルのアドバタイズモード動作をテスト"""
        # プレイヤーのアドバタイズモードを有効化
        self.player.advertise_mode = True
        
        # 300フレームのシミュレーションを実行（5秒相当）
        results = self._run_simulation(frames=300, enemy_count=5)
        
        # 評価基準の読み込み（存在すれば）
        criteria_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                    "evaluation", "criteria.md")
        
        # 結果の検証
        self.assertIsNotNone(results, "分析結果が生成されていません")
        
        # 中央滞在率のチェック
        center_ratio = results['center_time_ratio']
        print(f"中央滞在率: {center_ratio:.2%}")
        self.assertLessEqual(center_ratio, 0.5, "中央滞在率が高すぎます")
        
        # 振動率のチェック
        vibration_ratio = results['vibration_ratio']
        print(f"振動検出率: {vibration_ratio:.2%}")
        self.assertLessEqual(vibration_ratio, 0.2, "振動検出率が高すぎます")
        
        # 敵回避率のチェック
        avoidance_rate = results['enemy_avoidance_rate']
        print(f"敵回避率: {avoidance_rate:.2%}")
        self.assertGreaterEqual(avoidance_rate, 0.5, "敵回避率が低すぎます")
    
    def test_improved_behavior(self):
        """改善されたアドバタイズモード動作をテスト"""
        # アドバタイズモード改善ツールがあればテスト
        try:
            # 改善ツールのインスタンス化
            improver = AdvertiseModeImprover(main_module_name=None)
            
            # 改善パッチを現在のプレイヤーオブジェクトに直接適用
            # （通常は別のモジュールをパッチするが、ここではテスト用に直接適用）
            if hasattr(improver, '_defensive_movement'):
                self.player._defensive_movement = improver._defensive_movement
            if hasattr(improver, '_aggressive_movement'):
                self.player._aggressive_movement = improver._aggressive_movement
            if hasattr(improver, '_flanking_movement'):
                self.player._flanking_movement = improver._flanking_movement
            if hasattr(improver, '_balanced_movement'):
                self.player._balanced_movement = improver._balanced_movement
            
            # 戦略パラメータの初期化
            self.player._strategy_timer = 0
            self.player._current_strategy = 'balanced'
            self.player._last_position_change = (0, 0)
            self.player._consecutive_same_direction = 0
            
            # 改善されたアドバタイズモードのシミュレーション
            results = self._run_simulation(frames=300, enemy_count=5)
            
            # 結果の検証
            self.assertIsNotNone(results, "分析結果が生成されていません")
            
            # 中央滞在率のチェック
            center_ratio = results['center_time_ratio']
            print(f"改善後の中央滞在率: {center_ratio:.2%}")
            self.assertLessEqual(center_ratio, 0.4, "中央滞在率が高すぎます")
            
            # 振動率のチェック
            vibration_ratio = results['vibration_ratio']
            print(f"改善後の振動検出率: {vibration_ratio:.2%}")
            self.assertLessEqual(vibration_ratio, 0.15, "振動検出率が高すぎます")
            
            # 敵回避率のチェック
            avoidance_rate = results['enemy_avoidance_rate']
            print(f"改善後の敵回避率: {avoidance_rate:.2%}")
            self.assertGreaterEqual(avoidance_rate, 0.6, "敵回避率が低すぎます")
            
        except (ImportError, AttributeError) as e:
            self.skipTest(f"改善ツールが利用できないためテストをスキップします: {e}")
    
    def test_continuous_operation(self):
        """長時間の連続動作テスト"""
        # 長時間（10秒相当、600フレーム）のシミュレーションを実行
        frames = 600
        results = self._run_simulation(frames=frames, enemy_count=8)
        
        # アドバタイズモードが安定して動作することを確認
        self.assertIsNotNone(results, "分析結果が生成されていません")
        
        # 問題パターンの数をチェック
        problem_count = len(results['problematic_patterns'])
        print(f"検出された問題パターン数: {problem_count}")
        
        # 問題パターンの相対的な許容数（フレーム数に対して少なめであるべき）
        max_allowed_problems = frames / 100  # 100フレームあたり1つまで
        self.assertLessEqual(problem_count, max_allowed_problems, 
                           f"問題パターンの数が多すぎます: {problem_count} > {max_allowed_problems}")
    
    def test_adaptive_behavior(self):
        """敵の数に対する適応的な振る舞いをテスト"""
        # 少ない敵（3体）でのシミュレーション
        few_enemies_results = self._run_simulation(frames=240, enemy_count=3)
        
        # 多い敵（10体）でのシミュレーション
        many_enemies_results = self._run_simulation(frames=240, enemy_count=10)
        
        # 敵の数によって戦略が変わることを確認
        self.assertIsNotNone(few_enemies_results, "分析結果が生成されていません（少ない敵）")
        self.assertIsNotNone(many_enemies_results, "分析結果が生成されていません（多い敵）")
        
        # 戦略を確認（振動率や中央滞在率で判断）
        few_vibration = few_enemies_results['vibration_ratio']
        many_vibration = many_enemies_results['vibration_ratio']
        
        few_center = few_enemies_results['center_time_ratio']
        many_center = many_enemies_results['center_time_ratio']
        
        print(f"敵が少ない場合の振動率: {few_vibration:.2%}, 中央滞在率: {few_center:.2%}")
        print(f"敵が多い場合の振動率: {many_vibration:.2%}, 中央滞在率: {many_center:.2%}")
        
        # 敵が多い場合は、少ない場合と異なる行動を取るべき
        # （単純な同値チェックではなく、ある程度の差があることを確認）
        behavior_difference = abs(few_vibration - many_vibration) + abs(few_center - many_center)
        print(f"行動パターンの差異: {behavior_difference:.2%}")
        
        # 条件付きテスト（アドバタイズモードが十分に適応的かどうか）
        if hasattr(self.player, '_current_strategy'):
            self.assertGreaterEqual(behavior_difference, 0.05, 
                                  "敵の数による行動パターンの差が小さすぎます（適応性が低い）")
    
    def tearDown(self):
        """各テスト後の処理"""
        # Pygameのリソースを解放
        pygame.quit()
    
    @classmethod
    def tearDownClass(cls):
        """テストクラス全体の後処理"""
        # テスト実行時間を表示
        test_duration = time.time() - cls.test_start_time
        print(f"\nすべてのテストの実行時間: {test_duration:.2f}秒")
        
        # 結果ディレクトリを表示
        print(f"テスト結果は {os.path.abspath(cls.output_dir)} に保存されました")


class TestComparisonBenchmark(unittest.TestCase):
    """オリジナルと改善版のアドバタイズモードを比較するベンチマークテスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の前処理"""
        # テスト結果保存用のディレクトリを作成
        cls.output_dir = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not os.path.exists(cls.output_dir):
            os.makedirs(cls.output_dir)
    
    def setUp(self):
        """各テスト前の準備"""
        # Pygameの初期化
        pygame.init()
        
        # ゲーム環境の初期化
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.Surface((self.screen_width, self.screen_height))
        
        # オリジナルプレイヤーと改善版プレイヤーの準備
        self.original_player = Player()
        self.original_player.advertise_mode = True
        
        self.improved_player = Player()
        self.improved_player.advertise_mode = True
        
        # 敵と弾の初期化
        self.enemies = []
        self.bullets = []
        
        # アドバタイズモード改善機能を使用可能かチェック
        try:
            self.improver = AdvertiseModeImprover(main_module_name=None)
            
            # 改善版プレイヤーに改善パッチを適用
            if hasattr(self.improver, '_defensive_movement'):
                # 戦略関数を改善版プレイヤーに追加
                self.improved_player._defensive_movement = self.improver._defensive_movement.__get__(self.improved_player, Player)
                self.improved_player._aggressive_movement = self.improver._aggressive_movement.__get__(self.improved_player, Player)
                self.improved_player._flanking_movement = self.improver._flanking_movement.__get__(self.improved_player, Player)
                self.improved_player._balanced_movement = self.improver._balanced_movement.__get__(self.improved_player, Player)
                
                # 戦略メカニズムを上書き
                self.improved_player.update_advertise_movement = self.improver.improved_update_advertise_movement.__get__(self.improved_player, Player)
            
            # 戦略パラメータの初期化
            self.improved_player._strategy_timer = 0
            self.improved_player._current_strategy = 'balanced'
            self.improved_player._last_position_change = (0, 0)
            self.improved_player._consecutive_same_direction = 0
            
            self.has_improved_version = True
        except (ImportError, AttributeError) as e:
            print(f"改善版のアドバタイズモードが利用できません: {e}")
            self.has_improved_version = False
    
    def _run_benchmark(self, frames=300, enemy_count=5):
        """オリジナルと改善版の動作を比較するベンチマーク"""
        if not self.has_improved_version:
            self.skipTest("改善版のアドバタイズモードが利用できないためテストをスキップします")
        
        # 敵を生成
        self.enemies = []
        for _ in range(enemy_count):
            enemy = Enemy()
            enemy.x = 100 + (self.screen_width - 200) * (0.1 + 0.8 * (len(self.enemies) / max(1, enemy_count - 1)))
            enemy.y = 100 + (self.screen_height - 300) * (0.2 + 0.6 * (len(self.enemies) % 3) / 2)
            self.enemies.append(enemy)
        
        # オリジナルプレイヤーと改善版プレイヤーの位置履歴
        original_positions = []
        improved_positions = []
        
        # ベンチマークを実行
        for frame in range(frames):
            # オリジナル版の更新
            if hasattr(self.original_player, 'update_advertise_movement'):
                self.original_player.update_advertise_movement(self.enemies)
            else:
                self.original_player.update({}, self.enemies, self.bullets)
            
            # 改善版の更新
            self.improved_player.update_advertise_movement(self.enemies)
            
            # 位置履歴を記録
            original_positions.append((self.original_player.x, self.original_player.y))
            improved_positions.append((self.improved_player.x, self.improved_player.y))
            
            # 敵を更新（両方のプレイヤー用に同じ敵の動きにするため、コピーを作成）
            for enemy in self.enemies:
                enemy.update()
        
        # 結果を保存
        benchmark_result = {
            'frames': frames,
            'enemy_count': enemy_count,
            'original_positions': original_positions,
            'improved_positions': improved_positions
        }
        
        result_file = os.path.join(self.output_dir, f"benchmark_{enemy_count}enemies_{frames}frames.json")
        with open(result_file, 'w') as f:
            # 位置履歴はサイズが大きくなるので間引く
            simplified_result = benchmark_result.copy()
            simplified_result['original_positions'] = original_positions[::10]  # 10フレームごと
            simplified_result['improved_positions'] = improved_positions[::10]  # 10フレームごと
            json.dump(simplified_result, f)
        
        return benchmark_result
    
    def test_movement_comparison(self):
        """オリジナルと改善版の動きを比較"""
        # ベンチマークを実行
        results = self._run_benchmark(frames=300, enemy_count=5)
        
        # オリジナルと改善版の位置履歴
        original_positions = results['original_positions']
        improved_positions = results['improved_positions']
        
        # 中央からの平均距離を計算
        center_x, center_y = self.screen_width / 2, self.screen_height / 2
        
        original_avg_distance = sum(math.sqrt((x - center_x)**2 + (y - center_y)**2) 
                                 for x, y in original_positions) / len(original_positions)
        
        improved_avg_distance = sum(math.sqrt((x - center_x)**2 + (y - center_y)**2) 
                                for x, y in improved_positions) / len(improved_positions)
        
        print(f"オリジナル版の中央からの平均距離: {original_avg_distance:.2f}px")
        print(f"改善版の中央からの平均距離: {improved_avg_distance:.2f}px")
        
        # 振動カウント（方向変化回数）を計算
        def count_direction_changes(positions):
            changes = 0
            for i in range(2, len(positions)):
                p1, p2, p3 = positions[i-2], positions[i-1], positions[i]
                v1 = (p2[0] - p1[0], p2[1] - p1[1])
                v2 = (p3[0] - p2[0], p3[1] - p2[1])
                
                # 方向変化の検出（内積の符号で判定）
                dot_product = v1[0] * v2[0] + v1[1] * v2[1]
                v1_mag = math.sqrt(v1[0]**2 + v1[1]**2)
                v2_mag = math.sqrt(v2[0]**2 + v2[1]**2)
                
                # 速度が小さい場合は無視
                if v1_mag < 0.1 or v2_mag < 0.1:
                    continue
                
                # 方向が大きく変わった場合
                if dot_product < 0:
                    changes += 1
            
            return changes
        
        original_changes = count_direction_changes(original_positions)
        improved_changes = count_direction_changes(improved_positions)
        
        print(f"オリジナル版の方向変化回数: {original_changes}")
        print(f"改善版の方向変化回数: {improved_changes}")
        
        # 改善版は方向変化が少なく、スムーズな動きをすることを期待
        self.assertLessEqual(improved_changes, original_changes, 
                           "改善版の方向変化回数がオリジナルより多いです（スムーズさが低下）")
        
        # 改善版は中央からより離れた位置にいることを期待
        self.assertGreaterEqual(improved_avg_distance, original_avg_distance, 
                              "改善版の中央からの平均距離がオリジナルより短いです（中央滞在が改善されていない）")
    
    def tearDown(self):
        """各テスト後の処理"""
        # Pygameのリソースを解放
        pygame.quit()
    
    @classmethod
    def tearDownClass(cls):
        """テストクラス全体の後処理"""
        # テスト結果ディレクトリを表示
        print(f"ベンチマーク結果は {os.path.abspath(cls.output_dir)} に保存されました")


if __name__ == '__main__':
    # 直接実行された場合はテストを実行
    unittest.main() 
アドバタイズモードの統合テスト

複数のコンポーネントを連携させて、アドバタイズモード全体の動作をテストします。
"""

import unittest
import sys
import os
import time
import math
import pygame
import json
from datetime import datetime

# テスト用のパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 必要なモジュールをインポート
try:
    from advertise_mode_analyzer import AdvertiseModeAnalyzer, AdvertiseModeMonitor
    from advertise_mode_improver import AdvertiseModeImprover
except ImportError:
    print("アドバタイズモード分析/改善モジュールがインポートできません。パスが正しいか確認してください。")
    sys.exit(1)

# テスト用のモッククラスをインポート
from test_mock_classes import Player, Enemy, Bullet, DashSpec


class TestAdvertiseModeIntegration(unittest.TestCase):
    """アドバタイズモードの統合テスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の前処理"""
        # テスト結果保存用のディレクトリを作成
        cls.output_dir = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not os.path.exists(cls.output_dir):
            os.makedirs(cls.output_dir)
        
        # テスト実行時間を記録
        cls.test_start_time = time.time()
    
    def setUp(self):
        """各テスト前の準備"""
        # Pygameの初期化
        pygame.init()
        
        # ゲーム環境の初期化
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.Surface((self.screen_width, self.screen_height))
        
        # モニターとアナライザーの初期化
        self.analyzer = AdvertiseModeAnalyzer(verbose=False)
        
        # プレイヤーと敵の初期化
        self.player = Player()
        self.player.advertise_mode = True
        self.enemies = []
        self.bullets = []
        
        # 分析結果
        self.analysis_results = None
    
    def _run_simulation(self, frames=300, enemy_count=5):
        """指定フレーム数のシミュレーションを実行"""
        # 敵を生成
        self.enemies = []
        for _ in range(enemy_count):
            enemy = Enemy()
            enemy.x = 100 + (self.screen_width - 200) * (0.1 + 0.8 * (len(self.enemies) / max(1, enemy_count - 1)))
            enemy.y = 100 + (self.screen_height - 300) * (0.2 + 0.6 * (len(self.enemies) % 3) / 2)
            self.enemies.append(enemy)
        
        # シミュレーションを実行
        for frame in range(frames):
            # プレイヤー更新
            if hasattr(self.player, 'update_advertise_movement'):
                # 改善版があればそれを使用
                self.player.update_advertise_movement(self.enemies)
                if hasattr(self.player, 'perform_advertise_action'):
                    self.player.perform_advertise_action(self.enemies, self.bullets)
            else:
                # 通常の更新
                self.player.update({}, self.enemies, self.bullets)
            
            # 敵更新
            for enemy in self.enemies:
                enemy.update()
                
                # 画面の端で反射させる
                if enemy.x < 0 or enemy.x > self.screen_width:
                    enemy.direction_x = -enemy.direction_x
                if enemy.y < 0 or enemy.y > self.screen_height:
                    enemy.direction_y = -enemy.direction_y
            
            # 弾更新
            for bullet in self.bullets[:]:
                bullet.update()
                if not bullet.is_active:
                    self.bullets.remove(bullet)
            
            # 分析データを更新
            self.analyzer.update(self.player.x, self.player.y, self.enemies, frame)
        
        # 分析結果を生成
        self.analyzer.analyze_session(frames)
        self.analysis_results = self.analyzer.analysis_results
        
        # 分析結果をファイルに保存
        result_file = os.path.join(self.output_dir, f"analysis_{len(self.enemies)}enemies_{frames}frames.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
            
        return self.analysis_results
    
    def test_original_behavior(self):
        """オリジナルのアドバタイズモード動作をテスト"""
        # プレイヤーのアドバタイズモードを有効化
        self.player.advertise_mode = True
        
        # 300フレームのシミュレーションを実行（5秒相当）
        results = self._run_simulation(frames=300, enemy_count=5)
        
        # 評価基準の読み込み（存在すれば）
        criteria_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                    "evaluation", "criteria.md")
        
        # 結果の検証
        self.assertIsNotNone(results, "分析結果が生成されていません")
        
        # 中央滞在率のチェック
        center_ratio = results['center_time_ratio']
        print(f"中央滞在率: {center_ratio:.2%}")
        self.assertLessEqual(center_ratio, 0.5, "中央滞在率が高すぎます")
        
        # 振動率のチェック
        vibration_ratio = results['vibration_ratio']
        print(f"振動検出率: {vibration_ratio:.2%}")
        self.assertLessEqual(vibration_ratio, 0.2, "振動検出率が高すぎます")
        
        # 敵回避率のチェック
        avoidance_rate = results['enemy_avoidance_rate']
        print(f"敵回避率: {avoidance_rate:.2%}")
        self.assertGreaterEqual(avoidance_rate, 0.5, "敵回避率が低すぎます")
    
    def test_improved_behavior(self):
        """改善されたアドバタイズモード動作をテスト"""
        # アドバタイズモード改善ツールがあればテスト
        try:
            # 改善ツールのインスタンス化
            improver = AdvertiseModeImprover(main_module_name=None)
            
            # 改善パッチを現在のプレイヤーオブジェクトに直接適用
            # （通常は別のモジュールをパッチするが、ここではテスト用に直接適用）
            if hasattr(improver, '_defensive_movement'):
                self.player._defensive_movement = improver._defensive_movement
            if hasattr(improver, '_aggressive_movement'):
                self.player._aggressive_movement = improver._aggressive_movement
            if hasattr(improver, '_flanking_movement'):
                self.player._flanking_movement = improver._flanking_movement
            if hasattr(improver, '_balanced_movement'):
                self.player._balanced_movement = improver._balanced_movement
            
            # 戦略パラメータの初期化
            self.player._strategy_timer = 0
            self.player._current_strategy = 'balanced'
            self.player._last_position_change = (0, 0)
            self.player._consecutive_same_direction = 0
            
            # 改善されたアドバタイズモードのシミュレーション
            results = self._run_simulation(frames=300, enemy_count=5)
            
            # 結果の検証
            self.assertIsNotNone(results, "分析結果が生成されていません")
            
            # 中央滞在率のチェック
            center_ratio = results['center_time_ratio']
            print(f"改善後の中央滞在率: {center_ratio:.2%}")
            self.assertLessEqual(center_ratio, 0.4, "中央滞在率が高すぎます")
            
            # 振動率のチェック
            vibration_ratio = results['vibration_ratio']
            print(f"改善後の振動検出率: {vibration_ratio:.2%}")
            self.assertLessEqual(vibration_ratio, 0.15, "振動検出率が高すぎます")
            
            # 敵回避率のチェック
            avoidance_rate = results['enemy_avoidance_rate']
            print(f"改善後の敵回避率: {avoidance_rate:.2%}")
            self.assertGreaterEqual(avoidance_rate, 0.6, "敵回避率が低すぎます")
            
        except (ImportError, AttributeError) as e:
            self.skipTest(f"改善ツールが利用できないためテストをスキップします: {e}")
    
    def test_continuous_operation(self):
        """長時間の連続動作テスト"""
        # 長時間（10秒相当、600フレーム）のシミュレーションを実行
        frames = 600
        results = self._run_simulation(frames=frames, enemy_count=8)
        
        # アドバタイズモードが安定して動作することを確認
        self.assertIsNotNone(results, "分析結果が生成されていません")
        
        # 問題パターンの数をチェック
        problem_count = len(results['problematic_patterns'])
        print(f"検出された問題パターン数: {problem_count}")
        
        # 問題パターンの相対的な許容数（フレーム数に対して少なめであるべき）
        max_allowed_problems = frames / 100  # 100フレームあたり1つまで
        self.assertLessEqual(problem_count, max_allowed_problems, 
                           f"問題パターンの数が多すぎます: {problem_count} > {max_allowed_problems}")
    
    def test_adaptive_behavior(self):
        """敵の数に対する適応的な振る舞いをテスト"""
        # 少ない敵（3体）でのシミュレーション
        few_enemies_results = self._run_simulation(frames=240, enemy_count=3)
        
        # 多い敵（10体）でのシミュレーション
        many_enemies_results = self._run_simulation(frames=240, enemy_count=10)
        
        # 敵の数によって戦略が変わることを確認
        self.assertIsNotNone(few_enemies_results, "分析結果が生成されていません（少ない敵）")
        self.assertIsNotNone(many_enemies_results, "分析結果が生成されていません（多い敵）")
        
        # 戦略を確認（振動率や中央滞在率で判断）
        few_vibration = few_enemies_results['vibration_ratio']
        many_vibration = many_enemies_results['vibration_ratio']
        
        few_center = few_enemies_results['center_time_ratio']
        many_center = many_enemies_results['center_time_ratio']
        
        print(f"敵が少ない場合の振動率: {few_vibration:.2%}, 中央滞在率: {few_center:.2%}")
        print(f"敵が多い場合の振動率: {many_vibration:.2%}, 中央滞在率: {many_center:.2%}")
        
        # 敵が多い場合は、少ない場合と異なる行動を取るべき
        # （単純な同値チェックではなく、ある程度の差があることを確認）
        behavior_difference = abs(few_vibration - many_vibration) + abs(few_center - many_center)
        print(f"行動パターンの差異: {behavior_difference:.2%}")
        
        # 条件付きテスト（アドバタイズモードが十分に適応的かどうか）
        if hasattr(self.player, '_current_strategy'):
            self.assertGreaterEqual(behavior_difference, 0.05, 
                                  "敵の数による行動パターンの差が小さすぎます（適応性が低い）")
    
    def tearDown(self):
        """各テスト後の処理"""
        # Pygameのリソースを解放
        pygame.quit()
    
    @classmethod
    def tearDownClass(cls):
        """テストクラス全体の後処理"""
        # テスト実行時間を表示
        test_duration = time.time() - cls.test_start_time
        print(f"\nすべてのテストの実行時間: {test_duration:.2f}秒")
        
        # 結果ディレクトリを表示
        print(f"テスト結果は {os.path.abspath(cls.output_dir)} に保存されました")


class TestComparisonBenchmark(unittest.TestCase):
    """オリジナルと改善版のアドバタイズモードを比較するベンチマークテスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の前処理"""
        # テスト結果保存用のディレクトリを作成
        cls.output_dir = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not os.path.exists(cls.output_dir):
            os.makedirs(cls.output_dir)
    
    def setUp(self):
        """各テスト前の準備"""
        # Pygameの初期化
        pygame.init()
        
        # ゲーム環境の初期化
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.Surface((self.screen_width, self.screen_height))
        
        # オリジナルプレイヤーと改善版プレイヤーの準備
        self.original_player = Player()
        self.original_player.advertise_mode = True
        
        self.improved_player = Player()
        self.improved_player.advertise_mode = True
        
        # 敵と弾の初期化
        self.enemies = []
        self.bullets = []
        
        # アドバタイズモード改善機能を使用可能かチェック
        try:
            self.improver = AdvertiseModeImprover(main_module_name=None)
            
            # 改善版プレイヤーに改善パッチを適用
            if hasattr(self.improver, '_defensive_movement'):
                # 戦略関数を改善版プレイヤーに追加
                self.improved_player._defensive_movement = self.improver._defensive_movement.__get__(self.improved_player, Player)
                self.improved_player._aggressive_movement = self.improver._aggressive_movement.__get__(self.improved_player, Player)
                self.improved_player._flanking_movement = self.improver._flanking_movement.__get__(self.improved_player, Player)
                self.improved_player._balanced_movement = self.improver._balanced_movement.__get__(self.improved_player, Player)
                
                # 戦略メカニズムを上書き
                self.improved_player.update_advertise_movement = self.improver.improved_update_advertise_movement.__get__(self.improved_player, Player)
            
            # 戦略パラメータの初期化
            self.improved_player._strategy_timer = 0
            self.improved_player._current_strategy = 'balanced'
            self.improved_player._last_position_change = (0, 0)
            self.improved_player._consecutive_same_direction = 0
            
            self.has_improved_version = True
        except (ImportError, AttributeError) as e:
            print(f"改善版のアドバタイズモードが利用できません: {e}")
            self.has_improved_version = False
    
    def _run_benchmark(self, frames=300, enemy_count=5):
        """オリジナルと改善版の動作を比較するベンチマーク"""
        if not self.has_improved_version:
            self.skipTest("改善版のアドバタイズモードが利用できないためテストをスキップします")
        
        # 敵を生成
        self.enemies = []
        for _ in range(enemy_count):
            enemy = Enemy()
            enemy.x = 100 + (self.screen_width - 200) * (0.1 + 0.8 * (len(self.enemies) / max(1, enemy_count - 1)))
            enemy.y = 100 + (self.screen_height - 300) * (0.2 + 0.6 * (len(self.enemies) % 3) / 2)
            self.enemies.append(enemy)
        
        # オリジナルプレイヤーと改善版プレイヤーの位置履歴
        original_positions = []
        improved_positions = []
        
        # ベンチマークを実行
        for frame in range(frames):
            # オリジナル版の更新
            if hasattr(self.original_player, 'update_advertise_movement'):
                self.original_player.update_advertise_movement(self.enemies)
            else:
                self.original_player.update({}, self.enemies, self.bullets)
            
            # 改善版の更新
            self.improved_player.update_advertise_movement(self.enemies)
            
            # 位置履歴を記録
            original_positions.append((self.original_player.x, self.original_player.y))
            improved_positions.append((self.improved_player.x, self.improved_player.y))
            
            # 敵を更新（両方のプレイヤー用に同じ敵の動きにするため、コピーを作成）
            for enemy in self.enemies:
                enemy.update()
        
        # 結果を保存
        benchmark_result = {
            'frames': frames,
            'enemy_count': enemy_count,
            'original_positions': original_positions,
            'improved_positions': improved_positions
        }
        
        result_file = os.path.join(self.output_dir, f"benchmark_{enemy_count}enemies_{frames}frames.json")
        with open(result_file, 'w') as f:
            # 位置履歴はサイズが大きくなるので間引く
            simplified_result = benchmark_result.copy()
            simplified_result['original_positions'] = original_positions[::10]  # 10フレームごと
            simplified_result['improved_positions'] = improved_positions[::10]  # 10フレームごと
            json.dump(simplified_result, f)
        
        return benchmark_result
    
    def test_movement_comparison(self):
        """オリジナルと改善版の動きを比較"""
        # ベンチマークを実行
        results = self._run_benchmark(frames=300, enemy_count=5)
        
        # オリジナルと改善版の位置履歴
        original_positions = results['original_positions']
        improved_positions = results['improved_positions']
        
        # 中央からの平均距離を計算
        center_x, center_y = self.screen_width / 2, self.screen_height / 2
        
        original_avg_distance = sum(math.sqrt((x - center_x)**2 + (y - center_y)**2) 
                                 for x, y in original_positions) / len(original_positions)
        
        improved_avg_distance = sum(math.sqrt((x - center_x)**2 + (y - center_y)**2) 
                                for x, y in improved_positions) / len(improved_positions)
        
        print(f"オリジナル版の中央からの平均距離: {original_avg_distance:.2f}px")
        print(f"改善版の中央からの平均距離: {improved_avg_distance:.2f}px")
        
        # 振動カウント（方向変化回数）を計算
        def count_direction_changes(positions):
            changes = 0
            for i in range(2, len(positions)):
                p1, p2, p3 = positions[i-2], positions[i-1], positions[i]
                v1 = (p2[0] - p1[0], p2[1] - p1[1])
                v2 = (p3[0] - p2[0], p3[1] - p2[1])
                
                # 方向変化の検出（内積の符号で判定）
                dot_product = v1[0] * v2[0] + v1[1] * v2[1]
                v1_mag = math.sqrt(v1[0]**2 + v1[1]**2)
                v2_mag = math.sqrt(v2[0]**2 + v2[1]**2)
                
                # 速度が小さい場合は無視
                if v1_mag < 0.1 or v2_mag < 0.1:
                    continue
                
                # 方向が大きく変わった場合
                if dot_product < 0:
                    changes += 1
            
            return changes
        
        original_changes = count_direction_changes(original_positions)
        improved_changes = count_direction_changes(improved_positions)
        
        print(f"オリジナル版の方向変化回数: {original_changes}")
        print(f"改善版の方向変化回数: {improved_changes}")
        
        # 改善版は方向変化が少なく、スムーズな動きをすることを期待
        self.assertLessEqual(improved_changes, original_changes, 
                           "改善版の方向変化回数がオリジナルより多いです（スムーズさが低下）")
        
        # 改善版は中央からより離れた位置にいることを期待
        self.assertGreaterEqual(improved_avg_distance, original_avg_distance, 
                              "改善版の中央からの平均距離がオリジナルより短いです（中央滞在が改善されていない）")
    
    def tearDown(self):
        """各テスト後の処理"""
        # Pygameのリソースを解放
        pygame.quit()
    
    @classmethod
    def tearDownClass(cls):
        """テストクラス全体の後処理"""
        # テスト結果ディレクトリを表示
        print(f"ベンチマーク結果は {os.path.abspath(cls.output_dir)} に保存されました")


if __name__ == '__main__':
    # 直接実行された場合はテストを実行
    unittest.main() 