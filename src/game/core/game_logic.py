"""
ゲームロジックとGUIを分離するためのモジュール

このモジュールは、main.pyのゲームロジックを分離し、
GUIの有無に関わらず実行できるようにするためのヘルパークラスを提供します。
"""

import random
import math
from src.game.core.dash_spec import DashSpec

# メインゲームからクラスをインポート
# 注意: この段階では直接インポートせず、関数経由で利用する
# from main import Player, Enemy, Bullet, RingEffect

class GameState:
    """ゲームの状態を管理するクラス。GUIの有無に関わらず動作します。"""
    
    def __init__(self, screen_width=800, screen_height=600, with_gui=True):
        """ゲーム状態の初期化
        
        Args:
            screen_width: 画面の幅
            screen_height: 画面の高さ
            with_gui: GUIを使用するかどうか
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.with_gui = with_gui
        
        # メインゲームからクラスをインポート
        # GUIなしモードの場合はメイン処理の前にPygameをモック化する必要がある
        from src.game.core.main import Player, Enemy, Bullet, SCREEN_WIDTH, SCREEN_HEIGHT
        
        # ゲーム状態
        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.score = 0
        self.game_over = False
        self.current_difficulty_factor = 1.0
    
    def update(self, keys):
        """ゲーム状態を更新する
        
        Args:
            keys: キー入力状態の辞書
            
        Returns:
            game_over: ゲームオーバーかどうか
        """
        if self.game_over:
            return True
            
        # プレイヤーの更新
        self.player.update(keys, self.enemies, self.bullets)
        
        # 敵の更新
        self._update_enemies()
        
        # 弾の更新
        self._update_bullets()
        
        # 衝突判定
        self._check_collisions()
        
        # 敵のスポーン
        self._spawn_enemies()
        
        return self.game_over
    
    def _update_enemies(self):
        """敵の更新処理"""
        from src.game.core.main import SCREEN_WIDTH, SCREEN_HEIGHT
        
        # 削除予定の敵を格納するリスト
        enemies_to_remove = []
        
        for enemy in self.enemies:
            # 敵が画面外に出たら削除
            if (enemy.x < -100 or enemy.x > SCREEN_WIDTH + 100 or
                enemy.y < -100 or enemy.y > SCREEN_HEIGHT + 100):
                enemies_to_remove.append(enemy)
                continue
                
            # 敵の更新
            enemy.move(self.player.x, self.player.y)
            
            # 爆発中の敵の処理
            if enemy.is_exploding:
                enemy.update_explosion()
                if enemy.explosion_finished:
                    enemies_to_remove.append(enemy)
        
        # 削除予定の敵を実際に削除
        for enemy in enemies_to_remove:
            if enemy in self.enemies:
                self.enemies.remove(enemy)
    
    def _update_bullets(self):
        """弾の更新処理"""
        from src.game.core.main import SCREEN_WIDTH, SCREEN_HEIGHT
        
        # 削除予定の弾を格納するリスト
        bullets_to_remove = []
        
        for bullet in self.bullets:
            # 弾の移動
            bullet.move()
            
            # 画面外に出たらリストから削除
            if (bullet.x < -100 or bullet.x > SCREEN_WIDTH + 100 or
                bullet.y < -100 or bullet.y > SCREEN_HEIGHT + 100):
                bullets_to_remove.append(bullet)
        
        # 削除予定の弾を実際に削除
        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)
    
    def _check_collisions(self):
        """衝突判定処理"""
        from src.game.core.main import Enemy
        
        # プレイヤーの弾と敵の衝突判定
        for bullet in self.bullets[:]:  # コピーを使用して反復中の変更を回避
            if bullet.is_player_bullet:
                for enemy in self.enemies[:]:  # こちらもコピーを使用
                    if not enemy.is_defeated and self._check_bullet_enemy_collision(bullet, enemy):
                        # 衝突があった場合
                        enemy.take_damage(bullet.damage)
                        
                        # 敵が倒された場合
                        if enemy.is_defeated:
                            self.score += enemy.score_value
                            self.player.update_special_gauge(enemy_defeated=True)
                            
                            # 難易度更新
                            self.current_difficulty_factor = self._calculate_difficulty_factor()
                        
                        # ビーム弾はヒット後も消えない（貫通）が、爆発弾などは消える
                        if bullet.bullet_type != "beam_rifle" or bullet.charge_level == 0:
                            if bullet in self.bullets:
                                self.bullets.remove(bullet)
                            break
        
        # 敵の弾とプレイヤーの衝突判定
        if not self.player.is_invincible():
            for bullet in self.bullets[:]:
                if not bullet.is_player_bullet and self._check_bullet_player_collision(bullet, self.player):
                    # プレイヤーがダメージを受ける
                    self.player.take_damage(bullet.damage)
                    
                    # 弾を削除
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    
                    # プレイヤーのHPがゼロになったらゲームオーバー
                    if self.player.hp <= 0:
                        self.game_over = True
                    break
    
    def _check_bullet_enemy_collision(self, bullet, enemy):
        """弾と敵の衝突判定
        
        Args:
            bullet: 弾のオブジェクト
            enemy: 敵のオブジェクト
            
        Returns:
            bool: 衝突したかどうか
        """
        # 通常の矩形衝突判定
        bullet_rect = bullet.get_collision_rect()
        enemy_rect = enemy.get_collision_rect()
        
        # 矩形同士の衝突判定
        return (bullet_rect[0] < enemy_rect[0] + enemy_rect[2] and
                bullet_rect[0] + bullet_rect[2] > enemy_rect[0] and
                bullet_rect[1] < enemy_rect[1] + enemy_rect[3] and
                bullet_rect[1] + bullet_rect[3] > enemy_rect[1])
    
    def _check_bullet_player_collision(self, bullet, player):
        """弾とプレイヤーの衝突判定
        
        Args:
            bullet: 弾のオブジェクト
            player: プレイヤーオブジェクト
            
        Returns:
            bool: 衝突したかどうか
        """
        # 矩形同士の衝突判定
        bullet_rect = bullet.get_collision_rect()
        player_rect = [player.x, player.y, player.width, player.height]
        
        return (bullet_rect[0] < player_rect[0] + player_rect[2] and
                bullet_rect[0] + bullet_rect[2] > player_rect[0] and
                bullet_rect[1] < player_rect[1] + player_rect[3] and
                bullet_rect[1] + bullet_rect[3] > player_rect[1])
    
    def _spawn_enemies(self):
        """敵のスポーン処理"""
        from src.game.core.main import Enemy, SCREEN_WIDTH, SCREEN_HEIGHT, select_enemy_type, get_enemy_spawn_chance, get_enemy_speed_factor
        
        # 現在のスコアに基づいて敵の出現確率を取得
        spawn_chance = get_enemy_spawn_chance(self.score)
        
        # ランダムに敵をスポーン
        if random.random() < spawn_chance:
            # 敵の種類を選択
            enemy_type = select_enemy_type(self.score)
            
            # 敵の速度係数を取得
            speed_factor = get_enemy_speed_factor(self.score)
            
            # スポーン位置を決定（画面外から）
            side = random.choice(["left", "right", "top", "bottom"])
            
            if side == "left":
                x = -50
                y = random.randint(50, SCREEN_HEIGHT - 50)
            elif side == "right":
                x = SCREEN_WIDTH + 50
                y = random.randint(50, SCREEN_HEIGHT - 50)
            elif side == "top":
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = -50
            else:  # "bottom"
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = SCREEN_HEIGHT + 50
            
            # 敵を作成
            enemy = Enemy(enemy_type=enemy_type, speed_factor=speed_factor)
            enemy.x = x
            enemy.y = y
            
            # 敵リストに追加
            self.enemies.append(enemy)
    
    def _calculate_difficulty_factor(self):
        """難易度係数を計算する
        
        Returns:
            float: 難易度係数（1.0～3.0）
        """
        from src.game.core.main import calculate_difficulty_factor
        return calculate_difficulty_factor(self.score)
    
    def reset(self):
        """ゲームをリセットする"""
        from src.game.core.main import Player
        
        # 難易度を一段階下げる（最低値は1.0）
        if self.game_over:
            self.current_difficulty_factor = max(1.0, self.current_difficulty_factor - 0.5)
            self.score = max(0, int(self.score * 0.7))
        else:
            self.current_difficulty_factor = 1.0
            self.score = 0
        
        # ゲーム状態をリセット
        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.game_over = False 

    def check_game_over(self):
        """ゲームオーバー判定"""
        if self.player.hp <= 0:  # healthをhpに変更
            self.game_over = True 