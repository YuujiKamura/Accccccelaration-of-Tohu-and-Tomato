"""
テスト用モッククラス

テスト中に実際のクラスの代わりに使用するモッククラスを定義します。
"""

# ゲーム内定数の設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# ダッシュ仕様
class DashSpec:
    # 速度関連
    NORMAL_SPEED = 5.0
    DASH_SPEED = 10.0
    
    # 持続時間とクールダウン
    DASH_DURATION = 120  # フレーム (2秒)
    DASH_COOLDOWN = 45   # フレーム (0.75秒)
    
    # ヒートゲージ関連
    INITIAL_HEAT = 0
    MAX_HEAT = 100
    HEAT_INCREASE_RATE = 5
    HEAT_RECOVERY_RATE = 1
    
    # グリップ関連
    NORMAL_GRIP = 1.0
    DASH_GRIP = 0.5
    MAX_TURN_RATE = 0.1

# プレイヤークラス
class Player:
    def __init__(self):
        # 基本位置と寸法
        self.width = 32
        self.height = 32
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 100
        self.health = 100
        self.score = 0
        self.advertise_mode = False
        
        # ダッシュ関連
        self.is_dashing = False
        self.dash_duration = DashSpec.DASH_DURATION
        self.dash_cooldown = 0
        self.dash_cooldown_time = DashSpec.DASH_COOLDOWN
        self.max_speed = DashSpec.NORMAL_SPEED
        self.dash_speed = DashSpec.DASH_SPEED
        
        # ヒートゲージ
        self.heat = DashSpec.INITIAL_HEAT
        self.max_heat = DashSpec.MAX_HEAT
        self.heat_increase_rate = DashSpec.HEAT_INCREASE_RATE
        self.heat_recovery_rate = DashSpec.HEAT_RECOVERY_RATE
        
        # グリップと移動
        self.grip_level = DashSpec.NORMAL_GRIP
        self.dash_grip_level = DashSpec.DASH_GRIP
        self.movement_angle = 0
        self.target_angle = 0
        
        # ダッシュエフェクト
        self.dash_effects = []
        
        # 武器関連
        self.current_weapon = "beam_rifle"
        self.weapon_cooldown = 0
    
    def move(self, keys):
        """プレイヤーの移動処理"""
        # キー入力に基づいて移動方向を決定
        dx, dy = 0, 0
        
        if keys.get('left', False):
            dx -= 1
        if keys.get('right', False):
            dx += 1
        if keys.get('up', False):
            dy -= 1
        if keys.get('down', False):
            dy += 1
        
        # シフトキーが押されているかつヒートゲージが最大未満ならダッシュ
        dash_key_pressed = keys.get('shift', False)
        
        if dash_key_pressed and self.heat < self.max_heat and self.dash_cooldown <= 0:
            self.is_dashing = True
            self.heat += self.heat_increase_rate
        else:
            self.is_dashing = False
            if self.heat > 0:
                self.heat -= self.heat_recovery_rate
        
        # 速度の決定
        speed = self.dash_speed if self.is_dashing else self.max_speed
        
        # 移動処理
        if dx != 0 or dy != 0:
            # 簡易的な直接移動（角度計算を使用せず）
            self.x += dx * speed
            self.y += dy * speed
            
            # ダッシュエフェクトの生成
            if self.is_dashing:
                self.dash_effects.append({
                    'x': self.x - dx * 10,
                    'y': self.y - dy * 10,
                    'life': 10
                })
        
        # クールダウン処理
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
    
    def fire(self):
        """武器を発射"""
        if self.weapon_cooldown <= 0:
            self.weapon_cooldown = 10  # 発射後のクールダウン
            return True
        return False
    
    def update(self, keys, enemies, bullets):
        """プレイヤーの状態を更新"""
        # 移動処理
        self.move(keys)
        
        # 武器クールダウン
        if self.weapon_cooldown > 0:
            self.weapon_cooldown -= 1
        
        # 発射処理
        if keys.get('z', False) and self.can_fire():
            self.fire()
    
    def can_fire(self, weapon_type=None):
        """発射可能かどうかを確認"""
        return self.weapon_cooldown <= 0
    
    def draw(self, surface=None):
        """プレイヤーの描画処理"""
        # 実際のゲームでは描画処理がここに入る
        pass

# 敵クラス
class Enemy:
    def __init__(self, x=0, y=0, enemy_type="mob", speed_factor=1.0):
        # 基本位置と寸法
        self.width = 24
        self.height = 24
        self.x = x
        self.y = y
        
        # タイプと状態
        self.enemy_type = enemy_type
        self.health = 50
        self.max_health = 50
        self.speed = 2.0 * speed_factor
        self.is_defeated = False
        self.is_exploding = False
        self.explosion_frame = 0
        
        # 行動パターン
        self.movement_pattern = "straight"
        self.direction_x = 0
        self.direction_y = 1
    
    def take_damage(self, damage):
        """ダメージを受ける"""
        self.health -= damage
        if self.health <= 0:
            self.is_defeated = True
            self.is_exploding = True
    
    def update(self):
        """敵の状態を更新"""
        if self.is_exploding:
            self.explosion_frame += 1
            if self.explosion_frame >= 10:
                self.is_exploding = False
        elif not self.is_defeated:
            # 移動処理
            self.x += self.direction_x * self.speed
            self.y += self.direction_y * self.speed
    
    def draw(self, surface=None):
        """敵の描画処理"""
        # 実際のゲームでは描画処理がここに入る
        pass

# 弾クラス
class Bullet:
    def __init__(self, x=0, y=0, target=None, facing_right=True, bullet_type="beam_rifle", charge_level=0, target_pos=None):
        # 基本位置と寸法
        self.width = 8
        self.height = 4
        self.x = x
        self.y = y
        
        # 弾の特性
        self.bullet_type = bullet_type
        self.speed = 15
        self.damage = 10
        self.lifetime = 60  # フレーム数
        self.is_active = True
        self.is_player_bullet = True
        
        # 方向と目標
        self.facing_right = facing_right
        self.target = target
        self.target_pos = target_pos
        
        # チャージレベル
        self.charge_level = charge_level
    
    def move(self):
        """弾の移動処理"""
        # 基本的な直線移動
        direction = 1 if self.facing_right else -1
        self.x += self.speed * direction
        
        # 寿命の減少
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.is_active = False
    
    def update(self):
        """弾の状態を更新"""
        self.move()
    
    def draw(self, surface=None):
        """弾の描画処理"""
        # 実際のゲームでは描画処理がここに入る
        pass

# リングエフェクト
class RingEffect:
    def __init__(self, x, y, color=WHITE, max_radius=40, expand_speed=2, fade_speed=0.02):
        self.x = x
        self.y = y
        self.color = color
        self.current_radius = 0
        self.max_radius = max_radius
        self.expand_speed = expand_speed
        self.alpha = 1.0  # 透明度
        self.fade_speed = fade_speed
        self.is_active = True
    
    def update(self):
        """エフェクトの更新"""
        # 半径の拡大
        self.current_radius += self.expand_speed
        
        # フェードアウト
        if self.current_radius >= self.max_radius / 2:
            self.alpha -= self.fade_speed
        
        # 寿命の確認
        if self.alpha <= 0 or self.current_radius >= self.max_radius:
            self.is_active = False
    
    def draw(self, surface=None):
        """エフェクトの描画"""
        # 実際のゲームでは描画処理がここに入る
        pass

# ゲーム状態変数
game_over = False
score = 0
enemies = []
bullets = []
player = Player()
effects = []

# ゲームリセット関数
def reset_game():
    """ゲーム状態をリセットする"""
    global game_over, score, enemies, bullets, player, effects
    game_over = False
    score = 0
    enemies = []
    bullets = []
    effects = []
    player = Player()

# アドバタイズモード関数
def advertise_mode():
    """デモプレイモード"""
    global game_over
    # デモプレイ処理
    if game_over:
        reset_game()

# 難易度計算関数
def calculate_difficulty_factor(current_score):
    """スコアに基づいて難易度係数を計算する"""
    base_difficulty = 1.0
    score_factor = current_score / 10000.0
    difficulty = min(base_difficulty + score_factor, 3.0)
    return difficulty

# 難易度名取得関数
def get_difficulty_name(factor):
    """難易度係数から名前を取得する"""
    if factor < 1.25:
        return "EASY"
    elif factor < 1.75:
        return "NORMAL"
    elif factor < 2.25:
        return "HARD"
    elif factor < 2.75:
        return "EXPERT"
    else:
        return "MASTER" 