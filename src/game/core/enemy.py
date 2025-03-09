import pygame
import random
import math

# 画面設定
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
        
        # 爆発のタイムスタンプを記録
        self.explosion_start_time = pygame.time.get_ticks()
        
        # 爆発エフェクトの数（サイズに応じて変化）
        num_particles = int(self.explosion_radius / 4)
        
        # 複数の爆発パーティクルを作成
        for _ in range(num_particles):
            # ランダムな方向と速度
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            
            # ランダムな色（敵の色を基準に変化）
            base_color = self.color
            color_offset = random.randint(-20, 20)
            color = (
                max(0, min(255, base_color[0] + color_offset)),
                max(0, min(255, base_color[1] + color_offset)),
                max(0, min(255, base_color[2] + color_offset))
            )
            
            # ランダムなサイズ
            size = random.randint(2, 6)
            
            # ランダムな寿命
            lifetime = random.randint(20, 40)
            
            # エフェクトをリストに追加
            self.explosion_effects.append({
                'x': center_x,
                'y': center_y,
                'dx': dx,
                'dy': dy,
                'size': size,
                'color': color,
                'lifetime': lifetime,
                'age': 0
            })

    def check_chain_explosion(self):
        # 誘爆した敵のリスト
        chain_exploded = []
        
        # HPが0以下で爆発中の敵だけが周囲の敵に連鎖爆発を起こす
        if self.hp <= 0 and self.is_exploding:
            # 他の敵との当たり判定は、外部から行う
            pass
        
        return chain_exploded

    def update_explosion(self):
        # 爆発エフェクトの更新
        for effect in self.explosion_effects[:]:
            # エフェクトを移動
            effect['x'] += effect['dx']
            effect['y'] += effect['dy']
            
            # エフェクトの寿命を増やす
            effect['age'] += 1
            
            # 寿命が尽きたらエフェクトを削除
            if effect['age'] >= effect['lifetime']:
                self.explosion_effects.remove(effect)
        
        # 爆発が完了したかチェック
        current_time = pygame.time.get_ticks()
        if current_time - self.explosion_start_time > self.explosion_duration * 16.67:  # フレーム数をミリ秒に変換
            # 爆発完了、敵を削除
            self.active = False

    def move(self, player_x, player_y):
        # プレイヤーの方向へのベクトルを計算
        player_center_x = player_x
        player_center_y = player_y
        enemy_center_x = self.x + self.width/2
        enemy_center_y = self.y + self.height/2
        
        # プレイヤーへの方向ベクトル
        dx_to_player = player_center_x - enemy_center_x
        dy_to_player = player_center_y - enemy_center_y
        
        # ベクトルの長さを計算（プレイヤーまでの距離）
        distance = math.sqrt(dx_to_player**2 + dy_to_player**2)
        
        # ホーミング行動
        if distance > 0:
            # 方向ベクトルを正規化
            dx_to_player /= distance
            dy_to_player /= distance
            
            # 現在の方向と目標方向を補間
            self.dx = self.dx + (dx_to_player - self.dx) * self.homing_factor
            self.dy = self.dy + (dy_to_player - self.dy) * self.homing_factor
            
            # 移動方向ベクトルを正規化
            length = math.sqrt(self.dx**2 + self.dy**2)
            if length > 0:
                self.dx /= length
                self.dy /= length
        
        # 敵を移動
        if not self.is_exploding:  # 爆発中は移動しない
            self.x += self.dx * self.base_speed
            self.y += self.dy * self.base_speed
            
            # 画面端での跳ね返り
            if self.x < 0:
                self.x = 0
                self.dx *= -0.5  # 跳ね返り効果
            elif self.x > SCREEN_WIDTH - self.width:
                self.x = SCREEN_WIDTH - self.width
                self.dx *= -0.5  # 跳ね返り効果
                
            # 画面下端のチェックは外部で行う（画面外に出ると再配置される）

    def draw(self, screen):
        # 爆発エフェクトの描画
        if self.is_exploding:
            # 個々の爆発パーティクルを描画
            for effect in self.explosion_effects:
                # 年齢に応じてサイズと透明度を変化
                age_ratio = effect['age'] / effect['lifetime']
                size = effect['size'] * (1 - age_ratio)  # だんだん小さく
                alpha = int(255 * (1 - age_ratio))  # だんだん透明に
                
                # 半透明サーフェスの作成
                s = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*effect['color'], alpha), (int(size), int(size)), int(size))
                
                # 描画
                screen.blit(s, (effect['x'] - size, effect['y'] - size))
        else:
            # 通常の敵の描画
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            
            # HPバーの描画（敵の上部）
            hp_width = (self.width * self.hp) / ENEMY_TYPES["mob"]["hp"]  # 初期HPに対する現在のHP割合
            pygame.draw.rect(screen, GREEN, (self.x, self.y - 5, hp_width, 3)) 