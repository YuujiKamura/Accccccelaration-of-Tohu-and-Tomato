"""
アドバタイズモード改善ツール

アドバタイズモード（自動デモプレイ）の振る舞いを改善し、より自然な動きを実現します。
特に、敵から適切に回避する動作や無駄な振動を防ぐ処理を追加します。
"""

import sys
import os
import time
import math
import random
from pathlib import Path

# ゲームのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ダッシュ関連の定数
class DashSpec:
    NORMAL_SPEED = 5.0
    DASH_SPEED = 10.0
    DASH_DURATION = 120
    DASH_COOLDOWN = 45

# アドバタイズモードパッチクラス
class AdvertiseModeImprover:
    """アドバタイズモードを改善するクラス"""
    
    def __init__(self, main_module_name="main"):
        """初期化"""
        self.main_module_name = main_module_name
        self.patches_applied = False
        
        # メインモジュールを動的にインポート
        try:
            self.main_module = __import__(self.main_module_name)
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
        original_update_advertise_movement = self.main_module.Player.update_advertise_movement
        original_update_advertise_movement_visual = self.main_module.Player.update_advertise_movement_visual
        
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
            
            # 戦略の周期的な変更 (約3秒ごと)
            if self_player._strategy_timer - self_player._last_strategy_change > 180:
                strategies = ['aggressive', 'defensive', 'balanced', 'flanking']
                weights = [0.25, 0.35, 0.3, 0.1]  # 防御的な戦略を少し優先
                self_player._current_strategy = random.choices(strategies, weights=weights)[0]
                self_player._last_strategy_change = self_player._strategy_timer
                print(f"戦略変更: {self_player._current_strategy}")
            
            # 危険な敵を見つける（オリジナルの関数を使用）
            dangerous_enemies = self_player.find_dangerous_enemies(enemies)
            
            # 敵がいない場合は元の動きを使用
            if not enemies or not dangerous_enemies:
                return original_update_advertise_movement(self_player, enemies)
            
            # 現在の戦略に基づいて行動
            if self_player._current_strategy == 'defensive':
                return self._defensive_movement(self_player, dangerous_enemies, enemies)
            elif self_player._current_strategy == 'aggressive':
                return self._aggressive_movement(self_player, dangerous_enemies, enemies)
            elif self_player._current_strategy == 'flanking':
                return self._flanking_movement(self_player, dangerous_enemies, enemies)
            else:  # balanced
                return self._balanced_movement(self_player, dangerous_enemies, enemies)
        
        def _defensive_movement(self_player, dangerous_enemies, all_enemies):
            """防御的な動き - 敵から離れる"""
            # 最も危険な敵
            most_dangerous = dangerous_enemies[0]
            
            # 敵から離れる方向へのベクトル
            dx = self_player.x - most_dangerous.x
            dy = self_player.y - most_dangerous.y
            
            # 正規化
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                dx = dx / distance * self_player.max_speed
                dy = dy / distance * self_player.max_speed
            
            # 画面の端に近づきすぎないように調整
            screen_width = self_player.game_width if hasattr(self_player, 'game_width') else 800
            screen_height = self_player.game_height if hasattr(self_player, 'game_height') else 600
            
            # 画面の端からの距離を計算
            border = 100  # 画面の端から離す距離
            left_dist = self_player.x - border
            right_dist = screen_width - border - self_player.x
            top_dist = self_player.y - border
            bottom_dist = screen_height - border - self_player.y
            
            # 画面の端に近づきすぎている場合、方向を調整
            if left_dist < 0:
                dx = max(dx, -dx)  # 右向きの力を加える
            if right_dist < 0:
                dx = min(dx, -dx)  # 左向きの力を加える
            if top_dist < 0:
                dy = max(dy, -dy)  # 下向きの力を加える
            if bottom_dist < 0:
                dy = min(dy, -dy)  # 上向きの力を加える
            
            # 振動を防止するための処理
            if hasattr(self_player, '_last_position_change'):
                last_dx, last_dy = self_player._last_position_change
                
                # 前回と同じ方向に動いているかチェック
                same_direction = (dx * last_dx > 0 and dy * last_dy > 0)
                
                if same_direction:
                    self_player._consecutive_same_direction += 1
                else:
                    self_player._consecutive_same_direction = 0
                
                # あまりに頻繁に方向転換する場合、前の方向を維持
                if self_player._consecutive_same_direction < 3 and not same_direction:
                    dx = 0.7 * dx + 0.3 * last_dx
                    dy = 0.7 * dy + 0.3 * last_dy
            
            # 前回の方向を保存
            self_player._last_position_change = (dx, dy)
            
            # ダッシュを使うかどうかの判断
            should_dash = distance < 150 and self_player.heat < self_player.max_heat * 0.8
            
            # 移動処理
            keys = {}
            if dx < -0.5:
                keys['left'] = True
            elif dx > 0.5:
                keys['right'] = True
            if dy < -0.5:
                keys['up'] = True
            elif dy > 0.5:
                keys['down'] = True
            
            # ダッシュの設定
            if should_dash:
                keys['shift'] = True
            
            # プレイヤー移動用の関数を呼び出す
            self_player.move(keys)
        
        def _aggressive_movement(self_player, dangerous_enemies, all_enemies):
            """攻撃的な動き - 敵に近づく"""
            # 最も近い敵または弱い敵を選択
            target_enemy = None
            min_health = float('inf')
            
            for enemy in all_enemies:
                if not enemy.is_defeated and enemy.health < min_health:
                    min_health = enemy.health
                    target_enemy = enemy
            
            if not target_enemy and all_enemies:
                target_enemy = all_enemies[0]
            
            if not target_enemy:
                return _balanced_movement(self_player, dangerous_enemies, all_enemies)
            
            # 敵に向かうベクトル
            dx = target_enemy.x - self_player.x
            dy = target_enemy.y - self_player.y
            
            # 正規化
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                dx = dx / distance * self_player.max_speed
                dy = dy / distance * self_player.max_speed
            
            # 近すぎる場合は適切な距離を維持
            if distance < 100:
                dx = -dx
                dy = -dy
            
            # 振動防止処理
            if hasattr(self_player, '_last_position_change'):
                last_dx, last_dy = self_player._last_position_change
                
                # 前回と同じ方向に動いているかチェック
                same_direction = (dx * last_dx > 0 and dy * last_dy > 0)
                
                if same_direction:
                    self_player._consecutive_same_direction += 1
                else:
                    self_player._consecutive_same_direction = 0
                
                # あまりに頻繁に方向転換する場合、前の方向を維持
                if self_player._consecutive_same_direction < 3 and not same_direction:
                    dx = 0.7 * dx + 0.3 * last_dx
                    dy = 0.7 * dy + 0.3 * last_dy
            
            # 前回の方向を保存
            self_player._last_position_change = (dx, dy)
            
            # ダッシュを使うかどうかの判断
            should_dash = 150 < distance < 300 and self_player.heat < self_player.max_heat * 0.6
            
            # 移動処理
            keys = {}
            if dx < -0.5:
                keys['left'] = True
            elif dx > 0.5:
                keys['right'] = True
            if dy < -0.5:
                keys['up'] = True
            elif dy > 0.5:
                keys['down'] = True
            
            # ダッシュの設定
            if should_dash:
                keys['shift'] = True
            
            # プレイヤー移動用の関数を呼び出す
            self_player.move(keys)
        
        def _flanking_movement(self_player, dangerous_enemies, all_enemies):
            """側面移動 - 敵の側面に回り込む"""
            if not dangerous_enemies:
                return _balanced_movement(self_player, dangerous_enemies, all_enemies)
            
            # 最も危険な敵
            most_dangerous = dangerous_enemies[0]
            
            # 敵からの相対位置
            dx = self_player.x - most_dangerous.x
            dy = self_player.y - most_dangerous.y
            
            # 側面に回り込むベクトルを計算（元のベクトルを90度回転）
            flanking_dx = -dy
            flanking_dy = dx
            
            # ランダムに左右どちらに回り込むかを決定
            if random.random() < 0.5:
                flanking_dx = -flanking_dx
                flanking_dy = -flanking_dy
            
            # 正規化
            distance = math.sqrt(flanking_dx*flanking_dx + flanking_dy*flanking_dy)
            if distance > 0:
                flanking_dx = flanking_dx / distance * self_player.max_speed
                flanking_dy = flanking_dy / distance * self_player.max_speed
            
            # 画面の外に出ないように調整
            screen_width = self_player.game_width if hasattr(self_player, 'game_width') else 800
            screen_height = self_player.game_height if hasattr(self_player, 'game_height') else 600
            
            # 予測位置が画面外になる場合は逆方向に
            predicted_x = self_player.x + flanking_dx * 10
            predicted_y = self_player.y + flanking_dy * 10
            
            if predicted_x < 50 or predicted_x > screen_width - 50 or predicted_y < 50 or predicted_y > screen_height - 50:
                flanking_dx = -flanking_dx
                flanking_dy = -flanking_dy
            
            # 振動防止処理
            if hasattr(self_player, '_last_position_change'):
                last_dx, last_dy = self_player._last_position_change
                
                # あまりに頻繁に方向転換する場合、前の方向を維持
                flanking_dx = 0.7 * flanking_dx + 0.3 * last_dx
                flanking_dy = 0.7 * flanking_dy + 0.3 * last_dy
            
            # 前回の方向を保存
            self_player._last_position_change = (flanking_dx, flanking_dy)
            
            # ダッシュを使うかどうかの判断
            should_dash = random.random() < 0.3 and self_player.heat < self_player.max_heat * 0.7
            
            # 移動処理
            keys = {}
            if flanking_dx < -0.5:
                keys['left'] = True
            elif flanking_dx > 0.5:
                keys['right'] = True
            if flanking_dy < -0.5:
                keys['up'] = True
            elif flanking_dy > 0.5:
                keys['down'] = True
            
            # ダッシュの設定
            if should_dash:
                keys['shift'] = True
            
            # プレイヤー移動用の関数を呼び出す
            self_player.move(keys)
        
        def _balanced_movement(self_player, dangerous_enemies, all_enemies):
            """バランスの取れた動き - 状況に応じて戦略を変える"""
            # 敵の数や位置、プレイヤーの状態に応じて戦略を変える
            
            # 敵が多い場合は防御的に
            if len(all_enemies) > 3:
                return _defensive_movement(self_player, dangerous_enemies, all_enemies)
            
            # 体力が低い場合は防御的に
            if hasattr(self_player, 'health') and self_player.health < 30:
                return _defensive_movement(self_player, dangerous_enemies, all_enemies)
            
            # 周期的に戦略を変える（時間経過で行動パターンを変える）
            time_factor = (self_player._strategy_timer % 300) / 300.0
            
            if time_factor < 0.4:
                # 40%の時間は攻撃的に
                return _aggressive_movement(self_player, dangerous_enemies, all_enemies)
            elif time_factor < 0.7:
                # 30%の時間は側面に回り込む
                return _flanking_movement(self_player, dangerous_enemies, all_enemies)
            else:
                # 30%の時間は防御的に
                return _defensive_movement(self_player, dangerous_enemies, all_enemies)
        
        # メソッドをパッチ
        self.main_module.Player.update_advertise_movement = improved_update_advertise_movement
        self.main_module.Player._defensive_movement = _defensive_movement
        self.main_module.Player._aggressive_movement = _aggressive_movement
        self.main_module.Player._flanking_movement = _flanking_movement
        self.main_module.Player._balanced_movement = _balanced_movement
        
        # ビジュアル版の移動更新も同様にパッチ
        self.main_module.Player.update_advertise_movement_visual = improved_update_advertise_movement
    
    def _patch_find_dangerous_enemies(self):
        """危険な敵を検出する関数をパッチ"""
        # オリジナルの関数を保存
        original_find_dangerous_enemies = self.main_module.Player.find_dangerous_enemies
        
        def improved_find_dangerous_enemies(self_player, enemies):
            """危険な敵をより正確に検出する改善版"""
            if not enemies:
                return []
            
            # 自分の位置
            px, py = self_player.x, self_player.y
            
            # 各敵の危険度を計算
            dangerous_scores = []
            
            for enemy in enemies:
                if enemy.is_defeated:
                    continue
                
                # 距離の計算
                dx = enemy.x - px
                dy = enemy.y - py
                distance = math.sqrt(dx*dx + dy*dy)
                
                # 距離が0の場合は除外（異常値）
                if distance == 0:
                    continue
                
                # 敵の速度ベクトル (移動方向)
                enemy_dx = getattr(enemy, 'direction_x', 0)
                enemy_dy = getattr(enemy, 'direction_y', 0)
                
                # 敵のタイプに基づいた基本危険度
                base_danger = 1.0
                if hasattr(enemy, 'enemy_type'):
                    if enemy.enemy_type == 'boss':
                        base_danger = 2.0
                    elif enemy.enemy_type == 'fast':
                        base_danger = 1.5
                
                # 接近速度（敵の移動ベクトルとプレイヤーへの方向ベクトルの内積）
                approach_vector = [-dx/distance, -dy/distance]
                approach_speed = enemy_dx * approach_vector[0] + enemy_dy * approach_vector[1]
                
                # 距離に基づく危険度（近いほど危険）
                distance_factor = 500 / max(distance, 50)
                
                # 接近速度に基づく危険度（こちらに向かってくるほど危険）
                approach_factor = max(0, approach_speed) * 2 + 1
                
                # 最終的な危険度
                danger_score = base_danger * distance_factor * approach_factor
                
                dangerous_scores.append((enemy, danger_score))
            
            # 危険度でソート
            dangerous_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 危険な敵のリストを返す（上位3つまで）
            return [enemy for enemy, _ in dangerous_scores[:3]]
        
        # メソッドをパッチ
        self.main_module.Player.find_dangerous_enemies = improved_find_dangerous_enemies
    
    def _patch_perform_advertise_action(self):
        """アドバタイズモードのアクション処理をパッチ"""
        # オリジナルの関数を保存
        original_perform_advertise_action = self.main_module.Player.perform_advertise_action
        
        def improved_perform_advertise_action(self_player, enemies, bullets):
            """改善されたアドバタイズモードのアクション処理"""
            # 戦略タイマーの更新
            if not hasattr(self_player, '_action_timer'):
                self_player._action_timer = 0
                self_player._last_fire_time = 0
            
            self_player._action_timer += 1
            
            # 武器の発射判断を改善
            can_fire = self_player.can_fire()
            
            # 最も近い敵を見つける
            nearest_enemy = None
            min_distance = float('inf')
            
            for enemy in enemies:
                if enemy.is_defeated:
                    continue
                
                dx = enemy.x - self_player.x
                dy = enemy.y - self_player.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_enemy = enemy
            
            # 敵がいなければオリジナルの処理を実行
            if not nearest_enemy:
                return original_perform_advertise_action(self_player, enemies, bullets)
            
            # 敵の方向へ発射
            should_fire = False
            
            # 敵との距離に基づいた発射判断
            fire_probability = 0.2  # 基本確率
            
            # 距離による調整（近いほど高確率）
            if min_distance < 150:
                fire_probability = 0.9
            elif min_distance < 300:
                fire_probability = 0.6
            elif min_distance < 450:
                fire_probability = 0.3
            
            # 前回の発射からの経過時間による調整
            # (武器のクールダウンが終わってからの経過時間に応じて確率上昇)
            time_since_last_fire = self_player._action_timer - self_player._last_fire_time
            if time_since_last_fire > 60:  # 1秒以上経過
                fire_probability += min(0.4, (time_since_last_fire - 60) * 0.01)
            
            # チャージ攻撃の判断
            should_charge = min_distance > 300 and random.random() < 0.3
            
            # 発射判断
            if can_fire and random.random() < fire_probability:
                should_fire = True
                self_player._last_fire_time = self_player._action_timer
            
            # アクションの実行
            keys = {}
            
            # 発射キー
            if should_fire:
                keys['z'] = True
            
            # チャージキー
            if should_charge and hasattr(self_player, 'charge_level') and self_player.charge_level < 3:
                keys['x'] = True
            
            # 敵の方向に応じて向き調整
            if nearest_enemy.x < self_player.x:
                self_player.facing_right = False
            else:
                self_player.facing_right = True
            
            # プレイヤーの武器更新関数を呼び出す
            if hasattr(self_player, 'update_weapon'):
                self_player.update_weapon(keys)
            
            # 武器の発射
            if should_fire and hasattr(self_player, 'fire'):
                bullet_type = getattr(self_player, 'current_weapon', 'beam_rifle')
                self_player.fire()
                
                # 発射エフェクト等があれば実行
                if hasattr(self_player, 'fire_effects'):
                    self_player.fire_effects()
            
            return True
        
        # メソッドをパッチ
        self.main_module.Player.perform_advertise_action = improved_perform_advertise_action
    
    def _add_strategy_parameters(self):
        """プレイヤークラスに戦略パラメータを追加"""
        # プレイヤーのinit関数をパッチ
        original_init = self.main_module.Player.__init__
        
        def patched_init(self_player, *args, **kwargs):
            # オリジナルの初期化を呼び出す
            original_init(self_player, *args, **kwargs)
            
            # 戦略パラメータの追加
            self_player._strategy_timer = 0
            self_player._current_strategy = 'balanced'
            self_player._last_position_change = (0, 0)
            self_player._consecutive_same_direction = 0
            self_player._last_strategy_change = 0
            self_player._action_timer = 0
            self_player._last_fire_time = 0
            
            # ゲーム画面サイズの保存（境界チェック用）
            self_player.game_width = 800
            self_player.game_height = 600
        
        # メソッドをパッチ
        self.main_module.Player.__init__ = patched_init
    
    def run_improved_advertise_mode(self, duration=30):
        """改善されたアドバタイズモードを実行"""
        import pygame
        
        # パッチを適用
        self.apply_patches()
        
        # pygameの初期化
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("改善されたアドバタイズモード")
        clock = pygame.time.Clock()
        
        # ゲームリセット
        if hasattr(self.main_module, 'reset_game'):
            self.main_module.reset_game()
        
        # プレイヤーのアドバタイズモードを有効化
        if hasattr(self.main_module, 'player') and hasattr(self.main_module.player, 'toggle_advertise_mode'):
            self.main_module.player.toggle_advertise_mode()
            print("アドバタイズモードを有効化しました")
        
        # 初期敵の生成
        if hasattr(self.main_module, 'enemies') and len(self.main_module.enemies) == 0:
            for _ in range(5):
                x = random.randint(100, 700)
                y = random.randint(100, 400)
                if hasattr(self.main_module, 'Enemy'):
                    enemy = self.main_module.Enemy()
                    enemy.x = x
                    enemy.y = y
                    self.main_module.enemies.append(enemy)
        
        # メインループ
        running = True
        start_time = time.time()
        
        while running and time.time() - start_time < duration:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # ゲーム状態の更新
            if hasattr(self.main_module, 'update_game_state'):
                self.main_module.update_game_state()
            
            # 画面描画
            screen.fill((0, 0, 0))
            
            # 各オブジェクトの描画
            if hasattr(self.main_module, 'draw_game'):
                self.main_module.draw_game(screen)
            
            # 戦略情報の表示
            if hasattr(self.main_module, 'player') and hasattr(self.main_module.player, '_current_strategy'):
                font = pygame.font.SysFont(None, 24)
                strategy_text = f"戦略: {self.main_module.player._current_strategy}"
                text_surface = font.render(strategy_text, True, (255, 255, 255))
                screen.blit(text_surface, (10, 10))
            
            pygame.display.flip()
            
            # フレームレート制御
            clock.tick(60)
        
        # 終了処理
        pygame.quit()


def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='アドバタイズモード改善ツール')
    parser.add_argument('--module', default='main', help='メインモジュール名')
    parser.add_argument('--test', action='store_true', help='改善されたアドバタイズモードをテスト実行する')
    parser.add_argument('--duration', type=int, default=30, help='テスト実行の時間（秒）')
    
    args = parser.parse_args()
    
    improver = AdvertiseModeImprover(main_module_name=args.module)
    
    if args.test:
        improver.run_improved_advertise_mode(duration=args.duration)
    else:
        improver.apply_patches()
        print("パッチを適用しました。アドバタイズモードのコードを改善しました。")
        print("テスト実行するには --test オプションを使用してください。")


if __name__ == '__main__':
    main() 
アドバタイズモード改善ツール

アドバタイズモード（自動デモプレイ）の振る舞いを改善し、より自然な動きを実現します。
特に、敵から適切に回避する動作や無駄な振動を防ぐ処理を追加します。
"""

import sys
import os
import time
import math
import random
from pathlib import Path

# ゲームのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ダッシュ関連の定数
class DashSpec:
    NORMAL_SPEED = 5.0
    DASH_SPEED = 10.0
    DASH_DURATION = 120
    DASH_COOLDOWN = 45

# アドバタイズモードパッチクラス
class AdvertiseModeImprover:
    """アドバタイズモードを改善するクラス"""
    
    def __init__(self, main_module_name="main"):
        """初期化"""
        self.main_module_name = main_module_name
        self.patches_applied = False
        
        # メインモジュールを動的にインポート
        try:
            self.main_module = __import__(self.main_module_name)
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
        original_update_advertise_movement = self.main_module.Player.update_advertise_movement
        original_update_advertise_movement_visual = self.main_module.Player.update_advertise_movement_visual
        
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
            
            # 戦略の周期的な変更 (約3秒ごと)
            if self_player._strategy_timer - self_player._last_strategy_change > 180:
                strategies = ['aggressive', 'defensive', 'balanced', 'flanking']
                weights = [0.25, 0.35, 0.3, 0.1]  # 防御的な戦略を少し優先
                self_player._current_strategy = random.choices(strategies, weights=weights)[0]
                self_player._last_strategy_change = self_player._strategy_timer
                print(f"戦略変更: {self_player._current_strategy}")
            
            # 危険な敵を見つける（オリジナルの関数を使用）
            dangerous_enemies = self_player.find_dangerous_enemies(enemies)
            
            # 敵がいない場合は元の動きを使用
            if not enemies or not dangerous_enemies:
                return original_update_advertise_movement(self_player, enemies)
            
            # 現在の戦略に基づいて行動
            if self_player._current_strategy == 'defensive':
                return self._defensive_movement(self_player, dangerous_enemies, enemies)
            elif self_player._current_strategy == 'aggressive':
                return self._aggressive_movement(self_player, dangerous_enemies, enemies)
            elif self_player._current_strategy == 'flanking':
                return self._flanking_movement(self_player, dangerous_enemies, enemies)
            else:  # balanced
                return self._balanced_movement(self_player, dangerous_enemies, enemies)
        
        def _defensive_movement(self_player, dangerous_enemies, all_enemies):
            """防御的な動き - 敵から離れる"""
            # 最も危険な敵
            most_dangerous = dangerous_enemies[0]
            
            # 敵から離れる方向へのベクトル
            dx = self_player.x - most_dangerous.x
            dy = self_player.y - most_dangerous.y
            
            # 正規化
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                dx = dx / distance * self_player.max_speed
                dy = dy / distance * self_player.max_speed
            
            # 画面の端に近づきすぎないように調整
            screen_width = self_player.game_width if hasattr(self_player, 'game_width') else 800
            screen_height = self_player.game_height if hasattr(self_player, 'game_height') else 600
            
            # 画面の端からの距離を計算
            border = 100  # 画面の端から離す距離
            left_dist = self_player.x - border
            right_dist = screen_width - border - self_player.x
            top_dist = self_player.y - border
            bottom_dist = screen_height - border - self_player.y
            
            # 画面の端に近づきすぎている場合、方向を調整
            if left_dist < 0:
                dx = max(dx, -dx)  # 右向きの力を加える
            if right_dist < 0:
                dx = min(dx, -dx)  # 左向きの力を加える
            if top_dist < 0:
                dy = max(dy, -dy)  # 下向きの力を加える
            if bottom_dist < 0:
                dy = min(dy, -dy)  # 上向きの力を加える
            
            # 振動を防止するための処理
            if hasattr(self_player, '_last_position_change'):
                last_dx, last_dy = self_player._last_position_change
                
                # 前回と同じ方向に動いているかチェック
                same_direction = (dx * last_dx > 0 and dy * last_dy > 0)
                
                if same_direction:
                    self_player._consecutive_same_direction += 1
                else:
                    self_player._consecutive_same_direction = 0
                
                # あまりに頻繁に方向転換する場合、前の方向を維持
                if self_player._consecutive_same_direction < 3 and not same_direction:
                    dx = 0.7 * dx + 0.3 * last_dx
                    dy = 0.7 * dy + 0.3 * last_dy
            
            # 前回の方向を保存
            self_player._last_position_change = (dx, dy)
            
            # ダッシュを使うかどうかの判断
            should_dash = distance < 150 and self_player.heat < self_player.max_heat * 0.8
            
            # 移動処理
            keys = {}
            if dx < -0.5:
                keys['left'] = True
            elif dx > 0.5:
                keys['right'] = True
            if dy < -0.5:
                keys['up'] = True
            elif dy > 0.5:
                keys['down'] = True
            
            # ダッシュの設定
            if should_dash:
                keys['shift'] = True
            
            # プレイヤー移動用の関数を呼び出す
            self_player.move(keys)
        
        def _aggressive_movement(self_player, dangerous_enemies, all_enemies):
            """攻撃的な動き - 敵に近づく"""
            # 最も近い敵または弱い敵を選択
            target_enemy = None
            min_health = float('inf')
            
            for enemy in all_enemies:
                if not enemy.is_defeated and enemy.health < min_health:
                    min_health = enemy.health
                    target_enemy = enemy
            
            if not target_enemy and all_enemies:
                target_enemy = all_enemies[0]
            
            if not target_enemy:
                return _balanced_movement(self_player, dangerous_enemies, all_enemies)
            
            # 敵に向かうベクトル
            dx = target_enemy.x - self_player.x
            dy = target_enemy.y - self_player.y
            
            # 正規化
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                dx = dx / distance * self_player.max_speed
                dy = dy / distance * self_player.max_speed
            
            # 近すぎる場合は適切な距離を維持
            if distance < 100:
                dx = -dx
                dy = -dy
            
            # 振動防止処理
            if hasattr(self_player, '_last_position_change'):
                last_dx, last_dy = self_player._last_position_change
                
                # 前回と同じ方向に動いているかチェック
                same_direction = (dx * last_dx > 0 and dy * last_dy > 0)
                
                if same_direction:
                    self_player._consecutive_same_direction += 1
                else:
                    self_player._consecutive_same_direction = 0
                
                # あまりに頻繁に方向転換する場合、前の方向を維持
                if self_player._consecutive_same_direction < 3 and not same_direction:
                    dx = 0.7 * dx + 0.3 * last_dx
                    dy = 0.7 * dy + 0.3 * last_dy
            
            # 前回の方向を保存
            self_player._last_position_change = (dx, dy)
            
            # ダッシュを使うかどうかの判断
            should_dash = 150 < distance < 300 and self_player.heat < self_player.max_heat * 0.6
            
            # 移動処理
            keys = {}
            if dx < -0.5:
                keys['left'] = True
            elif dx > 0.5:
                keys['right'] = True
            if dy < -0.5:
                keys['up'] = True
            elif dy > 0.5:
                keys['down'] = True
            
            # ダッシュの設定
            if should_dash:
                keys['shift'] = True
            
            # プレイヤー移動用の関数を呼び出す
            self_player.move(keys)
        
        def _flanking_movement(self_player, dangerous_enemies, all_enemies):
            """側面移動 - 敵の側面に回り込む"""
            if not dangerous_enemies:
                return _balanced_movement(self_player, dangerous_enemies, all_enemies)
            
            # 最も危険な敵
            most_dangerous = dangerous_enemies[0]
            
            # 敵からの相対位置
            dx = self_player.x - most_dangerous.x
            dy = self_player.y - most_dangerous.y
            
            # 側面に回り込むベクトルを計算（元のベクトルを90度回転）
            flanking_dx = -dy
            flanking_dy = dx
            
            # ランダムに左右どちらに回り込むかを決定
            if random.random() < 0.5:
                flanking_dx = -flanking_dx
                flanking_dy = -flanking_dy
            
            # 正規化
            distance = math.sqrt(flanking_dx*flanking_dx + flanking_dy*flanking_dy)
            if distance > 0:
                flanking_dx = flanking_dx / distance * self_player.max_speed
                flanking_dy = flanking_dy / distance * self_player.max_speed
            
            # 画面の外に出ないように調整
            screen_width = self_player.game_width if hasattr(self_player, 'game_width') else 800
            screen_height = self_player.game_height if hasattr(self_player, 'game_height') else 600
            
            # 予測位置が画面外になる場合は逆方向に
            predicted_x = self_player.x + flanking_dx * 10
            predicted_y = self_player.y + flanking_dy * 10
            
            if predicted_x < 50 or predicted_x > screen_width - 50 or predicted_y < 50 or predicted_y > screen_height - 50:
                flanking_dx = -flanking_dx
                flanking_dy = -flanking_dy
            
            # 振動防止処理
            if hasattr(self_player, '_last_position_change'):
                last_dx, last_dy = self_player._last_position_change
                
                # あまりに頻繁に方向転換する場合、前の方向を維持
                flanking_dx = 0.7 * flanking_dx + 0.3 * last_dx
                flanking_dy = 0.7 * flanking_dy + 0.3 * last_dy
            
            # 前回の方向を保存
            self_player._last_position_change = (flanking_dx, flanking_dy)
            
            # ダッシュを使うかどうかの判断
            should_dash = random.random() < 0.3 and self_player.heat < self_player.max_heat * 0.7
            
            # 移動処理
            keys = {}
            if flanking_dx < -0.5:
                keys['left'] = True
            elif flanking_dx > 0.5:
                keys['right'] = True
            if flanking_dy < -0.5:
                keys['up'] = True
            elif flanking_dy > 0.5:
                keys['down'] = True
            
            # ダッシュの設定
            if should_dash:
                keys['shift'] = True
            
            # プレイヤー移動用の関数を呼び出す
            self_player.move(keys)
        
        def _balanced_movement(self_player, dangerous_enemies, all_enemies):
            """バランスの取れた動き - 状況に応じて戦略を変える"""
            # 敵の数や位置、プレイヤーの状態に応じて戦略を変える
            
            # 敵が多い場合は防御的に
            if len(all_enemies) > 3:
                return _defensive_movement(self_player, dangerous_enemies, all_enemies)
            
            # 体力が低い場合は防御的に
            if hasattr(self_player, 'health') and self_player.health < 30:
                return _defensive_movement(self_player, dangerous_enemies, all_enemies)
            
            # 周期的に戦略を変える（時間経過で行動パターンを変える）
            time_factor = (self_player._strategy_timer % 300) / 300.0
            
            if time_factor < 0.4:
                # 40%の時間は攻撃的に
                return _aggressive_movement(self_player, dangerous_enemies, all_enemies)
            elif time_factor < 0.7:
                # 30%の時間は側面に回り込む
                return _flanking_movement(self_player, dangerous_enemies, all_enemies)
            else:
                # 30%の時間は防御的に
                return _defensive_movement(self_player, dangerous_enemies, all_enemies)
        
        # メソッドをパッチ
        self.main_module.Player.update_advertise_movement = improved_update_advertise_movement
        self.main_module.Player._defensive_movement = _defensive_movement
        self.main_module.Player._aggressive_movement = _aggressive_movement
        self.main_module.Player._flanking_movement = _flanking_movement
        self.main_module.Player._balanced_movement = _balanced_movement
        
        # ビジュアル版の移動更新も同様にパッチ
        self.main_module.Player.update_advertise_movement_visual = improved_update_advertise_movement
    
    def _patch_find_dangerous_enemies(self):
        """危険な敵を検出する関数をパッチ"""
        # オリジナルの関数を保存
        original_find_dangerous_enemies = self.main_module.Player.find_dangerous_enemies
        
        def improved_find_dangerous_enemies(self_player, enemies):
            """危険な敵をより正確に検出する改善版"""
            if not enemies:
                return []
            
            # 自分の位置
            px, py = self_player.x, self_player.y
            
            # 各敵の危険度を計算
            dangerous_scores = []
            
            for enemy in enemies:
                if enemy.is_defeated:
                    continue
                
                # 距離の計算
                dx = enemy.x - px
                dy = enemy.y - py
                distance = math.sqrt(dx*dx + dy*dy)
                
                # 距離が0の場合は除外（異常値）
                if distance == 0:
                    continue
                
                # 敵の速度ベクトル (移動方向)
                enemy_dx = getattr(enemy, 'direction_x', 0)
                enemy_dy = getattr(enemy, 'direction_y', 0)
                
                # 敵のタイプに基づいた基本危険度
                base_danger = 1.0
                if hasattr(enemy, 'enemy_type'):
                    if enemy.enemy_type == 'boss':
                        base_danger = 2.0
                    elif enemy.enemy_type == 'fast':
                        base_danger = 1.5
                
                # 接近速度（敵の移動ベクトルとプレイヤーへの方向ベクトルの内積）
                approach_vector = [-dx/distance, -dy/distance]
                approach_speed = enemy_dx * approach_vector[0] + enemy_dy * approach_vector[1]
                
                # 距離に基づく危険度（近いほど危険）
                distance_factor = 500 / max(distance, 50)
                
                # 接近速度に基づく危険度（こちらに向かってくるほど危険）
                approach_factor = max(0, approach_speed) * 2 + 1
                
                # 最終的な危険度
                danger_score = base_danger * distance_factor * approach_factor
                
                dangerous_scores.append((enemy, danger_score))
            
            # 危険度でソート
            dangerous_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 危険な敵のリストを返す（上位3つまで）
            return [enemy for enemy, _ in dangerous_scores[:3]]
        
        # メソッドをパッチ
        self.main_module.Player.find_dangerous_enemies = improved_find_dangerous_enemies
    
    def _patch_perform_advertise_action(self):
        """アドバタイズモードのアクション処理をパッチ"""
        # オリジナルの関数を保存
        original_perform_advertise_action = self.main_module.Player.perform_advertise_action
        
        def improved_perform_advertise_action(self_player, enemies, bullets):
            """改善されたアドバタイズモードのアクション処理"""
            # 戦略タイマーの更新
            if not hasattr(self_player, '_action_timer'):
                self_player._action_timer = 0
                self_player._last_fire_time = 0
            
            self_player._action_timer += 1
            
            # 武器の発射判断を改善
            can_fire = self_player.can_fire()
            
            # 最も近い敵を見つける
            nearest_enemy = None
            min_distance = float('inf')
            
            for enemy in enemies:
                if enemy.is_defeated:
                    continue
                
                dx = enemy.x - self_player.x
                dy = enemy.y - self_player.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_enemy = enemy
            
            # 敵がいなければオリジナルの処理を実行
            if not nearest_enemy:
                return original_perform_advertise_action(self_player, enemies, bullets)
            
            # 敵の方向へ発射
            should_fire = False
            
            # 敵との距離に基づいた発射判断
            fire_probability = 0.2  # 基本確率
            
            # 距離による調整（近いほど高確率）
            if min_distance < 150:
                fire_probability = 0.9
            elif min_distance < 300:
                fire_probability = 0.6
            elif min_distance < 450:
                fire_probability = 0.3
            
            # 前回の発射からの経過時間による調整
            # (武器のクールダウンが終わってからの経過時間に応じて確率上昇)
            time_since_last_fire = self_player._action_timer - self_player._last_fire_time
            if time_since_last_fire > 60:  # 1秒以上経過
                fire_probability += min(0.4, (time_since_last_fire - 60) * 0.01)
            
            # チャージ攻撃の判断
            should_charge = min_distance > 300 and random.random() < 0.3
            
            # 発射判断
            if can_fire and random.random() < fire_probability:
                should_fire = True
                self_player._last_fire_time = self_player._action_timer
            
            # アクションの実行
            keys = {}
            
            # 発射キー
            if should_fire:
                keys['z'] = True
            
            # チャージキー
            if should_charge and hasattr(self_player, 'charge_level') and self_player.charge_level < 3:
                keys['x'] = True
            
            # 敵の方向に応じて向き調整
            if nearest_enemy.x < self_player.x:
                self_player.facing_right = False
            else:
                self_player.facing_right = True
            
            # プレイヤーの武器更新関数を呼び出す
            if hasattr(self_player, 'update_weapon'):
                self_player.update_weapon(keys)
            
            # 武器の発射
            if should_fire and hasattr(self_player, 'fire'):
                bullet_type = getattr(self_player, 'current_weapon', 'beam_rifle')
                self_player.fire()
                
                # 発射エフェクト等があれば実行
                if hasattr(self_player, 'fire_effects'):
                    self_player.fire_effects()
            
            return True
        
        # メソッドをパッチ
        self.main_module.Player.perform_advertise_action = improved_perform_advertise_action
    
    def _add_strategy_parameters(self):
        """プレイヤークラスに戦略パラメータを追加"""
        # プレイヤーのinit関数をパッチ
        original_init = self.main_module.Player.__init__
        
        def patched_init(self_player, *args, **kwargs):
            # オリジナルの初期化を呼び出す
            original_init(self_player, *args, **kwargs)
            
            # 戦略パラメータの追加
            self_player._strategy_timer = 0
            self_player._current_strategy = 'balanced'
            self_player._last_position_change = (0, 0)
            self_player._consecutive_same_direction = 0
            self_player._last_strategy_change = 0
            self_player._action_timer = 0
            self_player._last_fire_time = 0
            
            # ゲーム画面サイズの保存（境界チェック用）
            self_player.game_width = 800
            self_player.game_height = 600
        
        # メソッドをパッチ
        self.main_module.Player.__init__ = patched_init
    
    def run_improved_advertise_mode(self, duration=30):
        """改善されたアドバタイズモードを実行"""
        import pygame
        
        # パッチを適用
        self.apply_patches()
        
        # pygameの初期化
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("改善されたアドバタイズモード")
        clock = pygame.time.Clock()
        
        # ゲームリセット
        if hasattr(self.main_module, 'reset_game'):
            self.main_module.reset_game()
        
        # プレイヤーのアドバタイズモードを有効化
        if hasattr(self.main_module, 'player') and hasattr(self.main_module.player, 'toggle_advertise_mode'):
            self.main_module.player.toggle_advertise_mode()
            print("アドバタイズモードを有効化しました")
        
        # 初期敵の生成
        if hasattr(self.main_module, 'enemies') and len(self.main_module.enemies) == 0:
            for _ in range(5):
                x = random.randint(100, 700)
                y = random.randint(100, 400)
                if hasattr(self.main_module, 'Enemy'):
                    enemy = self.main_module.Enemy()
                    enemy.x = x
                    enemy.y = y
                    self.main_module.enemies.append(enemy)
        
        # メインループ
        running = True
        start_time = time.time()
        
        while running and time.time() - start_time < duration:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # ゲーム状態の更新
            if hasattr(self.main_module, 'update_game_state'):
                self.main_module.update_game_state()
            
            # 画面描画
            screen.fill((0, 0, 0))
            
            # 各オブジェクトの描画
            if hasattr(self.main_module, 'draw_game'):
                self.main_module.draw_game(screen)
            
            # 戦略情報の表示
            if hasattr(self.main_module, 'player') and hasattr(self.main_module.player, '_current_strategy'):
                font = pygame.font.SysFont(None, 24)
                strategy_text = f"戦略: {self.main_module.player._current_strategy}"
                text_surface = font.render(strategy_text, True, (255, 255, 255))
                screen.blit(text_surface, (10, 10))
            
            pygame.display.flip()
            
            # フレームレート制御
            clock.tick(60)
        
        # 終了処理
        pygame.quit()


def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='アドバタイズモード改善ツール')
    parser.add_argument('--module', default='main', help='メインモジュール名')
    parser.add_argument('--test', action='store_true', help='改善されたアドバタイズモードをテスト実行する')
    parser.add_argument('--duration', type=int, default=30, help='テスト実行の時間（秒）')
    
    args = parser.parse_args()
    
    improver = AdvertiseModeImprover(main_module_name=args.module)
    
    if args.test:
        improver.run_improved_advertise_mode(duration=args.duration)
    else:
        improver.apply_patches()
        print("パッチを適用しました。アドバタイズモードのコードを改善しました。")
        print("テスト実行するには --test オプションを使用してください。")


if __name__ == '__main__':
    main() 