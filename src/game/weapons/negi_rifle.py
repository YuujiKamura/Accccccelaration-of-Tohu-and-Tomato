"""
ネギライフル - プレイヤーの主要武器
"""
import pygame
import math
from typing import Tuple, Optional, List
from .base_weapon import BaseWeapon
from src.game.core.bullet import Bullet, BULLET_TYPES

# 定数
NEGI_COLOR = (200, 255, 200)  # 薄緑色
DARK_GREEN = (0, 100, 0)      # 深緑色

class NegiRifle(BaseWeapon):
    def __init__(self):
        """
        ネギライフルのコンストラクタ
        """
        super().__init__("ネギライフル", damage=10, cooldown=0.5)
        self.width = 40
        self.height = 10
        self.outline_width = 2
        self.charge_level = 0
        self.max_charge = 100
        self.is_charging = False
        self.ring_effects: List[dict] = []  # リングエフェクトのリスト
        self.angle = 0  # 武器の向き（度数法）
        
    def start_charge(self) -> None:
        """チャージを開始"""
        self.is_charging = True
        self.charge_level = 0
        
    def update_charge(self, dt: float) -> None:
        """
        チャージレベルを更新
        
        Args:
            dt (float): 経過時間（秒）
        """
        if self.is_charging:
            self.charge_level = min(self.charge_level + dt * 100, self.max_charge)  # チャージ速度を2倍に
            
    def release_charge(self) -> float:
        """
        チャージを解放
        
        Returns:
            float: チャージレベル（0-100）
        """
        charge = self.charge_level
        self.is_charging = False
        self.charge_level = 0
        return charge
        
    def _perform_shoot(self, start_pos: Tuple[float, float], target_pos: Optional[Tuple[float, float]] = None) -> None:
        if not self.owner:
            return
        
        # チャージレベルを取得（100%以上でレベル1）
        charge_level = 1 if self.charge_level >= self.max_charge else 0
        
        # 弾を生成
        bullet = Bullet(
            x=start_pos[0],
            y=start_pos[1],
            target=self.owner.locked_enemy if hasattr(self.owner, 'locked_enemy') else None,
            target_pos=target_pos,
            facing_right=self.owner.facing_right,
            bullet_type="beam_rifle",
            charge_level=charge_level
        )
        
        # 弾をリストに追加（bulletsリストが直接設定されている場合を優先）
        if hasattr(self, 'bullets') and self.bullets is not None:
            self.bullets.append(bullet)
        elif hasattr(self.owner, 'bullets') and self.owner.bullets is not None:
            self.owner.bullets.append(bullet)
        elif hasattr(self.owner, 'game') and hasattr(self.owner.game, 'bullets'):
            self.owner.game.bullets.append(bullet)
        
    def draw(self, screen: pygame.Surface, position: Tuple[float, float], angle: float = 0) -> None:
        """
        ネギライフルを描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            position (Tuple[float, float]): 描画位置
            angle (float, optional): 回転角度（度数法）
        """
        # リングエフェクトの更新と描画
        if self.is_charging:
            # 新しいリングを追加（一定間隔で）
            if len(self.ring_effects) == 0 or self.ring_effects[-1]["radius"] > 10:
                initial_radius = max(5, self.width / 4)  # 武器サイズに応じた初期半径
                self.ring_effects.append({
                    "radius": initial_radius,
                    "alpha": 255,
                    "color": (
                        min(255, NEGI_COLOR[0] + self.charge_level),
                        min(255, NEGI_COLOR[1] + self.charge_level),
                        NEGI_COLOR[2]
                    )
                })
            
            # リングの更新と描画
            new_effects = []
            for effect in self.ring_effects:
                # チャージレベルに応じて拡大速度を調整
                expand_speed = 1.0 + (self.charge_level / 50.0)  # 最大2倍の速度
                effect["radius"] += expand_speed
                effect["alpha"] = max(0, effect["alpha"] - 5)
                
                if effect["alpha"] > 0:
                    ring_surface = pygame.Surface((effect["radius"]*2 + 4, effect["radius"]*2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surface, 
                                    (*effect["color"], effect["alpha"]),
                                    (effect["radius"] + 2, effect["radius"] + 2),
                                    effect["radius"], 2)
                    ring_rect = ring_surface.get_rect(center=position)
                    screen.blit(ring_surface, ring_rect)
                    new_effects.append(effect)
                    
            self.ring_effects = new_effects
            
        # 回転用のサーフェスを作成
        surface = pygame.Surface((self.width + self.outline_width*2, 
                                self.height + self.outline_width*2), pygame.SRCALPHA)
                                
        # 輪郭を描画
        pygame.draw.rect(surface, DARK_GREEN, 
                        (0, 0, self.width + self.outline_width*2, 
                         self.height + self.outline_width*2))
                         
        # 本体を描画
        pygame.draw.rect(surface, NEGI_COLOR,
                        (self.outline_width, self.outline_width,
                         self.width, self.height))
                         
        # チャージ中は光らせる
        if self.is_charging:
            charge_color = (
                min(255, NEGI_COLOR[0] + self.charge_level),
                min(255, NEGI_COLOR[1] + self.charge_level),
                min(255, NEGI_COLOR[2])
            )
            glow_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*charge_color, 150),
                           (0, 0, self.width, self.height))
            surface.blit(glow_surface, (self.outline_width, self.outline_width))
            
        # 回転
        if angle != 0:
            surface = pygame.transform.rotate(surface, angle)
            
        # 描画位置の調整（中心を基準に）
        rect = surface.get_rect()
        rect.center = position
        
        # 画面に描画
        screen.blit(surface, rect) 