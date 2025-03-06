import pygame
import random
import math
import numpy

# 初期化
pygame.init()
pygame.mixer.init()  # 音声システムの初期化

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
LIGHT_GREEN = (250, 255, 250)  # ネギ用の緑色をより鮮やかに
DARK_GREEN = (70, 120, 20)    # 深みのある緑を追加
NEGI_COLOR = (150, 255, 150)  # ネギビーム用の色を追加
YELLOWISH_WHITE = (255, 255, 230)  # 黄色みがかった白を追加

# ネギライフルのパラメータ
NEGI_RIFLE_PARAMS = {
    "width": 8,           # 銃身の幅
    "height": 44,         # 銃身の長さ
    "outline_width": 4,   # 輪郭の太さ
    "tip_width": 4,       # 先端部分の幅
    "tip_length": 8,      # 先端部分の長さ
    "tip_highlight_length": 2,  # 先端のハイライト部分の長さ
    "color": LIGHT_GREEN, # メインカラー
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
                "color": NEGI_COLOR,  # ネギカラーに変更
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
        "explosion_damage": 30   # 爆発によるダメージ
    },
    # 後々追加する敵タイプのために余白を残しておく
}

# 敵のパラメータ定義の後に追加
MAX_ENEMIES = 100  # 敵の最大出現数

# リングエフェクトクラス
class RingEffect:
    def __init__(self, x, y, color=WHITE, max_radius=40, expand_speed=3, fade_speed=0.05):
        self.x = x
        self.y = y
        self.radius = 10
        self.max_radius = max_radius
        self.life = 1.0
        self.fade_speed = fade_speed
        self.expand_speed = expand_speed
        self.color = color
        
    def update(self):
        self.radius += self.expand_speed
        self.life -= self.fade_speed
        return self.life > 0
        
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * self.life)
            ring_surface = pygame.Surface((self.radius * 2 + 2, self.radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(ring_surface, (*self.color, alpha), (self.radius + 1, self.radius + 1), self.radius, 2)
            screen.blit(ring_surface, (self.x - self.radius - 1, self.y - self.radius - 1))

# プレイヤークラス
class Player:
    def __init__(self):
        self.width = 30
        self.height = 30
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 50
        self.base_speed = 4
        self.dash_speed = 8
        self.current_speed = self.base_speed
        self.heat = 0
        self.hp = 100
        self.invincible_time = 0
        self.last_direction = None
        self.is_dashing = False
        self.was_dashing = False
        self.ring_effects = []
        self.dash_effect_timer = 0
        self.locked_enemy = None
        self.lock_on_range = 500
        self.facing_right = True  # プレイヤーの向き（True: 右向き, False: 左向き）
        self.charge_level = 0
        self.charge_start_time = 0
        self.is_charging = False
        self.shot_cooldown = 0  # 射撃クールダウン用の変数を追加
        self.shot_cooldown_time = 10  # 発射間隔（フレーム数）
        self.weapon_cooldown = 0  # 武器のクールダウンタイマー
        self.charge_target_position = None  # チャージ完了時の密集ターゲット位置
        self.charge_complete = False  # チャージ完了フラグを追加
        self.dx = 0  # 現在の移動方向X
        self.dy = 0  # 現在の移動方向Y
        self.direction_smoothing = 0.2  # 通常時の方向転換の滑らかさ
        self.dash_direction_smoothing = 0.05  # ダッシュ時の方向転換の滑らかさ（小さいほどゆるやか）
        self.last_input_dx = 0  # 前回の入力方向X
        self.last_input_dy = 0  # 前回の入力方向Y
        self.charge_sound_playing = False  # チャージ音の再生状態を管理
        self.velocity_x = 0  # 速度Xを追加
        self.velocity_y = 0  # 速度Yを追加
        self.acceleration = 0.3  # 加速度
        self.deceleration = 0.2  # 減速度
        self.max_velocity = 4  # 最大速度（通常時）
        self.max_dash_velocity = 8  # 最大速度（ダッシュ時）
        self.input_buffer = {
            'left': False,
            'right': False,
            'up': False,
            'down': False,
            'shift': False
        }  # キー入力のバッファを追加
        self.dash_cooldown = 0  # ダッシュのクールダウンを追加
        self.dash_duration = 120  # ダッシュの持続時間（フレーム）を3倍に
        self.dash_cooldown_time = 45  # ダッシュのクールダウン時間（フレーム）
        
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
        if self.invincible_time <= 0:
            self.hp -= damage
            self.invincible_time = 60  # 1秒間の無敵時間
            sound_effects.play('damage')  # ダメージ音を再生
            return True
        return False
        
    def move(self, keys):
        if self.invincible_time > 0:
            self.invincible_time -= 1
        
        # ダッシュのクールダウンを更新
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # キー入力の状態を更新
        self.input_buffer['left'] = keys[pygame.K_LEFT]
        self.input_buffer['right'] = keys[pygame.K_RIGHT]
        self.input_buffer['up'] = keys[pygame.K_UP]
        self.input_buffer['down'] = keys[pygame.K_DOWN]
        
        # ダッシュの処理を改善
        shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        self.was_dashing = self.is_dashing
        
        if shift_pressed and self.dash_cooldown <= 0 and not self.is_dashing:
            # ダッシュ開始
            self.is_dashing = True
            self.dash_duration = 90
            sound_effects.play('dash')
        elif self.is_dashing:
            if self.dash_duration > 0:
                self.dash_duration -= 1
                # ダッシュ中のエフェクト生成
                if pygame.time.get_ticks() % 2 == 0:  # 2フレームごとにエフェクト生成
                    center_x = self.x + self.width/2
                    center_y = self.y + self.height/2
                    self.ring_effects.append(RingEffect(center_x, center_y, (255, 255, 255), 30, 4, 0.1))
            else:
                # ダッシュ終了
                self.is_dashing = False
                self.dash_cooldown = self.dash_cooldown_time

        # 移動方向の初期化
        current_direction = None
        self.dx = 0
        self.dy = 0

        # 8方向移動の入力処理（バッファを使用）
        if self.input_buffer['left']:
            self.dx -= 1
            self.facing_right = False
        if self.input_buffer['right']:
            self.dx += 1
            self.facing_right = True
        if self.input_buffer['up']:
            self.dy -= 1
        if self.input_buffer['down']:
            self.dy += 1
            
        # 斜め移動時の入力を正規化
        if self.dx != 0 and self.dy != 0:
            length = math.sqrt(2)  # √2で正規化
            self.dx /= length
            self.dy /= length
        
        # 移動方向の記録（8方向）
        if self.dx != 0 or self.dy != 0:
            if self.dx < 0:
                if self.dy < 0: current_direction = 'northwest'
                elif self.dy > 0: current_direction = 'southwest'
                else: current_direction = 'west'
            elif self.dx > 0:
                if self.dy < 0: current_direction = 'northeast'
                elif self.dy > 0: current_direction = 'southeast'
                else: current_direction = 'east'
            else:
                if self.dy < 0: current_direction = 'north'
                else: current_direction = 'south'
            
        # ヒートゲージの管理
        if self.is_dashing:
            if current_direction and current_direction != self.last_direction:
                self.heat = min(100, self.heat + 10)  # 方向転換時のヒート上昇を増加
            elif current_direction:
                self.heat = min(100, self.heat + 0.5)  # 通常時のヒート上昇も少し増加
        else:
            self.heat = max(0, self.heat - 1.5)  # 冷却速度を増加
            
        # ヒートが100%になると強制的に通常速度に
        max_speed = self.max_velocity if self.heat >= 100 or not self.is_dashing else self.max_dash_velocity
            
        self.last_direction = current_direction
        
        # 速度の更新
        if self.dx != 0:
            # 加速
            self.velocity_x += self.dx * self.acceleration
            # 最大速度制限
            self.velocity_x = max(-max_speed, min(max_speed, self.velocity_x))
        else:
            # 減速
            if self.velocity_x > 0:
                self.velocity_x = max(0, self.velocity_x - self.deceleration)
            elif self.velocity_x < 0:
                self.velocity_x = min(0, self.velocity_x + self.deceleration)
                
        if self.dy != 0:
            # 加速
            self.velocity_y += self.dy * self.acceleration
            # 最大速度制限
            self.velocity_y = max(-max_speed, min(max_speed, self.velocity_y))
        else:
            # 減速
            if self.velocity_y > 0:
                self.velocity_y = max(0, self.velocity_y - self.deceleration)
            elif self.velocity_y < 0:
                self.velocity_y = min(0, self.velocity_y + self.deceleration)
        
        # 位置の更新
        self.x += self.velocity_x
        self.y += self.velocity_y
            
        # 画面端の処理
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))
        
        # エフェクトの更新
        self.ring_effects = [effect for effect in self.ring_effects if effect.update()]
        
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
        # 射撃クールダウンの更新
        if self.shot_cooldown > 0:
            self.shot_cooldown -= 1

        # 通常射撃（チャージしていない場合）
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
        # エフェクトの描画（プレイヤーの前に描画）
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
                    
                    # 周囲の敵にダメージ
                    explosion_radius = 30
                    explosion_damage = self.damage * 0.2  # 通常の20%のダメージ
                    
                    for enemy in enemies[:]:
                        dx = (enemy.x + enemy.width/2) - pos[0]
                        dy = (enemy.y + enemy.height/2) - pos[1]
                        distance = math.sqrt(dx * dx + dy * dy)
                        
                        if distance <= explosion_radius:
                            damage_factor = 1 - (distance / explosion_radius)
                            actual_damage = explosion_damage * damage_factor
                            if enemy.take_damage(actual_damage):
                                # 敵を倒した場合の処理
                                enemies.remove(enemy)
                                score += enemy.score
                                sound_effects.play('enemy_destroy')
        
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
    def __init__(self, enemy_type="mob"):
        params = ENEMY_TYPES[enemy_type]
        self.width = params["width"]
        self.height = params["height"]
        self.hp = params["hp"]
        self.base_speed = params["base_speed"]
        self.color = params["color"]
        self.score = params["score"]
        self.homing_factor = params["homing_factor"]
        
        # 初期位置
        self.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.y = -self.height
        
        # 移動方向の初期化
        self.dx = 0
        self.dy = 1  # 基本的に下向きに移動
        
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
        
    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0
        
    def draw(self):
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
    global player, bullets, enemies, score, game_over, sound_effects
    player = Player()
    bullets = []
    enemies = []
    score = 0
    game_over = False
    sound_effects = SoundEffects()

player = Player()
bullets = []
enemies = []
clock = pygame.time.Clock()
score = 0
game_over = False
sound_effects = SoundEffects()  # グローバル変数として効果音オブジェクトを作成

# メインゲームループ
running = True
while running:
    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
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
        player.move(keys)
        player.update_lock_on(enemies, keys)
        player.update_charge(keys, enemies)
        player.update_weapon_cooldown()
        player.update(keys, enemies, bullets)
        
        # 敵の生成
        if len(enemies) < MAX_ENEMIES and random.random() < 0.02:  # 上限チェックを追加
            # 出現位置をランダムに分散
            spawn_x = random.randint(0, SCREEN_WIDTH - ENEMY_TYPES["mob"]["width"])
            spawn_type = "mob"  # 後々の拡張用
            new_enemy = Enemy(spawn_type)
            new_enemy.x = spawn_x
            enemies.append(new_enemy)
        
        # 弾の移動
        for bullet in bullets[:]:
            bullet.move()
            # 画面外判定を全方向に対応
            if (bullet.x < -50 or bullet.x > SCREEN_WIDTH + 50 or
                bullet.y < -50 or bullet.y > SCREEN_HEIGHT + 50):
                bullets.remove(bullet)
        
        # 敵の移動
        for enemy in enemies[:]:
            enemy.move(player.x + player.width/2, player.y + player.height/2)  # プレイヤーの中心座標を渡す
            if enemy.y > SCREEN_HEIGHT * 1.5:  # 画面高さの1.5倍まで生存できるように変更
                enemies.remove(enemy)
                
        # 衝突判定
        for enemy in enemies[:]:
            # プレイヤーと敵の衝突
            if (player.x < enemy.x + enemy.width and
                player.x + player.width > enemy.x and
                player.y < enemy.y + enemy.height and
                player.y + player.height > enemy.y):
                if player.take_damage(20):  # プレイヤーへのダメージ
                    # 衝突位置に派手な爆発エフェクトを生成
                    explosion_x = enemy.x + enemy.width/2
                    explosion_y = enemy.y + enemy.height/2
                    # 大きな赤いリング
                    player.ring_effects.append(RingEffect(explosion_x, explosion_y, RED, 100, 6, 0.02))
                    # 中くらいのオレンジのリング
                    player.ring_effects.append(RingEffect(explosion_x, explosion_y, ORANGE, 80, 5, 0.03))
                    # 小さな黄色いリング
                    player.ring_effects.append(RingEffect(explosion_x, explosion_y, YELLOW, 60, 4, 0.04))
                    enemies.remove(enemy)
                if player.hp <= 0:
                    game_over = True
                
            # 弾と敵の衝突
            for bullet in bullets[:]:
                # 通常の衝突判定
                if (bullet.x < enemy.x + enemy.width and
                    bullet.x + bullet.width > enemy.x and
                    bullet.y < enemy.y + enemy.height and
                    bullet.y + bullet.height > enemy.y):
                    if enemy.take_damage(bullet.damage):  # ダメージ処理
                        # 爆発位置を記録
                        explosion_x = enemy.x + enemy.width/2
                        explosion_y = enemy.y + enemy.height/2
                        
                        # 基本爆発エフェクト（より大きく、より長く）
                        player.ring_effects.append(RingEffect(explosion_x, explosion_y, RED, 150, 8, 0.02))
                        player.ring_effects.append(RingEffect(explosion_x, explosion_y, ORANGE, 130, 7, 0.025))
                        player.ring_effects.append(RingEffect(explosion_x, explosion_y, YELLOW, 110, 6, 0.03))
                        
                        # 追加の装飾的な爆発エフェクト
                        for i in range(5):  # 複数の小さな爆発を追加
                            offset_x = random.randint(-30, 30)
                            offset_y = random.randint(-30, 30)
                            size = random.randint(40, 80)
                            speed = random.uniform(3, 6)
                            color = random.choice([NEGI_COLOR, WHITE, YELLOWISH_WHITE])
                            player.ring_effects.append(RingEffect(explosion_x + offset_x, explosion_y + offset_y, 
                                                                color, size, speed, 0.04))
                        
                        # チャージショットの場合、超派手な爆発を追加
                        if bullet.penetrate:
                            # メインの大爆発
                            player.ring_effects.append(RingEffect(explosion_x, explosion_y, NEGI_COLOR, 200, 10, 0.015))
                            player.ring_effects.append(RingEffect(explosion_x, explosion_y, WHITE, 180, 9, 0.02))
                            player.ring_effects.append(RingEffect(explosion_x, explosion_y, NEGI_COLOR, 160, 8, 0.025))
                            
                            # 追加の装飾エフェクト
                            for i in range(8):  # より多くの追加爆発
                                offset_x = random.randint(-50, 50)
                                offset_y = random.randint(-50, 50)
                                size = random.randint(60, 120)
                                speed = random.uniform(4, 8)
                                color = random.choice([NEGI_COLOR, WHITE, YELLOWISH_WHITE])
                                player.ring_effects.append(RingEffect(explosion_x + offset_x, explosion_y + offset_y, 
                                                                    color, size, speed, 0.03))
                            
                        # 爆発による連鎖反応
                        explosion_radius = ENEMY_TYPES["mob"]["explosion_radius"] * 1.5  # 爆発範囲を1.5倍に
                        explosion_damage = ENEMY_TYPES["mob"]["explosion_damage"] * 1.2  # ダメージも1.2倍に
                        
                        # 周囲の敵に爆発ダメージを与える
                        for nearby_enemy in enemies[:]:  # リストのコピーを使用
                            if nearby_enemy != enemy:  # 自分自身以外の敵をチェック
                                dx = (nearby_enemy.x + nearby_enemy.width/2) - explosion_x
                                dy = (nearby_enemy.y + nearby_enemy.height/2) - explosion_y
                                distance = math.sqrt(dx * dx + dy * dy)
                                
                                if distance <= explosion_radius:
                                    # 距離に応じてダメージを減衰
                                    damage_factor = 1 - (distance / explosion_radius)
                                    actual_damage = explosion_damage * damage_factor
                                    
                                    if nearby_enemy.take_damage(actual_damage):
                                        # 連鎖爆発のエフェクト
                                        chain_x = nearby_enemy.x + nearby_enemy.width/2
                                        chain_y = nearby_enemy.y + nearby_enemy.height/2
                                        player.ring_effects.append(RingEffect(chain_x, chain_y, RED, 60, 4, 0.04))
                                        player.ring_effects.append(RingEffect(chain_x, chain_y, ORANGE, 40, 3, 0.05))
                                        
                                        enemies.remove(nearby_enemy)
                                        score += nearby_enemy.score
                                        sound_effects.play('enemy_destroy')
                                        break  # この敵の処理を完全に終了
                        
                        # 敵を削除し、スコアを加算
                        enemies.remove(enemy)
                        score += enemy.score
                        sound_effects.play('enemy_destroy')
                        break  # この敵の処理を完全に終了
                        
                    if bullet in bullets and not bullet.penetrate:  # 貫通弾でない場合のみ削除
                        bullets.remove(bullet)
                        break  # この弾の処理を終了
                        
                # 爆発の当たり判定（チャージショットの場合）
                elif bullet.penetrate:
                    damage_rects = bullet.get_explosion_damage_rect()
                    if damage_rects:
                        enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                        for damage_rect in damage_rects:
                            if damage_rect.colliderect(enemy_rect):
                                if enemy.take_damage(bullet.damage * 0.5):  # 爆発は通常の半分のダメージ
                                    # 爆発エフェクト（小規模）
                                    explosion_x = enemy.x + enemy.width/2
                                    explosion_y = enemy.y + enemy.height/2
                                    player.ring_effects.append(RingEffect(explosion_x, explosion_y, NEGI_COLOR, 60, 4, 0.1))
                                    player.ring_effects.append(RingEffect(explosion_x, explosion_y, WHITE, 40, 3, 0.12))
                                    enemies.remove(enemy)
                                    score += enemy.score
                                    sound_effects.play('enemy_destroy')
                                    break  # この敵の処理を完全に終了
    
    # 描画
    screen.fill(BLACK)
    player.draw()
    for bullet in bullets:
        bullet.draw()
    for enemy in enemies:
        enemy.draw()
        
    # スコア表示
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (SCREEN_WIDTH - 150, 10))  # 右上に配置
    
    if game_over:
        game_over_text = font.render("GAME OVER", True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 30))
        
        # リセット方法の表示
        reset_text = font.render("Press SPACE to Restart", True, WHITE)
        screen.blit(reset_text, (SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT//2 + 20))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit() 