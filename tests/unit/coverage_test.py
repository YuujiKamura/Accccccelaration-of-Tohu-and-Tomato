"""
テストカバレッジを測定するスクリプト

このスクリプトは、coverageライブラリを使用して
テストカバレッジを測定し、レポートを生成します。
"""

import sys
import os
import coverage
import unittest
from unittest.mock import MagicMock

def run_coverage():
    """テストカバレッジを測定して結果を表示する"""
    # pygameをモック化してGUIの初期化を防ぐ
    sys.modules['pygame'] = MagicMock()
    import pygame

    # 実際のPygameの初期化を防ぐためにモック
    pygame.init = MagicMock()
    pygame.display.set_mode = MagicMock()
    pygame.display.set_caption = MagicMock()
    pygame.time.Clock = MagicMock()
    pygame.mixer.init = MagicMock()
    pygame.mixer.Sound = MagicMock()
    pygame.Surface = MagicMock()
    pygame.draw = MagicMock()
    pygame.image = MagicMock()
    pygame.time.get_ticks = MagicMock(return_value=0)

    # coverage測定開始
    cov = coverage.Coverage(
        source=['main', 'game_logic'],  # カバレッジを測定するモジュール
        omit=['*/__pycache__/*', '*/site-packages/*'],  # 除外するファイル
    )
    cov.start()

    try:
        # テストを実行
        from scripts.run_tests import run_all_tests
        run_all_tests()
    finally:
        # coverage測定終了
        cov.stop()
        cov.save()

        # レポート出力
        print("\n===== カバレッジレポート =====")
        cov.report()
        
        # HTMLレポート生成
        print("\nHTMLレポートを 'htmlcov' ディレクトリに生成しています...")
        cov.html_report(directory='htmlcov')
        
        print(f"\nHTMLレポートが生成されました: {os.path.abspath('htmlcov/index.html')}")

if __name__ == "__main__":
    # coverageライブラリがインストールされているか確認
    try:
        import coverage
    except ImportError:
        print("coverageライブラリがインストールされていません。")
        print("以下のコマンドでインストールしてください:")
        print("pip install coverage")
        sys.exit(1)
    
    # カバレッジ測定を実行
    run_coverage() 