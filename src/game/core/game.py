import pygame
import random
import math
import sys

from src.game.core.player import Player
from src.game.core.bullet import Bullet, BULLET_TYPES
from src.game.core.enemy import Enemy, ENEMY_TYPES
from src.game.core.effects import RingEffect, SoundEffects
from src.game.core.controls import Controls
from src.game.core.debug_capture import ScreenshotAnalyzer
from src.game.core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, YELLOW, GREEN, BLUE,
    calculate_difficulty_factor, get_difficulty_name, select_enemy_type,
    get_enemy_spawn_chance, get_enemy_speed_factor
)

class Game:
    def __init__(self):
        # Pygameの初期化
        pygame.init()
        pygame.mixer.init()
        
        # 画面設定
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("アクセラレーションオブ豆腐")
        
        # クロックの初期化
        self.clock = pygame.time.Clock()
        
        # コントロールの初期化
        self.controls = Controls()
        
        # ゲームに必要なオブジェクトの初期化
        self.player = None
        self.bullets = []
        self.enemies = []
        self.score = 0
        self.high_score = 0
        self.game_over = False
        self.start_screen = True
        self.pause = False
        self.difficulty_factor = 1.0
        
        # エフェクト関連
        self.ring_effects = []
        self.sound_effects = SoundEffects()
        
        # フォントの初期化
        try:
            # 日本語フォントをロード
            self.font = pygame.font.Font("C:/Windows/Fonts/meiryo.ttc", 36)
            self.small_font = pygame.font.Font("C:/Windows/Fonts/meiryo.ttc", 24)
        except:
            # フォールバック: 日本語フォントが見つからない場合はSystemフォントを使用
            print("日本語フォントが見つからないため、システムフォントを使用します")
            self.font = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 24)
        
        # スクリーンショット解析システム
        self.screenshot_analyzer = ScreenshotAnalyzer()
        self.debug_mode = False  # デバッグモードフラグ
        
        # 収益化モード関連
        self.monetization_enabled = False  # 収益化機能有効フラグ
        
        # ゲーム状態のリセット
        self.reset_game()
        
    def reset_game(self):
        """ゲームをリセットする"""
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.score = 0
        self.game_over = False
        self.pause = False
        self.difficulty_factor = 1.0
        self.ring_effects = []
    
    def spawn_enemy(self):
        """敵を生成する"""
        # 現在のスコアと難易度に基づいて敵の種類と速度を決定
        enemy_type = select_enemy_type(self.score)
        speed_factor = get_enemy_speed_factor(self.score)
        
        # 敵を生成して追加
        enemy = Enemy(enemy_type=enemy_type, speed_factor=speed_factor)
        self.enemies.append(enemy)
    
    def update_enemies(self):
        """敵の更新処理"""
        for enemy in self.enemies[:]:
            if enemy.is_exploding:
                # 爆発中の敵の処理
                enemy.update_explosion()
                if not enemy.active:
                    self.enemies.remove(enemy)
            else:
                # 通常の敵の移動
                enemy.move(self.player.x + self.player.width/2, self.player.y + self.player.height/2)
                
                # 画面外判定
                if enemy.y > SCREEN_HEIGHT:
                    self.enemies.remove(enemy)
                    
                # プレイヤーとの衝突判定
                if not self.player.is_invincible() and not self.game_over:
                    player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
                    enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                    
                    if player_rect.colliderect(enemy_rect):
                        # プレイヤーが敵と衝突した場合
                        self.player.take_damage(10)
                        enemy.take_damage(enemy.hp)  # 敵も破壊
                        self.sound_effects.play('damage')
                        
                        # ダメージエフェクト
                        for _ in range(5):
                            ring = RingEffect(
                                self.player.x + self.player.width/2,
                                self.player.y + self.player.height/2,
                                RED,
                                max_radius=20,
                                expand_speed=3,
                                fade_speed=0.05
                            )
                            self.ring_effects.append(ring)

                        # プレイヤーのHPが0になったらゲームオーバー
                        if self.player.hp <= 0:
                            self.game_over = True
    
    def update_bullets(self):
        """弾の更新処理"""
        for bullet in self.bullets[:]:
            # 弾の移動
            if not bullet.move():
                # 画面外に出たら削除
                self.bullets.remove(bullet)
                continue
                
            # 敵との衝突判定
            bullet_rect = pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height)
            
            # 通常の衝突判定
            for enemy in self.enemies[:]:
                if enemy.is_exploding:
                    continue  # 爆発中の敵はスキップ
                    
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                
                if bullet_rect.colliderect(enemy_rect):
                    # 敵に命中
                    if enemy.take_damage(bullet.damage):
                        # 敵が破壊された場合
                        self.sound_effects.play('enemy_destroy')
                        self.score += enemy.score
                        
                        # 高スコア更新
                        if self.score > self.high_score:
                            self.high_score = self.score
                            
                        # プレイヤーの必殺技ゲージを増加
                        self.player.special_gauge += self.player.special_gain_rate
                        if self.player.special_gauge >= self.player.max_special_gauge:
                            self.player.special_gauge = self.player.max_special_gauge
                            self.player.special_ready = True
                            
                    # 貫通しない弾は命中したら消える
                    if not bullet.penetrate:
                        self.bullets.remove(bullet)
                        break
            
            # チャージショット（貫通弾）の爆発範囲判定
            explosion_rect = bullet.get_explosion_damage_rect()
            if explosion_rect:
                for enemy in self.enemies[:]:
                    if enemy.is_exploding:
                        continue
                        
                    enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                    
                    if explosion_rect.colliderect(enemy_rect):
                        # 爆発範囲内の敵にダメージ
                        if enemy.take_damage(bullet.damage * 0.5):  # 半分のダメージ
                            self.sound_effects.play('enemy_destroy')
                            self.score += enemy.score
                            
                            # 高スコア更新
                            if self.score > self.high_score:
                                self.high_score = self.score
                                
                            # プレイヤーの必殺技ゲージを増加
                            self.player.special_gauge += self.player.special_gain_rate
                            if self.player.special_gauge >= self.player.max_special_gauge:
                                self.player.special_gauge = self.player.max_special_gauge
                                self.player.special_ready = True
    
    def update_effects(self):
        """エフェクトの更新処理"""
        for ring in self.ring_effects[:]:
            if not ring.update():
                self.ring_effects.remove(ring)
    
    def draw_game(self):
        """ゲーム画面の描画"""
        # 背景を黒で塗りつぶす
        self.screen.fill(BLACK)
        
        # 敵の描画
        for enemy in self.enemies:
            enemy.draw(self.screen)
            
        # 弾の描画
        for bullet in self.bullets:
            bullet.draw(self.screen)
            
        # プレイヤーの描画
        self.player.draw(self.screen)
        
        # リングエフェクトの描画
        for ring in self.ring_effects:
            ring.draw(self.screen)
            
        # スコアとHPの描画
        self.draw_ui()
        
        # パズズ画面
        if self.pause:
            self.draw_pause_screen()
            
        # ゲームオーバー画面
        if self.game_over:
            self.draw_game_over_screen()
            
        # デバッグモードの場合、スクリーンショット解析オーバーレイを描画
        if self.debug_mode:
            self.screenshot_analyzer.draw_debug_overlay(self.screen)
            
        # 画面の更新
        pygame.display.flip()
    
    def draw_ui(self):
        """UIの描画"""
        # スコア表示
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # 難易度表示
        difficulty_name = get_difficulty_name(self.difficulty_factor)
        difficulty_text = self.small_font.render(f"難易度: {difficulty_name} ({self.difficulty_factor:.1f}x)", True, WHITE)
        self.screen.blit(difficulty_text, (10, 50))
        
        # HPゲージ
        hp_ratio = self.player.hp / self.player.max_hp
        hp_width = 200 * hp_ratio
        pygame.draw.rect(self.screen, RED, (SCREEN_WIDTH - 210, 10, 200, 20), 1)  # 枠
        pygame.draw.rect(self.screen, RED, (SCREEN_WIDTH - 210, 10, hp_width, 20))  # 中身
        hp_text = self.small_font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, WHITE)
        self.screen.blit(hp_text, (SCREEN_WIDTH - 210, 35))
        
        # 特殊ゲージ
        special_width = 200 * (self.player.special_gauge / self.player.max_special_gauge)
        pygame.draw.rect(self.screen, YELLOW, (SCREEN_WIDTH - 210, 60, 200, 10), 1)  # 枠
        pygame.draw.rect(self.screen, YELLOW, (SCREEN_WIDTH - 210, 60, special_width, 10))  # 中身
        special_text = self.small_font.render("Special", True, WHITE)
        self.screen.blit(special_text, (SCREEN_WIDTH - 210, 75))
        
        # ヒートゲージ
        heat_ratio = self.player.heat / self.player.max_heat
        heat_width = 150 * heat_ratio
        pygame.draw.rect(self.screen, BLUE, (SCREEN_WIDTH - 160, 100, 150, 10), 1)  # 枠
        pygame.draw.rect(self.screen, BLUE, (SCREEN_WIDTH - 160, 100, heat_width, 10))  # 中身
        heat_text = self.small_font.render("Heat", True, WHITE)
        self.screen.blit(heat_text, (SCREEN_WIDTH - 160, 115))
        
        # 収益化モード情報表示
        if hasattr(self.player, 'monetization_mode') and self.player.monetization_mode:
            monetization_stats = self.player.get_monetization_stats()
            # 半透明の背景パネル
            panel = pygame.Surface((300, 100), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 128))
            self.screen.blit(panel, (10, 80))
            
            # 収益化モード情報
            money_text = self.small_font.render(f"コイン: {monetization_stats['earnings']:.2f}", True, (255, 215, 0))
            self.screen.blit(money_text, (20, 90))
            
            # 残り時間
            hours = int(monetization_stats['remaining'] // 3600)
            minutes = int((monetization_stats['remaining'] % 3600) // 60)
            seconds = int(monetization_stats['remaining'] % 60)
            time_text = self.small_font.render(f"残り時間: {hours:02d}:{minutes:02d}:{seconds:02d}", True, WHITE)
            self.screen.blit(time_text, (20, 120))
            
            # レート
            rate_text = self.small_font.render(f"レート: {monetization_stats['rate']} コイン/100スコア", True, WHITE)
            self.screen.blit(rate_text, (20, 150))
    
    def draw_pause_screen(self):
        """ポーズ画面の描画"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # 半透明のオーバーレイ
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font.render("ポーズ中", True, WHITE)
        self.screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        
        resume_text = self.small_font.render("再開するには ESC または P キーを押してください", True, WHITE)
        self.screen.blit(resume_text, (SCREEN_WIDTH//2 - resume_text.get_width()//2, SCREEN_HEIGHT//2 + 10))
        
        quit_text = self.small_font.render("終了するには Q キーを押してください", True, WHITE)
        self.screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
    
    def draw_game_over_screen(self):
        """ゲームオーバー画面の描画"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 192))  # 半透明のオーバーレイ
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("ゲームオーバー", True, RED)
        self.screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
        
        score_text = self.font.render(f"スコア: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        
        high_score_text = self.font.render(f"最高スコア: {self.high_score}", True, WHITE)
        self.screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, SCREEN_HEIGHT//2))
        
        restart_text = self.small_font.render("リスタートするには R キーを押してください", True, WHITE)
        self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
        
        quit_text = self.small_font.render("終了するには Q キーを押してください", True, WHITE)
        self.screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, SCREEN_HEIGHT//2 + 80))
    
    def draw_start_screen(self):
        """スタート画面の描画"""
        self.screen.fill(BLACK)
        
        title_text = self.font.render("アクセラレーションオブ豆腐", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
        
        start_text = self.small_font.render("スタートするには SPACE キーを押してください", True, WHITE)
        self.screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, SCREEN_HEIGHT//2))
        
        quit_text = self.small_font.render("終了するには Q キーを押してください", True, WHITE)
        self.screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
        
        pygame.display.flip()
    
    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            # キー押下イベント
            if event.type == pygame.KEYDOWN:
                # ゲームオーバー時のリスタート
                if self.game_over and event.key == pygame.K_r:
                    self.reset_game()
                
                # ゲーム終了（Q）
                if event.key == pygame.K_q:
                    return False
                
                # ポーズ切り替え（ESC または P）
                if (event.key == pygame.K_ESCAPE or event.key == pygame.K_p) and not self.start_screen:
                    self.pause = not self.pause
                
                # スタート画面でのゲーム開始
                if self.start_screen and event.key == pygame.K_SPACE:
                    self.start_screen = False
                    
                # F1キーでアドバタイズモード切り替え
                if event.key == pygame.K_F1 and hasattr(self.player, 'toggle_advertise_mode'):
                    self.player.toggle_advertise_mode()
                    
                # F2キーで収益化モード切り替え
                if event.key == pygame.K_F2 and hasattr(self.player, 'toggle_monetization_mode'):
                    self.player.toggle_monetization_mode()
                    
                # F3キーで収益化時間設定（テスト用に短い時間設定）
                if event.key == pygame.K_F3 and hasattr(self.player, 'set_monetization_duration'):
                    self.player.set_monetization_duration(0.1)  # テスト用に6分間
                    
                # F4キーで収益化レート設定（テスト用に高レート）
                if event.key == pygame.K_F4 and hasattr(self.player, 'set_monetization_rate'):
                    self.player.set_monetization_rate(1.0)  # テスト用に高レート
                    
                # F12キーでデバッグモード切り替え
                if event.key == pygame.K_F12:
                    self.debug_mode = not self.debug_mode
                    if self.debug_mode:
                        print("デバッグモードで起動します")
                        self.screenshot_analyzer.start_auto_capture(30.0)  # 30秒ごとにキャプチャ
                    else:
                        self.screenshot_analyzer.stop_auto_capture()
                
                # F5キーでスクリーンショット撮影
                if event.key == pygame.K_F5 and self.debug_mode:
                    self.screenshot_analyzer.request_screenshot()
                    
        return True
    
    def run(self):
        """ゲームのメインループ"""
        running = True
        
        while running:
            # イベント処理
            running = self.handle_events()
            
            # ポーズ中は更新しない
            if self.pause:
                pygame.display.flip()
                self.clock.tick(60)
                continue
            
            # スタート画面
            if self.start_screen:
                self.draw_start_screen()
                pygame.display.flip()
                self.clock.tick(60)
                continue
            
            # ゲームオーバー画面
            if self.game_over:
                self.draw_game_over_screen()
                pygame.display.flip()
                self.clock.tick(60)
                continue
            
            # ゲーム画面の更新
            prev_hp = self.player.hp  # healthをhpに変更
            
            # 収益化モードの更新
            if hasattr(self.player, 'monetization_mode') and self.player.monetization_mode:
                self.player.update_monetization(self.score)
            
            # 敵の追加（一定確率）
            if random.random() < 0.02 * self.difficulty_factor:
                self.spawn_enemy()
            
            # 敵の更新
            self.update_enemies()
            
            # 弾の更新
            self.update_bullets()
            
            # プレイヤーの更新
            self.player.update(self.controls.get_keys(), self.enemies, self.bullets)
            
            # エフェクトの更新
            self.update_effects()
            
            # 難易度の更新
            self.difficulty_factor = calculate_difficulty_factor(self.score)
            
            # 画面描画
            self.draw_game()
            
            # デバッグモードの場合、デバッグオーバーレイを描画
            if self.debug_mode:
                self.screenshot_analyzer.draw_debug_overlay(self.screen)
            
            # 画面更新
            pygame.display.flip()
            
            # FPS制御
            self.clock.tick(60)
            
        # 終了処理
        self.screenshot_analyzer.stop_auto_capture()
        pygame.quit()
        
# 単体テスト用
if __name__ == "__main__":
    game = Game()
    game.run() 