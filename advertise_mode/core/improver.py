"""
アドバタイズモード改善モジュール

アドバタイズモード（自動デモプレイ）の振る舞いを改善し、より自然な動きを実現します。
特に、敵から適切に回避する動作や無駄な振動を防ぐ処理を追加します。
"""

import sys
import os
import time
import math
import random
import importlib
from pathlib import Path

# ダッシュ関連の定数
class DashSpec:
    NORMAL_SPEED = 5.0
    DASH_SPEED = 10.0
    DASH_DURATION = 120
    DASH_COOLDOWN = 45

class AdvertiseModeImprover:
    """アドバタイズモードを改善するクラス"""
    
    def __init__(self, main_module_name="main"):
        """初期化"""
        self.main_module_name = main_module_name
        self.patches_applied = False
        
        # メインモジュールを動的にインポート
        try:
            # importlib.import_moduleを使用してモジュールをインポート
            self.main_module = importlib.import_module(self.main_module_name)
            print(f"モジュール {self.main_module_name} を読み込みました")
        except ImportError:
            print(f"モジュール {self.main_module_name} が見つかりません。パス: {sys.path}")
            sys.exit(1)
    
    def apply_patches(self):
        """アドバタイズモード関連のメソッドをパッチする"""
        if self.patches_applied:
            return
        
        print("アドバタイズモードの振る舞いを改善するパッチを適用します...")
        
        # Player.update_advertise_movementをパッチ
        self._patch_advertise_movement()
        
        # Player.find_dangerous_enemiesをパッチ
        self._patch_find_dangerous_enemies()
        
        # Player.perform_advertise_actionをパッチ
        self._patch_perform_advertise_action()
        
        # プレイヤーの戦略パラメータを追加
        self._add_strategy_parameters()
        
        self.patches_applied = True
        print("パッチが適用されました")
    
    def _patch_advertise_movement(self):
        """プレイヤーの移動戦略を改善する"""
        # オリジナルの関数を保存
        if hasattr(self.main_module.Player, 'update_advertise_movement'):
            original_update_advertise_movement = self.main_module.Player.update_advertise_movement
        else:
            original_update_advertise_movement = None
            
        if hasattr(self.main_module.Player, 'update_advertise_movement_visual'):
            original_update_advertise_movement_visual = self.main_module.Player.update_advertise_movement_visual
        else:
            original_update_advertise_movement_visual = None
        
        def improved_update_advertise_movement(self_player, enemies):
            """改善されたアドバタイズモードの移動処理"""
            # 基本的な振る舞いは残しつつ、改善を加える
            
            # 戦略タイマーの更新
            if not hasattr(self_player, '_strategy_timer'):
                self_player._strategy_timer = 0
                self_player._current_strategy = 'balanced'
                self_player._last_position_change = (0, 0)
                self_player._consecutive_same_direction = 0
                self_player._last_strategy_change = 0
            
            self_player._strategy_timer += 1
            
            # 戦略の切り替え（一定時間ごとにランダムに変更）
            if self_player._strategy_timer > 180:  # 3秒ごとに戦略を変更
                self_player._strategy_timer = 0
                
                # 前回と異なる戦略を選択
                strategies = ['balanced', 'defensive', 'aggressive', 'flanking']
                if self_player._current_strategy in strategies:
                    strategies.remove(self_player._current_strategy)
                
                self_player._current_strategy = random.choice(strategies)
                self_player._last_strategy_change = 0
                
                # デバッグ情報
                # print(f"戦略を変更: {self_player._current_strategy}")
            
            # 現在の戦略に基づいて移動方向を決定
            if self_player._current_strategy == 'defensive':
                self._defensive_movement(self_player, enemies)
            elif self_player._current_strategy == 'aggressive':
                self._aggressive_movement(self_player, enemies)
            elif self_player._current_strategy == 'flanking':
                self._flanking_movement(self_player, enemies)
            else:  # balanced
                self._balanced_movement(self_player, enemies)
            
            # 同じ方向への連続移動をチェック
            if self_player._last_position_change != (0, 0):
                dx, dy = self_player.direction_x, self_player.direction_y
                last_dx, last_dy = self_player._last_position_change
                
                # 方向の類似性をチェック（内積で判定）
                similarity = dx * last_dx + dy * last_dy
                
                if similarity > 0.9:  # ほぼ同じ方向
                    self_player._consecutive_same_direction += 1
                    
                    # 長時間同じ方向に移動している場合、少しランダム性を加える
                    if self_player._consecutive_same_direction > 120:  # 2秒以上
                        # 方向にランダムな摂動を加える
                        angle = random.uniform(-0.5, 0.5)  # ±0.5ラジアン（約±30度）
                        cos_angle = math.cos(angle)
                        sin_angle = math.sin(angle)
                        
                        new_dx = dx * cos_angle - dy * sin_angle
                        new_dy = dx * sin_angle + dy * cos_angle
                        
                        self_player.direction_x = new_dx
                        self_player.direction_y = new_dy
                        
                        self_player._consecutive_same_direction = 0
                else:
                    self_player._consecutive_same_direction = 0
            
            # 現在の方向を保存
            self_player._last_position_change = (self_player.direction_x, self_player.direction_y)
            
            # 速度の計算と位置の更新
            speed = self_player.speed
            self_player.velocity_x = self_player.direction_x * speed
            self_player.velocity_y = self_player.direction_y * speed
            
            self_player.x += self_player.velocity_x
            self_player.y += self_player.velocity_y
            
            # 画面外に出ないように制限
            self_player.x = max(50, min(self_player.x, 750))
            self_player.y = max(50, min(self_player.y, 550))
        
        # 改善された関数をプレイヤークラスに設定
        self.main_module.Player.update_advertise_movement = improved_update_advertise_movement
        self.improved_update_advertise_movement = improved_update_advertise_movement
    
    def _defensive_movement(self, player, enemies):
        """防御的な移動戦略 - 敵から離れることを優先"""
        if not enemies:
            # 敵がいない場合はランダムな方向に移動
            if random.random() < 0.02:  # 2%の確率で方向変更
                player.direction_x = random.uniform(-1, 1)
                player.direction_y = random.uniform(-1, 1)
                
                # 正規化
                magnitude = max(0.01, math.sqrt(player.direction_x**2 + player.direction_y**2))
                player.direction_x /= magnitude
                player.direction_y /= magnitude
            return
        
        # 全ての敵からの逃げるベクトルを計算
        escape_x, escape_y = 0, 0
        
        for enemy in enemies:
            # 敵からプレイヤーへのベクトル
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            
            # 距離の二乗
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < 1:  # 0除算防止
                continue
                
            # 距離が近いほど影響を強く
            weight = 10000 / dist_sq
            
            escape_x += dx * weight
            escape_y += dy * weight
        
        # 画面中央からの逃げるベクトルも加える（中央に留まりすぎないように）
        center_x, center_y = 400, 300
        dx = player.x - center_x
        dy = player.y - center_y
        
        # 中央からの距離
        center_dist = math.sqrt(dx*dx + dy*dy)
        
        if center_dist < 100:  # 中央付近にいる場合
            # 中央から離れる成分を強める
            escape_x += dx * 0.5
            escape_y += dy * 0.5
        
        # 移動方向を正規化
        magnitude = math.sqrt(escape_x*escape_x + escape_y*escape_y)
        
        if magnitude > 0.01:
            player.direction_x = escape_x / magnitude
            player.direction_y = escape_y / magnitude
        else:
            # 適切な方向が見つからない場合はランダムに移動
            angle = random.uniform(0, 2 * math.pi)
            player.direction_x = math.cos(angle)
            player.direction_y = math.sin(angle)
    
    def _aggressive_movement(self, player, enemies):
        """攻撃的な移動戦略 - 敵に近づくが、あまりに近づきすぎない"""
        if not enemies:
            # 敵がいない場合は画面中央に向かう
            dx = 400 - player.x
            dy = 300 - player.y
            
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 0.01:
                player.direction_x = dx / dist
                player.direction_y = dy / dist
            else:
                # 中央にいる場合はランダムな方向に移動
                angle = random.uniform(0, 2 * math.pi)
                player.direction_x = math.cos(angle)
                player.direction_y = math.sin(angle)
            
            return
        
        # 最も近い敵を見つける
        nearest_enemy = min(enemies, key=lambda e: (e.x - player.x)**2 + (e.y - player.y)**2)
        
        # 敵へのベクトル
        dx = nearest_enemy.x - player.x
        dy = nearest_enemy.y - player.y
        
        # 距離
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 150:  # 近すぎる場合は少し離れる
            player.direction_x = -dx / dist
            player.direction_y = -dy / dist
        elif dist > 250:  # 遠すぎる場合は近づく
            player.direction_x = dx / dist
            player.direction_y = dy / dist
        else:  # 適切な距離の場合は横に動く（円を描くように）
            # 敵を中心とした円周上を移動
            player.direction_x = dy / dist
            player.direction_y = -dx / dist
            
            # ランダムな摂動を加える
            if random.random() < 0.05:  # 5%の確率
                player.direction_x += random.uniform(-0.3, 0.3)
                player.direction_y += random.uniform(-0.3, 0.3)
                
                # 正規化
                magnitude = math.sqrt(player.direction_x**2 + player.direction_y**2)
                if magnitude > 0.01:
                    player.direction_x /= magnitude
                    player.direction_y /= magnitude
    
    def _flanking_movement(self, player, enemies):
        """側面移動戦略 - 敵の横に回り込む"""
        if not enemies:
            # 敵がいない場合はランダムな方向に移動
            if random.random() < 0.02:  # 2%の確率で方向変更
                player.direction_x = random.uniform(-1, 1)
                player.direction_y = random.uniform(-1, 1)
                
                # 正規化
                magnitude = max(0.01, math.sqrt(player.direction_x**2 + player.direction_y**2))
                player.direction_x /= magnitude
                player.direction_y /= magnitude
            return
        
        # 敵の集団の中心を見つける
        center_x = sum(enemy.x for enemy in enemies) / len(enemies)
        center_y = sum(enemy.y for enemy in enemies) / len(enemies)
        
        # 中心へのベクトル
        dx = center_x - player.x
        dy = center_y - player.y
        
        # 距離
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 0.01:
            # 中心にいる場合はランダムな方向に移動
            angle = random.uniform(0, 2 * math.pi)
            player.direction_x = math.cos(angle)
            player.direction_y = math.sin(angle)
        else:
            # 中心に対して垂直方向に移動（側面に回り込む）
            # 時間経過で回り込む方向を変える
            if (player._last_strategy_change // 60) % 2 == 0:  # 1秒ごとに切り替え
                player.direction_x = dy / dist
                player.direction_y = -dx / dist
            else:
                player.direction_x = -dy / dist
                player.direction_y = dx / dist
            
            # 敵から適切な距離を保つ
            if dist < 100:  # 近すぎる場合
                # 離れる成分を加える
                player.direction_x = 0.7 * player.direction_x - 0.3 * dx / dist
                player.direction_y = 0.7 * player.direction_y - 0.3 * dy / dist
            elif dist > 300:  # 遠すぎる場合
                # 近づく成分を加える
                player.direction_x = 0.7 * player.direction_x + 0.3 * dx / dist
                player.direction_y = 0.7 * player.direction_y + 0.3 * dy / dist
            
            # 正規化
            magnitude = math.sqrt(player.direction_x**2 + player.direction_y**2)
            if magnitude > 0.01:
                player.direction_x /= magnitude
                player.direction_y /= magnitude
        
        player._last_strategy_change += 1
    
    def _balanced_movement(self, player, enemies):
        """バランスの取れた移動戦略 - 敵から適切な距離を保ちつつ、画面全体を使う"""
        if not enemies:
            # 敵がいない場合は画面の端に向かう
            # 画面の四隅を順番に巡回
            corners = [(100, 100), (700, 100), (700, 500), (100, 500)]
            current_corner = (player._last_strategy_change // 120) % 4  # 2秒ごとに切り替え
            
            target_x, target_y = corners[current_corner]
            
            dx = target_x - player.x
            dy = target_y - player.y
            
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 20:  # 目標地点から離れている場合
                player.direction_x = dx / dist
                player.direction_y = dy / dist
            else:
                # 次の目標地点に切り替え
                player._last_strategy_change += 120
                
                # その場で少し待機
                player.direction_x = 0
                player.direction_y = 0
            
            player._last_strategy_change += 1
            return
        
        # 敵からの影響を計算
        influence_x, influence_y = 0, 0
        
        for enemy in enemies:
            # 敵からプレイヤーへのベクトル
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            
            # 距離の二乗
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < 1:  # 0除算防止
                continue
                
            # 距離に応じた重み付け
            dist = math.sqrt(dist_sq)
            
            if dist < 150:  # 近い敵からは逃げる
                weight = 1.0 - dist / 150
                influence_x += dx / dist * weight * 2.0
                influence_y += dy / dist * weight * 2.0
            elif dist < 300:  # 中距離の敵は横に回り込む
                weight = 1.0 - (dist - 150) / 150
                influence_x += dy / dist * weight
                influence_y += -dx / dist * weight
        
        # 画面中央からの影響（中央に留まりすぎないように）
        center_x, center_y = 400, 300
        dx = player.x - center_x
        dy = player.y - center_y
        
        # 中央からの距離
        center_dist = math.sqrt(dx*dx + dy*dy)
        
        if center_dist < 100:  # 中央付近にいる場合
            # 中央から離れる成分を加える
            weight = 1.0 - center_dist / 100
            influence_x += dx / max(1, center_dist) * weight
            influence_y += dy / max(1, center_dist) * weight
        
        # 画面端からの影響（画面外に出ないように）
        edge_influence_x = 0
        edge_influence_y = 0
        
        if player.x < 100:
            edge_influence_x += (100 - player.x) / 100
        elif player.x > 700:
            edge_influence_x -= (player.x - 700) / 100
            
        if player.y < 100:
            edge_influence_y += (100 - player.y) / 100
        elif player.y > 500:
            edge_influence_y -= (player.y - 500) / 100
        
        # 全ての影響を合成
        player.direction_x = influence_x + edge_influence_x * 0.5
        player.direction_y = influence_y + edge_influence_y * 0.5
        
        # ランダムな摂動を加える（自然な動きに）
        if random.random() < 0.02:  # 2%の確率
            player.direction_x += random.uniform(-0.3, 0.3)
            player.direction_y += random.uniform(-0.3, 0.3)
        
        # 正規化
        magnitude = math.sqrt(player.direction_x**2 + player.direction_y**2)
        if magnitude > 0.01:
            player.direction_x /= magnitude
            player.direction_y /= magnitude
        else:
            # 適切な方向が見つからない場合はランダムに移動
            angle = random.uniform(0, 2 * math.pi)
            player.direction_x = math.cos(angle)
            player.direction_y = math.sin(angle)
        
        player._last_strategy_change += 1
    
    def _patch_find_dangerous_enemies(self):
        """敵の危険度判定を改善する"""
        # オリジナルの関数を保存
        if hasattr(self.main_module.Player, 'find_dangerous_enemies'):
            original_find_dangerous_enemies = self.main_module.Player.find_dangerous_enemies
        else:
            # 関数が存在しない場合は何もしない
            return
        
        def improved_find_dangerous_enemies(self_player, enemies):
            """改善された敵の危険度判定"""
            if not enemies:
                return []
            
            dangerous_enemies = []
            
            for enemy in enemies:
                # 敵との距離
                distance = math.sqrt((enemy.x - self_player.x)**2 + (enemy.y - self_player.y)**2)
                
                # 敵の移動方向とプレイヤーへの方向の内積
                enemy_direction = (0, 0)
                if hasattr(enemy, 'direction_x') and hasattr(enemy, 'direction_y'):
                    enemy_direction = (enemy.direction_x, enemy.direction_y)
                
                to_player_direction = (self_player.x - enemy.x, self_player.y - enemy.y)
                to_player_magnitude = math.sqrt(to_player_direction[0]**2 + to_player_direction[1]**2)
                
                if to_player_magnitude > 0:
                    to_player_direction = (to_player_direction[0] / to_player_magnitude, 
                                          to_player_direction[1] / to_player_magnitude)
                
                # 内積（-1から1の範囲、1に近いほどプレイヤーに向かっている）
                dot_product = enemy_direction[0] * to_player_direction[0] + enemy_direction[1] * to_player_direction[1]
                
                # 危険度の計算
                danger_level = 0
                
                # 距離による危険度（近いほど危険）
                if distance < 100:
                    danger_level += (100 - distance) / 100 * 5  # 最大5ポイント
                
                # 方向による危険度（プレイヤーに向かっているほど危険）
                if dot_product > 0:
                    danger_level += dot_product * 3  # 最大3ポイント
                
                # 敵の種類による危険度
                enemy_type = getattr(enemy, 'enemy_type', 'normal')
                if enemy_type == 'boss':
                    danger_level += 3
                elif enemy_type == 'elite':
                    danger_level += 2
                
                # 敵の速度による危険度
                enemy_speed = 0
                if hasattr(enemy, 'speed'):
                    enemy_speed = enemy.speed
                elif hasattr(enemy, 'velocity_x') and hasattr(enemy, 'velocity_y'):
                    enemy_speed = math.sqrt(enemy.velocity_x**2 + enemy.velocity_y**2)
                
                danger_level += enemy_speed / 5  # 速度5につき1ポイント
                
                # 危険と判断される敵を追加
                if danger_level >= 3 or distance < 150:
                    dangerous_enemies.append((enemy, danger_level))
            
            # 危険度でソート（降順）
            dangerous_enemies.sort(key=lambda x: x[1], reverse=True)
            
            # 敵のみのリストを返す
            return [enemy for enemy, _ in dangerous_enemies]
        
        # 改善された関数をプレイヤークラスに設定
        self.main_module.Player.find_dangerous_enemies = improved_find_dangerous_enemies
    
    def _patch_perform_advertise_action(self):
        """アドバタイズモードの行動を改善する"""
        # オリジナルの関数を保存
        if hasattr(self.main_module.Player, 'perform_advertise_action'):
            original_perform_advertise_action = self.main_module.Player.perform_advertise_action
        else:
            # 関数が存在しない場合は何もしない
            return
        
        def improved_perform_advertise_action(self_player, enemies, bullets):
            """改善されたアドバタイズモードの行動"""
            # 基本的な行動はオリジナルの関数を呼び出す
            if original_perform_advertise_action:
                original_perform_advertise_action(self_player, enemies, bullets)
            
            # 追加の改善: 戦略に基づいた行動
            if hasattr(self_player, '_current_strategy'):
                if self_player._current_strategy == 'aggressive':
                    # 攻撃的な戦略の場合、より積極的に攻撃
                    if random.random() < 0.1:  # 10%の確率でダッシュ
                        if hasattr(self_player, 'dash'):
                            self_player.dash()
                
                elif self_player._current_strategy == 'defensive':
                    # 防御的な戦略の場合、敵が近づいたらダッシュで逃げる
                    if enemies:
                        nearest_enemy = min(enemies, key=lambda e: (e.x - self_player.x)**2 + (e.y - self_player.y)**2)
                        distance = math.sqrt((nearest_enemy.x - self_player.x)**2 + (nearest_enemy.y - self_player.y)**2)
                        
                        if distance < 100 and random.random() < 0.3:  # 30%の確率でダッシュ
                            if hasattr(self_player, 'dash'):
                                self_player.dash()
        
        # 改善された関数をプレイヤークラスに設定
        self.main_module.Player.perform_advertise_action = improved_perform_advertise_action
    
    def _add_strategy_parameters(self):
        """プレイヤークラスに戦略パラメータを追加"""
        # プレイヤーのインスタンスに戦略パラメータを追加
        if hasattr(self.main_module, 'player'):
            player = self.main_module.player
            
            if not hasattr(player, '_strategy_timer'):
                player._strategy_timer = 0
                player._current_strategy = 'balanced'
                player._last_position_change = (0, 0)
                player._consecutive_same_direction = 0
                player._last_strategy_change = 0 