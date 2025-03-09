"""
アドバタイズモード分析ツール

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

# ゲームのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# pygameの初期化（GUI表示なし）
os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()

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
            'problematic_patterns': []
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
            self.log_file = open(f"advertise_analysis_{timestamp}.log", "w", encoding="utf-8")
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
            if len(self.player_positions) >= 10:
                prev_pos = self.player_positions[-10]
                current_pos = self.player_positions[-1]
                
                prev_distance = math.sqrt((nearest_enemy_pos[0] - prev_pos[0])**2 + 
                                        (nearest_enemy_pos[1] - prev_pos[1])**2)
                
                # 敵から離れる方向に動いていれば回避成功とカウント
                if current_pos != prev_pos and nearest_enemy_distance > prev_distance:
                    self.enemy_avoided_count += 1
                    if self.verbose:
                        print(f"\n[分析] 敵回避を検出: 距離 {nearest_enemy_distance:.1f}px -> {prev_distance:.1f}px")
                else:
                    if self.verbose and self.enemy_approach_count % 5 == 0:  # 頻度を制限
                        print(f"\n[分析] 敵回避失敗: 距離 {prev_distance:.1f}px -> {nearest_enemy_distance:.1f}px")
                    
                    # 問題パターンとして記録
                    if 'enemy_not_avoided' not in [p['type'] for p in self.analysis_results['problematic_patterns']]:
                        self.analysis_results['problematic_patterns'].append({
                            'type': 'enemy_not_avoided',
                            'position': current_pos,
                            'enemy_position': nearest_enemy_pos,
                            'time': len(self.player_positions) / 60,  # 60FPS仮定
                            'description': '敵が近づいていますが、適切に回避できていません。'
                        })
    
    def _check_if_enough_data(self, total_frame_count):
        """十分なデータが集まったかどうかをチェック"""
        # すでに十分と判断されていれば何もしない
        if self.enough_data_collected:
            return
        
        # 早期終了条件のチェック
        conditions_met = 0
        conditions_required = 3  # 少なくとも3つの条件が満たされれば十分と判断
        
        # 条件1: 敵接近イベントが十分に観測された
        condition1 = self.enemy_approach_count >= 5
        if condition1:
            conditions_met += 1
        
        # 条件2: 振動が検出された
        condition2 = self.vibration_count >= 3
        if condition2:
            conditions_met += 1
        
        # 条件3: プレイヤーが十分な範囲を移動した
        # 50セル以上訪問していれば十分（全体の約10%）
        condition3 = len(self.visited_cells) >= 50
        if condition3:
            conditions_met += 1
        
        # 条件4: 中央での滞在時間が十分
        condition4 = self.center_time >= 2.0  # 2秒以上
        if condition4:
            conditions_met += 1
        
        # 条件5: リスタートが複数回発生（最低2回）
        condition5 = self.restart_count >= 2
        if condition5:
            conditions_met += 1
        
        # 条件6: 最後のリスタートから十分な時間が経過
        condition6 = self.restart_count > 0 and total_frame_count - self.last_restart_time > 180  # 3秒以上
        if condition6:
            conditions_met += 1
        
        # 十分な条件が満たされたか、または十分なフレーム数が経過したか
        if conditions_met >= conditions_required or total_frame_count >= 600:  # 10秒以上
            self.enough_data_collected = True
            message = f"十分なデータが集まりました。条件充足: {conditions_met}/{conditions_required}, フレーム数: {total_frame_count}"
            self.log(message)
            
            if self.verbose:
                print(f"\n\n[分析] {message}")
                print(f"条件詳細:")
                print(f" - 敵接近イベント({self.enemy_approach_count}回): {'✓' if condition1 else '✗'}")
                print(f" - 振動検出({self.vibration_count}回): {'✓' if condition2 else '✗'}")
                print(f" - 移動範囲({len(self.visited_cells)}セル): {'✓' if condition3 else '✗'}")
                print(f" - 中央滞在時間({self.center_time:.1f}秒): {'✓' if condition4 else '✗'}")
                print(f" - リスタート回数({self.restart_count}回): {'✓' if condition5 else '✗'}")
                print(f" - リスタート後経過({total_frame_count - self.last_restart_time if self.restart_count > 0 else 0}フレーム): {'✓' if condition6 else '✗'}")
                print("")
    
    def analyze_session(self, total_frames):
        """セッション全体の分析を行う"""
        if not self.player_positions:
            return
        
        # 中央滞在時間の割合
        self.analysis_results['center_time_ratio'] = self.center_time / (total_frames / 60)
        
        # 振動の割合
        self.analysis_results['vibration_ratio'] = self.vibration_count / total_frames
        
        # 敵回避率
        if self.enemy_approach_count > 0:
            self.analysis_results['enemy_avoidance_rate'] = self.enemy_avoided_count / self.enemy_approach_count
        
        # 中央からの平均距離
        total_distance = sum(math.sqrt((x - CENTER_X)**2 + (y - CENTER_Y)**2) 
                           for x, y in self.player_positions)
        self.analysis_results['average_distance_from_center'] = total_distance / len(self.player_positions)
        
        # 問題パターンの分析
        if self.analysis_results['center_time_ratio'] > CENTER_TIME_THRESHOLD / (total_frames / 60):
            self.analysis_results['problematic_patterns'].append({
                'type': 'center_camping',
                'time': self.center_time,
                'description': f'プレイヤーが中央エリアに{self.center_time:.1f}秒間滞在しています。積極的な動きができていません。'
            })
        
        if self.analysis_results['enemy_avoidance_rate'] < ENEMY_AVOIDANCE_THRESHOLD and self.enemy_approach_count > 5:
            self.analysis_results['problematic_patterns'].append({
                'type': 'poor_enemy_avoidance',
                'rate': self.analysis_results['enemy_avoidance_rate'],
                'description': f'敵の回避率が{self.analysis_results["enemy_avoidance_rate"]:.1%}と低いです。敵から逃げる動作が不十分です。'
            })
        
        # 結果をログに出力
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
        with open("advertise_analysis_results.json", "w", encoding="utf-8") as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
    
    def _visualize_analysis(self):
        """分析結果を視覚化"""
        # 背景
        self.screen.fill((0, 0, 0))
        
        # ヒートマップ描画
        max_value = np.max(self.analysis_results['player_movement_heatmap'])
        if max_value > 0:
            normalized = self.analysis_results['player_movement_heatmap'] / max_value
            for y in range(normalized.shape[0]):
                for x in range(normalized.shape[1]):
                    value = normalized[y, x]
                    if value > 0:
                        alpha = int(min(value * 255, 200))
                        color = (int(255 * (1 - value)), int(255 * value), 0, alpha)
                        pygame.draw.rect(self.heatmap_surface, color, 
                                       (x * 10, y * 10, 10, 10))
        
        self.screen.blit(self.heatmap_surface, (0, 0))
        
        # 中央エリアを描画
        pygame.draw.circle(self.screen, (100, 100, 100), (CENTER_X, CENTER_Y), CENTER_AREA_RADIUS, 2)
        
        # プレイヤーの軌跡を描画
        if len(self.player_positions) >= 2:
            points = list(self.player_positions)
            for i in range(1, len(points)):
                start_color = (0, min(255, i * 2), min(255, i * 2))
                pygame.draw.line(self.screen, start_color, points[i-1], points[i], 2)
        
        # 問題のあるパターンを視覚化
        for pattern in self.analysis_results['problematic_patterns']:
            if 'position' in pattern:
                pos = pattern['position']
                pygame.draw.circle(self.screen, (255, 0, 0), pos, 10, 2)
                
                if pattern['type'] == 'enemy_not_avoided' and 'enemy_position' in pattern:
                    enemy_pos = pattern['enemy_position']
                    pygame.draw.line(self.screen, (255, 0, 0), pos, enemy_pos, 2)
                    pygame.draw.circle(self.screen, (255, 100, 0), enemy_pos, 8, 2)
        
        # テキスト情報を表示
        text_y = 10
        texts = [
            f"中央滞在比率: {self.analysis_results['center_time_ratio']:.2%}",
            f"振動検出比率: {self.analysis_results['vibration_ratio']:.2%}",
            f"敵回避率: {self.analysis_results['enemy_avoidance_rate']:.2%}",
            f"中央からの平均距離: {self.analysis_results['average_distance_from_center']:.1f}px"
        ]
        
        for text in texts:
            text_surface = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, text_y))
            text_y += 30
        
        # 問題パターンのリスト
        if self.analysis_results['problematic_patterns']:
            text_y += 20
            problem_header = self.font.render("検出された問題:", True, (255, 100, 100))
            self.screen.blit(problem_header, (10, text_y))
            text_y += 30
            
            for i, pattern in enumerate(self.analysis_results['problematic_patterns']):
                problem_text = self.font.render(f"{i+1}. {pattern['type']}", True, (255, 200, 200))
                self.screen.blit(problem_text, (10, text_y))
                text_y += 25
        
        # 画像として保存
        pygame.image.save(self.screen, "advertise_analysis_heatmap.png")
    
    def log(self, message):
        """ログにメッセージを追加"""
        if self.log_output and self.log_file:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_file.write(f"[{timestamp}] {message}\n")
            self.log_file.flush()
    
    def close(self):
        """リソースを解放"""
        if self.log_output and self.log_file:
            self.log_file.close()
        pygame.quit()


class AdvertiseModeMonitor:
    """アドバタイズモードの動作をモニタリングするクラス"""
    
    def __init__(self, main_module_name="main", max_frames=1800, headless=True, show_progress=False):
        """初期化"""
        self.main_module_name = main_module_name
        self.max_frames = max_frames  # 30秒間（60FPS想定）
        self.headless = headless
        self.frame_count = 0
        self.analyzer = AdvertiseModeAnalyzer(verbose=show_progress)
        self.show_progress = show_progress
        self.start_time = None
        self.restart_detected = False
        
        # メインモジュールを動的にインポート
        try:
            self.main_module = __import__(self.main_module_name)
            self.patched = False
        except ImportError:
            print(f"モジュール {self.main_module_name} が見つかりません。パス: {sys.path}")
            sys.exit(1)
    
    def _patch_main_module(self):
        """メインモジュールのコードをパッチして、アドバタイズモードの動作をモニタリングできるようにする"""
        if self.patched:
            return
        
        # オリジナルの関数を保存
        self.original_update = self.main_module.Player.update
        
        # モニタリング用の関数でラップ
        def patched_update(self_player, keys, enemies, bullets):
            # オリジナルの更新を実行
            result = self.original_update(self_player, keys, enemies, bullets)
            
            # アドバタイズモードの場合のみ分析
            if self_player.advertise_mode:
                self.analyzer.update(self_player.x, self_player.y, enemies, self.frame_count)
            
            return result
        
        # 関数を置き換え
        self.main_module.Player.update = patched_update
        self.patched = True
    
    def run_analysis(self):
        """アドバタイズモードを実行して分析"""
        try:
            # メインモジュールをパッチ
            self._patch_main_module()
            
            # 開始時間を記録
            self.start_time = time.time()
            
            # ゲーム変数を初期化
            self.main_module.reset_game()
            
            # プレイヤーのアドバタイズモードを有効化
            if hasattr(self.main_module, 'player') and hasattr(self.main_module.player, 'toggle_advertise_mode'):
                self.main_module.player.toggle_advertise_mode()
                if self.show_progress:
                    print("アドバタイズモードを有効化しました")
            else:
                print("アドバタイズモードを有効化できませんでした")
                return
            
            if self.show_progress:
                print(f"アドバタイズモードのモニタリングを開始します（最大 {self.max_frames} フレーム, 約{self.max_frames/60:.1f}秒）...")
                print(f"早期終了条件の検出を有効化: 十分なデータが集まり次第終了します")
            self.analyzer.log("アドバタイズモードのモニタリングを開始")
            
            # メインループ
            clock = pygame.time.Clock()
            running = True
            
            while running and self.frame_count < self.max_frames:
                # ゲームロジックを実行
                if hasattr(self.main_module, 'player') and hasattr(self.main_module, 'enemies') and hasattr(self.main_module, 'bullets'):
                    # プレイヤーの位置を確認
                    player = self.main_module.player
                    enemies = self.main_module.enemies
                    bullets = self.main_module.bullets
                    
                    # ゲーム状態の更新（キーはすべて押されていない状態）
                    keys = {}
                    
                    # プレイヤーを更新（パッチされたupdateが呼ばれる）
                    player.update(keys, enemies, bullets)
                    
                    # ゲーム状態の更新
                    for enemy in enemies:
                        enemy.update()
                    
                    for bullet in bullets:
                        bullet.update()
                
                self.frame_count += 1
                
                # アナライザーにプレイヤーと敵の情報を渡す
                if hasattr(self.main_module, 'player') and hasattr(self.main_module, 'enemies'):
                    enough_data = self.analyzer.update(
                        self.main_module.player.x, 
                        self.main_module.player.y, 
                        self.main_module.enemies,
                        self.frame_count
                    )
                    
                    # 十分なデータが集まった場合は早期終了
                    if enough_data:
                        if self.show_progress:
                            print("\n十分なデータが集まりました。分析を早期終了します。")
                        break
                
                # 進捗表示
                if self.show_progress and self.frame_count % (60 if self.frame_count < 60 else 30) == 0:
                    elapsed = time.time() - self.start_time
                    eta = (elapsed / self.frame_count) * (self.max_frames - self.frame_count) if self.frame_count > 0 else 0
                    progress = self.frame_count / self.max_frames * 100
                    print(f"\n進捗: {progress:.1f}% ({self.frame_count}/{self.max_frames}) - 経過: {elapsed:.1f}秒, 残り: {eta:.1f}秒")
                
                # リスタート文字列の検出（ログ出力から）
                if self.show_progress and "Auto-Restart" in str(self.main_module):
                    self.restart_detected = True
                    print("\nAdvertise Mode: Auto-Restart が検出されました")
                
                # ティックレートを制御（ヘッドレスモードでは高速化）
                if self.headless:
                    if self.frame_count % 10 == 0:
                        # 10フレームごとに少し待機して他のプロセスにCPUを譲る
                        time.sleep(0.001)
                else:
                    clock.tick(60)
            
            if self.show_progress:
                elapsed = time.time() - self.start_time
                print(f"\n進捗: 100% ({self.frame_count}/{self.max_frames}) - 完了: {elapsed:.1f}秒")
                print(f"モニタリング完了。{self.frame_count} フレーム分析しました（{elapsed:.1f}秒）。")
            
            # 分析結果を生成
            self.analyzer.analyze_session(self.frame_count)
            
            # 結果を要約
            self._summarize_results()
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # リソースを解放
            self.analyzer.close()
    
    def _summarize_results(self):
        """分析結果を要約して表示"""
        results = self.analyzer.analysis_results
        
        print("\n====== アドバタイズモード分析結果 ======")
        print(f"中央エリア滞在時間比率: {results['center_time_ratio']:.2%}")
        print(f"振動動作の比率: {results['vibration_ratio']:.2%}")
        print(f"敵回避率: {results['enemy_avoidance_rate']:.2%}")
        print(f"中央からの平均距離: {results['average_distance_from_center']:.1f}ピクセル")
        
        if results['problematic_patterns']:
            print("\n問題のあるパターン:")
            for i, pattern in enumerate(results['problematic_patterns']):
                print(f"{i+1}. {pattern['type']}: {pattern['description']}")
        
        print("\n分析結果は以下のファイルに保存されました:")
        print("- advertise_analysis_results.json（詳細な分析データ）")
        print("- advertise_analysis_heatmap.png（動きのヒートマップ）")
        print(f"- advertise_analysis_*.log（実行ログ）")


def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='アドバタイズモード分析ツール')
    parser.add_argument('--module', default='main', help='メインモジュール名')
    parser.add_argument('--frames', type=int, default=1800, help='分析するフレーム数（デフォルト: 1800）')
    parser.add_argument('--headless', action='store_true', help='GUIなしで実行する')
    
    args = parser.parse_args()
    
    monitor = AdvertiseModeMonitor(
        main_module_name=args.module,
        max_frames=args.frames,
        headless=args.headless
    )
    
    monitor.run_analysis()


if __name__ == '__main__':
    main() 