"""
アドバタイズモードモニタリングモジュール

アドバタイズモードの実行をモニタリングし、動作データを収集します。
メインモジュールをパッチして、アドバタイズモードが有効な間プレイヤーの動きを追跡します。
"""

import sys
import os
import time
import pygame
import importlib
from advertise_mode.analyzer.analyzer import AdvertiseModeAnalyzer

class AdvertiseModeMonitor:
    """アドバタイズモードの動作をモニタリングするクラス"""
    
    def __init__(self, main_module_name="main", max_frames=1800, headless=True, show_progress=False):
        """初期化"""
        self.main_module_name = main_module_name
        self.max_frames = max_frames  # 30秒間（60FPS想定）
        self.headless = headless
        self.frame_count = 0
        self.analyzer = AdvertiseModeAnalyzer(verbose=show_progress)
        self.show_progress = show_progress
        self.start_time = None
        self.restart_detected = False
        
        # メインモジュールを動的にインポート
        try:
            # スクリプトとして直接実行されている場合は、importlib.import_moduleを使用
            self.main_module = importlib.import_module(self.main_module_name)
            self.patched = False
        except ImportError:
            print(f"モジュール {self.main_module_name} が見つかりません。パス: {sys.path}")
            sys.exit(1)
    
    def _patch_main_module(self):
        """メインモジュールのコードをパッチして、アドバタイズモードの動作をモニタリングできるようにする"""
        if self.patched:
            return
        
        # オリジナルの関数を保存
        self.original_update = self.main_module.Player.update
        
        # モニタリング用の関数でラップ
        def patched_update(self_player, keys, enemies, bullets):
            # オリジナルの更新を実行
            result = self.original_update(self_player, keys, enemies, bullets)
            
            # アドバタイズモードの場合のみ分析
            if self_player.advertise_mode:
                self.analyzer.update(self_player.x, self_player.y, enemies, self.frame_count)
            
            return result
        
        # 関数を置き換え
        self.main_module.Player.update = patched_update
        self.patched = True
    
    def run_analysis(self):
        """アドバタイズモードを実行して分析"""
        try:
            # メインモジュールをパッチ
            self._patch_main_module()
            
            # 開始時間を記録
            self.start_time = time.time()
            
            # ゲーム変数を初期化
            self.main_module.reset_game()
            
            # プレイヤーのアドバタイズモードを有効化
            if hasattr(self.main_module, 'player') and hasattr(self.main_module.player, 'toggle_advertise_mode'):
                self.main_module.player.toggle_advertise_mode()
                if self.show_progress:
                    print("アドバタイズモードを有効化しました")
            else:
                print("アドバタイズモードを有効化できませんでした")
                return
            
            if self.show_progress:
                print(f"アドバタイズモードのモニタリングを開始します（最大 {self.max_frames} フレーム, 約{self.max_frames/60:.1f}秒）...")
                print(f"早期終了条件の検出を有効化: 十分なデータが集まり次第終了します")
            self.analyzer.log("アドバタイズモードのモニタリングを開始")
            
            # メインループ
            clock = pygame.time.Clock()
            running = True
            
            while running and self.frame_count < self.max_frames:
                # ゲームロジックを実行
                if hasattr(self.main_module, 'player') and hasattr(self.main_module, 'enemies') and hasattr(self.main_module, 'bullets'):
                    # プレイヤーの位置を確認
                    player = self.main_module.player
                    enemies = self.main_module.enemies
                    bullets = self.main_module.bullets
                    
                    # ゲーム状態の更新（キーはすべて押されていない状態）
                    keys = {}
                    
                    # プレイヤーを更新（パッチされたupdateが呼ばれる）
                    player.update(keys, enemies, bullets)
                    
                    # ゲーム状態の更新
                    for enemy in enemies:
                        enemy.update()
                    
                    for bullet in bullets:
                        bullet.update()
                
                self.frame_count += 1
                
                # アナライザーにプレイヤーと敵の情報を渡す
                if hasattr(self.main_module, 'player') and hasattr(self.main_module, 'enemies'):
                    enough_data = self.analyzer.update(
                        self.main_module.player.x, 
                        self.main_module.player.y, 
                        self.main_module.enemies,
                        self.frame_count
                    )
                    
                    # 十分なデータが集まった場合は早期終了
                    if enough_data:
                        if self.show_progress:
                            print("\n十分なデータが集まりました。分析を早期終了します。")
                        break
                
                # FPSを制御
                if not self.headless:
                    # GUIありの場合は実際のフレームレートを維持
                    clock.tick(60)
                else:
                    # ヘッドレスモードではFPSは心配せず最速で実行
                    pass
                    
                # プログレスバーの更新
                if self.show_progress and self.frame_count % 60 == 0:
                    if self.frame_count % 300 == 0:  # 5秒ごとに改行
                        print()
                    progress = min(self.frame_count / self.max_frames, 1.0)
                    print(f"\r進捗: {self.frame_count}/{self.max_frames} フレーム ({progress:.0%}) ", end="")
                    
                # リスタートの検出
                if self.analyzer.restart_count > 0 and not self.restart_detected:
                    self.restart_detected = True
                    if self.show_progress:
                        print("\nゲームリスタートを検出しました。モニタリングを継続します。")
            
            # 分析を完了
            self.analyzer.analyze_session(self.frame_count)
            
            # 結果の要約を表示
            if self.show_progress:
                elapsed_time = time.time() - self.start_time
                print(f"\n\nアドバタイズモードの分析が完了しました（{self.frame_count}フレーム, {elapsed_time:.1f}秒）")
                self._summarize_results()
        
        except KeyboardInterrupt:
            print("\n\nユーザーによって中断されました。")
            if self.frame_count > 300:  # 最低5秒分のデータがあれば分析
                self.analyzer.analyze_session(self.frame_count)
                if self.show_progress:
                    print("部分的なデータで分析を実行します。")
                    self._summarize_results()
        
        except Exception as e:
            print(f"\n\nエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # リソースを解放
            self.analyzer.close()
    
    def _summarize_results(self):
        """分析結果を要約して表示"""
        results = self.analyzer.analysis_results
        
        print("\n====== アドバタイズモード分析結果 ======")
        print(f"中央エリア滞在時間比率: {results['center_time_ratio']:.2%}")
        print(f"振動動作の比率: {results['vibration_ratio']:.2%}")
        print(f"敵回避率: {results['enemy_avoidance_rate']:.2%}")
        print(f"中央からの平均距離: {results['average_distance_from_center']:.1f}ピクセル")
        
        if results['problematic_patterns']:
            print("\n問題のあるパターン:")
            for i, pattern in enumerate(results['problematic_patterns']):
                print(f"{i+1}. {pattern['type']}: {pattern['description']}")
        
        log_dir = os.environ.get('ADVERTISE_ANALYSIS_PATH', '.')
        print("\n分析結果は以下のファイルに保存されました:")
        print(f"- {os.path.join(log_dir, 'advertise_analysis_results.json')}（詳細な分析データ）")
        print(f"- {os.path.join(log_dir, 'advertise_analysis_heatmap.png')}（動きのヒートマップ）")
        print(f"- {os.path.join(log_dir, 'advertise_analysis_*.log')}（実行ログ）") 
アドバタイズモードモニタリングモジュール

アドバタイズモードの実行をモニタリングし、動作データを収集します。
メインモジュールをパッチして、アドバタイズモードが有効な間プレイヤーの動きを追跡します。
"""

import sys
import os
import time
import pygame
import importlib
from advertise_mode.analyzer.analyzer import AdvertiseModeAnalyzer

class AdvertiseModeMonitor:
    """アドバタイズモードの動作をモニタリングするクラス"""
    
    def __init__(self, main_module_name="main", max_frames=1800, headless=True, show_progress=False):
        """初期化"""
        self.main_module_name = main_module_name
        self.max_frames = max_frames  # 30秒間（60FPS想定）
        self.headless = headless
        self.frame_count = 0
        self.analyzer = AdvertiseModeAnalyzer(verbose=show_progress)
        self.show_progress = show_progress
        self.start_time = None
        self.restart_detected = False
        
        # メインモジュールを動的にインポート
        try:
            # スクリプトとして直接実行されている場合は、importlib.import_moduleを使用
            self.main_module = importlib.import_module(self.main_module_name)
            self.patched = False
        except ImportError:
            print(f"モジュール {self.main_module_name} が見つかりません。パス: {sys.path}")
            sys.exit(1)
    
    def _patch_main_module(self):
        """メインモジュールのコードをパッチして、アドバタイズモードの動作をモニタリングできるようにする"""
        if self.patched:
            return
        
        # オリジナルの関数を保存
        self.original_update = self.main_module.Player.update
        
        # モニタリング用の関数でラップ
        def patched_update(self_player, keys, enemies, bullets):
            # オリジナルの更新を実行
            result = self.original_update(self_player, keys, enemies, bullets)
            
            # アドバタイズモードの場合のみ分析
            if self_player.advertise_mode:
                self.analyzer.update(self_player.x, self_player.y, enemies, self.frame_count)
            
            return result
        
        # 関数を置き換え
        self.main_module.Player.update = patched_update
        self.patched = True
    
    def run_analysis(self):
        """アドバタイズモードを実行して分析"""
        try:
            # メインモジュールをパッチ
            self._patch_main_module()
            
            # 開始時間を記録
            self.start_time = time.time()
            
            # ゲーム変数を初期化
            self.main_module.reset_game()
            
            # プレイヤーのアドバタイズモードを有効化
            if hasattr(self.main_module, 'player') and hasattr(self.main_module.player, 'toggle_advertise_mode'):
                self.main_module.player.toggle_advertise_mode()
                if self.show_progress:
                    print("アドバタイズモードを有効化しました")
            else:
                print("アドバタイズモードを有効化できませんでした")
                return
            
            if self.show_progress:
                print(f"アドバタイズモードのモニタリングを開始します（最大 {self.max_frames} フレーム, 約{self.max_frames/60:.1f}秒）...")
                print(f"早期終了条件の検出を有効化: 十分なデータが集まり次第終了します")
            self.analyzer.log("アドバタイズモードのモニタリングを開始")
            
            # メインループ
            clock = pygame.time.Clock()
            running = True
            
            while running and self.frame_count < self.max_frames:
                # ゲームロジックを実行
                if hasattr(self.main_module, 'player') and hasattr(self.main_module, 'enemies') and hasattr(self.main_module, 'bullets'):
                    # プレイヤーの位置を確認
                    player = self.main_module.player
                    enemies = self.main_module.enemies
                    bullets = self.main_module.bullets
                    
                    # ゲーム状態の更新（キーはすべて押されていない状態）
                    keys = {}
                    
                    # プレイヤーを更新（パッチされたupdateが呼ばれる）
                    player.update(keys, enemies, bullets)
                    
                    # ゲーム状態の更新
                    for enemy in enemies:
                        enemy.update()
                    
                    for bullet in bullets:
                        bullet.update()
                
                self.frame_count += 1
                
                # アナライザーにプレイヤーと敵の情報を渡す
                if hasattr(self.main_module, 'player') and hasattr(self.main_module, 'enemies'):
                    enough_data = self.analyzer.update(
                        self.main_module.player.x, 
                        self.main_module.player.y, 
                        self.main_module.enemies,
                        self.frame_count
                    )
                    
                    # 十分なデータが集まった場合は早期終了
                    if enough_data:
                        if self.show_progress:
                            print("\n十分なデータが集まりました。分析を早期終了します。")
                        break
                
                # FPSを制御
                if not self.headless:
                    # GUIありの場合は実際のフレームレートを維持
                    clock.tick(60)
                else:
                    # ヘッドレスモードではFPSは心配せず最速で実行
                    pass
                    
                # プログレスバーの更新
                if self.show_progress and self.frame_count % 60 == 0:
                    if self.frame_count % 300 == 0:  # 5秒ごとに改行
                        print()
                    progress = min(self.frame_count / self.max_frames, 1.0)
                    print(f"\r進捗: {self.frame_count}/{self.max_frames} フレーム ({progress:.0%}) ", end="")
                    
                # リスタートの検出
                if self.analyzer.restart_count > 0 and not self.restart_detected:
                    self.restart_detected = True
                    if self.show_progress:
                        print("\nゲームリスタートを検出しました。モニタリングを継続します。")
            
            # 分析を完了
            self.analyzer.analyze_session(self.frame_count)
            
            # 結果の要約を表示
            if self.show_progress:
                elapsed_time = time.time() - self.start_time
                print(f"\n\nアドバタイズモードの分析が完了しました（{self.frame_count}フレーム, {elapsed_time:.1f}秒）")
                self._summarize_results()
        
        except KeyboardInterrupt:
            print("\n\nユーザーによって中断されました。")
            if self.frame_count > 300:  # 最低5秒分のデータがあれば分析
                self.analyzer.analyze_session(self.frame_count)
                if self.show_progress:
                    print("部分的なデータで分析を実行します。")
                    self._summarize_results()
        
        except Exception as e:
            print(f"\n\nエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # リソースを解放
            self.analyzer.close()
    
    def _summarize_results(self):
        """分析結果を要約して表示"""
        results = self.analyzer.analysis_results
        
        print("\n====== アドバタイズモード分析結果 ======")
        print(f"中央エリア滞在時間比率: {results['center_time_ratio']:.2%}")
        print(f"振動動作の比率: {results['vibration_ratio']:.2%}")
        print(f"敵回避率: {results['enemy_avoidance_rate']:.2%}")
        print(f"中央からの平均距離: {results['average_distance_from_center']:.1f}ピクセル")
        
        if results['problematic_patterns']:
            print("\n問題のあるパターン:")
            for i, pattern in enumerate(results['problematic_patterns']):
                print(f"{i+1}. {pattern['type']}: {pattern['description']}")
        
        log_dir = os.environ.get('ADVERTISE_ANALYSIS_PATH', '.')
        print("\n分析結果は以下のファイルに保存されました:")
        print(f"- {os.path.join(log_dir, 'advertise_analysis_results.json')}（詳細な分析データ）")
        print(f"- {os.path.join(log_dir, 'advertise_analysis_heatmap.png')}（動きのヒートマップ）")
        print(f"- {os.path.join(log_dir, 'advertise_analysis_*.log')}（実行ログ）") 