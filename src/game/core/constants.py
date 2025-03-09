import pygame
import math
import random

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

# 難易度設定関数
def calculate_difficulty_factor(current_score):
    # 基本は1.0、最大3.0まで
    base_factor = 1.0
    # スコアに応じて上昇
    if current_score > 0:
        difficulty_increase = min(2.0, current_score / 10000)
        return base_factor + difficulty_increase
    return base_factor

def get_difficulty_name(factor):
    if factor < 1.1:
        return "豆腐初心者"
    elif factor < 1.5:
        return "豆腐見習い"
    elif factor < 2.0:
        return "豆腐使い"
    elif factor < 2.5:
        return "豆腐マスター"
    else:
        return "豆腐の達人"

def select_enemy_type(current_score):
    # スコアに基づいて出現可能な敵タイプをリストアップ
    available_types = []
    
    # 基本的な敵は常に出現
    available_types.append("mob")
    
    # スコアに応じて他の敵も出現
    if current_score >= 3000:
        available_types.append("speeder")
        
    if current_score >= 5000:
        available_types.append("tank")
        
    if current_score >= 10000:
        available_types.append("assassin")
    
    # ランダムに一つ選択
    return random.choice(available_types)

def get_enemy_spawn_chance(current_score):
    # ベースの出現確率
    base_chance = 0.02  # 2%
    
    # スコアに応じて上昇（最大10%まで）
    chance_increase = min(0.08, current_score / 50000 * 0.08)
    return base_chance + chance_increase

def get_enemy_speed_factor(current_score):
    # 難易度係数に基づいて敵の速度を調整
    difficulty = calculate_difficulty_factor(current_score)
    return difficulty * 0.8  # 難易度をそのまま使うと速すぎるので80%に 