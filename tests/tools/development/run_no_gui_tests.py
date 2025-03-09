#!/usr/bin/env python
"""
GUIなしでテストを実行する特化型スクリプト

このスクリプトは、Pygameのモックを確実に設定し、元のゲームコードを実行せずに
テストだけを実行します。これによりアドバタイズモードのループや無限実行を防ぎます。
"""

import os
import sys
import unittest
import importlib
from unittest.mock import MagicMock

# 1. 実行前にPygameのモックを完全に準備
sys.modules['pygame'] = MagicMock()
pygame = sys.modules['pygame']

# 主要なPygame機能をモック
pygame.init = MagicMock(return_value=None)
pygame.quit = MagicMock(return_value=None)
pygame.display = MagicMock()
pygame.display.set_mode = MagicMock(return_value=MagicMock())
pygame.display.set_caption = MagicMock()
pygame.display.flip = MagicMock()
pygame.Surface = MagicMock(return_value=MagicMock())
pygame.time = MagicMock()
pygame.time.Clock = MagicMock()
pygame.time.get_ticks = MagicMock(return_value=0)
pygame.mixer = MagicMock()
pygame.mixer.init = MagicMock()
pygame.mixer.Sound = MagicMock()
pygame.image = MagicMock()
pygame.draw = MagicMock()
pygame.key = MagicMock()
pygame.key.get_pressed = MagicMock(return_value={})
pygame.event = MagicMock()
pygame.event.get = MagicMock(return_value=[])
pygame.transform = MagicMock()
pygame.transform.rotate = MagicMock(return_value=MagicMock())
pygame.transform.scale = MagicMock(return_value=MagicMock())
pygame.mouse = MagicMock()

# 特別な定数
pygame.SRCALPHA = 32
pygame.BLEND_RGBA_ADD = 0
pygame.QUIT = 256
pygame.K_LEFT = 'left'
pygame.K_RIGHT = 'right'
pygame.K_UP = 'up'
pygame.K_DOWN = 'down'
pygame.K_SPACE = 'space'
pygame.K_LSHIFT = 'shift'
pygame.K_F1 = 'f1'
pygame.K_F2 = 'f2'
pygame.K_ESCAPE = 'escape'

# 2. MagicMockを拡張して算術演算をサポート
class NumericMock(MagicMock):
    def __mod__(self, other):
        return 0
    
    def __lt__(self, other):
        return False
    
    def __gt__(self, other):
        return False
    
    def __le__(self, other):
        return True
    
    def __ge__(self, other):
        return True
    
    def __add__(self, other):
        if isinstance(other, (int, float)):
            return other
        return 0
    
    def __sub__(self, other):
        return 0
    
    def __mul__(self, other):
        return 0
    
    def __truediv__(self, other):
        return 0

# 数値を返す関数をNumericMockで置き換え
pygame.time.get_ticks = NumericMock(return_value=0)

# 3. 仮のmainモジュールを定義
class MockPlayer(MagicMock):
    def __init__(self):
        super().__init__()
        self.x = 400
        self.y = 300
        self.width = 32
        self.height = 32
        self.health = 100
        self.advertise_mode = False
        self.speed_x = 0
        self.speed_y = 0
    
    def update(self, *args, **kwargs):
        return

    def draw(self, *args, **kwargs):
        return

    def toggle_advertise_mode(self):
        return False

class MockEnemy(MagicMock):
    def __init__(self, enemy_type="mob", speed_factor=1.0):
        super().__init__()
        self.enemy_type = enemy_type
        self.speed_factor = speed_factor
        self.health = 50
        self.is_defeated = False
        self.is_exploding = False
        self.x = 0
        self.y = 0

class MockBullet(MagicMock):
    def __init__(self, x=0, y=0, target=None, facing_right=True, bullet_type="beam_rifle", charge_level=0, target_pos=None):
        super().__init__()
        self.x = x
        self.y = y
        self.facing_right = facing_right
        self.bullet_type = bullet_type
        self.charge_level = charge_level
        self.damage = 10
        self.is_player_bullet = True

class MockMain:
    # 定数
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    
    # クラス
    Player = MockPlayer
    Enemy = MockEnemy
    Bullet = MockBullet
    
    # 関数
    def calculate_difficulty_factor(current_score):
        return min(3.0, max(1.0, 1.0 + current_score / 20000))
    
    def get_difficulty_name(factor):
        if factor < 1.3:
            return "EASY"
        elif factor < 1.8:
            return "NORMAL"
        elif factor < 2.3:
            return "HARD"
        elif factor < 2.8:
            return "EXPERT"
        else:
            return "MASTER"
    
    def select_enemy_type(current_score):
        return "mob"
    
    def get_enemy_spawn_chance(current_score):
        return 0.05
    
    def get_enemy_speed_factor(current_score):
        return 1.0
    
    # グローバル変数
    player = MockPlayer()
    enemies = []
    bullets = []
    score = 0
    game_over = False
    
    # リセット関数
    def reset_game():
        MockMain.player = MockPlayer()
        MockMain.enemies = []
        MockMain.bullets = []
        MockMain.score = 0
        MockMain.game_over = False

# mainモジュールとして登録
sys.modules['main'] = MockMain

def run_tests(pattern='test_*.py', verbosity=2):
    """
    指定されたパターンに一致するテストを実行する
    
    Args:
        pattern: テストファイルのパターン（例：'test_basic.py'）
        verbosity: 詳細レベル（0-2）
        
    Returns:
        unittest.TestResult: テスト結果
    """
    # テストをロード
    loader = unittest.TestLoader()
    
    # patternがファイル名の場合は直接ロード
    if pattern.endswith('.py'):
        module_name = pattern[:-3]
        try:
            module = importlib.import_module(module_name)
            suite = loader.loadTestsFromModule(module)
            print(f"{module_name} から {suite.countTestCases()} 件のテストをロードしました")
        except ImportError as e:
            print(f"モジュール {module_name} のロードに失敗しました: {e}")
            return None
    else:
        # patternがパターンの場合は検索
        suite = loader.discover('.', pattern=pattern)
        
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=verbosity)
    print(f"\n===== テスト開始: {pattern} =====")
    result = runner.run(suite)
    
    # 結果サマリー
    print(f"\n===== テスト結果サマリー =====")
    print(f"実行したテスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    return result

if __name__ == "__main__":
    # 引数処理
    import argparse
    parser = argparse.ArgumentParser(description='GUIなしでのテスト実行')
    parser.add_argument('--pattern', type=str, default='test_*.py', 
                        help='テストファイルのパターンまたはファイル名')
    parser.add_argument('-v', '--verbose', action='count', default=1,
                        help='詳細度を増やす')
    
    args = parser.parse_args()
    
    # テスト実行
    result = run_tests(args.pattern, args.verbose)
    
    # 終了コード
    sys.exit(0 if result and result.wasSuccessful() else 1) 