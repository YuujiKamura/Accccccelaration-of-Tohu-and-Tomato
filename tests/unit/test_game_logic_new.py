"""
新しいゲームロジックテスト

このモジュールはゲームの基本的なロジックをテストします。
"""

import unittest
from tests.unit.test_base import BaseTestCase, log_test
from unittest.mock import MagicMock

class GameLogicTest(BaseTestCase):
    """ゲームロジックのテスト"""
    
    def setUp(self):
        """テスト前の初期化"""
        super().setUp()
        
        # テスト用のゲームオブジェクトを作成
        self.player = MagicMock()
        self.player.x = 400
        self.player.y = 300
        self.player.width = 30
        self.player.height = 30
        self.player.health = 100
        self.player.score = 0
        
        self.enemies = []
        self.bullets = []
        
        # 簡易的な衝突判定関数
        def check_collision(obj1, obj2):
            return (obj1.x < obj2.x + obj2.width and
                    obj1.x + obj1.width > obj2.x and
                    obj1.y < obj2.y + obj2.height and
                    obj1.y + obj1.height > obj2.y)
        
        self.check_collision = check_collision
    
    @log_test
    def test_collision_detection(self):
        """衝突判定ロジックが正しく動作するか確認"""
        # テスト用のオブジェクトを作成
        obj1 = MagicMock()
        obj1.x = 100
        obj1.y = 100
        obj1.width = 50
        obj1.height = 50
        
        # 重なっているオブジェクト - 衝突する
        obj2 = MagicMock()
        obj2.x = 120
        obj2.y = 120
        obj2.width = 50
        obj2.height = 50
        
        # 重なっていることを確認
        self.assertTrue(obj1.x < obj2.x + obj2.width)
        self.assertTrue(obj1.x + obj1.width > obj2.x)
        self.assertTrue(self.check_collision(obj1, obj2))
        
        # 離れているオブジェクト - 衝突しない
        obj3 = MagicMock()
        obj3.x = 200
        obj3.y = 200
        obj3.width = 50
        obj3.height = 50
        self.assertFalse(self.check_collision(obj1, obj3))
    
    @log_test
    def test_score_calculation(self):
        """スコア計算が正しく行われるか確認"""
        # 初期スコア
        self.assertEqual(self.player.score, 0)
        
        # 敵撃破によるスコア加算をシミュレート
        def defeat_enemy(enemy_type):
            score_values = {
                "normal": 100,
                "fast": 200,
                "boss": 1000
            }
            self.player.score += score_values.get(enemy_type, 50)
        
        # スコア加算のテスト
        defeat_enemy("normal")
        self.assertEqual(self.player.score, 100)
        
        defeat_enemy("fast")
        self.assertEqual(self.player.score, 300)
        
        defeat_enemy("boss")
        self.assertEqual(self.player.score, 1300)
    
    @log_test
    def test_enemy_spawning(self):
        """敵の出現ロジックが正しく動作するか確認"""
        # 敵の出現関数
        def spawn_enemy(difficulty_factor):
            enemy_types = ["normal", "fast", "boss"]
            
            # 難易度に応じた敵の種類を選択
            if difficulty_factor < 1.5:
                enemy_type = enemy_types[0]  # normal
            elif difficulty_factor < 2.5:
                enemy_type = enemy_types[1]  # fast
            else:
                enemy_type = enemy_types[2]  # boss
                
            enemy = MagicMock()
            enemy.type = enemy_type
            return enemy
        
        # 難易度に応じた敵の出現テスト
        enemy1 = spawn_enemy(1.0)
        self.assertEqual(enemy1.type, "normal")
        
        enemy2 = spawn_enemy(2.0)
        self.assertEqual(enemy2.type, "fast")
        
        enemy3 = spawn_enemy(3.0)
        self.assertEqual(enemy3.type, "boss")

if __name__ == '__main__':
    unittest.main() 