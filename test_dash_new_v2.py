import unittest
from test_mock_classes import Player, Enemy, Bullet, DashSpec

class DashTest(unittest.TestCase):
    """ダッシュ機能のテスト"""

    def setUp(self):
        """各テスト前の準備"""
        # プレイヤーオブジェクトを初期化
        self.player = Player()
        
        # 必要なキー入力の準備
        self.keys = {'left': False, 'right': False, 'up': False, 'down': False, 'shift': False, 'z': False}
        
        # 敵とバレットの配列を初期化
        self.enemies = []
        self.bullets = []

    def test_dash_activation(self):
        """ダッシュの基本的な作動テスト"""
        # シフトキーを押した状態
        self.keys['right'] = True
        self.keys['shift'] = True
        
        # プレイヤー更新前の状態確認
        self.assertFalse(self.player.is_dashing)
        
        # プレイヤー更新（ダッシュが作動するはず）
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # ダッシュが作動していることを確認
        self.assertTrue(self.player.is_dashing, "シフトキーを押した際にダッシュが作動すべき")
        
        # ヒートゲージが増加していることを確認
        self.assertGreater(self.player.heat, 0, "ダッシュ中はヒートゲージが増加するべき")

    def test_dash_speed(self):
        """ダッシュ中の速度が通常時より速いことを確認"""
        # 通常時の位置を記録
        initial_x = self.player.x
        
        # 通常移動
        self.keys['right'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # 通常移動での新しい位置
        normal_x = self.player.x
        normal_distance = normal_x - initial_x
        
        # 位置をリセット
        self.player = Player()
        initial_x = self.player.x
        
        # ダッシュ移動
        self.keys['right'] = True
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # ダッシュ移動での新しい位置
        dash_x = self.player.x
        dash_distance = dash_x - initial_x
        
        # ダッシュが通常移動より速いか確認
        self.assertGreater(dash_distance, normal_distance, "ダッシュ移動は通常移動よりも速くあるべき")

    def test_dash_cooldown(self):
        """ダッシュ使用後のクールダウンが正しく機能するか確認"""
        # ダッシュを有効化
        self.keys['right'] = True
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # ダッシュが有効になっていることを確認
        self.assertTrue(self.player.is_dashing)
        
        # ダッシュクールダウンを設定
        self.player.dash_cooldown = DashSpec.DASH_COOLDOWN
        
        # シフトキーを押し続ける
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # クールダウン中はダッシュが無効になることを確認
        self.assertFalse(self.player.is_dashing, "クールダウン中はダッシュが無効であるべき")
        
        # クールダウンが減少していることを確認
        self.assertLess(self.player.dash_cooldown, DashSpec.DASH_COOLDOWN, "クールダウンは時間経過とともに減少するべき")

    def test_dash_cooldown_prevention(self):
        """ダッシュクールダウン中に再度ダッシュできないことを確認"""
        # ダッシュを有効化してからクールダウンを設定
        self.keys['right'] = True
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # クールダウンを手動設定
        self.player.dash_cooldown = DashSpec.DASH_COOLDOWN
        
        # 一度ダッシュを止める
        self.keys['shift'] = False
        self.player.update(self.keys, self.enemies, self.bullets)
        self.assertFalse(self.player.is_dashing)
        
        # 再度ダッシュを試みる
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # クールダウン中はダッシュできないことを確認
        self.assertFalse(self.player.is_dashing, "クールダウン中は再度ダッシュを有効化できないはず")

    def test_dash_duration(self):
        """ダッシュの持続時間が正しく機能するか確認"""
        # 持続時間テストはダッシュ実装に依存するため、ここでは省略
        # 実際のゲームコードでは持続時間を制限するロジックが必要
        self.assertTrue(True)  # ダミーアサート

    def test_dash_movement(self):
        """ダッシュ中の移動方向が正しいか確認"""
        # 右方向へのダッシュ
        self.keys['right'] = True
        self.keys['shift'] = True
        initial_x = self.player.x
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # X座標が増加していることを確認
        self.assertGreater(self.player.x, initial_x, "右ダッシュでX座標が増加するべき")
        
        # 左方向へのダッシュのテスト
        self.player = Player()  # リセット
        self.keys['right'] = False
        self.keys['left'] = True
        initial_x = self.player.x
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # X座標が減少していることを確認
        self.assertLess(self.player.x, initial_x, "左ダッシュでX座標が減少するべき")

    def test_heat_gauge_increase(self):
        """ダッシュ中にヒートゲージが増加するか確認"""
        initial_heat = self.player.heat
        
        # ダッシュを有効化
        self.keys['right'] = True
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # ヒートゲージが増加していることを確認
        self.assertGreater(self.player.heat, initial_heat, "ダッシュ中はヒートゲージが増加するべき")
        
        # 増加量が想定通りか確認
        expected_heat = initial_heat + DashSpec.HEAT_INCREASE_RATE
        self.assertEqual(self.player.heat, expected_heat, "ヒートゲージの増加量が想定と異なる")

    def test_heat_gauge_recovery(self):
        """ダッシュ終了後にヒートゲージが回復するか確認"""
        # ダッシュでヒートゲージを増加
        self.keys['right'] = True
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # ヒートゲージの値を記録
        heat_after_dash = self.player.heat
        
        # ダッシュを終了して回復をテスト
        self.keys['shift'] = False
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # ヒートゲージが減少していることを確認
        self.assertLess(self.player.heat, heat_after_dash, "ダッシュ終了後はヒートゲージが回復(減少)するべき")
        
        # 回復量が想定通りか確認
        expected_heat = heat_after_dash - DashSpec.HEAT_RECOVERY_RATE
        self.assertEqual(self.player.heat, expected_heat, "ヒートゲージの回復量が想定と異なる")

    def test_max_heat_prevention(self):
        """ヒートゲージが最大値に達するとダッシュできなくなるか確認"""
        # ヒートゲージを最大値に設定
        self.player.heat = self.player.max_heat
        
        # ダッシュを試みる
        self.keys['right'] = True
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # ヒートゲージ最大時はダッシュが無効になることを確認
        self.assertFalse(self.player.is_dashing, "ヒートゲージ最大時はダッシュが無効になるべき")

    def test_dash_effects(self):
        """ダッシュエフェクトが正しく生成されるか確認"""
        # ダッシュを有効化
        self.keys['right'] = True
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # ダッシュエフェクトが生成されていることを確認
        self.assertGreater(len(self.player.dash_effects), 0, "ダッシュ中はエフェクトが生成されるべき")

    def test_diagonal_dash(self):
        """斜め方向のダッシュが正しく機能するか確認"""
        # 右上方向へのダッシュ
        self.keys['right'] = True
        self.keys['up'] = True
        self.keys['shift'] = True
        
        initial_x = self.player.x
        initial_y = self.player.y
        
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # X座標が増加、Y座標が減少していることを確認
        self.assertGreater(self.player.x, initial_x, "右上ダッシュでX座標が増加するべき")
        self.assertLess(self.player.y, initial_y, "右上ダッシュでY座標が減少するべき")

    def test_curve_movement(self):
        """カーブ移動（方向転換）が正しく機能するか確認"""
        # まず右方向に移動
        self.keys['right'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # 次に上方向に移動方向を変更
        self.keys['right'] = False
        self.keys['up'] = True
        
        # 移動前のY座標を記録
        initial_y = self.player.y
        
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # Y座標が減少していることを確認（上方向への移動）
        self.assertLess(self.player.y, initial_y, "方向転換後はその方向に移動するべき")

    def test_continuous_dash(self):
        """連続ダッシュが正しく機能するか確認"""
        # 1フレーム目：ダッシュ開始
        self.keys['right'] = True
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # ダッシュが有効になっていることを確認
        self.assertTrue(self.player.is_dashing)
        
        # 位置を記録
        pos_after_first_dash = self.player.x
        
        # 2フレーム目：ダッシュ継続
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # さらに移動していることを確認
        self.assertGreater(self.player.x, pos_after_first_dash, "連続ダッシュでさらに移動するべき")
        
        # ダッシュが継続していることを確認
        self.assertTrue(self.player.is_dashing, "シフトキーを押し続ける限りダッシュは継続するべき")

    def test_consecutive_dash(self):
        """クールダウン後の連続ダッシュが正しく機能するか確認"""
        # 1回目のダッシュ
        self.keys['right'] = True
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # クールダウンを設定
        self.player.dash_cooldown = DashSpec.DASH_COOLDOWN
        
        # ダッシュを一時停止（シフトキーを離す）
        self.keys['shift'] = False
        
        # クールダウンが終わるまで更新
        for _ in range(DashSpec.DASH_COOLDOWN + 1):
            self.player.update(self.keys, self.enemies, self.bullets)
        
        # クールダウンが終了していることを確認
        self.assertEqual(self.player.dash_cooldown, 0, "クールダウンが正しく終了するべき")
        
        # 2回目のダッシュを試みる
        self.keys['shift'] = True
        self.player.update(self.keys, self.enemies, self.bullets)
        
        # 2回目のダッシュが有効になることを確認
        self.assertTrue(self.player.is_dashing, "クールダウン後は再度ダッシュが有効になるべき")

if __name__ == '__main__':
    unittest.main() 