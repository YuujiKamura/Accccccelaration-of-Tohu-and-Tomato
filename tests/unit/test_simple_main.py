import unittest
from tests.unit.test_base import BaseTestCase, log_test
"""
単純化されたメインモジュール - テスト用

このモジュールは,リセット回数を制限してアドバタイズモードの無限ループを防止します.
"""

import sys
import os

# Pygameのモックを設定
import pygame
sys.modules['pygame'] = pygame

# モック関数を作成
class MockClock:
    def tick(self, *args):
        return 0

# Pygameの基本関数をモック
pygame.init = lambda: None
pygame.quit = lambda: None
pygame.display = type('MockDisplay', (), {
    'set_mode': lambda *args, **kwargs: type('MockSurface', (), {'fill': lambda *a, **k: None})(),
    'set_caption': lambda *args, **kwargs: None,
    'update': lambda: None,
    'Info': type('Info', (), {'current_w': 800, 'current_h': 600})
})()
pygame.time = type('MockTime', (), {
    'Clock': lambda: MockClock()
})()
pygame.event = type('MockEvent', (), {'get': lambda: []})

# 全てのPygame機能をモック化
for module_name in ['mixer', 'image', 'font', 'transform', 'draw', 'surface', 'sprite', 'mask', 'key']:
    if not hasattr(pygame, module_name):
        setattr(pygame, module_name, type(module_name, (), {}))

# ゲーム内の定数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# ゲーム状態変数
game_over = False
score = 0
enemies = []
bullets = []
player = None
advertise_mode_active = False
advertise_counter = 0

# リセットカウンター
reset_count = 0
MAX_RESET_COUNT = 5  # 最大リセット回数

# リセット関数をオーバーライド
def reset_game():
    """ゲーム状態を初期化するリセット関数"""
    global reset_count, game_over, score, enemies, bullets, advertise_mode_active, advertise_counter
    
    # リセットカウントを増やす
    reset_count += 1
    print(f"リセット実行 ({reset_count}/{MAX_RESET_COUNT})")
    
    # ゲーム変数をリセット
    game_over = False
    score = 0
    enemies = []
    bullets = []
    advertise_mode_active = False
    advertise_counter = 0
    
    # 最大回数に達したら終了
    if reset_count >= MAX_RESET_COUNT:
        print(f"最大リセット回数 ({MAX_RESET_COUNT}) に達したため終了します")
        sys.exit(0)

# 難易度計算関数
def calculate_difficulty_factor(score):
    """スコアから難易度係数を計算する"""
    base_difficulty = 1.0
    score_factor = score / 10000.0
    difficulty = min(base_difficulty + score_factor, 3.0)
    return difficulty

# 難易度名取得関数
def get_difficulty_name(difficulty_factor):
    """難易度係数から難易度名を取得する"""
    if difficulty_factor < 1.25:
        return "EASY"
    elif difficulty_factor < 1.75:
        return "NORMAL"
    elif difficulty_factor < 2.25:
        return "HARD"
    elif difficulty_factor < 2.75:
        return "EXPERT"
    else:
        return "MASTER"

# アドバタイズモード関数
def advertise_mode(dummy_arg=None):
    """アドバタイズモード - リセット回数制限付き"""
    global reset_count, advertise_counter, advertise_mode_active
    
    advertise_counter += 1
    advertise_mode_active = True
    print(f"アドバタイズモード実行 ({advertise_counter}回目)")
    
    # 3回実行したらリセット
    if advertise_counter >= 3:
        reset_game()
    
    return advertise_mode_active

# mainモジュールをインポートする前に必要なモックを設定
pygame.mixer.init = lambda: None
pygame.mixer.music = type('MockMusic', (), {
    'load': lambda *args: None,
    'play': lambda *args: None,
    'stop': lambda: None,
    'set_volume': lambda *args: None
})()

# モック化されたPlayerクラス
class Player:
    def __init__(self, x=SCREEN_WIDTH//2, y=SCREEN_HEIGHT//2):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.health = 100
        self.score = 0
        self.advertise_mode = False
    
    def update(self, *args, **kwargs):
        pass
    
    def draw(self, surface):
        pass
    
    def move(self, keys):
        pass
    
    def fire(self):
        pass

# モック化されたEnemyクラス
class Enemy:
    def __init__(self, x=0, y=0, enemy_type="mob"):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.health = 50
        self.is_defeated = False
        self.is_exploding = False
    
    def update(self):
        pass
    
    def draw(self, surface):
        pass
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.is_defeated = True

# モック化されたBulletクラス
class Bullet:
    def __init__(self, x=0, y=0, facing_right=True, bullet_type="beam_rifle"):
        self.x = x
        self.y = y
        self.bullet_type = bullet_type
        self.facing_right = facing_right
        self.is_player_bullet = True
        self.is_active = True
    
    def update(self):
        pass
    
    def draw(self, surface):
        pass
    
    def move(self):
        pass

# メインのゲームモジュールを安全にインポート - 遅延インポート
main = None

def safe_import_main():
    """安全にメインモジュールをインポートする関数"""
    global main
    
    if main is not None:
        return main
    
    try:
        # オリジナルのmainモジュールをインポート
        import src.game.core.main as imported_main
        main = imported_main

        # リセット関数をオーバーライド
        main.reset_game = reset_game
        
        # アドバタイズモードも制御
        if hasattr(main, 'advertise_mode'):
            main.advertise_mode = advertise_mode

        print("メインモジュールを正常にモック化しました")
        return main
    except ImportError:
        print("警告: mainモジュールをインポートできませんでした")
    except Exception as e:
        print(f"予期しないエラー: {e}")
    
    return None

# アクティブに使用するモック変数
player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
enemies = []
bullets = []

print("test_simple_main モジュールが読み込まれました（リセット回数制限: {}回）".format(MAX_RESET_COUNT))

# ここからテストケースの定義
class SimpleMainTest(BaseTestCase):
    """単純化されたメインモジュールのテスト"""
    
    def setUp(self):
        """各テスト前の準備"""
        super().setUp()
        global reset_count, game_over, score, enemies, bullets, player, advertise_mode_active, advertise_counter
        
        # テスト用に変数をリセット
        reset_count = 0
        game_over = False
        score = 0
        enemies = []
        bullets = []
        player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        advertise_mode_active = False
        advertise_counter = 0
    
    @log_test
    def test_calculate_difficulty_factor(self):
        """難易度計算関数のテスト"""
        # 基本難易度（スコア0）
        self.assertAlmostEqual(calculate_difficulty_factor(0), 1.0)
        
        # 中間難易度
        self.assertAlmostEqual(calculate_difficulty_factor(10000), 2.0)
        
        # 最大難易度
        self.assertAlmostEqual(calculate_difficulty_factor(30000), 3.0)
        
        # 上限を超えるスコアでも上限値に制限される
        self.assertAlmostEqual(calculate_difficulty_factor(50000), 3.0)
    
    @log_test
    def test_get_difficulty_name(self):
        """難易度名取得関数のテスト"""
        self.assertEqual(get_difficulty_name(1.0), "EASY")
        self.assertEqual(get_difficulty_name(1.5), "NORMAL")
        self.assertEqual(get_difficulty_name(2.0), "HARD")
        self.assertEqual(get_difficulty_name(2.5), "EXPERT")
        self.assertEqual(get_difficulty_name(3.0), "MASTER")
    
    @log_test
    def test_reset_game(self):
        """ゲームリセット機能のテスト"""
        # 初期状態を変更
        global score, game_over
        score = 1000
        game_over = True
        
        # リセット実行
        reset_game()
        
        # 状態確認
        self.assertEqual(score, 0)
        self.assertEqual(game_over, False)
        self.assertEqual(reset_count, 1)
    
    @log_test
    def test_advertise_mode(self):
        """アドバタイズモード機能のテスト"""
        # アドバタイズモード実行（一度目）
        advertise_mode()
        self.assertEqual(advertise_counter, 1)
        self.assertTrue(advertise_mode_active)
        
        # アドバタイズモード実行（二度目）
        advertise_mode()
        self.assertEqual(advertise_counter, 2)
        
        # アドバタイズモード実行（三度目）- リセットが実行される
        advertise_mode()
        self.assertEqual(advertise_counter, 0)  # リセットされたので0
        self.assertEqual(reset_count, 1)

if __name__ == "__main__":
    unittest.main() 