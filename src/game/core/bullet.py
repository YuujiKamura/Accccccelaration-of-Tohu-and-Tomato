import pygame
import math

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)

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
    "negi_blast": {  # 必殺技：ネギブラスト
        "speed": 8,           # 中程度の速度
        "width": 150,         # かなり広い
        "height": 150,        # 正方形に近い
        "damage": 100,        # 非常に高ダメージ
        "homing_strength": 0, # ホーミングなし
        "max_turn_angle": 0,
        "min_homing_distance": 0,
        "max_homing_distance": 0,
        "color": (120, 255, 120),  # 鮮やかなネギ色
        "penetrate": True,    # 貫通効果あり
        "explosion_radius": 200,  # 大きな爆発範囲
        "explosion_damage": 50,  # 爆発時の二次ダメージ
        "cooldown": 300,      # 長めのクールダウン（5秒）
        "is_special": True,   # 必殺技フラグ
        "effect_scale": 3.0   # エフェクトスケール
    },
    "mesh_sword": {  # 近接斬撃用のメッシュソード
        "speed": 0,          # 速度0（プレイヤーの位置に固定）
        "width": 120,        # 幅広の斬撃
        "height": 80,        # 高さもそれなりに
        "damage": 50,        # 高威力
        "homing_strength": 0,  # ホーミングなし
        "max_turn_angle": 0,
        "min_homing_distance": 0,
        "max_homing_distance": 0,
        "color": (255, 100, 100),  # 赤みがかった色
        "lifespan": 10,      # 短い持続時間
        "is_melee": True,    # 近接攻撃フラグ
        "cooldown": 25,      # 発射間隔
        "knockback": 5.0,    # 敵をノックバックさせる
        "effect_scale": 2.0  # エフェクトスケール
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
    }
}

class Bullet:
    def __init__(self, x, y, target=None, facing_right=True, bullet_type="beam_rifle", charge_level=0, target_pos=None):
        self.x = x
        self.y = y
        self.bullet_type = bullet_type  # 弾の種類を保持
        self.charge_level = charge_level  # チャージレベルを保持
        
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
        self.penetrate = params.get("penetrate", False)  # 貫通効果
        self.explosion_effects = []  # 爆発エフェクトのリスト
        self.trail_positions = []  # 弾道の位置を記録
        self.trail_life = 30  # 弾道の持続フレーム数
        self.trail_explosion_timer = 0  # 弾道爆発のタイマー
        self.trail_explosion_interval = 5  # 爆発の間隔（フレーム）
        
        # 必殺技用パラメータ
        self.is_special = params.get("is_special", False)  # 必殺技フラグ
        self.explosion_radius = params.get("explosion_radius", 0)  # 爆発範囲
        self.explosion_damage = params.get("explosion_damage", 0)  # 爆発ダメージ
        self.effect_scale = params.get("effect_scale", 1.0)  # エフェクトスケール
        
        # 近接攻撃用パラメータ
        self.is_melee = params.get("is_melee", False)  # 近接攻撃フラグ
        self.lifespan = params.get("lifespan", 999)    # 持続フレーム数
        if self.is_melee:
            self.lifespan = 6  # 近接攻撃の持続時間を短く（10→6フレーム）
        self.current_life = 0                          # 現在の生存フレーム
        self.knockback = params.get("knockback", 0.0)  # ノックバック強度
        
        # チャージレベルに応じたパラメータ補正
        if charge_level > 0 and "charge_levels" in params:
            charge_params = params["charge_levels"].get(charge_level, {})
            self.speed *= charge_params.get("speed", 1.0)
            self.damage *= charge_params.get("damage", 1.0)
            self.width *= charge_params.get("width_multiplier", 1.0)
            self.height *= charge_params.get("height_multiplier", 1.0)
            self.color = charge_params.get("color", self.color)
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
        # 近接攻撃の場合はライフスパンを消費するだけ
        if self.is_melee:
            self.current_life += 1
            # ライフスパンが尽きたら弾を消す
            if self.current_life >= self.lifespan:
                return False  # 弾を削除するシグナル
            return True  # 弾を維持
            
        # 通常弾の場合は通常の移動処理
        # 現在位置を弾道履歴に追加
        self.trail_positions.append((self.x + self.width/2, self.y + self.height/2))
        if len(self.trail_positions) > self.trail_life:
            self.trail_positions.pop(0)
            
        # チャージショットの弾道爆発処理
        if self.penetrate and len(self.trail_positions) > 2:
            self.trail_explosion_timer += 1
            if self.trail_explosion_timer >= self.trail_explosion_interval:
                self.trail_explosion_timer = 0
                
        # ホーミング処理
        if self.target and self.homing_strength > 0:
            # ターゲットが存在するかチェック（削除された場合はホーミングしない）
            target_x = self.target.x + self.target.width/2
            target_y = self.target.y + self.target.height/2
            
            # ターゲットへの方向ベクトルを計算
            dx = target_x - (self.x + self.width/2)
            dy = target_y - (self.y + self.height/2)
            
            # ターゲットまでの距離を計算
            distance = math.sqrt(dx**2 + dy**2)
            
            # 距離に応じてホーミング強度を調整
            adjusted_homing = self.homing_strength
            if distance < self.min_homing_distance:
                adjusted_homing = 0  # 最小距離以下ではホーミングしない
            elif distance < self.max_homing_distance:
                # 最小〜最大距離の間では距離に応じて強度を線形補間
                ratio = (distance - self.min_homing_distance) / (self.max_homing_distance - self.min_homing_distance)
                adjusted_homing = self.homing_strength * ratio
                
            if distance > 0 and adjusted_homing > 0:
                # 現在の方向ベクトルを正規化
                current_dx, current_dy = self.dx, self.dy
                
                # ターゲットへの方向ベクトルを正規化
                target_dx = dx / distance
                target_dy = dy / distance
                
                # 現在の方向とターゲット方向を補間
                new_dx = current_dx + (target_dx - current_dx) * adjusted_homing
                new_dy = current_dy + (target_dy - current_dy) * adjusted_homing
                
                # 新しい方向ベクトルを正規化
                length = math.sqrt(new_dx**2 + new_dy**2)
                if length > 0:
                    new_dx /= length
                    new_dy /= length
                
                # 最大旋回角度を制限
                if self.max_turn_angle > 0:
                    # 現在の角度と新しい角度を計算
                    current_angle = math.degrees(math.atan2(current_dy, current_dx))
                    new_angle = math.degrees(math.atan2(new_dy, new_dx))
                    
                    # 角度の差を計算（-180〜180度の範囲に正規化）
                    angle_diff = (new_angle - current_angle + 180) % 360 - 180
                    
                    # 最大旋回角度を制限
                    if abs(angle_diff) > self.max_turn_angle:
                        limited_angle = current_angle
                        if angle_diff > 0:
                            limited_angle += self.max_turn_angle
                        else:
                            limited_angle -= self.max_turn_angle
                            
                        # 限定された角度から新しい方向ベクトルを計算
                        limited_angle_rad = math.radians(limited_angle)
                        new_dx = math.cos(limited_angle_rad)
                        new_dy = math.sin(limited_angle_rad)
                
                # 新しい方向を設定
                self.dx = new_dx
                self.dy = new_dy
                
                # 弾の角度を更新（描画用）
                self.angle = math.degrees(math.atan2(-self.dy, self.dx)) - 90
        
        # 弾を移動
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        
        # 画面外に出たかチェック
        if (self.x < -self.width or self.x > 800 or
            self.y < -self.height or self.y > 600):
            return False  # 弾を削除
        
        return True  # 弾を維持
    
    def draw(self, screen):
        # 必殺技（ネギブラスト）の描画
        if self.is_special:
            # 大きな円形の必殺技エフェクト
            radius = max(self.width, self.height) / 2
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            
            # 外側の円（やや透明）
            s = pygame.Surface((radius*2.2, radius*2.2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, 100), (radius*1.1, radius*1.1), radius*1.1)
            screen.blit(s, (center_x - radius*1.1, center_y - radius*1.1))
            
            # 内側の円（より不透明）
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, 180), (radius, radius), radius)
            screen.blit(s, (center_x - radius, center_y - radius))
            
            # 中心の円（完全不透明）
            s = pygame.Surface((radius, radius), pygame.SRCALPHA)
            pygame.draw.circle(s, self.color, (radius/2, radius/2), radius/2)
            screen.blit(s, (center_x - radius/2, center_y - radius/2))
            
            # 放射状の光線
            for i in range(8):
                angle = i * 45 + (pygame.time.get_ticks() % 360) / 4  # 回転効果
                rad = math.radians(angle)
                length = radius * 1.5
                end_x = center_x + math.cos(rad) * length
                end_y = center_y + math.sin(rad) * length
                
                # 太さが変化する光線
                for width in [5, 3, 1]:
                    color_alpha = 150 if width == 5 else 220 if width == 3 else 255
                    pygame.draw.line(screen, (*self.color, color_alpha), 
                                    (center_x, center_y), (end_x, end_y), width)
            
            return
            
        # 近接攻撃の描画
        elif self.is_melee:
            # 近接攻撃のアニメーション進行度（0〜1）
            progress = self.current_life / self.lifespan
            
            # 斬撃エフェクトの描画
            # 円弧状の軌跡を描く
            start_angle = -30
            end_angle = 30
            current_angle = start_angle + (end_angle - start_angle) * progress
            
            # 斬撃の中心位置
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            
            # 斬撃の軌跡を描画（半透明の円弧）
            radius = self.width // 2
            arc_width = 15  # 軌跡の太さ
            
            # 複数の円弧を重ねて描画（グラデーション効果）
            for i in range(5):
                arc_alpha = 255 - i * 50  # だんだん透明に
                arc_color = (*self.color, arc_alpha if arc_alpha > 0 else 0)
                
                # 円弧の描画面を作成
                arc_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                
                # 円弧を描画（開始角度から現在角度まで）
                pygame.draw.arc(arc_surf, arc_color, 
                                (0, 0, radius*2, radius*2),
                                math.radians(start_angle), math.radians(current_angle),
                                arc_width - i*2 if arc_width - i*2 > 0 else 1)
                
                # メイン画面に描画
                screen.blit(arc_surf, (center_x - radius, center_y - radius))
            
            return
        
        # 通常弾の描画
        # 弾道の描画
        if len(self.trail_positions) > 1:
            # 弾道が残っている場合、線を描画
            points = self.trail_positions.copy()
            
            # 弾道の透明度を位置に応じて変化させる
            for i in range(len(points) - 1):
                # インデックスが大きいほど新しい位置（つまり不透明）
                alpha = int(255 * (i + 1) / len(points))
                pygame.draw.line(screen, (*self.color, alpha), points[i], points[i+1], 2)
        
        # チャージショットはより複雑なエフェクト
        if self.penetrate:
            # チャージショットは複数のレイヤーで表現
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            rotation_rect = pygame.Rect(0, 0, self.width, self.height)
            rotation_rect.center = (center_x, center_y)
            
            # 外側のグロー効果（半透明）
            s1 = pygame.Surface((self.width+10, self.height+10), pygame.SRCALPHA)
            pygame.draw.ellipse(s1, (*self.color, 100), (0, 0, self.width+10, self.height+10))
            # 回転して描画
            rotated1 = pygame.transform.rotate(s1, self.angle)
            rot_rect1 = rotated1.get_rect(center=rotation_rect.center)
            screen.blit(rotated1, rot_rect1)
            
            # 内側の本体（不透明）
            s2 = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.ellipse(s2, self.color, (0, 0, self.width, self.height))
            # 回転して描画
            rotated2 = pygame.transform.rotate(s2, self.angle)
            rot_rect2 = rotated2.get_rect(center=rotation_rect.center)
            screen.blit(rotated2, rot_rect2)
            
            # 中心の明るい部分
            s3 = pygame.Surface((self.width//2, self.height//2), pygame.SRCALPHA)
            inner_color = (min(self.color[0] + 50, 255), 
                          min(self.color[1] + 50, 255), 
                          min(self.color[2] + 50, 255))
            pygame.draw.ellipse(s3, inner_color, (0, 0, self.width//2, self.height//2))
            # 回転して描画
            rotated3 = pygame.transform.rotate(s3, self.angle)
            rot_rect3 = rotated3.get_rect(center=rotation_rect.center)
            screen.blit(rotated3, rot_rect3)
        else:
            # 通常弾は単純な回転楕円
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.ellipse(s, self.color, (0, 0, self.width, self.height))
            
            # 弾を回転
            rotated = pygame.transform.rotate(s, self.angle)
            rot_rect = rotated.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
            screen.blit(rotated, rot_rect)
    
    def get_explosion_damage_rect(self):
        # チャージショットの場合、弾道上の爆発による当たり判定を返す
        if self.penetrate:
            # 弾道上の最新の位置を中心に爆発範囲を設定
            if len(self.trail_positions) > 0:
                explosion_center = self.trail_positions[-1]
                explosion_radius = 40  # 爆発の半径
                
                # 爆発の矩形を返す
                return pygame.Rect(
                    explosion_center[0] - explosion_radius,
                    explosion_center[1] - explosion_radius,
                    explosion_radius * 2,
                    explosion_radius * 2
                )
        return None 