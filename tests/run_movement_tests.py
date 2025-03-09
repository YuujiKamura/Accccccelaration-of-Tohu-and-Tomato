#!/usr/bin/env python
"""
プレイヤーの移動と射撃に関するテストを実行するスクリプト
"""

import unittest
import sys
import os

# テストモジュールへのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テストモジュールをインポート
from tests.unit.test_player_movement import TestPlayerMovement
from tests.unit.test_player_shooting import TestPlayerShooting

if __name__ == "__main__":
    # テストローダーを作成
    loader = unittest.TestLoader()
    
    # テストスイートを作成
    suite = unittest.TestSuite()
    
    # 移動テストをスイートに追加
    suite.addTests(loader.loadTestsFromTestCase(TestPlayerMovement))
    
    # 射撃テストをスイートに追加
    suite.addTests(loader.loadTestsFromTestCase(TestPlayerShooting))
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果に基づいて終了コードを設定
    sys.exit(not result.wasSuccessful()) 