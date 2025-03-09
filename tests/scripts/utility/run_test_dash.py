#!/usr/bin/env python
"""
ダッシュテスト実行スクリプト

このスクリプトはtests/unit/test_dash_simple.pyのテストを実行します。
"""

import unittest
import sys
import os

# プロジェクトルートをPATHに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# テストをインポート
from tests.unit.test_dash_simple import DashSimpleTest

if __name__ == "__main__":
    # テストスイート作成
    suite = unittest.TestLoader().loadTestsFromTestCase(DashSimpleTest)
    
    # テスト実行
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # 終了コード設定
    sys.exit(not result.wasSuccessful()) 