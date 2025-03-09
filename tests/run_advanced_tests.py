#!/usr/bin/env python
"""
高度な移動テストを実行し、詳細なレポートを出力するスクリプト
"""

import unittest
import sys
import os
import time
from datetime import datetime

# テストモジュールへのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テストモジュールをインポート
from tests.unit.test_advanced_movement import TestAdvancedMovement
from tests.helpers.test_base import BaseTestCase

def create_report_dir():
    """レポート出力ディレクトリを作成する"""
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    return reports_dir

if __name__ == "__main__":
    print("高度な移動テストを実行しています...")
    
    # レポートディレクトリを作成
    reports_dir = create_report_dir()
    
    # レポートファイル名を生成（現在時刻を含める）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = os.path.join(reports_dir, f'movement_test_report_{timestamp}.json')
    
    # テストスイートを作成
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAdvancedMovement)
    
    # テストを実行
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # テスト結果のレポートを生成
    print(f"\nテストレポートを生成中: {report_path}")
    TestAdvancedMovement.generate_report(report_path)
    
    print(f"\nレポートを {report_path} に保存しました")
    
    # テスト結果に基づいて終了コードを設定
    sys.exit(not result.wasSuccessful()) 