import pygame
import random
import math
import numpy

# 初期化
pygame.init()
pygame.mixer.init()  # 音声システムの初期化

# クロックの初期化
clock = pygame.time.Clock()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("アクセラレーションオブ豆腐とトマト")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)

# ネギライフル用の色
DARK_GREEN = (0, 100, 0)
LIGHT_GREEN = (150, 255, 150)
NEGI_COLOR = (150, 255, 150)  # ネギの色

# ネギライフルのパラメータ
NEGI_RIFLE_PARAMS = {
    "width": 8,           # 銃身の幅
    "height": 44,         # 銃身の長さ
    "outline_width": 4,   # 輪郭の太さ
    "tip_width": 4,       # 先端部分の幅
    "tip_length": 8,      # 先端部分の長さ
    "tip_highlight_length": 2,  # 先端のハイライト部分の長さ
    "color": (150, 255, 150), # メインカラー
    "tip_color": WHITE,   # 先端部分の色
    "tip_highlight_color": YELLOW,  # 先端のハイライト色
}

# 弾のパラメータ定義
BULLET_TYPES = {
    "beam_rifle": {  # 基本武装のビームライフル
        "speed": 12,          # 基本弾速（通常より速め）
        "width": 15,         # 弾の幅
        "height": 60,        # 弾の高さ
        "damage": 25,         # 基本威力
        "homing_strength": 0.001,  # よりホーミングを弱く
        "max_turn_angle": 5,     # 旋回角度も小さく
        "min_homing_distance": 0,  # 距離による補正を無効化
        "max_homing_distance": 9999,
        "color": (100, 200, 255),  # 青白い色
        "charge_levels": {  # チャージレベルの設定
            1: {
                "speed": 1.5,
                "damage": 2.0,
                "color": (150, 255, 150),  # ネギカラーに変更
                "height_multiplier": 2.0,  # 高さを2倍に
                "width_multiplier": 1.5,  # 幅を1.5倍に
                "penetrate": True,  # 貫通効果を追加
                "disable_homing": True  # ホーミング無効化
            }
        },
        "cooldown": 20  # 発射間隔（フレーム数）
    },
    "normal": {
        "speed": 10,
        "width": 5,
        "height": 10,
        "damage": 20,
        "homing_strength": 0.15,
        "max_turn_angle": 30,
        "min_homing_distance": 50,
        "max_homing_distance": 300,
        "color": WHITE,
    },
    "quick": {
        "speed": 15,
        "width": 3,
        "height": 8,
        "damage": 15,
        "homing_strength": 0.1,
        "max_turn_angle": 20,
        "min_homing_distance": 100,
        "max_homing_distance": 400,
        "color": YELLOW,
    },
    "heavy": {
        "speed": 7,
        "width": 8,
        "height": 15,
        "damage": 35,
        "homing_strength": 0.05,
        "max_turn_angle": 15,
        "min_homing_distance": 50,
        "max_homing_distance": 250,
        "color": RED,
    }
}

# 敵のパラメータ定義
ENEMY_TYPES = {
    "mob": {
        "width": 30,
        "height": 30,
        "hp": 45,           # ビームライフル(20ダメージ)で3発必要
        "base_speed": 3,    # 基本移動速度
        "color": RED,
        "score": 100,      # 撃破時のスコア
        "homing_factor": 0.1,  # 自機へのホーミング強度（小さいほど緩やか）
        "explosion_radius": 60,  # 爆発の影響範囲
        "explosion_damage": 30,   # 爆発によるダメージ
        "min_score": 0      # この敵が登場する最小スコア
    },
    "speeder": {
        "width": 25,
        "height": 25,
        "hp": 30,           # 耐久力は低いが素早い
        "base_speed": 5,    # 通常より速い
        "color": YELLOW,
        "score": 150,      # スコアも高め
        "homing_factor": 0.12,  # ホーミング性能も高め
        "explosion_radius": 45,  # 爆発範囲は小さめ
        "explosion_damage": 20,  # 爆発ダメージも小さめ
        "min_score": 3000   # 3000点以上で登場
    },
    "tank": {
        "width": 40,
        "height": 40,
        "hp": 100,          # 耐久力が高い
        "base_speed": 2,    # 移動は遅め
        "color": BLUE,
        "score": 250,      # 高得点
        "homing_factor": 0.05,  # ホーミングは鈍い
        "explosion_radius": 90,  # 爆発範囲が大きい
        "explosion_damage": 40,  # 爆発ダメージも大きい
        "min_score": 5000   # 5000点以上で登場
    },
    "assassin": {
        "width": 20,
        "height": 35,
        "hp": 70,           # それなりの耐久力
        "base_speed": 4,    # 素早い
        "color": (128, 0, 128),  # 紫色
        "score": 300,       # かなり高得点
        "homing_factor": 0.15,  # 強力なホーミング能力
        "explosion_radius": 70,  # かなりの爆発範囲
        "explosion_damage": 45,  # 大きな爆発ダメージ
        "min_score": 10000  # 10000点以上で登場
    }
}

# 敵のパラメータ定義の後に追加
MAX_ENEMIES = 100  # 敵の最大出現数
BASE_ENEMY_SPAWN_RATE = 0.02  # 基本の敵出現確率
BASE_ENEMY_SPEED = 3.0  # 基本の敵速度

# 難易度に関する関数
def calculate_difficulty_factor(current_score):
    # 基本は1.0、最大3.0まで
    base_factor = 1.0
    # スコアに応じて難易度上昇（10000点で最大）
    score_factor = min(current_score / 10000.0, 2.0)
    return base_factor + score_factor

# 難易度レベルの名前を取得（表示用）
def get_difficulty_name(factor):
    if factor < 1.2:
        return "EASY"
    elif factor < 1.6:
        return "NORMAL"
    elif factor < 2.0:
        return "HARD"
    elif factor < 2.5:
        return "VERY HARD"
    else:
        return "EXTREME"

# スコアに応じた敵タイプを選択
def select_enemy_type(current_score):
    # スコアに基づいて出現可能な敵タイプをリストアップ
    available_types = []
    for enemy_type, params in ENEMY_TYPES.items():
        if current_score >= params["min_score"]:
            available_types.append(enemy_type)
    
    # 利用可能な敵タイプがない場合は「mob」をデフォルトとして使用
    if not available_types:
        return "mob"
    
    # スコアに合わせた重み付けを計算
    weights = []
    for enemy_type in available_types:
        base_weight = 1.0
        score_diff = current_score - ENEMY_TYPES[enemy_type]["min_score"]
        if score_diff > 0:
            weight_bonus = min(score_diff / 5000.0, 2.0)
            base_weight += weight_bonus
        weights.append(base_weight)
    
    # 重み付きランダム選択
    return random.choices(available_types, weights=weights, k=1)[0]

# スコアに基づく敵の出現確率を計算
def get_enemy_spawn_chance(current_score):
    # ベースの出現確率
    base_chance = BASE_ENEMY_SPAWN_RATE
    # 難易度係数に基づいて出現確率を調整
    difficulty = calculate_difficulty_factor(current_score)
    return base_chance * difficulty

# スコアに基づく敵の速度係数を計算
def get_enemy_speed_factor(current_score):
    # 難易度係数に基づいて敵の速度を調整
    return calculate_difficulty_factor(current_score)

# リングエフェクトクラス
class RingEffect:
    def __init__(self, x, y, color=WHITE, max_radius=40, expand_speed=2, fade_speed=0.02, velocity_x=0, velocity_y=0, gravity=0):
        self.x = x
        self.y = y
        self.radius = max_radius  # 初期サイズを最大サイズに
        self.max_radius = max_radius
        self.expand_speed = expand_speed  # 拡大速度を保存
        self.life = 2.0  # 寿命を2倍に
        self.fade_speed = fade_speed * 2  # フェード速度を2倍に
        self.color = color
        
        # 移動用のパラメータ
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.gravity = gravity
        
    def update(self):
        # リングの拡大
        self.radius += self.expand_speed
        
        # 透明度の減少
        self.life -= self.fade_speed
        
        # 位置の更新（飛散効果）
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 重力の影響
        self.velocity_y += self.gravity
        
        return self.life > 0
        
    def draw(self, screen):
        if self.life <= 0 or self.radius <= 0:
            return
            
        try:
            # 色の処理をさらに安全に
            default_color = (255, 255, 255)  # デフォルト色（白）
            
            if not isinstance(self.color, (tuple, list)):
                rgb = default_color
            elif len(self.color) < 3:
                rgb = default_color
            else:
                # RGB値を整数に変換して範囲内に収める
                try:
                    r = max(0, min(255, int(self.color[0])))
                    g = max(0, min(255, int(self.color[1])))
                    b = max(0, min(255, int(self.color[2])))
                    rgb = (r, g, b)
                except (ValueError, TypeError):
                    rgb = default_color
            
            # アルファ値の計算（0〜1の範囲を確保）
            life_clamped = max(0.0, min(1.0, float(self.life)))
            alpha = int(255 * life_clamped)
            
            # サーフェスの作成
            radius_int = max(1, int(self.radius))
            ring_size = radius_int * 2 + 4
            ring_surface = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
            
            # 円の描画
            center = (ring_size // 2, ring_size // 2)
            width = 2 if radius_int > 2 else 1
            
            # 色とアルファ値を組み合わせる
            color_with_alpha = (*rgb, alpha)
            
            # 円を描画
            pygame.draw.circle(ring_surface, color_with_alpha, center, radius_int, width)
            
            # 画面に描画
            x_pos = int(self.x - center[0])
            y_pos = int(self.y - center[1])
            screen.blit(ring_surface, (x_pos, y_pos))
            
        except Exception as e:
            # どんなエラーが発生しても処理を続行
            pass

# プレイヤークラス
class Player:
    def __init__(self):
        # プレイヤーの位置と大きさ
        self.width = 30
        self.height = 30
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2
        
        # 移動関連
        self.max_speed = 5.6  # 7.0の80%に減速
        self.acceleration = 0.3
        self.deceleration = 0.2
        self.velocity_x = 0
        self.velocity_y = 0
        self.facing_right = True
        self.last_direction = 'east'  # 8方向のいずれか
        self.input_buffer = {'left': False, 'right': False, 'up': False, 'down': False, 'shift': False}
        
        # 旋回関連
        self.movement_angle = 0  # 移動の向き（度数法、0=右、90=上）
        self.target_angle = 0    # 目標の向き
        self.max_turn_rate = 30.0  # 最大旋回速度（度/フレーム）
        
        # ヒート関連
        self.heat = 0           # 現在のヒート値
        self.max_heat = 100     # 最大ヒート値
        
        # アドバタイズモード関連
        self.advertise_mode = True  # デフォルトで有効に変更
        self.advertise_action_timer = 0  # アクションタイマー
        self.advertise_action_interval = 60  # アクションの間隔（フレーム）
        self.advertise_movement_timer = 0  # 移動タイマー
        self.advertise_movement_duration = 120  # 一方向への移動持続時間
        self.advertise_target_x = None  # 移動目標X座標
        self.advertise_target_y = None  # 移動目標Y座標
        self.visual_mode = True  # 画面認識モードをデフォルトで有効
        self.detected_enemies = []  # 画面から検出した敵
        self.detected_safe_zones = []  # 画面から検出した安全地帯
        self.visual_analysis_timer = 0  # 画面分析タイマー
        
        # ダッシュ関連
        self.dash_speed = 8.0  # 10.0の80%に減速
        self.dash_duration = 120  # フレーム数
        self.dash_cooldown_time = 45  # クールダウン時間（フレーム数）
        self.dash_cooldown = 0  # 現在のクールダウン残り時間
        self.is_dashing = False
        self.was_dashing = False
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
        self.was_dashing = False
        self.heat = 0
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
        if self.invincible_time > 0:
            self.invincible_time -= 1
        
        # キー入力の状態を更新
        self.input_buffer['left'] = keys[pygame.K_LEFT]
        self.input_buffer['right'] = keys[pygame.K_RIGHT]
        self.input_buffer['up'] = keys[pygame.K_UP]
        self.input_buffer['down'] = keys[pygame.K_DOWN]
        self.input_buffer['shift'] = keys[pygame.K_LSHIFT]
        
        # ダッシュの処理
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
            
        # ヒートゲージの管理
        # ダッシュ中はヒートゲージを上昇させる
        if self.is_dashing:
            # ヒートゲージを上昇（上昇率は調整可能）
            self.heat += 1.0
            # 最大値に達したらダッシュ解除
            if self.heat >= self.max_heat:
                self.is_dashing = False
                self.dash_cooldown = self.dash_cooldown_time
            # 最大値を超えないようにする
            self.heat = min(self.heat, self.max_heat)
        else:
            # ダッシュしていない時はヒートゲージを徐々に下げる
            self.heat = max(0, self.heat - 0.2)

        # ヒートゲージが高温状態（90%以上）になるとダッシュできない
        heat_threshold = self.max_heat * 0.9
        can_dash = self.heat < heat_threshold and self.dash_cooldown <= 0
            
        # ダッシュの開始判定
        if self.input_buffer['shift'] and not self.was_dashing and can_dash:
            self.is_dashing = True
            self.dash_cooldown = self.dash_duration
            sound_effects.play('dash')
            # ダッシュエフェクトを追加（2倍の量で）
            center_x = self.x + self.width/2
            center_y = self.y + self.height/2
            # 外側のリング（2セット）
            self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3, 0.1))
            self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3.2, 0.1))
            # 内側のリング（2セット）
            self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.5, 0.15))
            self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.7, 0.15))
        elif not self.input_buffer['shift'] and self.dash_cooldown <= 0:
            self.is_dashing = False
            self.dash_cooldown = self.dash_cooldown_time
        
        self.was_dashing = self.is_dashing

        # ダッシュエフェクトの更新
        self.dash_effects = [effect for effect in self.dash_effects if effect.update()]
        if self.is_dashing and pygame.time.get_ticks() % 3 == 0:
            center_x = self.x + self.width/2
            center_y = self.y + self.height/2
            self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 20, 2, 0.2))
        
        # 移動方向の計算
        dx = 0
        dy = 0
        
        if self.input_buffer['left']: dx -= 1
        if self.input_buffer['right']: dx += 1
        if self.input_buffer['up']: dy -= 1
        if self.input_buffer['down']: dy += 1

        # 斜め移動の速度を正規化
        if dx != 0 and dy != 0:
            length = math.sqrt(2)
            dx /= length
            dy /= length

        # 入力方向に基づく目標角度の計算
        if dx != 0 or dy != 0:
            # 入力方向から角度を計算
            self.target_angle = math.degrees(math.atan2(-dy, dx))
            
            # 旋回速度を計算し、現在の角度を更新
            angle_diff = (self.target_angle - self.movement_angle + 180) % 360 - 180
            turn_rate = min(abs(angle_diff), self.max_turn_rate) * (1 if angle_diff > 0 else -1)
            self.movement_angle = (self.movement_angle + turn_rate) % 360

        # 目標速度の計算
        current_max_speed = self.dash_speed if self.is_dashing else self.max_speed
        
        # 入力と現在の角度に基づいて速度を計算
        if dx != 0 or dy != 0:
            # 方向キー入力がある場合、その方向へ80%、角度方向へ20%の重みで計算
            input_weight = 0.8
            angle_weight = 1.0 - input_weight
            
            # 入力方向の速度成分
            input_vel_x = dx * current_max_speed
            input_vel_y = dy * current_max_speed
            
            # 角度方向の速度成分
            angle_rad = math.radians(self.movement_angle)
            angle_vel_x = math.cos(angle_rad) * current_max_speed
            angle_vel_y = -math.sin(angle_rad) * current_max_speed
            
            # 重み付け合成
            target_velocity_x = input_vel_x * input_weight + angle_vel_x * angle_weight
            target_velocity_y = input_vel_y * input_weight + angle_vel_y * angle_weight
        else:
            # 入力がない場合は減速
            target_velocity_x = 0
            target_velocity_y = 0

        # 現在の速度を目標速度に近づける
        if dx != 0 or dy != 0:
            # 加速（ダッシュ中は加速度を上げる）
            current_acceleration = self.acceleration * (1.5 if self.is_dashing else 1.0)
            self.velocity_x += (target_velocity_x - self.velocity_x) * current_acceleration
            self.velocity_y += (target_velocity_y - self.velocity_y) * current_acceleration
        else:
            # 減速
            self.velocity_x *= (1 - self.deceleration)
            self.velocity_y *= (1 - self.deceleration)

        # 位置の更新
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 画面端の処理
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))
        
        # 向きの更新
        if dx != 0:
            self.facing_right = dx > 0
        
        # 移動方向の記録（8方向）
        if dx != 0 or dy != 0:
            if dx < 0:
                if dy < 0: self.last_direction = 'northwest'
                elif dy > 0: self.last_direction = 'southwest'
                else: self.last_direction = 'west'
            elif dx > 0:
                if dy < 0: self.last_direction = 'northeast'
                elif dy > 0: self.last_direction = 'southeast'
                else: self.last_direction = 'east'
            else:
                if dy < 0: self.last_direction = 'north'
                else: self.last_direction = 'south'

        # エフェクトの更新
        self.ring_effects = [effect for effect in self.ring_effects if effect.update()]

    def find_nearest_enemy(self, enemies, force_next=False):
        if not enemies:
            return None
            
        # 現在のロックオン対象をスキップするフラグ
        skip_current = force_next and self.locked_enemy in enemies
        
        min_dist = float('inf')
        nearest = None
        
        for enemy in enemies:
            if skip_current and enemy == self.locked_enemy:
                continue
                
            dx = enemy.x + enemy.width/2 - (self.x + self.width/2)
            dy = enemy.y + enemy.height/2 - (self.y + self.height/2)
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist < min_dist and dist < self.lock_on_range:
                min_dist = dist
                nearest = enemy
                
        return nearest

    def update_lock_on(self, enemies, keys):
        # 現在のロックオン対象が画面外に出たか、破壊された場合
        if self.locked_enemy not in enemies:
            self.locked_enemy = None
            
        # Zキーでロックオン対象切り替え
        if keys[pygame.K_z]:
            self.locked_enemy = self.find_nearest_enemy(enemies, force_next=True)
        # ロックオン対象がない場合は最も近い敵を自動ロック
        elif self.locked_enemy is None:
            self.locked_enemy = self.find_nearest_enemy(enemies)
            
        # ロックオン対象がある場合、その方向を向く
        if self.locked_enemy:
            dx = self.locked_enemy.x - self.x
            self.facing_right = dx > 0

    def take_damage(self, damage):
        # ダメージを受けてHPが減少
        self.hp = max(0, self.hp - damage)
        
        # 被弾エフェクト
        self.damage_effect_time = 15  # 15フレーム（約0.25秒）の無敵時間
        
        return self.hp <= 0
    
    def is_invincible(self):
        # 被弾直後の無敵状態をチェック
        return self.damage_effect_time > 0
        
    def update_charge(self, keys, enemies):
        # スペースキーが押されている間チャージ
        if keys[pygame.K_SPACE]:
            if not self.is_charging:
                self.shot_cooldown = self.shot_cooldown_time
                self.is_charging = True
                self.charge_start_time = pygame.time.get_ticks()
                self.charge_target_position = None
                self.charge_complete = False
                self.charge_sound_playing = True
                sound_effects.play('charge')  # チャージ開始音を再生
            else:
                charge_time = (pygame.time.get_ticks() - self.charge_start_time) / 1000  # 秒単位
                
                # チャージ中のリングエフェクト生成
                if pygame.time.get_ticks() % 3 == 0:  # 頻繁にエフェクトを生成
                    center_x = self.x + self.width/2
                    center_y = self.y + self.height/2
                    # チャージ中は青白い小さなリング
                    self.ring_effects.append(RingEffect(center_x, center_y, (100, 200, 255), 20, 2, 0.1))
                
                if charge_time >= 1.0:  # 1秒でフルチャージ
                    self.charge_level = 1
                    # 密集地点を常に更新
                    self.charge_target_position = self.find_cluster_center(enemies)
                    if self.charge_target_position:  # 密集地点がある場合、その方向を向く
                        dx = self.charge_target_position[0] - (self.x + self.width/2)
                        self.facing_right = dx > 0
                    if not self.charge_complete:  # チャージ完了エフェクトを一度だけ生成
                        self.charge_complete = True
                        sound_effects.play('charge_complete')  # チャージ完了音を再生
                        # 派手なリングエフェクトを生成
                        center_x = self.x + self.width/2
                        center_y = self.y + self.height/2
                        # 大きな白いリング
                        self.ring_effects.append(RingEffect(center_x, center_y, WHITE, 80, 5, 0.03))
                        # 中くらいの青白いリング
                        self.ring_effects.append(RingEffect(center_x, center_y, (100, 200, 255), 60, 4, 0.04))
                        # 小さな白いリング
                        self.ring_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3, 0.05))
                else:
                    self.charge_level = 0
        else:
            if self.is_charging:
                self.charge_sound_playing = False
            self.is_charging = False
            self.charge_target_position = None
            self.charge_complete = False
        
    def update_weapon_cooldown(self):
        if self.weapon_cooldown > 0:
            self.weapon_cooldown -= 1
            
    def can_fire(self, weapon_type="beam_rifle"):
        return self.weapon_cooldown <= 0

    def update(self, keys, enemies, bullets):
        # アドバタイズモードが有効なら自動操作を行う
        if self.advertise_mode:
            self.update_advertise_mode(enemies, bullets)
        else:
            # 通常の操作処理
            self.move(keys)
            self.update_lock_on(enemies, keys)
            self.update_charge(keys, enemies)
        
        # 共通の更新処理
        # 射撃クールダウンの更新
        if self.weapon_cooldown > 0:
            self.weapon_cooldown -= 1
        
        # ビームライフルのクールダウン更新
        if self.beam_rifle_cooldown > 0:
            self.beam_rifle_cooldown -= 1
            
        # リングエフェクトの更新
        self.ring_effects = [effect for effect in self.ring_effects if effect.update()]
                
        # ダッシュエフェクトの更新
        self.dash_effects = [effect for effect in self.dash_effects if effect.update()]
                
        # 被弾エフェクトの更新
        if self.damage_effect_time > 0:
            self.damage_effect_time -= 1
        
        # 通常射撃の処理
        if keys[pygame.K_SPACE] and self.can_fire():
            # 画面上の敵を探索
            visible_enemies = [enemy for enemy in enemies if not enemy.is_exploding and 
                              0 <= enemy.x <= SCREEN_WIDTH and
                              0 <= enemy.y <= SCREEN_HEIGHT]
            
            if visible_enemies:
                # 最大3体までの敵を優先的に狙う
                targets = sorted(visible_enemies, key=lambda e: ((e.x - self.x) ** 2 + (e.y - self.y) ** 2))[:3]
                
                sound_effects.play('shoot')
                for target in targets:
                    # 敵ごとにビームを発射
                    bullet_x = self.x + (self.width if self.facing_right else 0)
                    bullet_y = self.y + self.height // 2
                    bullets.append(Bullet(bullet_x, bullet_y, target=target, facing_right=self.facing_right))
                
                # 射撃後クールダウン
                self.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"]
            else:
                # 敵がいない場合は正面に発射
                sound_effects.play('shoot')
                bullet_x = self.x + (self.width if self.facing_right else 0)
                bullet_y = self.y + self.height // 2
                bullets.append(Bullet(bullet_x, bullet_y, facing_right=self.facing_right))
                self.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"]
        
        # チャージショットの処理
        if keys[pygame.K_SPACE] and not self.is_charging and self.shot_cooldown <= 0:
            target_pos = self.charge_target_position if self.charge_level > 0 else None
            bullets.append(Bullet(
                self.x + self.width/2 - 10,
                self.y,
                self.locked_enemy,
                self.facing_right,
                "beam_rifle",
                0,  # チャージレベルを明示的に0に設定
                target_pos
            ))
            sound_effects.play('shoot')  # 通常射撃音
            self.shot_cooldown = self.shot_cooldown_time
            self.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"]
        
    def draw(self):
        # ダッシュエフェクトの描画（プレイヤーの前に描画）
        for effect in self.dash_effects:
            effect.draw(screen)

        # 通常のエフェクトの描画
        for effect in self.ring_effects:
            effect.draw(screen)
            
        # プレイヤーの描画（無敵時間中は点滅）
        if self.invincible_time <= 0 or self.invincible_time % 4 >= 2:
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))
            
            # 銃口の描画（回転あり）
            muzzle_width = NEGI_RIFLE_PARAMS["width"]
            muzzle_height = NEGI_RIFLE_PARAMS["height"]
            muzzle_angle = 0  # デフォルトの角度
            
            # 発射方向の計算
            if self.charge_target_position and self.charge_level > 0:
                # チャージ完了時は密集地点方向
                dx = self.charge_target_position[0] - (self.x + self.width/2)
                dy = self.charge_target_position[1] - (self.y + self.height/2)
                muzzle_angle = math.degrees(math.atan2(dy, dx))
                
                # チャージ完了時のロックオン表示
                site_size = 40
                site_x = self.charge_target_position[0] - site_size/2
                site_y = self.charge_target_position[1] - site_size/2
                
                # 点滅効果
                alpha = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.01))
                site_surface = pygame.Surface((site_size, site_size), pygame.SRCALPHA)
                
                # ロックオンサイトの描画（青白色で）
                pygame.draw.rect(site_surface, (100, 200, 255, alpha), (0, 0, site_size, site_size), 2)
                pygame.draw.line(site_surface, (100, 200, 255, alpha), (0, site_size/2), (site_size, site_size/2), 2)
                pygame.draw.line(site_surface, (100, 200, 255, alpha), (site_size/2, 0), (site_size/2, site_size), 2)
                
                screen.blit(site_surface, (site_x, site_y))
                
                # ロックオン線の描画
                pygame.draw.line(screen, (100, 200, 255, alpha//2),
                               (self.x + self.width/2, self.y + self.height/2),
                               self.charge_target_position, 1)
            elif self.locked_enemy:
                # ロックオン時は敵の方向
                dx = self.locked_enemy.x + self.locked_enemy.width/2 - (self.x + self.width/2)
                dy = self.locked_enemy.y + self.locked_enemy.height/2 - (self.y + self.height/2)
                muzzle_angle = math.degrees(math.atan2(dy, dx))
            else:
                # 通常時は左右方向
                muzzle_angle = 0 if self.facing_right else 180
                
            # 銃口の回転描画
            muzzle_surface = pygame.Surface((muzzle_height + NEGI_RIFLE_PARAMS["outline_width"], 
                                          muzzle_width + NEGI_RIFLE_PARAMS["outline_width"]), pygame.SRCALPHA)
            # 輪郭を描画（深みのある緑）
            pygame.draw.rect(muzzle_surface, DARK_GREEN, 
                           (0, 0, muzzle_height + NEGI_RIFLE_PARAMS["outline_width"], 
                            muzzle_width + NEGI_RIFLE_PARAMS["outline_width"]))
                            
            # グラデーション効果の描画
            gradient_length = muzzle_height - 4
            for i in range(gradient_length):
                # 深みのある緑から明るい緑へのグラデーション
                progress = i / gradient_length
                # グラデーションを3倍強く
                gradient_factor = progress * 3
                gradient_factor = min(1.0, gradient_factor)  # 1.0を超えないように制限
                
                r = int(DARK_GREEN[0] + (LIGHT_GREEN[0] - DARK_GREEN[0]) * gradient_factor)
                g = int(DARK_GREEN[1] + (LIGHT_GREEN[1] - DARK_GREEN[1]) * gradient_factor)
                b = int(DARK_GREEN[2] + (LIGHT_GREEN[2] - DARK_GREEN[2]) * gradient_factor)
                gradient_color = (r, g, b)
                
                # 1ピクセルずつ縦線を描画
                pygame.draw.line(muzzle_surface, gradient_color, 
                               (i + 2, 2), 
                               (i + 2, muzzle_width + 1))
                               
            # 端部を白く（長さを指定）
            pygame.draw.rect(muzzle_surface, NEGI_RIFLE_PARAMS["tip_color"], 
                           (muzzle_height - NEGI_RIFLE_PARAMS["tip_length"], 2, 
                            NEGI_RIFLE_PARAMS["tip_length"], muzzle_width))
                            
            # 最先端の2ピクセルを黄色く
            pygame.draw.rect(muzzle_surface, NEGI_RIFLE_PARAMS["tip_highlight_color"],
                           (muzzle_height - NEGI_RIFLE_PARAMS["tip_highlight_length"], 2,
                            NEGI_RIFLE_PARAMS["tip_highlight_length"], muzzle_width))
                            
            rotated_muzzle = pygame.transform.rotate(muzzle_surface, -muzzle_angle)
            
            # 銃口の位置調整（プレイヤーの中心から描画）
            muzzle_pos_x = self.x + self.width/2 - rotated_muzzle.get_width()/2
            muzzle_pos_y = self.y + self.height/2 - rotated_muzzle.get_height()/2
            screen.blit(rotated_muzzle, (muzzle_pos_x, muzzle_pos_y))
        
        # ロックオンサイトの描画
        if self.locked_enemy:
            # ロックオンサイトの外枠
            site_size = 40
            site_x = self.locked_enemy.x + self.locked_enemy.width/2 - site_size/2
            site_y = self.locked_enemy.y + self.locked_enemy.height/2 - site_size/2
            
            # 点滅効果
            alpha = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.01))
            site_surface = pygame.Surface((site_size, site_size), pygame.SRCALPHA)
            
            # ロックオンサイトの描画
            pygame.draw.rect(site_surface, (255, 0, 0, alpha), (0, 0, site_size, site_size), 2)
            pygame.draw.line(site_surface, (255, 0, 0, alpha), (0, site_size/2), (site_size, site_size/2), 2)
            pygame.draw.line(site_surface, (255, 0, 0, alpha), (site_size/2, 0), (site_size/2, site_size), 2)
            
            screen.blit(site_surface, (site_x, site_y))
            
            # ロックオン線の描画
            pygame.draw.line(screen, (255, 0, 0, alpha//2),
                           (self.x + self.width/2, self.y + self.height/2),
                           (self.locked_enemy.x + self.locked_enemy.width/2,
                            self.locked_enemy.y + self.locked_enemy.height/2), 1)
        
        # ゲージの描画（左上に配置）
        self.draw_gauges()
        
        # チャージ中のエフェクト表示
        if self.is_charging and self.charge_level > 0:
            charge_color = (255, 255, 255)  # フルチャージ時は白色
            charge_size = 25  # チャージ時のエフェクトサイズ
            charge_surface = pygame.Surface((charge_size, charge_size), pygame.SRCALPHA)
            pygame.draw.circle(charge_surface, (*charge_color, 127), 
                             (charge_size//2, charge_size//2), charge_size//2)
            screen.blit(charge_surface, 
                       (self.x + self.width//2 - charge_size//2, 
                        self.y + self.height//2 - charge_size//2))

        # 入力状態の表示（デバッグ情報）
        debug_y = SCREEN_HEIGHT - 120
        font = pygame.font.Font(None, 24)
        
        # キー入力状態
        input_text = "Input: "
        if self.input_buffer['left']: input_text += "←"
        if self.input_buffer['right']: input_text += "→"
        if self.input_buffer['up']: input_text += "↑"
        if self.input_buffer['down']: input_text += "↓"
        if self.input_buffer['shift']: input_text += " SHIFT"
        debug_surface = font.render(input_text, True, WHITE)
        screen.blit(debug_surface, (10, debug_y))
        
        # 速度情報
        velocity_text = f"Velocity: X={self.velocity_x:.2f} Y={self.velocity_y:.2f}"
        velocity_surface = font.render(velocity_text, True, WHITE)
        screen.blit(velocity_surface, (10, debug_y + 20))
        
        # 実際の移動方向
        direction_text = f"Direction: {self.last_direction if self.last_direction else 'none'}"
        direction_surface = font.render(direction_text, True, WHITE)
        screen.blit(direction_surface, (10, debug_y + 40))
        
        # ダッシュ状態（修正：より詳細な情報を表示）
        dash_text = f"Dash: {'ON' if self.is_dashing else 'OFF'} (Cooldown: {self.dash_cooldown}, Duration: {self.dash_duration if self.is_dashing else 0})"
        dash_surface = font.render(dash_text, True, WHITE if not self.is_dashing else BLUE)
        screen.blit(dash_surface, (10, debug_y + 60))

        # アドバタイズモードのデバッグ情報
        self.draw_advertise_debug_info(screen)

    def draw_gauges(self):
        gauge_width = 200
        gauge_height = 15
        gauge_x = 10
        margin = 5
        
        # HPゲージ
        hp_y = 10
        # 背景（黒）
        pygame.draw.rect(screen, BLACK, (gauge_x-1, hp_y-1, gauge_width+2, gauge_height+2))
        # 枠（白）
        pygame.draw.rect(screen, WHITE, (gauge_x, hp_y, gauge_width, gauge_height), 1)
        # HPゲージ本体（緑）
        if self.hp > 0:
            hp_width = int(gauge_width * (self.hp / 100))
            pygame.draw.rect(screen, GREEN, (gauge_x, hp_y, hp_width, gauge_height))
        
        # ヒートゲージ
        heat_y = hp_y + gauge_height + margin
        # 背景（黒）
        pygame.draw.rect(screen, BLACK, (gauge_x-1, heat_y-1, gauge_width+2, gauge_height+2))
        # 枠（白）
        pygame.draw.rect(screen, WHITE, (gauge_x, heat_y, gauge_width, gauge_height), 1)
        # ヒートゲージ本体（色は熱さに応じて変化）
        if self.heat > 0:
            heat_width = int(gauge_width * (self.heat / 100))
            if self.heat < 50:
                color = YELLOW
            elif self.heat < 80:
                color = ORANGE
            else:
                color = RED
            pygame.draw.rect(screen, color, (gauge_x, heat_y, heat_width, gauge_height))
        
        # ゲージの値を表示
        font = pygame.font.Font(None, 24)
        hp_text = font.render(f"HP: {int(self.hp)}%", True, WHITE)
        heat_text = font.render(f"HEAT: {int(self.heat)}%", True, WHITE)
        screen.blit(hp_text, (gauge_x + gauge_width + margin, hp_y))
        screen.blit(heat_text, (gauge_x + gauge_width + margin, heat_y))

    def find_cluster_center(self, enemies):
        if not enemies:
            return None
            
        # プレイヤーの周囲500ピクセル以内の敵のみを対象とする
        nearby_enemies = []
        player_center_x = self.x + self.width/2
        player_center_y = self.y + self.height/2
        
        for enemy in enemies:
            enemy_center_x = enemy.x + enemy.width/2
            enemy_center_y = enemy.y + enemy.height/2
            dx = enemy_center_x - player_center_x
            dy = enemy_center_y - player_center_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance <= 500:  # 500ピクセル以内の敵のみを追加
                nearby_enemies.append(enemy)
        
        if not nearby_enemies:
            return None
            
        # 画面を4x4のグリッドに分割
        grid_size = 4
        grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        
        # 各グリッドの敵の数をカウント
        for enemy in nearby_enemies:  # nearby_enemiesを使用
            grid_x = int(enemy.x * grid_size / SCREEN_WIDTH)
            grid_y = int(enemy.y * grid_size / SCREEN_HEIGHT)
            grid_x = max(0, min(grid_x, grid_size-1))
            grid_y = max(0, min(grid_y, grid_size-1))
            grid[grid_y][grid_x] += 1
        
        # 最も敵が多いグリッドを見つける
        max_count = 0
        max_x = 0
        max_y = 0
        for y in range(grid_size):
            for x in range(grid_size):
                if grid[y][x] > max_count:
                    max_count = grid[y][x]
                    max_x = x
                    max_y = y
        
        if max_count > 0:
            # グリッドの中心座標を返す
            center_x = (max_x + 0.5) * SCREEN_WIDTH / grid_size
            center_y = (max_y + 0.5) * SCREEN_HEIGHT / grid_size
            return (center_x, center_y)
        return None
        
    # アドバタイズモード関連
    def toggle_advertise_mode(self):
        """アドバタイズモード（自動操作）の切り替え"""
        self.advertise_mode = not self.advertise_mode
        # モード切り替え時にタイマーリセット
        if self.advertise_mode:
            self.advertise_action_timer = 0
            self.advertise_movement_timer = 0
            self.advertise_target_x = None
            self.advertise_target_y = None
            # 画面認識モードの初期化
            self.visual_mode = True  # 画面認識モードをオン
            self.detected_enemies = []  # 画面から検出した敵
            self.detected_safe_zones = []  # 画面から検出した安全地帯
            self.visual_analysis_timer = 0  # 画面分析タイマー
        return self.advertise_mode
        
    def update_advertise_mode(self, enemies, bullets):
        """アドバタイズモードの更新処理"""
        if not self.advertise_mode:
            return

        # 自機の状態をチェック
        if self.hp < self.max_hp * 0.3:  # HPが30%以下になったら危険回避行動
            # HPが低い時は攻撃頻度を下げて回避行動を優先
            self.advertise_action_interval = 120  # 通常の2倍の間隔
        else:
            # HPが十分ある時は通常の攻撃頻度
            self.advertise_action_interval = 60
            
        # 画面分析（10フレームごと）
        self.visual_analysis_timer += 1
        if self.visual_mode and self.visual_analysis_timer >= 10:
            self.visual_analysis_timer = 0
            self.analyze_screen()
            
        # 移動処理の更新（画面認識結果を使用）
        if self.visual_mode:
            self.update_advertise_movement_visual()
        else:
            # 従来の内部データ参照方式
            self.update_advertise_movement(enemies)
        
        # アクション処理の更新
        self.advertise_action_timer += 1
        if self.advertise_action_timer >= self.advertise_action_interval:
            self.advertise_action_timer = 0
            if self.visual_mode:
                self.perform_advertise_action_visual(bullets)
            else:
                self.perform_advertise_action(enemies, bullets)
                
    def analyze_screen(self):
        """画面をキャプチャして分析"""
        # 画面全体をキャプチャ
        screen_copy = screen.copy()
        
        # 敵の検出（赤色ピクセルを探す）
        self.detected_enemies = []
        
        # 画面を小さなグリッドに分割して分析（パフォーマンス向上のため）
        grid_size = 10  # 20x20から10x10ピクセルのグリッドに変更して検出精度を上げる
        for x in range(0, SCREEN_WIDTH, grid_size):
            for y in range(0, SCREEN_HEIGHT, grid_size):
                # このグリッド内の一部のピクセルをサンプリング
                grid_rect = pygame.Rect(x, y, grid_size, grid_size)
                grid_surface = screen_copy.subsurface(grid_rect)
                
                # 中央のピクセルの色を取得
                try:
                    center_color = grid_surface.get_at((grid_size//2, grid_size//2))
                    
                    # 敵の色（赤系、青系、紫系など）を検出して範囲を広げる
                    if ((center_color[0] > 150 and center_color[1] < 100 and center_color[2] < 100) or  # 赤系
                        (center_color[0] < 100 and center_color[1] < 100 and center_color[2] > 150) or  # 青系
                        (center_color[0] > 100 and center_color[1] < 100 and center_color[2] > 100)):   # 紫系
                        # 敵らしきピクセルを検出
                        enemy_pos = (x + grid_size//2, y + grid_size//2)
                        
                        # 既に近い位置で検出済みでなければ追加
                        is_new = True
                        for ex, ey in self.detected_enemies:
                            dist = math.sqrt((ex - enemy_pos[0])**2 + (ey - enemy_pos[1])**2)
                            if dist < 30:  # 40から30に変更してより細かく識別
                                is_new = False
                                break
                                
                        if is_new:
                            self.detected_enemies.append(enemy_pos)
                except:
                    # インデックスエラーなどは無視
                    pass
        
        # 安全地帯の検出（暗い領域 = 敵が少ない）
        self.detected_safe_zones = []
        
        # 画面を5x5の大きなグリッドに分割（より細かく区分）
        safe_grid_size_x = SCREEN_WIDTH // 5
        safe_grid_size_y = SCREEN_HEIGHT // 5
        
        for x in range(0, SCREEN_WIDTH, safe_grid_size_x):
            for y in range(0, SCREEN_HEIGHT, safe_grid_size_y):
                # このグリッド内の敵の数をカウント
                enemy_count = 0
                for ex, ey in self.detected_enemies:
                    if x <= ex < x + safe_grid_size_x and y <= ey < y + safe_grid_size_y:
                        enemy_count += 1
                
                # セーフゾーンの中心座標
                safe_center = (x + safe_grid_size_x//2, y + safe_grid_size_y//2)
                
                # 最も近い敵との距離を計算
                min_distance = float('inf')
                for ex, ey in self.detected_enemies:
                    distance = math.sqrt((safe_center[0] - ex)**2 + (safe_center[1] - ey)**2)
                    min_distance = min(min_distance, distance)
                
                # 敵がいない場合は最大安全度
                if not self.detected_enemies:
                    min_distance = float('inf')
                
                # 安全度をレベル分け（0=低, 1=中, 2=高）
                safety_level = 2  # デフォルトで最高安全度
                if min_distance < 150:
                    safety_level = 0  # 危険
                elif min_distance < 300:
                    safety_level = 1  # 中程度
                
                # 敵がいないグリッドまたは敵から十分離れたグリッドを安全地帯として記録
                if enemy_count == 0 or min_distance > 100:
                    self.detected_safe_zones.append((safe_center[0], safe_center[1], safety_level))
    
    def update_advertise_movement_visual(self):
        """画面認識に基づく移動更新"""
        # 移動タイマーの更新
        self.advertise_movement_timer += 1
        
        # 円周運動戦術の発動条件: 一定数以上の敵が検出された場合
        circular_tactic_threshold = 3  # この数以上の敵がいる場合に発動
        use_circular_tactic = len(self.detected_enemies) >= circular_tactic_threshold and random.random() < 0.15
        
        # 敵が一定数以上いる場合は円周運動による誘導戦術を実行
        if use_circular_tactic:
            # 円運動のために時間をベースにした角度を計算
            time_factor = (pygame.time.get_ticks() % 10000) / 10000.0  # 0～1の値（10秒周期）
            angle = time_factor * 2 * math.pi  # 0～2πの角度
            
            # 画面中央を中心とした円運動を計算
            center_x = SCREEN_WIDTH // 2
            center_y = SCREEN_HEIGHT // 2
            radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.3  # 画面の30%の半径
            
            # 目標座標を円周上に設定
            target_x = center_x + math.cos(angle) * radius
            target_y = center_y + math.sin(angle) * radius
            
            # 現在位置と目標位置の差分
            dx = target_x - (self.x + self.width/2)
            dy = target_y - (self.y + self.height/2)
            
            # 移動方向の正規化
            distance = max(1, math.sqrt(dx*dx + dy*dy))
            dx /= distance
            dy /= distance
            
            # 向きの更新（移動方向を向く）
            if dx > 0:
                self.facing_right = True
            elif dx < 0:
                self.facing_right = False
            
            # 通常速度で移動
            move_speed = self.max_speed * 1.2  # 少し速めに移動して円を描く
            self.x += dx * move_speed
            self.y += dy * move_speed
            
            # 誘導効果のビジュアルフィードバック
            if random.random() < 0.2:  # 20%の確率でエフェクト発生
                center_x = self.x + self.width/2
                center_y = self.y + self.height/2
                # 引きつけ効果のリング（青→白のグラデーション）
                self.ring_effects.append(RingEffect(center_x, center_y, (100, 150, 255), 80, 2.5, 0.04))
            
            # 敵が十分集まったと判断したら（近距離に4体以上）、攻撃行動へのフラグを立てる
            dangerous_enemies = []
            for ex, ey in self.detected_enemies:
                dx = ex - (self.x + self.width/2)
                dy = ey - (self.y + self.height/2)
                distance = math.sqrt(dx*dx + dy*dy)
                if distance < 200:  # 200ピクセル以内を危険/近距離とみなす
                    dangerous_enemies.append((ex, ey, distance))
            
            close_enemies_count = len(dangerous_enemies)
            if close_enemies_count >= 4:  # 4体以上が近くに集まったら攻撃準備
                # タイマーをリセットして次のアクションで必ず攻撃するようにする
                self.advertise_action_timer = self.advertise_action_interval - 1
                
                # チャージショットのためのエフェクト
                center_x = self.x + self.width/2
                center_y = self.y + self.height/2
                for i in range(3):
                    self.ring_effects.append(RingEffect(center_x, center_y, (150, 255, 150), 50 + i*10, 2, 0.1))
            
            # 誘導戦術実行中は他の移動ロジックをスキップ
            return
        
        # 誘導型戦術の発動条件: 既存のロジック維持
        use_grouping_tactics = len(self.detected_enemies) >= 3 and random.random() < 0.1 and not use_circular_tactic
        
        # 危険な敵を探す（検出した敵から判断）
        dangerous_enemies = []
        for ex, ey in self.detected_enemies:
            # プレイヤーと敵の距離を計算
            dx = ex - (self.x + self.width/2)
            dy = ey - (self.y + self.height/2)
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 200:  # 150から200ピクセルに増加して早期検出
                dangerous_enemies.append((ex, ey, distance))
        
        # 距離でソート（最も近い敵を優先）
        dangerous_enemies.sort(key=lambda e: e[2])
        
        # 誘導型戦術の実行: 敵を引きつけてグループ化
        if use_grouping_tactics and len(self.detected_enemies) >= 3:
            # 画面の中央付近に移動して敵を引きつける
            center_x = SCREEN_WIDTH // 2 + random.randint(-100, 100)
            center_y = SCREEN_HEIGHT // 2 + random.randint(-100, 100)
            
            # 現在位置と目標位置の差分
            dx = center_x - (self.x + self.width/2)
            dy = center_y - (self.y + self.height/2)
            
            # 移動方向の正規化
            distance = max(1, math.sqrt(dx*dx + dy*dy))
            dx /= distance
            dy /= distance
            
            # 通常速度で移動（敵を引きつけるため）
            self.x += dx * self.max_speed * 0.7  # 少し遅めに移動して敵を惹きつける
            self.y += dy * self.max_speed * 0.7
            
            # 引きつけ効果のビジュアルフィードバック
            if random.random() < 0.3:  # 30%の確率でエフェクト発生
                center_x = self.x + self.width/2
                center_y = self.y + self.height/2
                # 引きつけ効果のリング（青→白のグラデーション）
                self.ring_effects.append(RingEffect(center_x, center_y, (100, 150, 255), 100, 3, 0.03))
            
            # 敵が十分集まったと判断したら（近距離に3体以上）、攻撃行動へのフラグを立てる
            close_enemies_count = sum(1 for ex, ey, dist in dangerous_enemies if dist < 150)
            if close_enemies_count >= 3:
                # タイマーをリセットして次のアクションで必ず攻撃するようにする
                self.advertise_action_timer = self.advertise_action_interval - 1
                
                # チャージショットのためのエフェクト
                center_x = self.x + self.width/2
                center_y = self.y + self.height/2
                for i in range(3):
                    self.ring_effects.append(RingEffect(center_x, center_y, (150, 255, 150), 50 + i*10, 2, 0.1))
            
            return  # 誘導戦術実行中は他の行動をスキップ
        
        # 危険な敵がいる場合は回避行動を優先
        elif dangerous_enemies:
            # 最も危険な敵
            ex, ey, distance = dangerous_enemies[0]
            
            # 敵から離れる方向を計算
            dx = (self.x + self.width/2) - ex
            dy = (self.y + self.height/2) - ey
            
            # 回避方向の正規化
            magnitude = max(1, math.sqrt(dx*dx + dy*dy))
            dx /= magnitude
            dy /= magnitude
            
            # 敵との距離に応じて回避の緊急度を調整
            urgency_factor = 1.0
            if distance < 100:  # かなり近い
                urgency_factor = 1.5  # より急いで逃げる
            
            # 画面端に近い場合、方向を調整
            if self.x < 50:
                dx = max(0, dx)  # 左端なら右方向に修正
            elif self.x > SCREEN_WIDTH - 50:
                dx = min(0, dx)  # 右端なら左方向に修正
                
            if self.y < 50:
                dy = max(0, dy)  # 上端なら下方向に修正
            elif self.y > SCREEN_HEIGHT - 50:
                dy = min(0, dy)  # 下端なら上方向に修正
            
            # 緊急回避のためダッシュを使用
            move_speed = self.dash_speed * urgency_factor
            
            # ダッシュエフェクト
            center_x = self.x + self.width/2
            center_y = self.y + self.height/2
            self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3, 0.1))
            self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.5, 0.15))
            
            # 回避移動
            self.x += dx * move_speed
            self.y += dy * move_speed
            
            # 回避行動のため目標位置リセット
            self.advertise_target_x = None
            self.advertise_target_y = None
        else:
            # 通常の移動ロジック（危険がない場合）
            # 新しい目標位置の設定
            if self.advertise_target_x is None or self.advertise_movement_timer >= self.advertise_movement_duration:
                self.advertise_movement_timer = 0
                margin = 100  # 画面端からのマージン
                
                # 高安全度のセーフゾーンがあれば優先的に選択
                high_safety_zones = [zone for zone in self.detected_safe_zones if zone[2] == 2]
                medium_safety_zones = [zone for zone in self.detected_safe_zones if zone[2] == 1]
                low_safety_zones = [zone for zone in self.detected_safe_zones if zone[2] == 0]
                
                # 優先度の高いセーフゾーンから順に選択
                if high_safety_zones and random.random() < 0.8:  # 80%の確率で高安全地帯を選択
                    chosen_zone = random.choice(high_safety_zones)
                    self.advertise_target_x = chosen_zone[0]
                    self.advertise_target_y = chosen_zone[1]
                elif medium_safety_zones and random.random() < 0.6:  # 60%の確率で中安全地帯を選択
                    chosen_zone = random.choice(medium_safety_zones)
                    self.advertise_target_x = chosen_zone[0]
                    self.advertise_target_y = chosen_zone[1]
                elif low_safety_zones and random.random() < 0.3:  # 30%の確率で低安全地帯を選択
                    chosen_zone = random.choice(low_safety_zones)
                    self.advertise_target_x = chosen_zone[0]
                    self.advertise_target_y = chosen_zone[1]
                else:
                    # セーフゾーンが見つからない場合はランダムな位置を選択
                    self.advertise_target_x = random.randint(margin, SCREEN_WIDTH - margin)
                    self.advertise_target_y = random.randint(margin, SCREEN_HEIGHT - margin)
            
            # 目標位置に向かって移動
            if self.advertise_target_x is not None:
                # 現在位置と目標位置の差分
                dx = self.advertise_target_x - (self.x + self.width/2)
                dy = self.advertise_target_y - (self.y + self.height/2)
                
                # 差分が小さい場合、到着したと判断
                if abs(dx) < 10 and abs(dy) < 10:
                    self.advertise_target_x = None
                    self.advertise_target_y = None
                    return
                
                # 移動方向の正規化
                distance = max(1, math.sqrt(dx*dx + dy*dy))
                dx /= distance
                dy /= distance
                
                # 向きの更新
                if dx > 0:
                    self.facing_right = True
                elif dx < 0:
                    self.facing_right = False
                
                # 最終的な速度を計算
                move_speed = self.max_speed
                if random.random() < 0.05:  # 5%の確率でダッシュ
                    move_speed = self.dash_speed
                    # ダッシュエフェクト
                    center_x = self.x + self.width/2
                    center_y = self.y + self.height/2
                    # 外側のリング
                    self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3, 0.1))
                    self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3.2, 0.1))
                    # 内側のリング
                    self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.5, 0.15))
                    self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.7, 0.15))
                    
                # 移動の適用
                self.x += dx * move_speed
                self.y += dy * move_speed
        
        # 画面外に出ないように調整
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))

    def perform_advertise_action_visual(self, bullets):
        """画面認識に基づくアクション実行"""
        # アクション選択の重み付けを変更して攻撃を優先
        action_weights = {
            "beam_rifle": 0.45,  # 頻度を増加
            "charge_shot": 0.25, # チャージショットも増加
            "dash": 0.2,        
            "scan": 0.1         
        }
        
        # 重み付けに基づいてアクションを選択
        actions = list(action_weights.keys())
        weights = list(action_weights.values())
        action = random.choices(actions, weights=weights, k=1)[0]
        
        # 敵が近くにいる場合は攻撃確率を上げる
        close_enemies = []
        for ex, ey in self.detected_enemies:
            dx = ex - (self.x + self.width/2)
            dy = ey - (self.y + self.height/2)
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < 300:  # 300ピクセル以内なら接近中と判断
                close_enemies.append((ex, ey, distance))
        
        # 接近してくる敵がいる場合は80%の確率で攻撃アクションに強制変更
        if close_enemies and random.random() < 0.8:
            action = random.choice(["beam_rifle", "charge_shot"])
        
        # 周囲に多数の敵が集まっている場合（誘導戦術の結果）は必ずチャージショット
        group_attack_threshold = 3  # この数以上の敵が近くにいる場合
        close_enemies_count = len([e for e in close_enemies if e[2] < 150])
        if close_enemies_count >= group_attack_threshold:
            action = "charge_shot"
        
        if action == "beam_rifle" and self.can_fire():
            # 通常射撃 - 検出した敵がいれば、その方向に射撃
            if self.detected_enemies:
                # 接近中の敵を優先
                target_positions = close_enemies if close_enemies else [
                    (ex, ey, math.sqrt((ex - (self.x + self.width/2))**2 + (ey - (self.y + self.height/2))**2))
                    for ex, ey in self.detected_enemies
                ]
                
                # 距離でソート
                target_positions.sort(key=lambda e: e[2])
                
                # 最大3体まで狙う
                targets = target_positions[:3]
                
                sound_effects.play('shoot')
                for tx, ty, _ in targets:
                    # 敵の方向に弾を発射
                    bullet_x = self.x + (self.width if self.facing_right else 0)
                    bullet_y = self.y + self.height // 2
                    
                    # 敵の方向を計算
                    dx = tx - bullet_x
                    dy = ty - bullet_y
                    angle = math.atan2(dy, dx)
                    
                    # この角度情報から弾を発射
                    facing_right = dx > 0
                    # ターゲット座標を明示的に設定
                    target_pos = (tx, ty)
                    bullets.append(Bullet(bullet_x, bullet_y, facing_right=facing_right, target_pos=target_pos))
                
                # 射撃後クールダウン
                self.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"]
            else:
                # 敵が見つからなければ正面に発射
                sound_effects.play('shoot')
                bullet_x = self.x + (self.width if self.facing_right else 0)
                bullet_y = self.y + self.height // 2
                bullets.append(Bullet(bullet_x, bullet_y, facing_right=self.facing_right))
                self.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"]
                
        elif action == "charge_shot" and self.can_fire():
            # チャージショット - 画面をスキャンして敵が密集している方向に発射
            sound_effects.play('charge_shot')
            charge_level = 1
            bullet_x = self.x + (self.width if self.facing_right else 0)
            bullet_y = self.y + self.height // 2
            
            # 敵が検出されていれば、その方向に発射
            if self.detected_enemies:
                # 集団攻撃モード: 複数の敵が近くにいる場合
                if close_enemies_count >= group_attack_threshold:
                    # 群集の中心を計算
                    total_x, total_y = 0, 0
                    for ex, ey, _ in close_enemies:
                        total_x += ex
                        total_y += ey
                    center_x = total_x / len(close_enemies)
                    center_y = total_y / len(close_enemies)
                    
                    # 群集の中心に向けてチャージショット
                    dx = center_x - (self.x + self.width/2)
                    dy = center_y - (self.y + self.height/2)
                    facing_right = dx > 0
                    target_pos = (center_x, center_y)
                    
                    # チャージショット発射（集団攻撃用の特別パラメータ）
                    # より強力なチャージショット
                    charge_level = 1  # 最大チャージ
                    
                    # 爆発的なエフェクト（攻撃エフェクト強化）
                    for i in range(5):
                        center_x = self.x + self.width/2
                        center_y = self.y + self.height/2
                        self.ring_effects.append(RingEffect(
                            center_x, center_y, 
                            (150 + random.randint(0, 105), 200 + random.randint(0, 55), 150),
                            30 + i*10, 2 + random.random(), 0.08 + random.random() * 0.05
                        ))
                    
                    # チャージショット発射
                    bullets.append(Bullet(bullet_x, bullet_y, facing_right=facing_right, 
                                         bullet_type="beam_rifle", charge_level=charge_level, target_pos=target_pos))
                
                # 通常の接近敵優先ロジック
                elif close_enemies:
                    # 最も近い敵に向けてチャージショット
                    ex, ey, _ = min(close_enemies, key=lambda e: e[2])
                    dx = ex - (self.x + self.width/2)
                    dy = ey - (self.y + self.height/2)
                    facing_right = dx > 0
                    target_pos = (ex, ey)
                    
                    # チャージショット発射
                    bullets.append(Bullet(bullet_x, bullet_y, facing_right=facing_right, 
                                         bullet_type="beam_rifle", charge_level=charge_level, target_pos=target_pos))
                else:
                    # 敵の密度が高い方向を計算
                    enemy_clusters = {}
                    for ex, ey in self.detected_enemies:
                        # 方向を45度単位で量子化
                        dx = ex - (self.x + self.width/2)
                        dy = ey - (self.y + self.height/2)
                        angle = math.degrees(math.atan2(dy, dx))
                        angle_quantized = int(angle / 45) * 45
                        
                        # その方向の敵カウントを増やす
                        if angle_quantized in enemy_clusters:
                            enemy_clusters[angle_quantized] += 1
                        else:
                            enemy_clusters[angle_quantized] = 1
                    
                    # 最も敵が多い方向を選択
                    if enemy_clusters:
                        best_angle = max(enemy_clusters, key=enemy_clusters.get)
                        # この角度から発射方向を決定
                        dx = math.cos(math.radians(best_angle))
                        dy = math.sin(math.radians(best_angle))
                        facing_right = dx > 0
                        
                        # チャージショット発射
                        bullets.append(Bullet(bullet_x, bullet_y, facing_right=facing_right, 
                                             bullet_type="beam_rifle", charge_level=charge_level))
                    else:
                        # 方向が決まらなければ正面に発射
                        bullets.append(Bullet(bullet_x, bullet_y, facing_right=self.facing_right, 
                                             bullet_type="beam_rifle", charge_level=charge_level))
            else:
                # 敵が見つからなければ正面に発射
                bullets.append(Bullet(bullet_x, bullet_y, facing_right=self.facing_right, 
                                     bullet_type="beam_rifle", charge_level=charge_level))
            
            # 射撃後クールダウン（チャージショット後は少し長く）
            self.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"] * 3
                
        elif action == "dash":
            # ダッシュ演出
            sound_effects.play('dash')
            # 複数のダッシュエフェクトを生成
            for i in range(3):  # 3セットのエフェクト
                center_x = self.x + self.width/2
                center_y = self.y + self.height/2
                # 外側のリング
                self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3, 0.1))
                # 内側のリング
                self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.5, 0.15))
                
        elif action == "scan":
            # スキャン演出（周囲に広がる波紋）
            center_x = self.x + self.width/2
            center_y = self.y + self.height/2
            
            # スキャン波紋エフェクト（大中小3サイズ）
            self.ring_effects.append(RingEffect(center_x, center_y, WHITE, 150, 4, 0.01))
            self.ring_effects.append(RingEffect(center_x, center_y, (150, 220, 255), 100, 3, 0.015))
            self.ring_effects.append(RingEffect(center_x, center_y, (100, 180, 255), 50, 2, 0.02))
            
            # 新しいターゲットを設定
            if enemies:
                self.locked_enemy = random.choice(enemies)

    def find_dangerous_enemies(self, enemies):
        """危険な敵（近くにいる敵）を見つける"""
        dangerous_distance = 150  # 危険と判断する距離
        dangerous_enemies = []
        
        for enemy in enemies:
            if enemy.is_exploding:
                continue  # 爆発中の敵は無視
                
            # 敵とプレイヤーの距離を計算
            dx = (enemy.x + enemy.width/2) - (self.x + self.width/2)
            dy = (enemy.y + enemy.height/2) - (self.y + self.height/2)
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < dangerous_distance:
                dangerous_enemies.append((enemy, distance))
        
        # 距離の昇順でソート（最も近い敵を先頭に）
        dangerous_enemies.sort(key=lambda x: x[1])
        return [enemy for enemy, _ in dangerous_enemies]

    def perform_advertise_action(self, enemies, bullets):
        """アドバタイズモードのアクション実行"""
        # ランダムなアクションを選択
        action = random.choice([
            "beam_rifle",  # 通常射撃
            "charge_shot", # チャージショット
            "dash",        # ダッシュ
            "scan"         # 敵スキャン
        ])
        
        if action == "beam_rifle" and self.can_fire():
            # 通常射撃
            # 画面上の敵を探索
            visible_enemies = [enemy for enemy in enemies if not enemy.is_exploding and 
                              0 <= enemy.x <= SCREEN_WIDTH and
                              0 <= enemy.y <= SCREEN_HEIGHT]
            
            if visible_enemies:
                # 最大3体までの敵を優先的に狙う
                targets = sorted(visible_enemies, key=lambda e: ((e.x - self.x) ** 2 + (e.y - self.y) ** 2))[:3]
                
                sound_effects.play('shoot')
                for target in targets:
                    # 敵ごとにビームを発射
                    bullet_x = self.x + (self.width if self.facing_right else 0)
                    bullet_y = self.y + self.height // 2
                    bullets.append(Bullet(bullet_x, bullet_y, target=target, facing_right=self.facing_right))
                
                # 射撃後クールダウン
                self.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"]
            else:
                # 敵がいない場合は正面に発射
                sound_effects.play('shoot')
                bullet_x = self.x + (self.width if self.facing_right else 0)
                bullet_y = self.y + self.height // 2
                bullets.append(Bullet(bullet_x, bullet_y, facing_right=self.facing_right))
                self.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"]
                
        elif action == "charge_shot" and self.can_fire():
            # チャージショット
            sound_effects.play('charge_shot')
            # 完全チャージ状態のビームを発射
            charge_level = 1  # チャージレベルを1に変更（有効な値に）
            bullet_x = self.x + (self.width if self.facing_right else 0)
            bullet_y = self.y + self.height // 2
            
            # 敵がいる場合はその方向に発射
            if enemies:
                target = random.choice(enemies)
                bullets.append(Bullet(bullet_x, bullet_y, target=target, facing_right=self.facing_right, 
                                     bullet_type="beam_rifle", charge_level=charge_level))
            else:
                # 敵がいない場合は正面に発射
                bullets.append(Bullet(bullet_x, bullet_y, facing_right=self.facing_right, 
                                     bullet_type="beam_rifle", charge_level=charge_level))
            
            # 射撃後クールダウン
            self.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"] * 3
                
        elif action == "dash":
            # ダッシュ演出
            sound_effects.play('dash')
            # 複数のダッシュエフェクトを生成
            for i in range(3):  # 3セットのエフェクト
                center_x = self.x + self.width/2
                center_y = self.y + self.height/2
                # 外側のリング
                self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3, 0.1))
                # 内側のリング
                self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.5, 0.15))
                
        elif action == "scan":
            # スキャン演出（周囲に広がる波紋）
            center_x = self.x + self.width/2
            center_y = self.y + self.height/2
            
            # スキャン波紋エフェクト（大中小3サイズ）
            self.ring_effects.append(RingEffect(center_x, center_y, WHITE, 150, 4, 0.01))
            self.ring_effects.append(RingEffect(center_x, center_y, (150, 220, 255), 100, 3, 0.015))
            self.ring_effects.append(RingEffect(center_x, center_y, (100, 180, 255), 50, 2, 0.02))
            
            # 新しいターゲットを設定
            if enemies:
                self.locked_enemy = random.choice(enemies)

    def draw_advertise_debug_info(self, screen):
        """アドバタイズモードでのAI状態情報を表示"""
        if not self.advertise_mode:
            return
            
        # デバッグ情報のフォント
        debug_font = pygame.font.SysFont(None, 24)
        
        # 背景の半透明パネル
        panel_surface = pygame.Surface((400, 240), pygame.SRCALPHA)  # 高さを少し増やす
        panel_surface.fill((0, 0, 0, 180))  # 半透明の黒
        screen.blit(panel_surface, (10, 10))
        
        # AI状態情報
        y_offset = 20
        
        # 危険な敵の数を計算
        dangerous_count = 0
        if 'enemies' in globals():
            dangerous_enemies = self.find_dangerous_enemies(enemies)
            dangerous_count = len(dangerous_enemies)
        
        # AIの行動モードを表示
        if hasattr(self, 'ai_behavior_mode'):
            mode_text = {
                "normal": "Normal Patrolling",
                "evade": "Evading Danger",
                "group_tactical": "Group Tactical Mode"
            }.get(self.ai_behavior_mode, "Unknown")
            
            mode_info = f"AI Behavior: {mode_text} ({self.ai_mode_timer}/{self.ai_mode_duration})"
            mode_surface = debug_font.render(mode_info, True, (255, 255, 255))
            screen.blit(mode_surface, (20, y_offset))
            y_offset += 25
        
        # 現在のAI判断を決定
        if 'enemies' in globals() and self.find_dangerous_enemies(enemies):
            ai_action = "Avoiding Danger" 
        else:
            ai_action = "Patrolling"
        
        # 画面認識モードに関する情報
        vision_mode = "Visual Recognition Mode" if self.visual_mode else "Internal Data Mode"
        detected_count = len(self.detected_enemies) if hasattr(self, 'detected_enemies') else 0
        safe_zones = len(self.detected_safe_zones) if hasattr(self, 'detected_safe_zones') else 0
            
        info_lines = [
            f"AI Status: Active ({vision_mode})",
            f"HP: {self.hp}/{self.max_hp}",
            f"Heat: {int(self.heat)}/{self.max_heat}",
            f"Action Interval: {self.advertise_action_interval}f",
            f"Next Action: {self.advertise_action_interval - self.advertise_action_timer}f",
            f"Dangerous Enemies: {dangerous_count}",
            f"Detected Objects: {detected_count}",
            f"Safe Zones: {safe_zones}",
            f"Target: {'Set' if self.advertise_target_x else 'None'}",
            f"Dash Status: {'Active' if self.is_dashing else 'Inactive'}",
            f"Current Decision: {ai_action}"
        ]
        
        # 画面描画
        for line in info_lines:
            text_surface = debug_font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (20, y_offset))
            y_offset += 20
        
        # 視覚的なAI認識情報の描画
        
        # 1. 検出した敵を可視化（黄色い枠）
        if hasattr(self, 'detected_enemies'):
            for ex, ey in self.detected_enemies:
                # 黄色い枠で検出した敵を表示
                rect_size = 30
                pygame.draw.rect(
                    screen, 
                    (255, 255, 0), 
                    (ex - rect_size//2, ey - rect_size//2, rect_size, rect_size), 
                    1
                )
                
                # 検出状態テキスト
                detect_text = debug_font.render("Detected", True, (255, 255, 0))
                screen.blit(detect_text, (ex + rect_size//2, ey - rect_size//2))
        
        # 2. 危険な敵への認識を表示（赤い円）
        for enemy in dangerous_enemies:
            # 赤い円で危険な敵を強調
            pygame.draw.circle(
                screen, 
                (255, 0, 0, 128), 
                (int(enemy.x + enemy.width/2), int(enemy.y + enemy.height/2)), 
                150, 
                2
            )
            
            # 敵からプレイヤーへの方向線（回避方向の反対）
            pygame.draw.line(
                screen,
                (255, 0, 0),
                (int(enemy.x + enemy.width/2), int(enemy.y + enemy.height/2)),
                (int(self.x + self.width/2), int(self.y + self.height/2)),
                1
            )
            
            # 危険状態テキスト
            danger_text = debug_font.render("Danger", True, (255, 0, 0))
            screen.blit(danger_text, (int(enemy.x), int(enemy.y) - 20))
        
        # 3. 安全地帯の可視化（段階的な色で表示）
        if hasattr(self, 'detected_safe_zones'):
            for sx, sy, safety_level in self.detected_safe_zones:
                # 安全度に応じて色を選択
                if safety_level == 2:
                    safe_color = (0, 255, 0)  # 高安全度 - 緑
                    radius = 50
                    safe_text = "Safe (High)"
                elif safety_level == 1:
                    safe_color = (255, 255, 0)  # 中安全度 - 黄
                    radius = 40
                    safe_text = "Safe (Medium)"
                else:
                    safe_color = (255, 165, 0)  # 低安全度 - オレンジ
                    radius = 30
                    safe_text = "Safe (Low)"
                
                # 色分けされた円で安全地帯を表示
                pygame.draw.circle(
                    screen, 
                    safe_color, 
                    (int(sx), int(sy)), 
                    radius, 
                    1
                )
                
                # 安全地帯テキスト
                safe_text_surface = debug_font.render(safe_text, True, safe_color)
                screen.blit(safe_text_surface, (int(sx) - 30, int(sy) - 10))
        
        # 4. 移動目標を表示（緑の×印）
        if self.advertise_target_x and self.advertise_target_y:
            # 緑の×印で移動目標を表示
            target_x = int(self.advertise_target_x)
            target_y = int(self.advertise_target_y)
            size = 10
            
            # ×印を描画
            pygame.draw.line(screen, (0, 255, 0), (target_x - size, target_y - size), 
                           (target_x + size, target_y + size), 2)
            pygame.draw.line(screen, (0, 255, 0), (target_x - size, target_y + size), 
                           (target_x + size, target_y - size), 2)
            
            # プレイヤーから目標への線
            pygame.draw.line(
                screen,
                (0, 255, 0),
                (int(self.x + self.width/2), int(self.y + self.height/2)),
                (target_x, target_y),
                1
            )
            
            # 目標への距離を表示
            dx = target_x - (self.x + self.width/2)
            dy = target_y - (self.y + self.height/2)
            distance = math.sqrt(dx*dx + dy*dy)
            dist_text = debug_font.render(f"{int(distance)}px", True, (0, 255, 0))
            screen.blit(dist_text, (target_x + 15, target_y - 10))

    def update_advertise_movement(self, enemies):
        """アドバタイズモードの移動更新（内部データ参照バージョン）"""
        # 移動タイマーの更新
        self.advertise_movement_timer += 1
        
        # 危険な敵を探す（衝突回避のため）
        dangerous_enemies = self.find_dangerous_enemies(enemies)
        
        # 危険な敵がいる場合は回避行動を優先
        if dangerous_enemies:
            # 最も危険な敵（最も近い敵）
            nearest_enemy = dangerous_enemies[0]
            
            # 敵から離れる方向を計算
            dx = (self.x + self.width/2) - (nearest_enemy.x + nearest_enemy.width/2)
            dy = (self.y + self.height/2) - (nearest_enemy.y + nearest_enemy.height/2)
            
            # 回避方向の正規化
            distance = max(1, math.sqrt(dx*dx + dy*dy))
            dx /= distance
            dy /= distance
            
            # 画面端に近い場合、方向を調整
            if self.x < 50:
                dx = max(0, dx)  # 左端なら右方向に修正
            elif self.x > SCREEN_WIDTH - 50:
                dx = min(0, dx)  # 右端なら左方向に修正
                
            if self.y < 50:
                dy = max(0, dy)  # 上端なら下方向に修正
            elif self.y > SCREEN_HEIGHT - 50:
                dy = min(0, dy)  # 下端なら上方向に修正
            
            # 緊急回避のためダッシュを使用
            move_speed = self.dash_speed
            
            # ダッシュエフェクト
            center_x = self.x + self.width/2
            center_y = self.y + self.height/2
            self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3, 0.1))
            self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.5, 0.15))
            
            # 回避移動
            self.x += dx * move_speed
            self.y += dy * move_speed
            
            # 回避行動のため目標位置リセット
            self.advertise_target_x = None
            self.advertise_target_y = None
        else:
            # 通常の移動ロジック（危険がない場合）
            # 新しい目標位置の設定
            if self.advertise_target_x is None or self.advertise_movement_timer >= self.advertise_movement_duration:
                self.advertise_movement_timer = 0
                margin = 100  # 画面端からのマージン
                
                # 安全地帯の評価
                safe_zones = []
                
                # 画面を5x5のグリッドに分割
                grid_size = 5
                grid_width = SCREEN_WIDTH / grid_size
                grid_height = SCREEN_HEIGHT / grid_size
                
                # 各グリッドの敵との距離に基づく安全度を計算
                for grid_y in range(grid_size):
                    for grid_x in range(grid_size):
                        grid_center_x = grid_x * grid_width + grid_width / 2
                        grid_center_y = grid_y * grid_height + grid_height / 2
                        
                        # 最も近い敵との距離を計算
                        min_distance = float('inf')
                        for enemy in enemies:
                            enemy_center_x = enemy.x + enemy.width / 2
                            enemy_center_y = enemy.y + enemy.height / 2
                            distance = math.sqrt((grid_center_x - enemy_center_x)**2 + (grid_center_y - enemy_center_y)**2)
                            min_distance = min(min_distance, distance)
                        
                        # 敵がいない場合は最大安全度
                        if not enemies:
                            min_distance = float('inf')
                        
                        # 安全度をレベル分け（0=低, 1=中, 2=高）
                        safety_level = 2  # デフォルトで最高安全度
                        if min_distance < 150:
                            safety_level = 0  # 危険
                        elif min_distance < 300:
                            safety_level = 1  # 中程度
                        
                        # グリッド内の敵の数もカウント
                        enemy_count = 0
                        for enemy in enemies:
                            if (grid_x * grid_width <= enemy.x < (grid_x + 1) * grid_width and
                                grid_y * grid_height <= enemy.y < (grid_y + 1) * grid_height):
                                enemy_count += 1
                        
                        # 敵がいないグリッドまたは敵から十分離れたグリッドを安全地帯として記録
                        if enemy_count == 0 or min_distance > 100:
                            safe_zones.append((grid_center_x, grid_center_y, safety_level))
                
                # 優先度の高いセーフゾーンから順に選択
                high_safety_zones = [zone for zone in safe_zones if zone[2] == 2]
                medium_safety_zones = [zone for zone in safe_zones if zone[2] == 1]
                low_safety_zones = [zone for zone in safe_zones if zone[2] == 0]
                
                if high_safety_zones and random.random() < 0.8:  # 80%の確率で高安全地帯を選択
                    chosen_zone = random.choice(high_safety_zones)
                    self.advertise_target_x = chosen_zone[0]
                    self.advertise_target_y = chosen_zone[1]
                elif medium_safety_zones and random.random() < 0.6:  # 60%の確率で中安全地帯を選択
                    chosen_zone = random.choice(medium_safety_zones)
                    self.advertise_target_x = chosen_zone[0]
                    self.advertise_target_y = chosen_zone[1]
                elif low_safety_zones and random.random() < 0.3:  # 30%の確率で低安全地帯を選択
                    chosen_zone = random.choice(low_safety_zones)
                    self.advertise_target_x = chosen_zone[0]
                    self.advertise_target_y = chosen_zone[1]
                else:
                    # セーフゾーンが見つからない場合はランダムな位置を選択
                    self.advertise_target_x = random.randint(margin, SCREEN_WIDTH - margin)
                    self.advertise_target_y = random.randint(margin, SCREEN_HEIGHT - margin)
            
            # 目標位置に向かって移動
            if self.advertise_target_x is not None:
                # 現在位置と目標位置の差分
                dx = self.advertise_target_x - (self.x + self.width/2)
                dy = self.advertise_target_y - (self.y + self.height/2)
                
                # 差分が小さい場合、到着したと判断
                if abs(dx) < 10 and abs(dy) < 10:
                    self.advertise_target_x = None
                    self.advertise_target_y = None
                    return
                
                # 移動方向の正規化
                distance = max(1, math.sqrt(dx*dx + dy*dy))
                dx /= distance
                dy /= distance
                
                # 向きの更新
                if dx > 0:
                    self.facing_right = True
                elif dx < 0:
                    self.facing_right = False
                
                # 最終的な速度を計算
                move_speed = self.max_speed
                if random.random() < 0.05:  # 5%の確率でダッシュ
                    move_speed = self.dash_speed
                    # ダッシュエフェクト
                    center_x = self.x + self.width/2
                    center_y = self.y + self.height/2
                    # 外側のリング
                    self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3, 0.1))
                    self.dash_effects.append(RingEffect(center_x, center_y, WHITE, 40, 3.2, 0.1))
                    # 内側のリング
                    self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.5, 0.15))
                    self.dash_effects.append(RingEffect(center_x, center_y, BLUE, 30, 2.7, 0.15))
                    
                # 移動の適用
                self.x += dx * move_speed
                self.y += dy * move_speed
        
        # 画面外に出ないように調整
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))

# 弾クラス
class Bullet:
    def __init__(self, x, y, target=None, facing_right=True, bullet_type="beam_rifle", charge_level=0, target_pos=None):
        self.x = x
        self.y = y
        
        # 弾の種類に応じたパラメータを設定
        params = BULLET_TYPES[bullet_type]
        self.speed = params["speed"]
        self.width = params["width"]
        self.height = params["height"]
        self.damage = params["damage"]
        self.homing_strength = params["homing_strength"]
        self.max_turn_angle = params["max_turn_angle"]
        self.min_homing_distance = params["min_homing_distance"]
        self.max_homing_distance = params["max_homing_distance"]
        self.color = params["color"]
        self.penetrate = False  # デフォルトは貫通なし
        self.explosion_effects = []  # 爆発エフェクトのリスト
        self.trail_positions = []  # 弾道の位置を記録
        self.trail_life = 30  # 弾道の持続フレーム数
        self.trail_explosion_timer = 0  # 弾道爆発のタイマー
        self.trail_explosion_interval = 5  # 爆発の間隔（フレーム）
        self.trail_explosion_duration = 60  # 弾道爆発の持続時間
        
        # チャージレベルに応じたパラメータ補正
        if charge_level > 0 and "charge_levels" in params:
            charge_params = params["charge_levels"][charge_level]
            self.speed *= charge_params["speed"]
            self.damage *= charge_params["damage"]
            self.color = charge_params["color"]
            if "height_multiplier" in charge_params:
                self.height = int(self.height * charge_params["height_multiplier"])
            if "width_multiplier" in charge_params:
                self.width = int(self.width * charge_params["width_multiplier"])
            if "penetrate" in charge_params:
                self.penetrate = charge_params["penetrate"]
            if "disable_homing" in charge_params:
                self.homing_strength = 0  # ホーミングを無効化
        
        self.target = target
        
        # 初期の移動方向を設定
        if target_pos:  # チャージ弾の密集地点がある場合
            dx = target_pos[0] - (x + self.width/2)
            dy = target_pos[1] - (y + self.height/2)
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                self.dx = dx / length
                self.dy = dy / length
            else:
                self.dx = 0
                self.dy = -1
        elif target:  # 通常のロックオン対象がある場合
            dx = (target.x + target.width/2) - (x + self.width/2)
            dy = (target.y + target.height/2) - (y + self.height/2)
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                self.dx = dx / length
                self.dy = dy / length
            else:
                self.dx = 0
                self.dy = -1
        else:  # ターゲットがない場合
            self.dx = 1 if facing_right else -1
            self.dy = 0
        
        # 弾の角度を計算（描画用）
        self.angle = math.degrees(math.atan2(-self.dy, self.dx)) - 90
        
    def move(self):
        # 現在位置を弾道履歴に追加
        self.trail_positions.append((self.x + self.width/2, self.y + self.height/2))
        if len(self.trail_positions) > self.trail_life:
            self.trail_positions.pop(0)
            
        # チャージショットの弾道爆発処理
        if self.penetrate and len(self.trail_positions) > 2:
            self.trail_explosion_timer += 1
            if self.trail_explosion_timer >= self.trail_explosion_interval:
                self.trail_explosion_timer = 0
                # ランダムな位置で爆発を生成
                if len(self.trail_positions) > 2:
                    explosion_index = random.randint(0, len(self.trail_positions) - 1)
                    pos = self.trail_positions[explosion_index]
                    # 小規模な爆発エフェクト
                    self.explosion_effects.append(RingEffect(pos[0], pos[1], NEGI_COLOR, 30, 2, 0.15))
                    self.explosion_effects.append(RingEffect(pos[0], pos[1], WHITE, 20, 1.5, 0.2))
        
        # 通常のビームライフルの弾道爆発処理を追加
        elif not self.penetrate and len(self.trail_positions) > 2:
            self.trail_explosion_timer += 1
            if self.trail_explosion_timer >= self.trail_explosion_interval:
                self.trail_explosion_timer = 0
                # ランダムな位置で爆発を生成
                if len(self.trail_positions) > 2:
                    explosion_index = random.randint(0, len(self.trail_positions) - 1)
                    pos = self.trail_positions[explosion_index]
                    # 青白い小規模な爆発エフェクト
                    self.explosion_effects.append(RingEffect(pos[0], pos[1], (100, 200, 255), 20, 2, 0.15))
                    self.explosion_effects.append(RingEffect(pos[0], pos[1], WHITE, 15, 1.5, 0.2))
        
        # 既存の移動処理
        if self.target and self.target.y > 0 and self.homing_strength > 0:
            # ターゲットまでのベクトルを計算
            dx = (self.target.x + self.target.width/2) - (self.x + self.width/2)
            dy = (self.target.y + self.target.height/2) - (self.y + self.height/2)
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                # 目標角度を計算
                target_angle = math.degrees(math.atan2(-dy, dx))
                current_angle = math.degrees(math.atan2(-self.dy, self.dx))
                
                # 角度の差を計算（-180から180の範囲に正規化）
                angle_diff = (target_angle - current_angle + 180) % 360 - 180
                
                # 最大旋回角度を適用（距離による補正なし）
                turn_angle = min(max(angle_diff * self.homing_strength, -self.max_turn_angle), self.max_turn_angle)
                
                # 新しい角度を計算
                new_angle = current_angle + turn_angle
                
                # 新しい方向ベクトルを計算
                self.dx = math.cos(math.radians(new_angle))
                self.dy = -math.sin(math.radians(new_angle))
                
                # 弾の表示角度を更新
                self.angle = math.degrees(math.atan2(-self.dy, self.dx)) - 90
        
        # 移動処理
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        
    def draw(self):
        # 弾道の描画（チャージショットの場合のみ）
        if self.penetrate:
            for i in range(len(self.trail_positions) - 1):
                pos1 = self.trail_positions[i]
                pos2 = self.trail_positions[i + 1]
                alpha = int(255 * (i / len(self.trail_positions)))
                trail_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
                pygame.draw.circle(trail_surface, (*NEGI_COLOR, alpha), (2, 2), 2)
                screen.blit(trail_surface, (pos1[0] - 2, pos1[1] - 2))
                
        # 爆発エフェクトの更新と描画
        self.explosion_effects = [effect for effect in self.explosion_effects if effect.update()]
        for effect in self.explosion_effects:
            effect.draw(screen)
            
        # 弾を回転させて描画
        bullet_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # グラデーション効果の描画（先端部分を白く）
        tip_length = min(20, self.height // 3)  # 先端の白い部分の長さ
        
        # 基本色で全体を描画
        pygame.draw.rect(bullet_surface, self.color, (0, 0, self.width, self.height))
        
        # 先端部分のグラデーション
        for i in range(tip_length):
            progress = i / tip_length
            # 白への遷移を4倍強く
            white_factor = (1 - progress) * 4
            white_factor = min(1.0, white_factor)  # 1.0を超えないように制限
            
            r = int(self.color[0] + (255 - self.color[0]) * white_factor)
            g = int(self.color[1] + (255 - self.color[1]) * white_factor)
            b = int(self.color[2] + (255 - self.color[2]) * white_factor)
            gradient_color = (r, g, b)
            
            # 先端部分に白いグラデーションを描画
            pygame.draw.rect(bullet_surface, gradient_color, 
                           (0, i, self.width, 1))
        
        rotated_surface = pygame.transform.rotate(bullet_surface, self.angle)
        screen.blit(rotated_surface, (self.x - rotated_surface.get_width()/2, self.y - rotated_surface.get_height()/2))

    def get_explosion_damage_rect(self):
        # チャージショットの場合、弾道上の爆発による当たり判定を返す
        if not self.penetrate:
            return None
            
        damage_rects = []
        for pos in self.trail_positions:
            damage_rects.append(pygame.Rect(pos[0] - 20, pos[1] - 20, 40, 40))
        return damage_rects

# 敵クラス
class Enemy:
    def __init__(self, enemy_type="mob", speed_factor=1.0):
        params = ENEMY_TYPES[enemy_type]
        self.width = params["width"]
        self.height = params["height"]
        self.hp = params["hp"]
        self.base_speed = params["base_speed"] * speed_factor  # 速度係数を適用
        self.color = params["color"]
        self.score = params["score"]
        self.homing_factor = params["homing_factor"]
        self.explosion_radius = params["explosion_radius"]  # 爆発の影響範囲
        self.explosion_damage = params["explosion_damage"]  # 爆発によるダメージ
        
        # 初期位置
        self.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.y = -self.height
        
        # 移動方向の初期化
        self.dx = 0
        self.dy = 1  # 基本的に下向きに移動
        
        # 爆発エフェクト関連
        self.is_exploding = False
        self.explosion_effects = []
        self.explosion_start_time = 0
        self.explosion_duration = 30  # 30フレームで爆発終了
        
        # 生存フラグ
        self.active = True
        
    def deactivate(self):
        # 敵を非アクティブにする（削除フラグを立てる）
        self.active = False
        return True  # 非アクティブ化に成功したことを返す

    def take_damage(self, damage):
        # ダメージを受ける処理
        self.hp -= damage
        
        # HPが0以下になったら爆発開始
        if self.hp <= 0 and not self.is_exploding:
            self.is_exploding = True
            # 爆発エフェクトを作成
            self.create_explosion_effects()
            return True  # 敵が破壊されたことを返す
        
        return False  # 敵はまだ生存

    def create_explosion_effects(self):
        # 爆発の中心座標
        center_x = self.x + self.width/2
        center_y = self.y + self.height/2
        
        # 爆発エフェクト配列を初期化
        self.explosion_effects = []
        
        # 爆発エフェクトを作成（中心に明るい輝き）
        self.explosion_effects.append(RingEffect(center_x, center_y, WHITE, 30, 5, 0.1))
        
        # 複数の破片（小さなリング）を飛散させる
        for _ in range(20):
            # ランダムな角度と速度
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 4)
            
            # 速度の計算
            vel_x = math.cos(angle) * speed
            vel_y = math.sin(angle) * speed
            
            # ランダムなサイズと色（赤〜オレンジ〜黄色）
            size = random.randint(10, 30)
            color_val = random.randint(0, 2)
            if color_val == 0:
                color = RED
            elif color_val == 1:
                color = ORANGE
            else:
                color = YELLOW
            
            # 重力と拡大・フェード速度もランダムに
            gravity = random.uniform(0.05, 0.15)
            expand_speed = random.uniform(0.5, 2.0)
            fade_speed = random.uniform(0.02, 0.08)
            
            # エフェクト追加
            self.explosion_effects.append(RingEffect(
                center_x, center_y, color, size, expand_speed, fade_speed,
                vel_x, vel_y, gravity
            ))
        
        # 煙エフェクト（ゆっくり上昇する）
        for _ in range(5):
            offset_x = random.uniform(-10, 10)
            offset_y = random.uniform(-10, 10)
            size = random.randint(20, 40)
            color = (80, 80, 80)  # 灰色
            self.explosion_effects.append(RingEffect(
                center_x + offset_x, center_y + offset_y, color, size, 1, 0.03,
                0, -0.5, -0.02  # 上に向かってゆっくり移動、若干加速
            ))
            
        # 爆発開始時間を記録
        self.explosion_start_time = pygame.time.get_ticks()
        
        # 誘爆判定（このメソッドを呼び出した側で処理）
        return self.check_chain_explosion()
        
    def check_chain_explosion(self):
        # 誘爆した敵のリスト
        chain_exploded = []
        
        # グローバル変数のenemiesリストにアクセスするため、この関数は外部から呼ばれる必要がある
        # このメソッドを呼び出す側で、適切に処理する
        return chain_exploded
        
    def update_explosion(self):
        # 爆発エフェクトの更新
        for effect in self.explosion_effects[:]:
            if not effect.update():
                self.explosion_effects.remove(effect)
                
        # 爆発終了判定
        if pygame.time.get_ticks() - self.explosion_start_time >= self.explosion_duration * 16.67:  # 16.67ms/frame for 60FPS
            # エフェクトも全て完了したら非アクティブに
            if len(self.explosion_effects) == 0:
                self.deactivate()
                return False
        
        return True  # 爆発中

    def move(self, player_x, player_y):
        # プレイヤーの方向へのベクトルを計算
        target_dx = (player_x - self.x) / SCREEN_WIDTH  # 正規化
        target_dy = (player_y - self.y) / SCREEN_HEIGHT # 正規化
        
        # 現在の移動方向を徐々にプレイヤー方向に補正
        self.dx = self.dx * (1 - self.homing_factor) + target_dx * self.homing_factor
        self.dy = self.dy * (1 - self.homing_factor) + target_dy * self.homing_factor
        
        # ベクトルの正規化
        length = math.sqrt(self.dx * self.dx + self.dy * self.dy)
        if length > 0:
            self.dx /= length
            self.dy /= length
        
        # 移動
        self.x += self.dx * self.base_speed
        self.y += self.dy * self.base_speed
        
        # 画面端での跳ね返り（左右のみ）
        if self.x < 0:
            self.x = 0
            self.dx *= -0.5  # 勢いを弱めて跳ね返る
        elif self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
            self.dx *= -0.5
        
    def draw(self):
        # 爆発エフェクトの描画
        for effect in self.explosion_effects:
            effect.draw(screen)
            
        # 爆発中でない場合のみ、敵本体とHPバーを描画
        if not self.is_exploding:
            # HPバーの表示
            hp_width = self.width * (self.hp / ENEMY_TYPES["mob"]["hp"])
            hp_height = 3
            pygame.draw.rect(screen, RED, (self.x, self.y - hp_height - 2, self.width, hp_height))
            pygame.draw.rect(screen, GREEN, (self.x, self.y - hp_height - 2, hp_width, hp_height))
            
            # 敵本体の描画
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

# 効果音管理クラス
class SoundEffects:
    def __init__(self):
        # 基本設定
        pygame.mixer.set_num_channels(8)
        self.volume = 0.3
        
        # 各効果音の生成
        self.sounds = {
            'shoot': self.create_shoot_sound(),      # ピシューン
            'charge': self.create_charge_sound(),    # シュンシュンシュン
            'charge_complete': self.create_charge_complete_sound(),  # シャキーン！
            'damage': self.create_damage_sound(),    # バス！
            'enemy_destroy': self.create_destroy_sound(),  # バーン！
            'charge_shot': self.create_charge_shot_sound(),  # シュバーン
            'dash': self.create_dash_sound()  # キュイーン！
        }
        
        # 音量設定
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
            
    def create_shoot_sound(self):
        # ピシューン（高音の短い音）
        samples = []
        for i in range(4410):  # 0.1秒
            value = 128 + int(64 * math.sin(i * 0.1))
            samples.append(value)
        return pygame.mixer.Sound(buffer=bytes(samples))
        
    def create_charge_sound(self):
        # シュンシュンシュン（上昇音）
        samples = []
        for i in range(4410):
            value = 128 + int(64 * math.sin(i * 0.2))
            samples.append(value)
        return pygame.mixer.Sound(buffer=bytes(samples))
        
    def create_charge_complete_sound(self):
        # シャキーン！（高音の長い音）
        samples = []
        for i in range(8820):  # 0.2秒
            value = 128 + int(96 * math.sin(i * 0.3))
            samples.append(value)
        return pygame.mixer.Sound(buffer=bytes(samples))
        
    def create_damage_sound(self):
        # バス！（低音のノイズ）
        samples = []
        for i in range(4410):
            value = 128 + random.randint(-32, 32)
            samples.append(value)
        return pygame.mixer.Sound(buffer=bytes(samples))
        
    def create_destroy_sound(self):
        # バーン！（大きめのノイズ）
        samples = []
        for i in range(6615):  # 0.15秒
            value = 128 + random.randint(-64, 64)
            samples.append(value)
        return pygame.mixer.Sound(buffer=bytes(samples))
        
    def create_charge_shot_sound(self):
        # シュバーン（高音の長い音）
        samples = []
        for i in range(8820):  # 0.2秒
            value = 128 + int(96 * math.sin(i * 0.4))
            samples.append(value)
        return pygame.mixer.Sound(buffer=bytes(samples))
            
    def create_dash_sound(self):
        # キュイーン！（上昇する高音）
        samples = []
        for i in range(4410):  # 0.1秒
            # 周波数を徐々に上げる
            freq = 0.1 + (i / 4410) * 0.3  # 0.1から0.4まで上昇
            value = 128 + int(64 * math.sin(i * freq))
            samples.append(value)
        return pygame.mixer.Sound(buffer=bytes(samples))
            
    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

# ゲームの初期化
def reset_game():
    global player, enemies, bullets, score, game_over, game_start_time, current_difficulty_factor, sound_effects, game_over_timer
    
    # ゲームオーバータイマーをリセット
    game_over_timer = 0
    
    # 難易度を一段階下げる（最低値は1.0）
    if game_over:  # ゲームオーバーからのリセットの場合
        # 現在の難易度から0.5下げる（最低1.0）
        current_difficulty_factor = max(1.0, current_difficulty_factor - 0.5)
        # スコアも難易度に応じて調整
        score = max(0, int(score * 0.7))
    else:  # 新規ゲーム開始の場合
        current_difficulty_factor = 1.0
        score = 0
    
    player = Player()
    enemies = []
    bullets = []
    game_over = False
    game_start_time = pygame.time.get_ticks()
    
    # サウンドエフェクトが定義されていない場合は初期化
    if sound_effects is None:
        sound_effects = SoundEffects()

# グローバル変数
player = None
enemies = []
bullets = []
score = 0
game_over = False
game_over_timer = 0  # ゲームオーバー後の自動リスタートタイマー
game_start_time = 0
current_difficulty_factor = 1.0  # 難易度係数の初期値
sound_effects = None

# ゲームの初期化を実行
reset_game()

# メインゲームループ
running = True
show_control_message = True  # ゲーム開始時にコントロールメッセージを表示
control_message_timer = 180  # 3秒間表示（60FPS×3）

while running:
    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # アドバタイズモード中に任意のキーが押されたら操作モードに切り替え
            if player.advertise_mode and event.key not in [pygame.K_F1, pygame.K_F2]:
                player.advertise_mode = False
                show_control_message = True  # コントロールメッセージを再表示
                control_message_timer = 180
                print("Switched to Manual Control Mode")
            # F1キーでアドバタイズモード切り替え
            elif event.key == pygame.K_F1:
                is_advertise_mode = player.toggle_advertise_mode()
                print(f"Advertise Mode: {'ON' if is_advertise_mode else 'OFF'}")
                if is_advertise_mode:
                    show_control_message = True
                    control_message_timer = 180
            # F2キーで画面認識モード切り替え
            elif event.key == pygame.K_F2 and player.advertise_mode:
                player.visual_mode = not player.visual_mode
                print(f"Visual Recognition Mode: {'ON' if player.visual_mode else 'OFF'}")
        elif event.type == pygame.KEYUP:
            if game_over:
                if event.key == pygame.K_SPACE:
                    reset_game()  # ゲームオーバー時のリセット
            elif player.can_fire("beam_rifle"):
                if event.key == pygame.K_SPACE:
                    # スペースキーを離したときに発射
                    target_pos = player.charge_target_position if player.charge_level > 0 else None
                    bullets.append(Bullet(
                        player.x + player.width/2 - 10,
                        player.y, 
                        player.locked_enemy,
                        player.facing_right, 
                        "beam_rifle",
                        player.charge_level,
                        target_pos
                    ))
                    # チャージレベルに応じて効果音を変える
                    if player.charge_level > 0:
                        sound_effects.play('charge_shot')  # チャージショット発射音
                    else:
                        sound_effects.play('shoot')  # 通常射撃音
                    player.charge_level = 0
                    player.charge_target_position = None
                    player.weapon_cooldown = BULLET_TYPES["beam_rifle"]["cooldown"]
                elif event.key == pygame.K_x:
                    # 高速弾
                    bullets.append(Bullet(player.x + player.width/2 - 1.5, player.y, player.locked_enemy, player.facing_right, "quick"))
                elif event.key == pygame.K_c:
                    # 重弾
                    bullets.append(Bullet(player.x + player.width/2 - 4, player.y, player.locked_enemy, player.facing_right, "heavy"))

    if not game_over:
        # プレイヤーの移動と状態更新
        keys = pygame.key.get_pressed()
        # 全ての更新処理はupdateメソッド内で行われるようになった
        player.update(keys, enemies, bullets)
        
        # 敵の生成
        if len(enemies) < MAX_ENEMIES and random.random() < get_enemy_spawn_chance(score):  # 上限チェックを追加
            # スコアに応じた敵タイプを選択
            enemy_type = select_enemy_type(score)
            
            # 出現位置をランダムに分散
            spawn_x = random.randint(0, SCREEN_WIDTH - ENEMY_TYPES[enemy_type]["width"])
            
            # スコアに応じた速度係数を適用
            speed_factor = get_enemy_speed_factor(score)
            
            new_enemy = Enemy(enemy_type, speed_factor)
            new_enemy.x = spawn_x
            enemies.append(new_enemy)
        
        # 弾の移動
        for bullet in bullets[:]:
            bullet.move()
            # 画面外判定を全方向に対応
            if (bullet.x < -50 or bullet.x > SCREEN_WIDTH + 50 or
                bullet.y < -50 or bullet.y > SCREEN_HEIGHT + 50):
                bullets.remove(bullet)
        
        # 敵の移動と状態更新
        for enemy in enemies[:]:
            # 爆発中の敵の処理
            if enemy.is_exploding:
                enemy.update_explosion()
                continue
                
            # 通常の移動処理
            enemy.move(player.x + player.width/2, player.y + player.height/2)
            
            # 画面外に出た敵は非アクティブ化
            if enemy.y > SCREEN_HEIGHT * 1.5:
                enemy.deactivate()
                
            # 弾との衝突判定
            for bullet in bullets[:]:
                if (bullet.x < enemy.x + enemy.width and
                    bullet.x + bullet.width > enemy.x and
                    bullet.y < enemy.y + enemy.height and
                    bullet.y + bullet.height > enemy.y):
                    
                    # 弾が敵に当たった場合
                    if enemy.take_damage(bullet.damage):
                        # 敵を倒した場合のスコア加算
                        score += enemy.score
                        sound_effects.play('enemy_destroy')
                        
                        # 敵の中心位置で誘爆チェック
                        center_x = enemy.x + enemy.width/2
                        center_y = enemy.y + enemy.height/2
                        radius = enemy.explosion_radius
                        
                        # 誘爆処理（周囲の敵にダメージ）
                        for nearby_enemy in enemies[:]:
                            if nearby_enemy != enemy and not nearby_enemy.is_exploding:
                                # 中心間の距離を計算
                                nearby_center_x = nearby_enemy.x + nearby_enemy.width/2
                                nearby_center_y = nearby_enemy.y + nearby_enemy.height/2
                                distance = math.sqrt((center_x - nearby_center_x)**2 + (center_y - nearby_center_y)**2)
                                
                                # 爆発範囲内なら誘爆
                                if distance < radius:
                                    if nearby_enemy.take_damage(enemy.explosion_damage):
                                        # 敵が破壊された場合のスコア加算
                                        score += nearby_enemy.score
                                        sound_effects.play('enemy_destroy')
                        
                        break  # この敵は処理済み
                    
                    # 貫通弾でなければ弾を削除
                    if not bullet.penetrate and bullet in bullets:
                        bullets.remove(bullet)
            
            # プレイヤーとの衝突判定
            if not player.is_invincible() and not game_over:
                if (player.x < enemy.x + enemy.width and
                    player.x + player.width > enemy.x and
                    player.y < enemy.y + enemy.height and
                    player.y + player.height > enemy.y):
                    
                    # プレイヤーにダメージ
                    player.take_damage(10)
                    sound_effects.play('player_damage')
                    
                    # 敵は爆発
                    enemy.take_damage(enemy.hp)  # 即死
                    
                    # ゲームオーバー判定
                    if player.hp <= 0:
                        game_over = True
        
        # 非アクティブな敵を一括削除
        enemies = [enemy for enemy in enemies if enemy.active]
    
    # 描画
    screen.fill(BLACK)
    
    # ... existing drawing code ...
    
    # プレイヤー、敵、弾の描画
    player.draw()
    for enemy in enemies[:]:
        enemy.draw()
    for bullet in bullets[:]:
        bullet.draw()
        
    # 自機のゲージ描画
    player.draw_gauges()
    
    # 操作説明メッセージの表示
    if show_control_message:
        control_message_timer -= 1
        if control_message_timer <= 0:
            show_control_message = False
        
        # 半透明の背景パネル
        message_panel = pygame.Surface((500, 150), pygame.SRCALPHA)
        message_panel.fill((0, 0, 0, 180))
        screen.blit(message_panel, (SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT - 180))
        
        # メッセージテキスト
        message_font = pygame.font.SysFont(None, 28)
        
        if player.advertise_mode:
            messages = [
                "ADVERTISE MODE ACTIVE",
                "Press any key to take manual control",
                "F1: Toggle Advertise Mode",
                "F2: Toggle Visual Recognition Mode"
            ]
        else:
            messages = [
                "MANUAL CONTROL MODE",
                "Arrow Keys: Move",
                "SPACE: Charge Shot",
                "SHIFT: Dash",
                "F1: Switch to Advertise Mode"
            ]
        
        y_offset = SCREEN_HEIGHT - 160
        for msg in messages:
            msg_surface = message_font.render(msg, True, (255, 255, 255))
            screen.blit(msg_surface, (SCREEN_WIDTH//2 - msg_surface.get_width()//2, y_offset))
            y_offset += 30
    
    # スコア表示
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (SCREEN_WIDTH - 150, 10))
    
    # 難易度表示
    difficulty_factor = calculate_difficulty_factor(score)
    difficulty_name = get_difficulty_name(difficulty_factor)
    difficulty_color = WHITE
    if difficulty_factor > 2.0:
        difficulty_color = ORANGE
    if difficulty_factor > 2.5:
        difficulty_color = RED
    
    difficulty_text = font.render(f"Lv: {difficulty_name}", True, difficulty_color)
    screen.blit(difficulty_text, (SCREEN_WIDTH - 150, 45))
    
    # ゲームオーバー時の処理
    if game_over:
        # アドバタイズモードなら自動的にリスタート
        if player.advertise_mode:
            game_over_timer += 1
            # 3秒待ってから自動リスタート
            if game_over_timer > 180:  # 60フレーム/秒 × 3秒 = 180フレーム
                reset_game()
                print("Advertise Mode: Auto-Restart")
        
        game_over_text = font.render("GAME OVER", True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 30))
        
        # リセット方法の表示（アドバタイズモードでない場合）
        if not player.advertise_mode:
            reset_text = font.render("Press SPACE to Restart", True, WHITE)
            screen.blit(reset_text, (SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 + 20))
        else:
            # アドバタイズモードの場合はカウントダウン表示
            seconds_left = 3 - (game_over_timer // 60)
            if seconds_left > 0:
                auto_reset_text = font.render(f"Auto Restart in {seconds_left}...", True, WHITE)
                screen.blit(auto_reset_text, (SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 + 20))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit() 