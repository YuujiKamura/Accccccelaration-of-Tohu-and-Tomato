"""
アドバタイズモードのテスト用モッククラス

テスト環境におけるゲームオブジェクトのモック実装を提供します。
本番コードの依存関係なしで独立したテストを実行するため、コア機能を模倣します。
"""

import math
import random


class DashSpec:
    """ダッシュ機能の仕様を表すクラス"""
    def __init__(self):
        self.cooldown = 60  # ダッシュのクールダウン時間（フレーム）
        self.duration = 10  # ダッシュの持続時間（フレーム）
        self.speed = 10.0  # ダッシュ時の速度倍率


class Player:
    """テスト用のプレイヤークラスモック"""
    def __init__(self):
        # 位置と移動関連
        self.x = 400
        self.y = 300
        self.speed = 5.0
        self.velocity_x = 0
        self.velocity_y = 0
        self.direction_x = 0
        self.direction_y = 0
        
        # ダッシュ関連
        self.dash_spec = DashSpec()
        self.dash_cooldown_timer = 0
        self.dash_duration_timer = 0
        self.is_dashing = False
        
        # アドバタイズモード
        self.advertise_mode = False
        self._strategy_timer = 0
        self._current_strategy = 'balanced'  # balanced, defensive, aggressive, flanking
        self._last_position_change = (0, 0)
        self._consecutive_same_direction = 0
        
        # その他のゲーム状態
        self.health = 100
        self.score = 0
    
    def update(self, keys, enemies=None, bullets=None):
        """プレイヤーの状態を更新"""
        if enemies is None:
            enemies = []
        if bullets is None:
            bullets = []
        
        # アドバタイズモードが有効ならAI制御
        if self.advertise_mode:
            self.update_advertise_movement(enemies)
            # 弾の発射などの行動
            if hasattr(self, 'perform_advertise_action'):
                self.perform_advertise_action(enemies, bullets)
            return
        
        # 通常の入力処理（実際のゲームコードではキー入力に応じた処理）
        self.direction_x = 0
        self.direction_y = 0
        
        # ダッシュのクールダウンとタイマー更新
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1
        
        if self.dash_duration_timer > 0:
            self.dash_duration_timer -= 1
        else:
            self.is_dashing = False
        
        # 速度の計算と位置の更新
        speed_multiplier = self.dash_spec.speed if self.is_dashing else 1.0
        
        self.velocity_x = self.direction_x * self.speed * speed_multiplier
        self.velocity_y = self.direction_y * self.speed * speed_multiplier
        
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 画面外に出ないように制限
        self.x = max(0, min(self.x, 800))
        self.y = max(0, min(self.y, 600))
    
    def update_advertise_movement(self, enemies):
        """アドバタイズモード用の移動更新（デフォルト実装）"""
        # 戦略の定期的な変更
        self._strategy_timer += 1
        if self._strategy_timer > 180:  # 3秒ごとに戦略を変更
            self._strategy_timer = 0
            strategies = ['balanced', 'defensive', 'aggressive', 'flanking']
            self._current_strategy = random.choice(strategies)
        
        # デフォルトの基本移動アルゴリズム
        if not enemies:
            # 敵がいない場合はランダムな方向に移動
            if random.random() < 0.02:  # 2%の確率で方向変更
                self.direction_x = random.uniform(-1, 1)
                self.direction_y = random.uniform(-1, 1)
                
                # 正規化
                magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
                self.direction_x /= magnitude
                self.direction_y /= magnitude
        else:
            # 最も近い敵から逃げる（単純な回避アルゴリズム）
            closest_enemy = min(enemies, key=lambda e: math.sqrt((e.x - self.x)**2 + (e.y - self.y)**2))
            dx = self.x - closest_enemy.x
            dy = self.y - closest_enemy.y
            
            # ゼロ除算を防ぐ
            distance = max(0.1, math.sqrt(dx**2 + dy**2))
            
            # 逃げる方向（正規化）
            self.direction_x = dx / distance
            self.direction_y = dy / distance
            
            # 画面中央に留まりすぎないための調整
            center_x, center_y = 400, 300
            if abs(self.x - center_x) < 100 and abs(self.y - center_y) < 100:
                # 中央から離れる成分を追加
                center_dx = self.x - center_x
                center_dy = self.y - center_y
                center_dist = max(0.1, math.sqrt(center_dx**2 + center_dy**2))
                
                # 敵回避と中央回避を組み合わせる
                self.direction_x = 0.7 * (dx / distance) + 0.3 * (center_dx / center_dist)
                self.direction_y = 0.7 * (dy / distance) + 0.3 * (center_dy / center_dist)
                
                # 正規化
                magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
                self.direction_x /= magnitude
                self.direction_y /= magnitude
        
        # シンプルな物理更新
        speed = self.speed
        self.velocity_x = self.direction_x * speed
        self.velocity_y = self.direction_y * speed
        
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 画面外に出ないように制限
        self.x = max(50, min(self.x, 750))
        self.y = max(50, min(self.y, 550))
    
    def dash(self):
        """ダッシュを実行"""
        if self.dash_cooldown_timer <= 0 and not self.is_dashing:
            self.is_dashing = True
            self.dash_duration_timer = self.dash_spec.duration
            self.dash_cooldown_timer = self.dash_spec.cooldown
            return True
        return False


class Enemy:
    """テスト用の敵クラスモック"""
    def __init__(self):
        self.x = random.randint(50, 750)
        self.y = random.randint(50, 550)
        self.speed = random.uniform(1.0, 3.0)
        self.direction_x = random.uniform(-1, 1)
        self.direction_y = random.uniform(-1, 1)
        self.health = 30
        self.is_active = True
        
        # 方向を正規化
        magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
        self.direction_x /= magnitude
        self.direction_y /= magnitude
    
    def update(self):
        """敵の状態を更新"""
        # ランダムな方向変更（低確率）
        if random.random() < 0.01:  # 1%の確率で方向変更
            angle_change = random.uniform(-0.3, 0.3)
            cos_angle = math.cos(angle_change)
            sin_angle = math.sin(angle_change)
            
            new_dir_x = self.direction_x * cos_angle - self.direction_y * sin_angle
            new_dir_y = self.direction_x * sin_angle + self.direction_y * cos_angle
            
            self.direction_x = new_dir_x
            self.direction_y = new_dir_y
            
            # 方向を正規化
            magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
            self.direction_x /= magnitude
            self.direction_y /= magnitude
        
        # 位置の更新
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed
        
        # 画面外に出ないように境界チェック（実装例ではテスト用に簡略化）
        if self.x < 0 or self.x > 800:
            self.direction_x *= -1
        if self.y < 0 or self.y > 600:
            self.direction_y *= -1
    
    def take_damage(self, amount):
        """ダメージを受ける"""
        self.health -= amount
        if self.health <= 0:
            self.is_active = False


class Bullet:
    """テスト用の弾クラスモック"""
    def __init__(self, x, y, direction_x, direction_y, speed=10, damage=10):
        self.x = x
        self.y = y
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.speed = speed
        self.damage = damage
        self.is_active = True
        
        # 方向を正規化
        magnitude = max(0.01, math.sqrt(direction_x**2 + direction_y**2))
        self.direction_x /= magnitude
        self.direction_y /= magnitude
    
    def update(self):
        """弾の状態を更新"""
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed
        
        # 画面外に出たら非アクティブにする
        if self.x < 0 or self.x > 800 or self.y < 0 or self.y > 600:
            self.is_active = False
    
    def check_collision(self, game_object):
        """他のゲームオブジェクトとの衝突判定"""
        # 簡易的な円形衝突判定
        distance = math.sqrt((self.x - game_object.x)**2 + (self.y - game_object.y)**2)
        collision_threshold = 20  # 衝突判定の閾値（半径）
        
        if distance < collision_threshold:
            self.is_active = False
            return True
        return False 
アドバタイズモードのテスト用モッククラス

テスト環境におけるゲームオブジェクトのモック実装を提供します。
本番コードの依存関係なしで独立したテストを実行するため、コア機能を模倣します。
"""

import math
import random


class DashSpec:
    """ダッシュ機能の仕様を表すクラス"""
    def __init__(self):
        self.cooldown = 60  # ダッシュのクールダウン時間（フレーム）
        self.duration = 10  # ダッシュの持続時間（フレーム）
        self.speed = 10.0  # ダッシュ時の速度倍率


class Player:
    """テスト用のプレイヤークラスモック"""
    def __init__(self):
        # 位置と移動関連
        self.x = 400
        self.y = 300
        self.speed = 5.0
        self.velocity_x = 0
        self.velocity_y = 0
        self.direction_x = 0
        self.direction_y = 0
        
        # ダッシュ関連
        self.dash_spec = DashSpec()
        self.dash_cooldown_timer = 0
        self.dash_duration_timer = 0
        self.is_dashing = False
        
        # アドバタイズモード
        self.advertise_mode = False
        self._strategy_timer = 0
        self._current_strategy = 'balanced'  # balanced, defensive, aggressive, flanking
        self._last_position_change = (0, 0)
        self._consecutive_same_direction = 0
        
        # その他のゲーム状態
        self.health = 100
        self.score = 0
    
    def update(self, keys, enemies=None, bullets=None):
        """プレイヤーの状態を更新"""
        if enemies is None:
            enemies = []
        if bullets is None:
            bullets = []
        
        # アドバタイズモードが有効ならAI制御
        if self.advertise_mode:
            self.update_advertise_movement(enemies)
            # 弾の発射などの行動
            if hasattr(self, 'perform_advertise_action'):
                self.perform_advertise_action(enemies, bullets)
            return
        
        # 通常の入力処理（実際のゲームコードではキー入力に応じた処理）
        self.direction_x = 0
        self.direction_y = 0
        
        # ダッシュのクールダウンとタイマー更新
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1
        
        if self.dash_duration_timer > 0:
            self.dash_duration_timer -= 1
        else:
            self.is_dashing = False
        
        # 速度の計算と位置の更新
        speed_multiplier = self.dash_spec.speed if self.is_dashing else 1.0
        
        self.velocity_x = self.direction_x * self.speed * speed_multiplier
        self.velocity_y = self.direction_y * self.speed * speed_multiplier
        
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 画面外に出ないように制限
        self.x = max(0, min(self.x, 800))
        self.y = max(0, min(self.y, 600))
    
    def update_advertise_movement(self, enemies):
        """アドバタイズモード用の移動更新（デフォルト実装）"""
        # 戦略の定期的な変更
        self._strategy_timer += 1
        if self._strategy_timer > 180:  # 3秒ごとに戦略を変更
            self._strategy_timer = 0
            strategies = ['balanced', 'defensive', 'aggressive', 'flanking']
            self._current_strategy = random.choice(strategies)
        
        # デフォルトの基本移動アルゴリズム
        if not enemies:
            # 敵がいない場合はランダムな方向に移動
            if random.random() < 0.02:  # 2%の確率で方向変更
                self.direction_x = random.uniform(-1, 1)
                self.direction_y = random.uniform(-1, 1)
                
                # 正規化
                magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
                self.direction_x /= magnitude
                self.direction_y /= magnitude
        else:
            # 最も近い敵から逃げる（単純な回避アルゴリズム）
            closest_enemy = min(enemies, key=lambda e: math.sqrt((e.x - self.x)**2 + (e.y - self.y)**2))
            dx = self.x - closest_enemy.x
            dy = self.y - closest_enemy.y
            
            # ゼロ除算を防ぐ
            distance = max(0.1, math.sqrt(dx**2 + dy**2))
            
            # 逃げる方向（正規化）
            self.direction_x = dx / distance
            self.direction_y = dy / distance
            
            # 画面中央に留まりすぎないための調整
            center_x, center_y = 400, 300
            if abs(self.x - center_x) < 100 and abs(self.y - center_y) < 100:
                # 中央から離れる成分を追加
                center_dx = self.x - center_x
                center_dy = self.y - center_y
                center_dist = max(0.1, math.sqrt(center_dx**2 + center_dy**2))
                
                # 敵回避と中央回避を組み合わせる
                self.direction_x = 0.7 * (dx / distance) + 0.3 * (center_dx / center_dist)
                self.direction_y = 0.7 * (dy / distance) + 0.3 * (center_dy / center_dist)
                
                # 正規化
                magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
                self.direction_x /= magnitude
                self.direction_y /= magnitude
        
        # シンプルな物理更新
        speed = self.speed
        self.velocity_x = self.direction_x * speed
        self.velocity_y = self.direction_y * speed
        
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 画面外に出ないように制限
        self.x = max(50, min(self.x, 750))
        self.y = max(50, min(self.y, 550))
    
    def dash(self):
        """ダッシュを実行"""
        if self.dash_cooldown_timer <= 0 and not self.is_dashing:
            self.is_dashing = True
            self.dash_duration_timer = self.dash_spec.duration
            self.dash_cooldown_timer = self.dash_spec.cooldown
            return True
        return False


class Enemy:
    """テスト用の敵クラスモック"""
    def __init__(self):
        self.x = random.randint(50, 750)
        self.y = random.randint(50, 550)
        self.speed = random.uniform(1.0, 3.0)
        self.direction_x = random.uniform(-1, 1)
        self.direction_y = random.uniform(-1, 1)
        self.health = 30
        self.is_active = True
        
        # 方向を正規化
        magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
        self.direction_x /= magnitude
        self.direction_y /= magnitude
    
    def update(self):
        """敵の状態を更新"""
        # ランダムな方向変更（低確率）
        if random.random() < 0.01:  # 1%の確率で方向変更
            angle_change = random.uniform(-0.3, 0.3)
            cos_angle = math.cos(angle_change)
            sin_angle = math.sin(angle_change)
            
            new_dir_x = self.direction_x * cos_angle - self.direction_y * sin_angle
            new_dir_y = self.direction_x * sin_angle + self.direction_y * cos_angle
            
            self.direction_x = new_dir_x
            self.direction_y = new_dir_y
            
            # 方向を正規化
            magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
            self.direction_x /= magnitude
            self.direction_y /= magnitude
        
        # 位置の更新
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed
        
        # 画面外に出ないように境界チェック（実装例ではテスト用に簡略化）
        if self.x < 0 or self.x > 800:
            self.direction_x *= -1
        if self.y < 0 or self.y > 600:
            self.direction_y *= -1
    
    def take_damage(self, amount):
        """ダメージを受ける"""
        self.health -= amount
        if self.health <= 0:
            self.is_active = False


class Bullet:
    """テスト用の弾クラスモック"""
    def __init__(self, x, y, direction_x, direction_y, speed=10, damage=10):
        self.x = x
        self.y = y
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.speed = speed
        self.damage = damage
        self.is_active = True
        
        # 方向を正規化
        magnitude = max(0.01, math.sqrt(direction_x**2 + direction_y**2))
        self.direction_x /= magnitude
        self.direction_y /= magnitude
    
    def update(self):
        """弾の状態を更新"""
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed
        
        # 画面外に出たら非アクティブにする
        if self.x < 0 or self.x > 800 or self.y < 0 or self.y > 600:
            self.is_active = False
    
    def check_collision(self, game_object):
        """他のゲームオブジェクトとの衝突判定"""
        # 簡易的な円形衝突判定
        distance = math.sqrt((self.x - game_object.x)**2 + (self.y - game_object.y)**2)
        collision_threshold = 20  # 衝突判定の閾値（半径）
        
        if distance < collision_threshold:
            self.is_active = False
            return True
        return False 