"""
Pygameの高度なモック

このモジュールは、より実際のPygameに近い動作をするモック実装を提供し、
GUIを起動せずにPygameの機能を正確にテストできるようにします。
"""

import sys
from unittest.mock import MagicMock

class PygameMock:
    """Pygameをモック化するクラス"""

    def __init__(self):
        # 基本モック
        self.init = MagicMock(return_value=None)
        self.quit = MagicMock(return_value=None)
        
        # 画面設定
        self.display = self._create_display_mock()
        
        # 描画関連
        self.draw = self._create_draw_mock()
        self.Surface = self._create_surface_mock()
        self.Rect = self._create_rect_mock()
        
        # 変形
        self.transform = self._create_transform_mock()
        
        # キー入力
        self.key = self._create_key_mock()
        
        # イベント
        self.event = self._create_event_mock()
        self.QUIT = 256
        
        # 時間
        self.time = self._create_time_mock()
        
        # 色の定数
        self.Color = self._create_color_mock()
        
        # サウンド
        self.mixer = self._create_mixer_mock()
        
        # フォント
        self.font = self._create_font_mock()
        
        # 画像
        self.image = self._create_image_mock()
        
        # キー定数
        self.K_LEFT = 'left'
        self.K_RIGHT = 'right'
        self.K_UP = 'up'
        self.K_DOWN = 'down'
        self.K_SPACE = 'space'
        self.K_LSHIFT = 'shift'
        self.K_F1 = 'f1'
        self.K_F2 = 'f2'
        self.K_ESCAPE = 'escape'
        
        # マウス
        self.mouse = self._create_mouse_mock()
        
        # 定数とフラグ
        self.SRCALPHA = 32
        self.BLEND_RGBA_ADD = 0
        self.BLEND_RGBA_MULT = 1
        self.BLEND_RGBA_SUB = 2
        self.KEYDOWN = 768
        self.KEYUP = 769
        self.MOUSEBUTTONDOWN = 1024
        self.MOUSEBUTTONUP = 1025
        self.MOUSEMOTION = 1026

    def _create_display_mock(self):
        """ディスプレイ関連のモックを作成"""
        display = MagicMock()
        display.set_mode = MagicMock(return_value=self._create_surface_mock()())
        display.set_caption = MagicMock()
        display.flip = MagicMock()
        display.update = MagicMock()
        display.get_surface = MagicMock(return_value=self._create_surface_mock()())
        return display

    def _create_surface_mock(self):
        """サーフェイス関連のモックを作成"""
        surface_instance = MagicMock()
        surface_instance.get_rect = MagicMock(return_value=self._create_rect_mock()())
        surface_instance.fill = MagicMock()
        surface_instance.blit = MagicMock()
        surface_instance.get_size = MagicMock(return_value=(800, 600))
        surface_instance.get_at = MagicMock(return_value=(0, 0, 0, 255))
        surface_instance.set_at = MagicMock()
        surface_instance.subsurface = MagicMock(return_value=surface_instance)
        surface_instance.copy = MagicMock(return_value=surface_instance)
        surface_instance.convert_alpha = MagicMock(return_value=surface_instance)
        surface_instance.convert = MagicMock(return_value=surface_instance)
        surface_instance.get_alpha = MagicMock(return_value=255)
        surface_instance.set_alpha = MagicMock()
        
        surface = MagicMock(return_value=surface_instance)
        return surface

    def _create_rect_mock(self):
        """矩形関連のモックを作成"""
        rect_instance = MagicMock()
        rect_instance.x = 0
        rect_instance.y = 0
        rect_instance.width = 100
        rect_instance.height = 100
        rect_instance.centerx = 50
        rect_instance.centery = 50
        rect_instance.center = (50, 50)
        rect_instance.topleft = (0, 0)
        rect_instance.topright = (100, 0)
        rect_instance.bottomleft = (0, 100)
        rect_instance.bottomright = (100, 100)
        rect_instance.colliderect = MagicMock(return_value=False)
        rect_instance.collidepoint = MagicMock(return_value=False)
        rect_instance.collidepoint.side_effect = lambda x, y: 0 <= x < 100 and 0 <= y < 100
        rect_instance.colliderect.side_effect = lambda other: (
            rect_instance.x < other.x + other.width and
            rect_instance.x + rect_instance.width > other.x and
            rect_instance.y < other.y + other.height and
            rect_instance.y + rect_instance.height > other.y
        )
        
        rect = MagicMock(return_value=rect_instance)
        return rect

    def _create_key_mock(self):
        """キー入力関連のモックを作成"""
        key = MagicMock()
        pressed_keys = {
            'left': False,
            'right': False,
            'up': False,
            'down': False,
            'space': False,
            'shift': False,
            'f1': False,
            'f2': False,
            'escape': False
        }
        key.get_pressed = MagicMock(return_value=pressed_keys)
        return key

    def _create_event_mock(self):
        """イベント関連のモックを作成"""
        event = MagicMock()
        event.get = MagicMock(return_value=[])
        event.poll = MagicMock(return_value=MagicMock(type=0))
        event.Event = MagicMock(return_value=MagicMock(type=0))
        return event

    def _create_time_mock(self):
        """時間関連のモックを作成"""
        time = MagicMock()
        time.Clock = MagicMock()
        time.Clock.return_value.tick = MagicMock(return_value=16)  # 約60FPS
        time.get_ticks = MagicMock(return_value=0)
        time.delay = MagicMock()
        time.wait = MagicMock()
        
        # get_ticksは呼び出すたびに値が増えるようにする
        tick_value = [0]
        def increase_ticks():
            tick_value[0] += 16  # 約16ms (60FPS)
            return tick_value[0]
        time.get_ticks.side_effect = increase_ticks
        
        return time

    def _create_color_mock(self):
        """色関連のモックを作成"""
        color = MagicMock()
        color.side_effect = lambda *args: args if len(args) in (3, 4) else (0, 0, 0)
        return color

    def _create_mixer_mock(self):
        """サウンド関連のモックを作成"""
        mixer = MagicMock()
        mixer.init = MagicMock()
        mixer.quit = MagicMock()
        
        sound_instance = MagicMock()
        sound_instance.play = MagicMock()
        sound_instance.stop = MagicMock()
        sound_instance.set_volume = MagicMock()
        
        mixer.Sound = MagicMock(return_value=sound_instance)
        
        music = MagicMock()
        music.load = MagicMock()
        music.play = MagicMock()
        music.stop = MagicMock()
        music.set_volume = MagicMock()
        music.get_busy = MagicMock(return_value=False)
        
        mixer.music = music
        
        return mixer

    def _create_font_mock(self):
        """フォント関連のモックを作成"""
        font = MagicMock()
        
        font_instance = MagicMock()
        font_instance.render = MagicMock(return_value=self._create_surface_mock()())
        font_instance.size = MagicMock(return_value=(100, 20))
        
        font.Font = MagicMock(return_value=font_instance)
        font.SysFont = MagicMock(return_value=font_instance)
        font.get_fonts = MagicMock(return_value=['arial', 'times', 'calibri'])
        
        return font

    def _create_image_mock(self):
        """画像関連のモックを作成"""
        image = MagicMock()
        image.load = MagicMock(return_value=self._create_surface_mock()())
        image.save = MagicMock()
        return image

    def _create_mouse_mock(self):
        """マウス関連のモックを作成"""
        mouse = MagicMock()
        mouse.get_pos = MagicMock(return_value=(400, 300))
        mouse.get_pressed = MagicMock(return_value=(False, False, False))
        mouse.set_visible = MagicMock()
        mouse.set_pos = MagicMock()
        return mouse

    def _create_draw_mock(self):
        """描画関連のモックを作成"""
        draw = MagicMock()
        draw.rect = MagicMock()
        draw.circle = MagicMock()
        draw.line = MagicMock()
        draw.lines = MagicMock()
        draw.polygon = MagicMock()
        draw.ellipse = MagicMock()
        draw.arc = MagicMock()
        return draw

    def _create_transform_mock(self):
        """変形関連のモックを作成"""
        transform = MagicMock()
        transform.rotate = MagicMock(return_value=self._create_surface_mock()())
        transform.scale = MagicMock(return_value=self._create_surface_mock()())
        transform.flip = MagicMock(return_value=self._create_surface_mock()())
        transform.rotozoom = MagicMock(return_value=self._create_surface_mock()())
        return transform

def install_pygame_mock():
    """Pygameモックを設定する"""
    # 既存のpygameモジュールを削除（既にインポートされている場合）
    if 'pygame' in sys.modules:
        del sys.modules['pygame']
    
    # モックを作成
    pygame_mock = PygameMock()
    
    # モックをシステムのモジュールとして登録
    sys.modules['pygame'] = pygame_mock
    
    return pygame_mock

if __name__ == "__main__":
    # モジュールが直接実行された場合、モックをインストール
    pygame_mock = install_pygame_mock()
    print("Pygameモックが正常にインストールされました。")
    
    # 動作確認
    import pygame
    print("Pygameモックのバージョンが正常に読み込まれました。") 