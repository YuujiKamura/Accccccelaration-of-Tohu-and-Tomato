import pygame

class Controls:
    """
    ゲームのキーバインドを管理するクラス
    キー設定の定義と入力状態の管理を行う
    テストでの入力シミュレーションにも使用可能
    """
    
    def __init__(self):
        # デフォルトのキー割り当て
        self.key_bindings = {
            'up': pygame.K_UP,
            'down': pygame.K_DOWN,
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'shoot': pygame.K_z,
            'charge': pygame.K_x,
            'dash': pygame.K_LSHIFT,
            'special': pygame.K_c,
            'pause': pygame.K_ESCAPE,
        }
        
        # 現在の入力状態
        self.pressed_keys = {}
        
        # シミュレートされた入力状態（テスト用）
        self.simulated_keys = {}
        
        # シミュレーションモードかどうか
        self.simulation_mode = False
    
    def set_key_binding(self, action, key_code):
        """
        キー割り当てを変更する
        
        Args:
            action (str): 変更する操作名
            key_code (int): 割り当てるキーコード
        """
        if action in self.key_bindings:
            self.key_bindings[action] = key_code
    
    def get_key_binding(self, action):
        """
        特定の操作に割り当てられたキーコードを取得する
        
        Args:
            action (str): 操作名
            
        Returns:
            int: キーコード。割り当てがない場合はNone
        """
        return self.key_bindings.get(action)
    
    def is_pressed(self, action):
        """
        特定の操作キーが押されているかどうかを確認する
        
        Args:
            action (str): 操作名
            
        Returns:
            bool: キーが押されていればTrue、そうでなければFalse
        """
        if self.simulation_mode:
            # シミュレーションモードでは、シミュレートされた入力状態を使用
            return self.simulated_keys.get(action, False)
        else:
            # 実際のキー入力状態を使用
            key = self.key_bindings.get(action)
            if key is None:
                return False
            
            # pygame.key.get_pressed()の結果から対応するキーの状態を取得
            key_state = self.pressed_keys.get(key, False)
            return key_state
    
    def update_key_states(self):
        """
        現在のキー入力状態を更新する
        """
        if not self.simulation_mode:
            # pygame.key.get_pressed()の結果を取得
            keys = pygame.key.get_pressed()
            
            # 全てのバインドされたキーについて、押されているかどうかを記録
            for action, key in self.key_bindings.items():
                self.pressed_keys[key] = keys[key]
    
    def set_simulation_mode(self, enabled):
        """
        シミュレーションモードの有効/無効を切り替える
        
        Args:
            enabled (bool): シミュレーションモードを有効にする場合はTrue
        """
        self.simulation_mode = enabled
        if enabled:
            # シミュレーションモードを有効にした時、全ての入力をリセット
            self.simulated_keys = {action: False for action in self.key_bindings}
    
    def simulate_key_press(self, action, pressed=True):
        """
        キー入力をシミュレートする（テスト用）
        
        Args:
            action (str): シミュレートする操作名
            pressed (bool): 押された状態にする場合はTrue、離した状態にする場合はFalse
        """
        if self.simulation_mode and action in self.key_bindings:
            self.simulated_keys[action] = pressed
    
    def get_movement_vector(self):
        """
        移動方向ベクトルを取得する
        
        Returns:
            tuple: (x方向, y方向)の正規化されたベクトル
        """
        dx = 0
        dy = 0
        
        if self.is_pressed('left'):
            dx -= 1
        if self.is_pressed('right'):
            dx += 1
        if self.is_pressed('up'):
            dy -= 1
        if self.is_pressed('down'):
            dy += 1
            
        # 斜め移動時に速度が速くならないよう正規化
        if dx != 0 and dy != 0:
            # 0.7071はルート2分の1の近似値
            dx *= 0.7071
            dy *= 0.7071
            
        return (dx, dy)
    
    def create_keys_dict(self):
        """
        Playerクラスなどに渡すための、pygameのキー状態辞書を作成する
        
        Returns:
            dict: 各キーが押されているかどうかを示す辞書
        """
        if self.simulation_mode:
            # シミュレーションモードでは、設定されたシミュレーション状態から辞書を生成
            keys_dict = {}
            for action, key in self.key_bindings.items():
                keys_dict[key] = self.simulated_keys.get(action, False)
            return keys_dict
        else:
            # 実際のキー入力状態をそのまま返す
            return self.pressed_keys
            
    def get_keys(self):
        """
        Playerクラスのupdateメソッドに渡すためのキー状態辞書を取得する
        
        Returns:
            dict: 各キーが押されているかどうかを示す辞書
        """
        # キー状態を最新の状態に更新
        self.update_key_states()
        
        # create_keys_dictと同じ形式のデータを返す
        return self.create_keys_dict() 