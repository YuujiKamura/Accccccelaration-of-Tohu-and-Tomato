import unittest
from tests.unit.test_base import BaseTestCase, log_test
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
        self.width = 30
        self.height = 30
        self.velocity_x = 0
        self.velocity_y = 0
        self.speed = 5.0
        self.dash_speed = 10.0
        
        # ダッシュ状態
        self.is_dashing = False
        self.dash_cooldown = 0
        self.dash_duration = 0
        self.heat = 0
        self.max_heat = 100
        
        # 武器関連
        self.fire_cooldown = 0
        self.weapon_type = "normal"
        self.health = 100
        self.max_health = 100
        self.score = 0
        
        # 移動方向
        self.direction_x = 0
        self.direction_y = 0
    
    def update(self):
        """プレイヤーの更新"""
        # 移動処理
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 画面外に出ないように制限
        self.x = max(0, min(800, self.x))
        self.y = max(0, min(600, self.y))
        
        # クールダウン処理
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
    
    def move(self, direction):
        """
        方向に応じて移動
        
        Args:
            direction: (dx, dy)の方向ベクトル
        """
        dx, dy = direction
        
        if dx != 0 or dy != 0:
            # 方向を設定
            self.direction_x = dx
            self.direction_y = dy
            
            # 正規化
            magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
            self.direction_x /= magnitude
            self.direction_y /= magnitude
            
            # 速度設定
            speed = self.dash_speed if self.is_dashing else self.speed
            self.velocity_x = self.direction_x * speed
            self.velocity_y = self.direction_y * speed
        else:
            # 移動していない場合は停止
            self.velocity_x = 0
            self.velocity_y = 0
    
    def dash(self):
        """ダッシュを実行"""
        if not self.is_dashing and self.dash_cooldown <= 0 and self.heat < self.max_heat:
            self.is_dashing = True
            self.dash_duration = 10
            self.heat += 20
    
    def fire(self):
        """武器発射"""
        if self.fire_cooldown <= 0:
            self.fire_cooldown = 15
            return True
        return False
    
    def take_damage(self, amount):
        """ダメージを受ける"""
        self.health = max(0, self.health - amount)


class Enemy:
    """テスト用の敵クラスモック"""
    def __init__(self, x=0, y=0, enemy_type="normal"):
        # 位置と移動関連
        self.x = x
        self.y = y
        self.width = 25
        self.height = 25
        self.velocity_x = 0
        self.velocity_y = 0
        self.speed = 3.0
        
        # 敵タイプと状態
        self.enemy_type = enemy_type
        self.health = 30
        self.max_health = 30
        self.is_active = True
        
        # 移動パターン
        self.direction_x = 0
        self.direction_y = 1
    
    def update(self):
        """敵の更新"""
        if not self.is_active:
            return
        
        # 移動処理
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 画面外に出ないように制限
        self.x = max(-50, min(850, self.x))
        self.y = max(-50, min(650, self.y))
    
    def move(self, target=None):
        """
        移動処理を実行
        
        Args:
            target: 追跡対象のオブジェクト（省略可）
        """
        if target:
            # ターゲットに向かって移動
            dx = target.x - self.x
            dy = target.y - self.y
            
            # 正規化
            magnitude = max(0.01, math.sqrt(dx**2 + dy**2))
            self.direction_x = dx / magnitude
            self.direction_y = dy / magnitude
        
        # 速度設定
        self.velocity_x = self.direction_x * self.speed
        self.velocity_y = self.direction_y * self.speed
    
    def take_damage(self, amount):
        """ダメージを受ける"""
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.is_active = False


class Bullet:
    """テスト用の弾クラスモック"""
    def __init__(self, x, y, direction=(1, 0), speed=10, damage=10, owner="player"):
        # 位置と移動関連
        self.x = x
        self.y = y
        self.width = 10
        self.height = 5
        self.speed = speed
        
        # 方向
        self.direction_x, self.direction_y = direction
        # 正規化
        magnitude = max(0.01, math.sqrt(self.direction_x**2 + self.direction_y**2))
        self.direction_x /= magnitude
        self.direction_y /= magnitude
        
        # 弾の特性
        self.damage = damage
        self.owner = owner  # "player" または "enemy"
        self.is_active = True
        self.lifetime = 60  # フレーム単位の寿命
    
    def update(self):
        """弾の更新"""
        if not self.is_active:
            return
        
        # 移動処理
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed
        
        # 寿命減少
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.is_active = False
        
        # 画面外チェック
        if self.x < -50 or self.x > 850 or self.y < -50 or self.y > 650:
            self.is_active = False
    
    def check_collision(self, other):
        """衝突判定"""
        # 簡易的な矩形判定
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)

# テスト用のゲーム状態管理クラス
class GameState:
    """テスト用のゲーム状態管理クラス"""
    def __init__(self):
        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.score = 0
        self.game_over = False
        self.level = 1
        self.spawn_timer = 0
        
    def update(self):
        """ゲーム状態の更新"""
        # プレイヤー更新
        self.player.update()
        
        # 敵の更新
        for enemy in self.enemies:
            enemy.update()
            # プレイヤー追跡
            enemy.move(self.player)
        
        # 弾の更新
        for bullet in self.bullets:
            bullet.update()
        
        # 衝突判定
        self.check_collisions()
        
        # 非アクティブなオブジェクトの削除
        self.clean_inactive_objects()
        
        # 敵のスポーン
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_timer = 60  # 1秒ごとに敵をスポーン
    
    def check_collisions(self):
        """衝突判定を行う"""
        # プレイヤーの弾と敵の衝突
        for bullet in self.bullets:
            if bullet.owner == "player" and bullet.is_active:
                for enemy in self.enemies:
                    if enemy.is_active and bullet.check_collision(enemy):
                        enemy.take_damage(bullet.damage)
                        bullet.is_active = False
                        
                        # スコア加算
                        if enemy.health <= 0:
                            self.score += 100
    
    def clean_inactive_objects(self):
        """非アクティブなオブジェクトを削除"""
        self.enemies = [enemy for enemy in self.enemies if enemy.is_active]
        self.bullets = [bullet for bullet in self.bullets if bullet.is_active]
    
    def spawn_enemy(self):
        """敵を生成"""
        # 画面外からランダムな位置に敵を生成
        side = random.randint(0, 3)  # 0:上, 1:右, 2:下, 3:左
        
        if side == 0:  # 上
            x = random.randint(0, 800)
            y = -30
        elif side == 1:  # 右
            x = 830
            y = random.randint(0, 600)
        elif side == 2:  # 下
            x = random.randint(0, 800)
            y = 630
        else:  # 左
            x = -30
            y = random.randint(0, 600)
        
        # 敵タイプをランダムに決定
        enemy_type = random.choice(["normal", "fast", "tough"])
        enemy = Enemy(x, y, enemy_type)
        
        # タイプごとの特性設定
        if enemy_type == "fast":
            enemy.speed = 4.5
            enemy.health = 20
        elif enemy_type == "tough":
            enemy.speed = 2.0
            enemy.health = 50
        
        self.enemies.append(enemy)
    
    def fire_player_bullet(self):
        """プレイヤーの弾を発射"""
        if self.player.fire():
            # 弾の方向はプレイヤーの向き
            direction = (self.player.direction_x, self.player.direction_y)
            if direction == (0, 0):
                direction = (0, -1)  # デフォルトは上方向
            
            bullet = Bullet(
                self.player.x + self.player.width/2,
                self.player.y + self.player.height/2,
                direction,
                15,  # 速度
                10,  # ダメージ
                "player"
            )
            self.bullets.append(bullet)
            return True
        return False 