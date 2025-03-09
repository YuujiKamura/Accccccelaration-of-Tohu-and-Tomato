import pygame
import math
import random

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)

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