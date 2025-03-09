"""
シンプルなテストケース

基本的なゲーム機能をテストするシンプルなテストケース
main.pyに直接依存せず、モックオブジェクトを使用します。
"""

import unittest
import sys
import os
from unittest.mock import MagicMock
from tests.unit.test_base import BaseTestCase, log_test

# 定数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# モック化されたPlayerクラス
class Player:
    def __init__(self, x=400, y=300):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.health = 100
        self.score = 0
        self.advertise_mode = False
    
    def update(self):
        pass
    
    def draw(self, surface):
        pass

class SimpleGameTest(BaseTestCase):
    """基本的なゲーム機能のテスト"""
    
    def setUp(self):
        super().setUp()
        # テスト用のオブジェクトを初期化
        self.player = MagicMock()
        self.player.x = 400
        self.player.y = 300
        self.player.health = 100
        self.player.score = 0
        
        self.enemies = []
        self.bullets = []
    
    @log_test
    def test_constants(self):
        """ゲームの定数が正しく設定されているか確認"""
        self.assertEqual(SCREEN_WIDTH, 800)
        self.assertEqual(SCREEN_HEIGHT, 600)
        self.assertEqual(WHITE, (255, 255, 255))
        self.assertEqual(BLACK, (0, 0, 0))
        self.assertEqual(RED, (255, 0, 0))
    
    @log_test
    def test_player_creation(self):
        """プレイヤーが正しく生成されるか確認"""
        player = Player(x=400, y=300)
        
        # 初期位置
        self.assertEqual(player.x, 400)
        self.assertEqual(player.y, 300)
        
        # デフォルト値
        self.assertEqual(player.health, 100)
        self.assertEqual(player.score, 0)
    
    @log_test
    def test_difficulty_calculation(self):
        """難易度計算の基本的なロジックをテスト"""
        def calculate_difficulty(score):
            return min(3.0, max(1.0, 1.0 + score / 20000))
        
        # 難易度計算のテスト
        self.assertEqual(calculate_difficulty(0), 1.0)  # 初期スコアでは最低難易度
        self.assertEqual(calculate_difficulty(20000), 2.0)  # 中間スコア
        self.assertEqual(calculate_difficulty(40000), 3.0)  # 最高難易度
        self.assertEqual(calculate_difficulty(100000), 3.0)  # 上限を超えても最高難易度のまま
    
    @log_test
    def test_difficulty_names(self):
        """難易度名が正しく取得できるか確認"""
        # モック関数
        def get_difficulty_name(factor):
            if factor < 1.25:
                return "EASY"
            elif factor < 1.75:
                return "NORMAL"
            elif factor < 2.25:
                return "HARD"
            elif factor < 2.75:
                return "EXPERT"
            else:
                return "MASTER"
                
        # 各難易度の境界値をテスト
        self.assertEqual(get_difficulty_name(1.0), "EASY")
        self.assertEqual(get_difficulty_name(1.5), "NORMAL")
        self.assertEqual(get_difficulty_name(2.0), "HARD")
        self.assertEqual(get_difficulty_name(2.5), "EXPERT")
        self.assertEqual(get_difficulty_name(3.0), "MASTER")
    
    # 意図的に失敗するテストケース - 紛らわしいのでコメントアウト
    '''
    @log_test
    def test_intentional_failure(self):
        """意図的に失敗するテスト - ロガーの挙動確認用"""
        # 明らかに失敗するアサーション
        self.assertEqual(1, 2, "数値が一致しません（意図的な失敗）")
    '''

if __name__ == '__main__':
    unittest.main() 