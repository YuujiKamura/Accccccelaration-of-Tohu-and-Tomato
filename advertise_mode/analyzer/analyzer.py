"""
アドバタイズモード分析モジュール

アドバタイズモード（自動デモプレイ）の動作を分析し、問題点を検出して視覚化します。
特に、プレイヤーが敵から適切に逃げられているか、中央付近で振動していないかなどを分析します。
"""

import sys
import os
import time
import pygame
import math
import json
import numpy as np
from datetime import datetime
from collections import deque

# ゲーム設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2
CENTER_AREA_RADIUS = 100  # 中央エリアの半径

# 分析設定
POSITION_HISTORY_LENGTH = 120  # 2秒間（60FPS想定）
VELOCITY_THRESHOLD = 2.0  # 振動検出の閾値
CENTER_TIME_THRESHOLD = 3.0  # 中央滞在警告の閾値（秒）
ENEMY_APPROACH_THRESHOLD = 150  # 敵接近の閾値（ピクセル）
ENEMY_AVOIDANCE_THRESHOLD = 0.5  # 敵回避率の閾値（0-1）

class AdvertiseModeAnalyzer:
    """アドバタイズモードの動作を分析するクラス"""
    
    def __init__(self, visual_output=True, log_output=True, verbose=True):
        """初期化"""
        self.visual_output = visual_output
        self.log_output = log_output
        self.verbose = verbose  # 詳細なコンソール出力
        
        # 分析用データ構造
        self.player_positions = deque(maxlen=POSITION_HISTORY_LENGTH)
        self.enemy_positions = []
        self.player_velocity = [0, 0]
        self.center_time = 0
        self.enemy_approach_count = 0
        self.enemy_avoided_count = 0
        self.vibration_detected = False
        self.vibration_count = 0
        
        # 分析結果
        self.analysis_results = {
            'center_time_ratio': 0,
            'vibration_ratio': 0,
            'enemy_avoidance_rate': 0,
            'average_distance_from_center': 0,
            'average_distance_to_nearest_enemy': 0,
            'player_movement_heatmap': np.zeros((SCREEN_HEIGHT // 10, SCREEN_WIDTH // 10)),
            'problematic_patterns': [],
            'position_history': []  # 可視化ツール用に位置履歴も保存
        }
        
        # 早期終了判定用のパラメータ
        self.visited_cells = set()  # 訪問したグリッドセル
        self.vibration_sequences = 0  # 連続振動検出回数
        self.enough_data_collected = False  # 十分なデータが集まったかのフラグ
        self.restart_count = 0  # リスタート回数
        self.last_restart_time = 0  # 最後のリスタート時のフレーム数
        self.last_status_report = 0  # 最後のステータスレポート時のフレーム数
        
        # 視覚化用のSurface
        if self.visual_output:
            self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.heatmap_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            self.font = pygame.font.SysFont(None, 24)
        
        # ログファイル
        self.log_file = None
        if self.log_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = os.environ.get('ADVERTISE_ANALYSIS_PATH', '.')
            self.log_file = open(os.path.join(log_dir, f"advertise_analysis_{timestamp}.log"), "w", encoding="utf-8")
            self.log(f"アドバタイズモード分析開始: {timestamp}")
            
        if self.verbose:
            print("アドバタイズモード分析を初期化しました")
    
    def update(self, player_x, player_y, enemies, total_frame_count):
        """フレームごとの更新と分析"""
        # プレイヤーの位置を記録
        self.player_positions.append((player_x, player_y))
        
        # 敵の位置を記録
        self.enemy_positions = [(enemy.x, enemy.y) for enemy in enemies if not getattr(enemy, 'is_defeated', False)]
        
        # プレイヤーの速度を計算（位置履歴から）
        if len(self.player_positions) >= 2:
            prev_x, prev_y = self.player_positions[-2]
            curr_x, curr_y = self.player_positions[-1]
            self.player_velocity = [curr_x - prev_x, curr_y - prev_y]
        
        # 中央エリア滞在時間を更新
        distance_from_center = math.sqrt((player_x - CENTER_X) ** 2 + (player_y - CENTER_Y) ** 2)
        if distance_from_center < CENTER_AREA_RADIUS:
            self.center_time += 1/60  # 60FPSと仮定
        
        # 振動検出
        self._detect_vibration()
        
        # 敵からの回避を分析
        self._analyze_enemy_avoidance()
        
        # ヒートマップを更新
        grid_x = min(int(player_x) // 10, (SCREEN_WIDTH // 10) - 1)
        grid_y = min(int(player_y) // 10, (SCREEN_HEIGHT // 10) - 1)
        try:
            self.analysis_results['player_movement_heatmap'][grid_y, grid_x] += 1
            self.visited_cells.add((grid_x, grid_y))
        except IndexError:
            pass  # 画面外の場合は無視
            
        # リスタート検出
        # 急に位置が中央付近に移動した場合はリスタートと判断
        if len(self.player_positions) >= 2:
            prev_x, prev_y = self.player_positions[-2]
            curr_x, curr_y = self.player_positions[-1]
            
            if (abs(curr_x - CENTER_X) < 20 and abs(curr_y - CENTER_Y - 100) < 20 and 
                math.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2) > 100):
                self.restart_count += 1
                self.last_restart_time = total_frame_count
                
                message = f"リスタートを検出: {self.restart_count}回目 (フレーム {total_frame_count})"
                self.log(message)
                if self.verbose:
                    print(f"\n[分析] {message}")
        
        # 定期的にステータスレポートを表示（最初の30フレームは毎フレーム、その後は30フレームごと）
        if self.verbose and (total_frame_count < 30 or total_frame_count - self.last_status_report >= 30):
            self.last_status_report = total_frame_count
            self._print_status_report(total_frame_count)
        
        # 十分なデータが集まったかチェック
        self._check_if_enough_data(total_frame_count)
        
        return self.enough_data_collected
    
    def _print_status_report(self, frame_count):
        """現在の分析状況を簡潔に表示"""
        # 敵回避率を計算
        avoidance_rate = self.enemy_avoided_count / max(self.enemy_approach_count, 1)
        
        # プレイヤー位置
        if self.player_positions:
            curr_x, curr_y = self.player_positions[-1]
            distance_from_center = math.sqrt((curr_x - CENTER_X)**2 + (curr_y - CENTER_Y)**2)
        else:
            curr_x, curr_y = 0, 0
            distance_from_center = 0
            
        # 訪問セル数の割合（全体の約10%を目標）
        cells_ratio = len(self.visited_cells) / (SCREEN_WIDTH // 10 * SCREEN_HEIGHT // 10)
        
        # 更新情報をコンソールに表示
        print(f"\r[フレーム {frame_count}] "
              f"位置: ({int(curr_x)},{int(curr_y)}) "
              f"中央距離: {int(distance_from_center)}px "
              f"振動: {self.vibration_count}回 "
              f"回避率: {avoidance_rate:.2f} "
              f"訪問範囲: {len(self.visited_cells)}セル({cells_ratio:.1%}) "
              f"リスタート: {self.restart_count}回", end="")
    
    def _detect_vibration(self):
        """振動（小さなジグザグ動作）を検出"""
        if len(self.player_positions) < 10:
            return
        
        # 過去10フレームの動きを分析
        recent_positions = list(self.player_positions)[-10:]
        direction_changes = 0
        
        for i in range(2, len(recent_positions)):
            # 3点を使って方向変化を検出
            p1 = recent_positions[i-2]
            p2 = recent_positions[i-1]
            p3 = recent_positions[i]
            
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
            
            # 方向が大きく変わった場合
            if dot_product < 0:
                direction_changes += 1
        
        # 方向変化が多く、速度が小さい場合は振動と判定
        velocity_magnitude = math.sqrt(self.player_velocity[0]**2 + self.player_velocity[1]**2)
        prev_vibration = self.vibration_detected
        
        if direction_changes >= 3 and velocity_magnitude < VELOCITY_THRESHOLD:
            self.vibration_detected = True
            self.vibration_count += 1
            
            if not prev_vibration and self.verbose:
                curr_x, curr_y = self.player_positions[-1]
                print(f"\n[分析] 振動動作を検出: 位置({int(curr_x)},{int(curr_y)}), 速度={velocity_magnitude:.1f}")
            
            # 問題パターンとして記録
            if 'vibration' not in [p['type'] for p in self.analysis_results['problematic_patterns']]:
                self.analysis_results['problematic_patterns'].append({
                    'type': 'vibration',
                    'position': self.player_positions[-1],
                    'time': len(self.player_positions) / 60,  # 60FPS仮定
                    'description': '小さな振動動作が検出されました。決断力のない動きになっています。'
                })
        else:
            self.vibration_detected = False
    
    def _analyze_enemy_avoidance(self):
        """敵からの回避行動を分析"""
        if not self.enemy_positions or len(self.player_positions) < 30:
            return
        
        # 最も近い敵を見つける
        nearest_enemy_pos = min(self.enemy_positions, 
                               key=lambda pos: (pos[0] - self.player_positions[-1][0])**2 + 
                                              (pos[1] - self.player_positions[-1][1])**2)
        
        nearest_enemy_distance = math.sqrt((nearest_enemy_pos[0] - self.player_positions[-1][0])**2 + 
                                         (nearest_enemy_pos[1] - self.player_positions[-1][1])**2)
        
        # 敵が近づいているかを検出
        if nearest_enemy_distance < ENEMY_APPROACH_THRESHOLD:
            self.enemy_approach_count += 1
            
            # プレイヤーの動きが敵から離れる方向かを確認
            if len(self.player_positions) >= 30:
                # 30フレーム前と現在の位置
                old_pos = self.player_positions[-30]
                curr_pos = self.player_positions[-1]
                
                # 敵からの距離の変化
                old_distance = math.sqrt((nearest_enemy_pos[0] - old_pos[0])**2 + 
                                       (nearest_enemy_pos[1] - old_pos[1])**2)
                
                # 距離が増えていれば回避成功
                if nearest_enemy_distance > old_distance + 5:  # 5ピクセル以上増加
                    self.enemy_avoided_count += 1
                    
                # 一番近い敵に近づいている場合は警告
                elif nearest_enemy_distance < old_distance - 20 and nearest_enemy_distance < 100:
                    # 問題パターンとして記録
                    self.analysis_results['problematic_patterns'].append({
                        'type': 'approaching_enemy',
                        'position': curr_pos,
                        'enemy_position': nearest_enemy_pos,
                        'time': len(self.player_positions) / 60,  # 60FPS仮定
                        'description': f'敵に近づいています（距離: {nearest_enemy_distance:.1f}px）。回避行動が必要です。'
                    })
                    
                    if self.verbose:
                        print(f"\n[分析] 警告: 敵に近づいています（距離: {nearest_enemy_distance:.1f}px）")
    
    def _check_if_enough_data(self, total_frame_count):
        """十分なデータが集まったかを確認する"""
        # リスタートから一定時間立っているか確認
        if self.restart_count > 0 and total_frame_count - self.last_restart_time < 300:
            return  # リスタート直後は判断を保留
            
        # 最低フレーム数を確保
        if total_frame_count < 600:  # 最低10秒間（60FPS想定）
            return
            
        # 終了判断条件
        conditions_met = 0
        
        # 1. 中央付近の滞在時間が長すぎる
        center_time_ratio = self.center_time / (total_frame_count / 60)
        if center_time_ratio > 0.7:  # 70%以上の時間を中央で過ごしている
            self.analysis_results['problematic_patterns'].append({
                'type': 'center_dwelling',
                'position': (CENTER_X, CENTER_Y),
                'time': self.center_time,
                'description': f'長時間（{self.center_time:.1f}秒）中央付近に留まっています。画面全体を使った動きが必要です。'
            })
            conditions_met += 1
                
        # 2. 振動が多すぎる
        vibration_ratio = self.vibration_count / max(total_frame_count / 60, 1)
        if vibration_ratio > 0.5:  # 50%以上の時間で振動
            conditions_met += 1
            
        # 3. 敵回避率が極端に低い
        avoidance_rate = self.enemy_avoided_count / max(self.enemy_approach_count, 1)
        if self.enemy_approach_count > 5 and avoidance_rate < 0.2:  # 20%未満の回避率
            conditions_met += 1
            
        # 4. 十分な領域をカバーしている
        cells_ratio = len(self.visited_cells) / (SCREEN_WIDTH // 10 * SCREEN_HEIGHT // 10)
        if cells_ratio > 0.25:  # 25%以上のエリアをカバー
            conditions_met += 1
            
        # 十分なデータが集まった判定
        self.enough_data_collected = (conditions_met >= 2 and total_frame_count >= 900) or total_frame_count >= 1800
    
    def analyze_session(self, total_frames):
        """セッション全体の分析を行う"""
        # 分析結果を保存する辞書
        self.analysis_results['position_history'] = list(self.player_positions)
        
        # 中央エリア滞在時間の比率
        self.analysis_results['center_time_ratio'] = self.center_time / (total_frames / 60)
        
        # 振動検出の比率
        self.analysis_results['vibration_ratio'] = self.vibration_count / max(total_frames / 60, 1)
        
        # 敵回避率
        self.analysis_results['enemy_avoidance_rate'] = self.enemy_avoided_count / max(self.enemy_approach_count, 1)
        
        # 中央からの平均距離
        if self.player_positions:
            distances = [math.sqrt((pos[0] - CENTER_X)**2 + (pos[1] - CENTER_Y)**2) for pos in self.player_positions]
            self.analysis_results['average_distance_from_center'] = sum(distances) / len(distances)
        
        # 近接敵からの平均距離
        if self.enemy_positions and self.player_positions:
            nearest_distances = []
            for pos in self.player_positions:
                if self.enemy_positions:  # 敵がいる場合のみ
                    nearest = min(self.enemy_positions, 
                                 key=lambda e_pos: (e_pos[0] - pos[0])**2 + (e_pos[1] - pos[1])**2)
                    dist = math.sqrt((nearest[0] - pos[0])**2 + (nearest[1] - pos[1])**2)
                    nearest_distances.append(dist)
            
            if nearest_distances:
                self.analysis_results['average_distance_to_nearest_enemy'] = sum(nearest_distances) / len(nearest_distances)
        
        # ログに出力
        self._log_analysis_results()
        
        # 視覚化
        if self.visual_output:
            self._visualize_analysis()
    
    def _log_analysis_results(self):
        """分析結果をログに出力"""
        if not self.log_output:
            return
        
        self.log("\n====== アドバタイズモード分析結果 ======")
        self.log(f"中央エリア滞在時間比率: {self.analysis_results['center_time_ratio']:.2%}")
        self.log(f"振動動作の比率: {self.analysis_results['vibration_ratio']:.2%}")
        self.log(f"敵回避率: {self.analysis_results['enemy_avoidance_rate']:.2%}")
        self.log(f"中央からの平均距離: {self.analysis_results['average_distance_from_center']:.1f}ピクセル")
        
        if self.analysis_results['problematic_patterns']:
            self.log("\n問題のあるパターン:")
            for i, pattern in enumerate(self.analysis_results['problematic_patterns']):
                self.log(f"{i+1}. {pattern['type']}: {pattern['description']}")
        
        # JSONでも保存
        log_dir = os.environ.get('ADVERTISE_ANALYSIS_PATH', '.')
        with open(os.path.join(log_dir, "advertise_analysis_results.json"), "w", encoding="utf-8") as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
    
    def _visualize_analysis(self):
        """分析結果を視覚化（ヒートマップなど）"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.colors import LinearSegmentedColormap
            
            # ヒートマップ用のデータを準備
            heatmap_data = self.analysis_results['player_movement_heatmap']
            
            # カスタムカラーマップの作成（青から赤へのグラデーション）
            colors = [(0, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0), (1, 0, 0)]
            cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=256)
            
            plt.figure(figsize=(10, 8))
            plt.imshow(heatmap_data, cmap=cmap, interpolation='bicubic')
            plt.colorbar(label='頻度')
            plt.title('アドバタイズモード移動ヒートマップ')
            
            # 問題パターンの位置をマーク
            for pattern in self.analysis_results['problematic_patterns']:
                if 'position' in pattern:
                    x, y = pattern['position']
                    grid_x = x // 10
                    grid_y = y // 10
                    plt.plot(grid_x, grid_y, 'ro', markersize=10, alpha=0.7)
                    
                    # 簡単な説明を追加
                    plt.text(grid_x + 1, grid_y + 1, pattern['type'][:10], color='white', 
                            fontsize=8, ha='left', va='bottom')
            
            # 画面中央の位置をマーク
            center_x, center_y = CENTER_X // 10, CENTER_Y // 10
            plt.plot(center_x, center_y, 'wx', markersize=12)
            
            # 中央エリアを円で表示
            circle = plt.Circle((center_x, center_y), CENTER_AREA_RADIUS // 10, 
                               fill=False, edgecolor='white', linestyle='--')
            plt.gca().add_patch(circle)
            
            # 結果を保存
            log_dir = os.environ.get('ADVERTISE_ANALYSIS_PATH', '.')
            plt.savefig(os.path.join(log_dir, "advertise_analysis_heatmap.png"), dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"視覚化の生成中にエラーが発生しました: {e}")
    
    def log(self, message):
        """ログを出力"""
        if self.log_file:
            self.log_file.write(f"{message}\n")
            self.log_file.flush()
    
    def close(self):
        """リソースを解放"""
        if self.log_file:
            self.log_file.close()
            
        if pygame.get_init():
            pass  # pygameのリソース解放が必要であればここで行う 
アドバタイズモード分析モジュール

アドバタイズモード（自動デモプレイ）の動作を分析し、問題点を検出して視覚化します。
特に、プレイヤーが敵から適切に逃げられているか、中央付近で振動していないかなどを分析します。
"""

import sys
import os
import time
import pygame
import math
import json
import numpy as np
from datetime import datetime
from collections import deque

# ゲーム設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2
CENTER_AREA_RADIUS = 100  # 中央エリアの半径

# 分析設定
POSITION_HISTORY_LENGTH = 120  # 2秒間（60FPS想定）
VELOCITY_THRESHOLD = 2.0  # 振動検出の閾値
CENTER_TIME_THRESHOLD = 3.0  # 中央滞在警告の閾値（秒）
ENEMY_APPROACH_THRESHOLD = 150  # 敵接近の閾値（ピクセル）
ENEMY_AVOIDANCE_THRESHOLD = 0.5  # 敵回避率の閾値（0-1）

class AdvertiseModeAnalyzer:
    """アドバタイズモードの動作を分析するクラス"""
    
    def __init__(self, visual_output=True, log_output=True, verbose=True):
        """初期化"""
        self.visual_output = visual_output
        self.log_output = log_output
        self.verbose = verbose  # 詳細なコンソール出力
        
        # 分析用データ構造
        self.player_positions = deque(maxlen=POSITION_HISTORY_LENGTH)
        self.enemy_positions = []
        self.player_velocity = [0, 0]
        self.center_time = 0
        self.enemy_approach_count = 0
        self.enemy_avoided_count = 0
        self.vibration_detected = False
        self.vibration_count = 0
        
        # 分析結果
        self.analysis_results = {
            'center_time_ratio': 0,
            'vibration_ratio': 0,
            'enemy_avoidance_rate': 0,
            'average_distance_from_center': 0,
            'average_distance_to_nearest_enemy': 0,
            'player_movement_heatmap': np.zeros((SCREEN_HEIGHT // 10, SCREEN_WIDTH // 10)),
            'problematic_patterns': [],
            'position_history': []  # 可視化ツール用に位置履歴も保存
        }
        
        # 早期終了判定用のパラメータ
        self.visited_cells = set()  # 訪問したグリッドセル
        self.vibration_sequences = 0  # 連続振動検出回数
        self.enough_data_collected = False  # 十分なデータが集まったかのフラグ
        self.restart_count = 0  # リスタート回数
        self.last_restart_time = 0  # 最後のリスタート時のフレーム数
        self.last_status_report = 0  # 最後のステータスレポート時のフレーム数
        
        # 視覚化用のSurface
        if self.visual_output:
            self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.heatmap_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            self.font = pygame.font.SysFont(None, 24)
        
        # ログファイル
        self.log_file = None
        if self.log_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = os.environ.get('ADVERTISE_ANALYSIS_PATH', '.')
            self.log_file = open(os.path.join(log_dir, f"advertise_analysis_{timestamp}.log"), "w", encoding="utf-8")
            self.log(f"アドバタイズモード分析開始: {timestamp}")
            
        if self.verbose:
            print("アドバタイズモード分析を初期化しました")
    
    def update(self, player_x, player_y, enemies, total_frame_count):
        """フレームごとの更新と分析"""
        # プレイヤーの位置を記録
        self.player_positions.append((player_x, player_y))
        
        # 敵の位置を記録
        self.enemy_positions = [(enemy.x, enemy.y) for enemy in enemies if not getattr(enemy, 'is_defeated', False)]
        
        # プレイヤーの速度を計算（位置履歴から）
        if len(self.player_positions) >= 2:
            prev_x, prev_y = self.player_positions[-2]
            curr_x, curr_y = self.player_positions[-1]
            self.player_velocity = [curr_x - prev_x, curr_y - prev_y]
        
        # 中央エリア滞在時間を更新
        distance_from_center = math.sqrt((player_x - CENTER_X) ** 2 + (player_y - CENTER_Y) ** 2)
        if distance_from_center < CENTER_AREA_RADIUS:
            self.center_time += 1/60  # 60FPSと仮定
        
        # 振動検出
        self._detect_vibration()
        
        # 敵からの回避を分析
        self._analyze_enemy_avoidance()
        
        # ヒートマップを更新
        grid_x = min(int(player_x) // 10, (SCREEN_WIDTH // 10) - 1)
        grid_y = min(int(player_y) // 10, (SCREEN_HEIGHT // 10) - 1)
        try:
            self.analysis_results['player_movement_heatmap'][grid_y, grid_x] += 1
            self.visited_cells.add((grid_x, grid_y))
        except IndexError:
            pass  # 画面外の場合は無視
            
        # リスタート検出
        # 急に位置が中央付近に移動した場合はリスタートと判断
        if len(self.player_positions) >= 2:
            prev_x, prev_y = self.player_positions[-2]
            curr_x, curr_y = self.player_positions[-1]
            
            if (abs(curr_x - CENTER_X) < 20 and abs(curr_y - CENTER_Y - 100) < 20 and 
                math.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2) > 100):
                self.restart_count += 1
                self.last_restart_time = total_frame_count
                
                message = f"リスタートを検出: {self.restart_count}回目 (フレーム {total_frame_count})"
                self.log(message)
                if self.verbose:
                    print(f"\n[分析] {message}")
        
        # 定期的にステータスレポートを表示（最初の30フレームは毎フレーム、その後は30フレームごと）
        if self.verbose and (total_frame_count < 30 or total_frame_count - self.last_status_report >= 30):
            self.last_status_report = total_frame_count
            self._print_status_report(total_frame_count)
        
        # 十分なデータが集まったかチェック
        self._check_if_enough_data(total_frame_count)
        
        return self.enough_data_collected
    
    def _print_status_report(self, frame_count):
        """現在の分析状況を簡潔に表示"""
        # 敵回避率を計算
        avoidance_rate = self.enemy_avoided_count / max(self.enemy_approach_count, 1)
        
        # プレイヤー位置
        if self.player_positions:
            curr_x, curr_y = self.player_positions[-1]
            distance_from_center = math.sqrt((curr_x - CENTER_X)**2 + (curr_y - CENTER_Y)**2)
        else:
            curr_x, curr_y = 0, 0
            distance_from_center = 0
            
        # 訪問セル数の割合（全体の約10%を目標）
        cells_ratio = len(self.visited_cells) / (SCREEN_WIDTH // 10 * SCREEN_HEIGHT // 10)
        
        # 更新情報をコンソールに表示
        print(f"\r[フレーム {frame_count}] "
              f"位置: ({int(curr_x)},{int(curr_y)}) "
              f"中央距離: {int(distance_from_center)}px "
              f"振動: {self.vibration_count}回 "
              f"回避率: {avoidance_rate:.2f} "
              f"訪問範囲: {len(self.visited_cells)}セル({cells_ratio:.1%}) "
              f"リスタート: {self.restart_count}回", end="")
    
    def _detect_vibration(self):
        """振動（小さなジグザグ動作）を検出"""
        if len(self.player_positions) < 10:
            return
        
        # 過去10フレームの動きを分析
        recent_positions = list(self.player_positions)[-10:]
        direction_changes = 0
        
        for i in range(2, len(recent_positions)):
            # 3点を使って方向変化を検出
            p1 = recent_positions[i-2]
            p2 = recent_positions[i-1]
            p3 = recent_positions[i]
            
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
            
            # 方向が大きく変わった場合
            if dot_product < 0:
                direction_changes += 1
        
        # 方向変化が多く、速度が小さい場合は振動と判定
        velocity_magnitude = math.sqrt(self.player_velocity[0]**2 + self.player_velocity[1]**2)
        prev_vibration = self.vibration_detected
        
        if direction_changes >= 3 and velocity_magnitude < VELOCITY_THRESHOLD:
            self.vibration_detected = True
            self.vibration_count += 1
            
            if not prev_vibration and self.verbose:
                curr_x, curr_y = self.player_positions[-1]
                print(f"\n[分析] 振動動作を検出: 位置({int(curr_x)},{int(curr_y)}), 速度={velocity_magnitude:.1f}")
            
            # 問題パターンとして記録
            if 'vibration' not in [p['type'] for p in self.analysis_results['problematic_patterns']]:
                self.analysis_results['problematic_patterns'].append({
                    'type': 'vibration',
                    'position': self.player_positions[-1],
                    'time': len(self.player_positions) / 60,  # 60FPS仮定
                    'description': '小さな振動動作が検出されました。決断力のない動きになっています。'
                })
        else:
            self.vibration_detected = False
    
    def _analyze_enemy_avoidance(self):
        """敵からの回避行動を分析"""
        if not self.enemy_positions or len(self.player_positions) < 30:
            return
        
        # 最も近い敵を見つける
        nearest_enemy_pos = min(self.enemy_positions, 
                               key=lambda pos: (pos[0] - self.player_positions[-1][0])**2 + 
                                              (pos[1] - self.player_positions[-1][1])**2)
        
        nearest_enemy_distance = math.sqrt((nearest_enemy_pos[0] - self.player_positions[-1][0])**2 + 
                                         (nearest_enemy_pos[1] - self.player_positions[-1][1])**2)
        
        # 敵が近づいているかを検出
        if nearest_enemy_distance < ENEMY_APPROACH_THRESHOLD:
            self.enemy_approach_count += 1
            
            # プレイヤーの動きが敵から離れる方向かを確認
            if len(self.player_positions) >= 30:
                # 30フレーム前と現在の位置
                old_pos = self.player_positions[-30]
                curr_pos = self.player_positions[-1]
                
                # 敵からの距離の変化
                old_distance = math.sqrt((nearest_enemy_pos[0] - old_pos[0])**2 + 
                                       (nearest_enemy_pos[1] - old_pos[1])**2)
                
                # 距離が増えていれば回避成功
                if nearest_enemy_distance > old_distance + 5:  # 5ピクセル以上増加
                    self.enemy_avoided_count += 1
                    
                # 一番近い敵に近づいている場合は警告
                elif nearest_enemy_distance < old_distance - 20 and nearest_enemy_distance < 100:
                    # 問題パターンとして記録
                    self.analysis_results['problematic_patterns'].append({
                        'type': 'approaching_enemy',
                        'position': curr_pos,
                        'enemy_position': nearest_enemy_pos,
                        'time': len(self.player_positions) / 60,  # 60FPS仮定
                        'description': f'敵に近づいています（距離: {nearest_enemy_distance:.1f}px）。回避行動が必要です。'
                    })
                    
                    if self.verbose:
                        print(f"\n[分析] 警告: 敵に近づいています（距離: {nearest_enemy_distance:.1f}px）")
    
    def _check_if_enough_data(self, total_frame_count):
        """十分なデータが集まったかを確認する"""
        # リスタートから一定時間立っているか確認
        if self.restart_count > 0 and total_frame_count - self.last_restart_time < 300:
            return  # リスタート直後は判断を保留
            
        # 最低フレーム数を確保
        if total_frame_count < 600:  # 最低10秒間（60FPS想定）
            return
            
        # 終了判断条件
        conditions_met = 0
        
        # 1. 中央付近の滞在時間が長すぎる
        center_time_ratio = self.center_time / (total_frame_count / 60)
        if center_time_ratio > 0.7:  # 70%以上の時間を中央で過ごしている
            self.analysis_results['problematic_patterns'].append({
                'type': 'center_dwelling',
                'position': (CENTER_X, CENTER_Y),
                'time': self.center_time,
                'description': f'長時間（{self.center_time:.1f}秒）中央付近に留まっています。画面全体を使った動きが必要です。'
            })
            conditions_met += 1
                
        # 2. 振動が多すぎる
        vibration_ratio = self.vibration_count / max(total_frame_count / 60, 1)
        if vibration_ratio > 0.5:  # 50%以上の時間で振動
            conditions_met += 1
            
        # 3. 敵回避率が極端に低い
        avoidance_rate = self.enemy_avoided_count / max(self.enemy_approach_count, 1)
        if self.enemy_approach_count > 5 and avoidance_rate < 0.2:  # 20%未満の回避率
            conditions_met += 1
            
        # 4. 十分な領域をカバーしている
        cells_ratio = len(self.visited_cells) / (SCREEN_WIDTH // 10 * SCREEN_HEIGHT // 10)
        if cells_ratio > 0.25:  # 25%以上のエリアをカバー
            conditions_met += 1
            
        # 十分なデータが集まった判定
        self.enough_data_collected = (conditions_met >= 2 and total_frame_count >= 900) or total_frame_count >= 1800
    
    def analyze_session(self, total_frames):
        """セッション全体の分析を行う"""
        # 分析結果を保存する辞書
        self.analysis_results['position_history'] = list(self.player_positions)
        
        # 中央エリア滞在時間の比率
        self.analysis_results['center_time_ratio'] = self.center_time / (total_frames / 60)
        
        # 振動検出の比率
        self.analysis_results['vibration_ratio'] = self.vibration_count / max(total_frames / 60, 1)
        
        # 敵回避率
        self.analysis_results['enemy_avoidance_rate'] = self.enemy_avoided_count / max(self.enemy_approach_count, 1)
        
        # 中央からの平均距離
        if self.player_positions:
            distances = [math.sqrt((pos[0] - CENTER_X)**2 + (pos[1] - CENTER_Y)**2) for pos in self.player_positions]
            self.analysis_results['average_distance_from_center'] = sum(distances) / len(distances)
        
        # 近接敵からの平均距離
        if self.enemy_positions and self.player_positions:
            nearest_distances = []
            for pos in self.player_positions:
                if self.enemy_positions:  # 敵がいる場合のみ
                    nearest = min(self.enemy_positions, 
                                 key=lambda e_pos: (e_pos[0] - pos[0])**2 + (e_pos[1] - pos[1])**2)
                    dist = math.sqrt((nearest[0] - pos[0])**2 + (nearest[1] - pos[1])**2)
                    nearest_distances.append(dist)
            
            if nearest_distances:
                self.analysis_results['average_distance_to_nearest_enemy'] = sum(nearest_distances) / len(nearest_distances)
        
        # ログに出力
        self._log_analysis_results()
        
        # 視覚化
        if self.visual_output:
            self._visualize_analysis()
    
    def _log_analysis_results(self):
        """分析結果をログに出力"""
        if not self.log_output:
            return
        
        self.log("\n====== アドバタイズモード分析結果 ======")
        self.log(f"中央エリア滞在時間比率: {self.analysis_results['center_time_ratio']:.2%}")
        self.log(f"振動動作の比率: {self.analysis_results['vibration_ratio']:.2%}")
        self.log(f"敵回避率: {self.analysis_results['enemy_avoidance_rate']:.2%}")
        self.log(f"中央からの平均距離: {self.analysis_results['average_distance_from_center']:.1f}ピクセル")
        
        if self.analysis_results['problematic_patterns']:
            self.log("\n問題のあるパターン:")
            for i, pattern in enumerate(self.analysis_results['problematic_patterns']):
                self.log(f"{i+1}. {pattern['type']}: {pattern['description']}")
        
        # JSONでも保存
        log_dir = os.environ.get('ADVERTISE_ANALYSIS_PATH', '.')
        with open(os.path.join(log_dir, "advertise_analysis_results.json"), "w", encoding="utf-8") as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
    
    def _visualize_analysis(self):
        """分析結果を視覚化（ヒートマップなど）"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.colors import LinearSegmentedColormap
            
            # ヒートマップ用のデータを準備
            heatmap_data = self.analysis_results['player_movement_heatmap']
            
            # カスタムカラーマップの作成（青から赤へのグラデーション）
            colors = [(0, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0), (1, 0, 0)]
            cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=256)
            
            plt.figure(figsize=(10, 8))
            plt.imshow(heatmap_data, cmap=cmap, interpolation='bicubic')
            plt.colorbar(label='頻度')
            plt.title('アドバタイズモード移動ヒートマップ')
            
            # 問題パターンの位置をマーク
            for pattern in self.analysis_results['problematic_patterns']:
                if 'position' in pattern:
                    x, y = pattern['position']
                    grid_x = x // 10
                    grid_y = y // 10
                    plt.plot(grid_x, grid_y, 'ro', markersize=10, alpha=0.7)
                    
                    # 簡単な説明を追加
                    plt.text(grid_x + 1, grid_y + 1, pattern['type'][:10], color='white', 
                            fontsize=8, ha='left', va='bottom')
            
            # 画面中央の位置をマーク
            center_x, center_y = CENTER_X // 10, CENTER_Y // 10
            plt.plot(center_x, center_y, 'wx', markersize=12)
            
            # 中央エリアを円で表示
            circle = plt.Circle((center_x, center_y), CENTER_AREA_RADIUS // 10, 
                               fill=False, edgecolor='white', linestyle='--')
            plt.gca().add_patch(circle)
            
            # 結果を保存
            log_dir = os.environ.get('ADVERTISE_ANALYSIS_PATH', '.')
            plt.savefig(os.path.join(log_dir, "advertise_analysis_heatmap.png"), dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"視覚化の生成中にエラーが発生しました: {e}")
    
    def log(self, message):
        """ログを出力"""
        if self.log_file:
            self.log_file.write(f"{message}\n")
            self.log_file.flush()
    
    def close(self):
        """リソースを解放"""
        if self.log_file:
            self.log_file.close()
            
        if pygame.get_init():
            pass  # pygameのリソース解放が必要であればここで行う 