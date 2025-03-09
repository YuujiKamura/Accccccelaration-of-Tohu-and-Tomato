"""
単一のテストケースを実行するシンプルなスクリプト
"""

import sys
import os
import unittest

# テスト用のモック環境をセットアップ
def setup_test_environment():
    """テスト用環境をセットアップする"""
    print("テスト用環境をセットアップ中...")
    
    # pygameをモック化
    import sys
    from unittest.mock import MagicMock
    
    # モックPygameを設定
    sys.modules['pygame'] = MagicMock()
    import pygame
    
    # 特定のメソッドをオーバーライド
    pygame.time.get_ticks = MagicMock(return_value=0)
    
    # スコア初期化
    global score
    score = 0
    
    # メインゲームループフラグ
    global game_over
    game_over = False
    
    # ゲーム内オブジェクト
    global enemies, bullets
    enemies = []
    bullets = []
    
    # リセット回数
    global reset_count
    reset_count = 0
    MAX_RESET_COUNT = 5
    
    # リセット関数
    def reset_game():
        global reset_count, score, game_over, enemies, bullets
        reset_count += 1
        print(f"リセット実行 ({reset_count}/{MAX_RESET_COUNT})")
        
        # ゲーム状態の初期化
        score = 0
        game_over = False
        enemies = []
        bullets = []
        
        # 最大回数に達したら終了
        if reset_count >= MAX_RESET_COUNT:
            print(f"最大リセット回数 ({MAX_RESET_COUNT}) に達したため終了")
            sys.exit(0)
    
    # テスト用の関数をグローバルに設定
    sys.modules['__main__'].reset_game = reset_game
    sys.modules['__main__'].score = score
    sys.modules['__main__'].game_over = game_over
    sys.modules['__main__'].enemies = enemies
    sys.modules['__main__'].bullets = bullets
    
    print("テスト環境のセットアップが完了しました")

# メイン関数
def main():
    """単一のテストケースを実行する"""
    # テスト環境をセットアップ
    setup_test_environment()
    
    # コマンドライン引数から実行するテストを取得
    if len(sys.argv) < 3:
        print("使用方法: python run_single_test.py <テストファイル> <テストクラス>.<テストメソッド>")
        return 1
    
    test_file = sys.argv[1]
    test_method = sys.argv[2]
    
    # テストの実行
    test_command = f"python -m unittest {test_file}.{test_method}"
    print(f"テストを実行します: {test_command}")
    
    return os.system(test_command) >> 8  # 終了コードを取得

# スクリプト実行
if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 