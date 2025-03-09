import pygame
import math
import random
from src.game.core.dash_spec import DashSpec
from src.game.core.bullet import Bullet, BULLET_TYPES

# 画面設定（オリジナルのmain.pyから取得）
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)

class Player:
    def __init__(self):
        """プレイヤーの初期化"""
        # [SPEC-DASH-101] 基本パラメータ
        self.width = 32
        self.height = 32
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - 100
        self.speed_x = 0
        self.speed_y = 0
        self.max_speed = DashSpec.NORMAL_SPEED
        self.dash_speed = DashSpec.DASH_SPEED
        self.acceleration = DashSpec.ACCELERATION
        self.friction = DashSpec.FRICTION
        
        # プレイヤーの体力
        self.health = 100
        
        # [SPEC-DASH-102] ヒートゲージパラメータ
        self.heat = DashSpec.INITIAL_HEAT
        self.max_heat = DashSpec.MAX_HEAT
        
        # [SPEC-DASH-103] カーブ移動パラメータ
        self.max_turn_rate = DashSpec.MAX_TURN_RATE
        self.movement_angle = 0
        self.target_angle = 0
        self.grip_level = DashSpec.NORMAL_GRIP
        
        # ダッシュ状態管理
        self.is_dashing = False
        self.dash_effects = []
        self.facing_right = True
        
        # 入力バッファ
        self.input_buffer = {'left': False, 'right': False, 'up': False, 'down': False, 'shift': False}
        
        # ロックオン関連
        self.locked_enemy = None
        self.lock_on_range = 350  # ロックオン可能な範囲
        self.lock_changed_cooldown = 0  # ロックオン切り替えのクールダウン
        
        # チャージショット関連
        self.is_charging = False
        self.charge_level = 0
        self.max_charge_level = 1.0  # 最大チャージレベル
        self.charge_speed = 0.02  # チャージ速度
        self.charge_target_position = None
        
        # AIモード用の変数
        self.advertise_mode = True  # デフォルトで有効に変更
        self.advertise_action_timer = 0  # アクションタイマー
        self.advertise_action_interval = 40  # アクションの間隔（フレーム）（60から40に短縮）
        self.advertise_movement_timer = 0  # 移動タイマー
        self.advertise_movement_duration = 120  # 一方向への移動持続時間
        self.advertise_target_x = None  # 移動目標X座標
        self.advertise_target_y = None  # 移動目標Y座標
        self.visual_mode = True  # 画面認識モードをデフォルトで有効
        self.detected_enemies = []  # 画面から検出した敵
        self.detected_safe_zones = []  # 画面から検出した安全地帯
        self.visual_analysis_timer = 0  # 画面分析タイマー
        
        # 必殺技関連
        self.special_gauge = 0.0      # 必殺技ゲージ（0.0～1.0）
        self.max_special_gauge = 1.0  # 最大ゲージ値
        self.special_gain_rate = 0.005  # 敵を倒した時のゲージ上昇率
        self.special_cooldown = 0     # 必殺技クールダウン
        self.special_ready = False    # 必殺技準備完了フラグ
        self.special_activation_time = 0  # 必殺技発動時のタイムスタンプ
        self.special_animation_frames = 90  # 必殺技アニメーションのフレーム数
        
        # ダッシュ関連
        self.dash_speed = 8.0  # 10.0の80%に減速
        self.dash_duration = 120  # フレーム数
        self.dash_cooldown_time = 45  # クールダウン時間（フレーム数）
        self.dash_cooldown = 0  # 現在のクールダウン残り時間
        self.is_dashing = False
        self.was_dashing = False  # 前フレームでダッシュしていたかどうか
        self.dash_effects = []  # ダッシュ時のエフェクト
        
        # その他のパラメータ
        self.hp = 100
        self.max_hp = 100
        
        # 被弾エフェクト関連
        self.damage_effect_time = 0
        self.ring_effects = []
        
        # 武器関連
        self.weapon_cooldown = 0
        self.beam_rifle_cooldown = 0
        self.beam_rifle_cooldown_time = 20  # ビームライフルのクールダウン時間
        self.charge_level = 0
        self.charge_target_position = None
        
        # ドリフト関連
        self.drift_angle = 0      # ドリフト時の角度
        self.drift_power = 0      # ドリフトの強さ
        self.max_drift_angle = 45 # 最大ドリフト角度
        self.drift_recovery = 0.1 # ドリフトからの復帰速度
        self.is_drifting = False
        
        # 慣性とカーブ用のパラメータ
        self.turn_acceleration = 0.01  # 旋回加速度
        self.current_turn_rate = 0  # 現在の旋回速度
        self.movement_angle = 0  # 現在の移動角度（ラジアン）
        self.target_angle = 0  # 目標角度（ラジアン）
        self.grip_level = 1.0    # グリップレベル（1.0が通常）
        
        self.dash_cooldown = 0
        self.dash_duration = 120   # ダッシュ持続時間
        self.dash_cooldown_time = 45  # ダッシュのクールダウン時間
        self.facing_right = True
        self.last_direction = None
        self.is_dashing = False
        
        # 近接攻撃関連
        self.should_melee_attack = False
        self.melee_target = None
        self.melee_cooldown = 0
        
        self.heat = 0           # 現在のヒート値
        self.max_heat = 100     # 最大ヒート値
        self.invincible_time = 0
        self.locked_enemy = None
        self.lock_on_range = 500
        self.charge_start_time = 0
        self.is_charging = False
        self.shot_cooldown = 0
        self.shot_cooldown_time = 10
        self.charge_sound_playing = False
        self.dash_effects = []  # ダッシュエフェクトのリストを追加
  
    def move(self, keys):
        """移動処理
        
        [SPEC-DASH-201] 即時発動
        [SPEC-DASH-202] 継続条件
        [SPEC-DASH-203] ヒート制限
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
        
        # [SPEC-DASH-201] 即時発動
        if dash_requested and not self.is_dashing and self.dash_cooldown <= 0:
            # ヒートが一定以下ならダッシュ発動
            if self.heat < self.max_heat * 0.8:  # [SPEC-DASH-203] ヒート制限
                self.is_dashing = True
                self.dash_duration = 120  # ダッシュ持続時間をリセット
                
                # ダッシュ方向を記録
                if dx != 0 or dy != 0:
                    self.last_direction = (dx, dy)
        
        # [SPEC-DASH-202] 継続条件
        if self.is_dashing:
            # ダッシュ中はヒートが上昇
            self.heat += 0.5
            
            # ヒートが上限に達したらダッシュ終了
            if self.heat >= self.max_heat:
                self.is_dashing = False
                self.dash_cooldown = self.dash_cooldown_time
            
            # ダッシュ持続時間が終了したらダッシュ終了
            self.dash_duration -= 1
            if self.dash_duration <= 0:
                self.is_dashing = False
                self.dash_cooldown = self.dash_cooldown_time
            
            # ダッシュ中もカーブできるように、新しい入力があれば方向を更新
            if dx != 0 or dy != 0:
                self.last_direction = (dx, dy)
            
            # ダッシュ中は最後の方向に移動
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
        
        # 目標速度の設定
        target_speed_x = dx * current_speed
        target_speed_y = dy * current_speed
        
        # 現在の速度から目標速度への補間（慣性）
        if dx == 0:
            # 減速（摩擦）
            if abs(self.speed_x) > self.friction:
                self.speed_x -= math.copysign(self.friction, self.speed_x)
            else:
                self.speed_x = 0
        else:
            # 加速
            self.speed_x += (target_speed_x - self.speed_x) * self.acceleration
            
        if dy == 0:
            # 減速（摩擦）
            if abs(self.speed_y) > self.friction:
                self.speed_y -= math.copysign(self.friction, self.speed_y)
            else:
                self.speed_y = 0
        else:
            # 加速
            self.speed_y += (target_speed_y - self.speed_y) * self.acceleration
        
        # 位置の更新
        self.x += self.speed_x
        self.y += self.speed_y
        
        # 画面外に出ないようにする
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))
        
        # 前フレームのダッシュ状態を保存
        self.was_dashing = self.is_dashing
        
    def find_nearest_enemy(self, enemies, force_next=False):
        """最も近い敵を探す"""
        if not enemies:
            return None
            
        # プレイヤーの中心座標
        player_center_x = self.x + self.width / 2
        player_center_y = self.y + self.height / 2
        
        current_locked_enemy = self.locked_enemy
        nearest_enemy = None
        min_distance = float('inf')
        
        # 現在のロックオン対象の次の敵をロックオンする場合（TABキーが押された場合など）
        if force_next and current_locked_enemy in enemies:
            current_index = enemies.index(current_locked_enemy)
            next_index = (current_index + 1) % len(enemies)
            return enemies[next_index]
        
        # ロックオン範囲内で最も近い敵を探す
        for enemy in enemies:
            # 敵の中心座標
            enemy_center_x = enemy.x + enemy.width / 2
            enemy_center_y = enemy.y + enemy.height / 2
            
            # 距離を計算
            dx = enemy_center_x - player_center_x
            dy = enemy_center_y - player_center_y
            distance = math.sqrt(dx**2 + dy**2)
            
            # ロックオン範囲内かつ、最も近い敵を選択
            if distance <= self.lock_on_range and distance < min_distance:
                min_distance = distance
                nearest_enemy = enemy
                
        return nearest_enemy
        
    def update_lock_on(self, enemies, keys):
        """ロックオン対象の更新"""
        # TABキーでロックオン切り替え（実際のゲームではこれは別のキーかもしれません）
        force_next = keys.get(pygame.K_TAB, False) and self.lock_changed_cooldown <= 0
        
        # ロックオン切り替えクールダウンの更新
        if self.lock_changed_cooldown > 0:
            self.lock_changed_cooldown -= 1
            
        # ロックオン切り替えが要求された場合、クールダウンを設定
        if force_next:
            self.lock_changed_cooldown = 10  # 10フレームのクールダウン
            
        # 最も近い敵を探してロックオン
        self.locked_enemy = self.find_nearest_enemy(enemies, force_next)
        
    def take_damage(self, damage):
        """ダメージを受ける処理"""
        if self.invincible_time <= 0:
            self.hp -= damage
            self.invincible_time = 60  # 無敵時間（フレーム数）
            return True
        return False
        
    def is_invincible(self):
        """無敵状態かどうかを返す"""
        return self.invincible_time > 0
        
    def update_charge(self, keys, enemies):
        """チャージ処理の更新"""
        # チャージボタン（X）が押されているかチェック
        charge_button_pressed = keys[pygame.K_x]
        
        if charge_button_pressed:
            # チャージ開始または継続
            if not self.is_charging:
                # チャージ開始
                self.is_charging = True
                self.charge_level = 0
                self.charge_start_time = pygame.time.get_ticks()
                
            # チャージレベルを上昇
            self.charge_level += self.charge_speed
            if self.charge_level > self.max_charge_level:
                self.charge_level = self.max_charge_level
                
            # チャージターゲット位置の更新（ロックオン対象がある場合）
            if self.locked_enemy:
                self.charge_target_position = (
                    self.locked_enemy.x + self.locked_enemy.width/2,
                    self.locked_enemy.y + self.locked_enemy.height/2
                )
            else:
                # ロックオン対象がない場合はプレイヤーの前方
                offset_x = 200 if self.facing_right else -200
                self.charge_target_position = (self.x + self.width/2 + offset_x, self.y + self.height/2)
        else:
            # チャージボタンが離された
            if self.is_charging:
                # チャージ中だった場合、チャージショットを発射
                if self.charge_level > 0 and self.can_fire("beam_rifle"):
                    self.fire_charge_shot(enemies)
                
                # チャージ状態をリセット
                self.is_charging = False
                self.charge_level = 0
                self.charge_target_position = None
        
    def fire_normal_shot(self, bullets):
        """通常射撃を発射する"""
        # 弾の発射位置（プレイヤーの前方）
        bullet_x = self.x + self.width if self.facing_right else self.x
        bullet_y = self.y + self.height / 2 - 5  # 少し上に調整
        
        # ロックオン対象がある場合はそれをターゲットに
        target = self.locked_enemy
        
        # 弾を作成
        bullet = Bullet(
            bullet_x,
            bullet_y,
            target=target,
            facing_right=self.facing_right,
            bullet_type="beam_rifle"
        )
        
        # 弾をリストに追加
        bullets.append(bullet)
        
        # クールダウンを設定
        self.beam_rifle_cooldown = self.beam_rifle_cooldown_time
        
    def fire_charge_shot(self, bullets):
        """チャージショットを発射する"""
        # 弾の発射位置（プレイヤーの前方）
        bullet_x = self.x + self.width if self.facing_right else self.x
        bullet_y = self.y + self.height / 2 - 5  # 少し上に調整
        
        # チャージレベルを整数値に丸める（1が最大）
        charge_level = 1 if self.charge_level >= self.max_charge_level else 0
        
        # 弾を作成
        bullet = Bullet(
            bullet_x,
            bullet_y,
            target=self.locked_enemy,
            facing_right=self.facing_right,
            bullet_type="beam_rifle",
            charge_level=charge_level,
            target_pos=self.charge_target_position
        )
        
        # 弾をリストに追加
        bullets.append(bullet)
        
        # クールダウンを設定
        self.beam_rifle_cooldown = self.beam_rifle_cooldown_time * 2  # チャージショットは長めのクールダウン
        
    def update_weapon_cooldown(self):
        """武器のクールダウン更新"""
        if self.weapon_cooldown > 0:
            self.weapon_cooldown -= 1
        if self.beam_rifle_cooldown > 0:
            self.beam_rifle_cooldown -= 1
        if self.shot_cooldown > 0:
            self.shot_cooldown -= 1
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
        
    def can_fire(self, weapon_type="beam_rifle"):
        """武器が発射可能かどうか"""
        if weapon_type == "beam_rifle":
            return self.beam_rifle_cooldown <= 0
        else:
            return self.weapon_cooldown <= 0
        
    def update(self, keys, enemies, bullets):
        """プレイヤーの状態更新"""
        # 無敵時間の更新
        if self.invincible_time > 0:
            self.invincible_time -= 1
            
        # 移動処理
        self.move(keys)
        
        # ロックオン更新
        self.update_lock_on(enemies, keys)
        
        # 武器のクールダウン更新
        self.update_weapon_cooldown()
        
        # チャージ処理の更新
        self.update_charge(keys, bullets)
        
        # 射撃処理
        # Zキーが押されているかチェック
        shoot_button_pressed = keys[pygame.K_z]
        
        if shoot_button_pressed and not self.is_charging:
            # 射撃可能な状態であれば発射
            if self.can_fire("beam_rifle"):
                self.fire_normal_shot(bullets)
        
    def draw(self, screen):
        """プレイヤーの描画"""
        # プレイヤーを描画
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))
        
        # ダッシュエフェクトの描画
        if self.is_dashing:
            # ダッシュエフェクトの位置を調整
            effect_x = self.x - 10 if self.facing_right else self.x + self.width + 10
            effect_y = self.y
            
            # ダッシュエフェクトの大きさ
            effect_width = 5
            effect_height = self.height
            
            # ダッシュエフェクトの色
            effect_color = YELLOW
            
            # ダッシュエフェクト描画
            pygame.draw.rect(screen, effect_color, (effect_x, effect_y, effect_width, effect_height))
        
    def draw_gauges(self, screen):
        """ゲージの描画"""
        # HPゲージの描画
        hp_ratio = self.hp / self.max_hp
        hp_width = 200 * hp_ratio
        pygame.draw.rect(screen, RED, (SCREEN_WIDTH - 210, 10, 200, 20), 1)  # 枠
        pygame.draw.rect(screen, RED, (SCREEN_WIDTH - 210, 10, hp_width, 20))  # 中身
        
        # 特殊ゲージの描画
        special_width = 200 * (self.special_gauge / self.max_special_gauge)
        pygame.draw.rect(screen, YELLOW, (SCREEN_WIDTH - 210, 40, 200, 10), 1)  # 枠
        pygame.draw.rect(screen, YELLOW, (SCREEN_WIDTH - 210, 40, special_width, 10))  # 中身
        
        # ヒートゲージの描画
        heat_ratio = self.heat / self.max_heat
        heat_width = 150 * heat_ratio
        pygame.draw.rect(screen, BLUE, (SCREEN_WIDTH - 160, 60, 150, 10), 1)  # 枠
        pygame.draw.rect(screen, BLUE, (SCREEN_WIDTH - 160, 60, heat_width, 10))  # 中身
        
    # その他のPlayerクラスメソッドも同様に追加する必要があります
    # toggle_advertise_mode, update_advertise_mode, analyze_screen, etc. 

    # 収益化モード関連
    def toggle_monetization_mode(self):
        """収益化モード（自動稼ぎ）の切り替え"""
        if not hasattr(self, 'monetization_mode'):
            self.monetization_mode = False
            self.monetization_timer = 0
            self.monetization_start_time = 0
            self.monetization_duration = 3600 # デフォルト1時間
            self.monetization_earnings = 0
            self.monetization_rate = 0.1  # 仮想通貨獲得レート（スコア100ごとに0.1コイン）
            self.monetization_last_score = 0
            # 保存済みデータがあれば読み込む
            self._load_monetization_data()
            
        self.monetization_mode = not self.monetization_mode
        
        # モード切り替え時の処理
        if self.monetization_mode:
            import time
            # アドバタイズモードも有効化
            if hasattr(self, 'advertise_mode') and not self.advertise_mode:
                if hasattr(self, 'toggle_advertise_mode'):
                    self.toggle_advertise_mode()
            self.monetization_start_time = time.time()
            self.monetization_timer = 0
            self.monetization_last_score = 0
            print(f"収益化モードを開始しました。{self.monetization_duration/3600:.1f}時間稼働します。")
        else:
            # アドバタイズモードも無効化
            if hasattr(self, 'advertise_mode') and self.advertise_mode:
                if hasattr(self, 'toggle_advertise_mode'):
                    self.toggle_advertise_mode()
            print(f"収益化モードを終了しました。獲得コイン: {self.monetization_earnings:.2f}")
            # データを保存
            self._save_monetization_data()
            
        return self.monetization_mode
        
    def update_monetization(self, current_score):
        """収益化モードの更新処理"""
        if not hasattr(self, 'monetization_mode') or not self.monetization_mode:
            return
            
        import time
        # 経過時間を確認
        elapsed_time = time.time() - self.monetization_start_time
        self.monetization_timer = elapsed_time
        
        # 収益の計算（スコア差分に基づく）
        score_diff = max(0, current_score - self.monetization_last_score)
        earned_coins = score_diff * self.monetization_rate / 100  # スコア100ごとに設定レートのコイン獲得
        self.monetization_earnings += earned_coins
        self.monetization_last_score = current_score
        
        # 設定時間が経過したら自動で終了
        if elapsed_time >= self.monetization_duration:
            self.toggle_monetization_mode()
            
    def set_monetization_duration(self, hours):
        """収益化モードの稼働時間を設定"""
        if not hasattr(self, 'monetization_mode'):
            self.monetization_mode = False
            self.monetization_timer = 0
            self.monetization_duration = 3600  # デフォルト1時間
            self.monetization_earnings = 0
            
        self.monetization_duration = hours * 3600  # 時間を秒に変換
        print(f"収益化モードの稼働時間を{hours}時間に設定しました")
        
    def set_monetization_rate(self, rate):
        """仮想通貨獲得レートを設定"""
        if not hasattr(self, 'monetization_mode'):
            self.monetization_mode = False
            self.monetization_timer = 0
            self.monetization_duration = 3600  # デフォルト1時間
            self.monetization_earnings = 0
            self.monetization_rate = 0.1
            
        self.monetization_rate = rate
        print(f"収益化レートを{rate}に設定しました（スコア100ごとに{rate}コイン獲得）")
            
    def _save_monetization_data(self):
        """収益化データを保存"""
        import os
        import json
        import time
        
        # データ保存用のディレクトリを確保
        save_dir = "user_data"
        os.makedirs(save_dir, exist_ok=True)
        
        # 保存するデータを準備
        data = {
            "total_earnings": self.monetization_earnings,
            "rate": self.monetization_rate,
            "last_update": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # JSONファイルに保存
        try:
            with open(os.path.join(save_dir, "monetization.json"), "w") as f:
                json.dump(data, f, indent=2)
            print("収益化データを保存しました")
        except Exception as e:
            print(f"収益化データの保存に失敗しました: {e}")
            
    def _load_monetization_data(self):
        """保存された収益化データを読み込む"""
        import os
        import json
        
        # データファイルのパス
        data_path = os.path.join("user_data", "monetization.json")
        
        # ファイルが存在すれば読み込む
        if os.path.exists(data_path):
            try:
                with open(data_path, "r") as f:
                    data = json.load(f)
                
                # データを適用
                self.monetization_earnings = data.get("total_earnings", 0)
                self.monetization_rate = data.get("rate", 0.1)
                print(f"前回の収益化データを読み込みました（総獲得コイン: {self.monetization_earnings:.2f}）")
            except Exception as e:
                print(f"収益化データの読み込みに失敗しました: {e}")
                
    def get_monetization_stats(self):
        """収益化モードの状態情報を取得"""
        if not hasattr(self, 'monetization_mode'):
            return {
                "active": False,
                "earnings": 0,
                "duration": 0,
                "remaining": 0
            }
            
        import time
        elapsed_time = 0
        remaining_time = 0
        
        if self.monetization_mode:
            elapsed_time = time.time() - self.monetization_start_time
            remaining_time = max(0, self.monetization_duration - elapsed_time)
            
        return {
            "active": self.monetization_mode,
            "earnings": self.monetization_earnings,
            "duration": elapsed_time,
            "remaining": remaining_time,
            "rate": self.monetization_rate,
            "last_score": self.monetization_last_score
        } 