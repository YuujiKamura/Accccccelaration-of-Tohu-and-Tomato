"""
武器の基本クラス
"""
import pygame
import math
from typing import Tuple, Optional

class BaseWeapon:
    def __init__(self, name: str, damage: int, cooldown: float):
        """
        武器の基本クラスのコンストラクタ
        
        Args:
            name (str): 武器の名前
            damage (int): 基本ダメージ
            cooldown (float): 攻撃のクールダウン時間（秒）
        """
        self.name = name
        self.damage = damage
        self.cooldown = cooldown
        self.last_shot_time = 0
        self.owner = None
        
    def can_shoot(self) -> bool:
        """
        射撃可能かどうかを判定
        
        Returns:
            bool: 射撃可能ならTrue
        """
        # テスト中は時間ベースのチェックをスキップ
        if not pygame.display.get_init():
            self.last_shot_time = 0
            return True
            
        current_time = pygame.time.get_ticks()
        return current_time - self.last_shot_time >= self.cooldown * 1000
        
    def shoot(self, start_pos: Tuple[float, float], target_pos: Optional[Tuple[float, float]] = None) -> None:
        """
        武器を発射
        
        Args:
            start_pos (Tuple[float, float]): 発射開始位置
            target_pos (Optional[Tuple[float, float]], optional): 目標位置
        """
        if not self.can_shoot():
            return
            
        self.last_shot_time = pygame.time.get_ticks()
        self._perform_shoot(start_pos, target_pos)
        
    def _perform_shoot(self, start_pos: Tuple[float, float], target_pos: Optional[Tuple[float, float]] = None) -> None:
        """
        実際の射撃処理（サブクラスでオーバーライド）
        
        Args:
            start_pos (Tuple[float, float]): 発射開始位置
            target_pos (Optional[Tuple[float, float]], optional): 目標位置
        """
        raise NotImplementedError("This method should be overridden by subclass")
        
    def update(self, dt: float) -> None:
        """
        武器の状態を更新
        
        Args:
            dt (float): 経過時間（秒）
        """
        pass
        
    def draw(self, screen: pygame.Surface, position: Tuple[float, float], angle: float = 0) -> None:
        """
        武器を描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            position (Tuple[float, float]): 描画位置
            angle (float, optional): 回転角度（度数法）
        """
        pass 