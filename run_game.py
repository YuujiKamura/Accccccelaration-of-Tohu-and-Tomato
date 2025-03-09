#!/usr/bin/env python3
"""
アクセラレーションオブ豆腐 - ゲーム起動スクリプト
"""

import sys
import os
import argparse

# ルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.game.core.game import Game

if __name__ == "__main__":
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='アクセラレーションオブ豆腐を起動します')
    parser.add_argument('--debug', action='store_true', help='デバッグモードで起動')
    parser.add_argument('--capture-interval', type=float, default=30.0, 
                        help='スクリーンショットのキャプチャ間隔（秒）')
    parser.add_argument('--api-url', type=str, 
                        help='スクリーンショットを送信するAPIのURL')
    parser.add_argument('--api-token', type=str, 
                        help='API認証トークン')
    parser.add_argument('--no-upload', action='store_true',
                        help='APIへの自動アップロードを無効化（デフォルト）')
    parser.add_argument('--enable-upload', action='store_true',
                        help='APIへの自動アップロードを有効化')
    parser.add_argument('--text-areas', type=str,
                        help='日本語テキスト検出領域の設定（JSON形式）')
    parser.add_argument('--enable-imgur', action='store_true',
                        help='Imgurへの自動アップロードを有効化')
    parser.add_argument('--imgur-client-id', type=str,
                        help='ImgurのClient ID')
    parser.add_argument('--monetize', action='store_true',
                        help='起動時に収益化モードを有効化')
    parser.add_argument('--monetize-hours', type=float, default=1.0,
                        help='収益化モードの実行時間（時間単位、デフォルト: 1時間）')
    parser.add_argument('--monetize-rate', type=float, default=0.1,
                        help='収益化モードのコイン獲得レート（スコア100ごとのコイン数、デフォルト: 0.1）')
    args = parser.parse_args()
    
    # ゲームのインスタンス化と起動
    game = Game()
    
    # デバッグモードの設定
    if args.debug:
        game.debug_mode = True
        game.screenshot_analyzer.start_auto_capture(interval=args.capture_interval)
        
        # APIの設定
        if args.api_url:
            api_config = {
                "url": args.api_url,
                "token": args.api_token
            }
            game.screenshot_analyzer.set_api_config(api_config)
        
        # 自動アップロードの設定
        if args.enable_upload:
            game.screenshot_analyzer.toggle_auto_upload(True)
            print("API自動アップロード: 有効")
        elif args.no_upload:
            game.screenshot_analyzer.toggle_auto_upload(False)
            print("API自動アップロード: 無効")
            
        # テキスト領域設定
        if args.text_areas:
            import json
            try:
                areas = json.loads(args.text_areas)
                game.screenshot_analyzer.text_areas = areas
                print(f"テキスト検出領域を設定しました: {len(areas)}箇所")
            except json.JSONDecodeError:
                print(f"テキスト領域の設定が不正なJSON形式です: {args.text_areas}")
        
        # Imgurアップロード設定
        if args.enable_imgur:
            game.screenshot_analyzer.toggle_imgur_upload(True)
            print("Imgurへの自動アップロード: 有効")
            
            if args.imgur_client_id:
                game.screenshot_analyzer.imgur_uploader.client_id = args.imgur_client_id
                print(f"ImgurクライアントIDを設定しました")
    
    # ゲームを実行してプレイヤーインスタンスが作成されるのを待つ
    # ここでゲームを一度更新して、プレイヤーインスタンスを作成する
    game.reset_game()
    
    # 収益化モードの設定
    if args.monetize and hasattr(game.player, 'monetization_mode'):
        # 時間とレートの設定
        if hasattr(game.player, 'set_monetization_duration'):
            game.player.set_monetization_duration(args.monetize_hours)
        
        if hasattr(game.player, 'set_monetization_rate'):
            game.player.set_monetization_rate(args.monetize_rate)
        
        # 収益化モードを有効化
        if hasattr(game.player, 'toggle_monetization_mode'):
            game.player.toggle_monetization_mode()
            print(f"収益化モードを有効化しました（{args.monetize_hours}時間, レート: {args.monetize_rate}）")
    
    # ゲーム実行
    game.run() 