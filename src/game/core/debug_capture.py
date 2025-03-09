import os
import datetime
import time
import threading
import pyautogui
import cv2
import numpy as np
import pygame
import requests
import json
import base64
from collections import defaultdict

# NumPy型をJSONに変換するためのカスタムエンコーダ
class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyJSONEncoder, self).default(obj)

class EventManager:
    """スクリーンショットイベントを管理するクラス"""
    
    def __init__(self):
        # イベントタイプごとの最終発生時刻
        self.last_event_times = defaultdict(float)
        
        # イベントタイプごとのクールダウン時間（秒）
        self.cooldowns = {
            "auto": 5.0,        # 自動キャプチャ
            "firing": 1.0,      # 発射イベント
            "damaged": 1.5,     # ダメージイベント
            "manual": 0.0,      # 手動（F5キー）
            "player_enemy_interaction": 2.0,  # プレイヤーと敵の相互作用
            "default": 1.0      # その他
        }
        
        # イベント優先度（高いほど優先）
        self.priority = {
            "manual": 100,       # 手動は常に最優先
            "damaged": 80,       # ダメージは高優先
            "firing": 60,        # 発射は中優先
            "player_enemy_interaction": 40,
            "auto": 20,          # 自動キャプチャは低優先
            "default": 0
        }
        
        # 直近のイベント履歴（最大10件）
        self.recent_events = []
        self.max_history = 10
        
        # 同時発生イベントの処理用バッファ
        self.event_buffer = []
        self.buffer_process_time = 0.1  # バッファ処理間隔（秒）
        self.last_buffer_process = time.time()
    
    def can_trigger(self, event_type):
        """
        指定されたイベントタイプが発火可能かチェック
        
        Args:
            event_type (str): イベントタイプ
            
        Returns:
            bool: 発火可能ならTrue
        """
        now = time.time()
        cooldown = self.cooldowns.get(event_type, self.cooldowns["default"])
        last_time = self.last_event_times.get(event_type, 0)
        
        # クールダウン期間中ならFalse
        if now - last_time < cooldown:
            return False
            
        return True
    
    def register_event(self, event_type):
        """
        イベントを登録（バッファに追加）
        
        Args:
            event_type (str): イベントタイプ
            
        Returns:
            bool: イベント登録成功ならTrue
        """
        # バッファにイベントを追加
        self.event_buffer.append({
            "type": event_type,
            "time": time.time(),
            "priority": self.priority.get(event_type, 0)
        })
        
        # バッファ処理が必要かチェック
        now = time.time()
        if now - self.last_buffer_process >= self.buffer_process_time:
            return self.process_buffer()
            
        return False
    
    def process_buffer(self):
        """
        イベントバッファを処理
        
        Returns:
            tuple: (処理するイベントタイプ, 処理するかどうか)
        """
        if not self.event_buffer:
            return (None, False)
            
        # 現在時刻を更新
        now = time.time()
        self.last_buffer_process = now
        
        # 優先度でソート
        self.event_buffer.sort(key=lambda x: x["priority"], reverse=True)
        
        # 最優先イベントを取得
        top_event = self.event_buffer[0]
        event_type = top_event["type"]
        
        # クールダウンチェック
        if not self.can_trigger(event_type):
            self.event_buffer = []  # バッファをクリア
            return (None, False)
        
        # イベント発火時刻を更新
        self.last_event_times[event_type] = now
        
        # 履歴に追加
        self.recent_events.append({
            "type": event_type,
            "time": now
        })
        
        # 履歴が最大数を超えたら古いものを削除
        if len(self.recent_events) > self.max_history:
            self.recent_events.pop(0)
        
        # バッファをクリア
        self.event_buffer = []
        
        return (event_type, True)
    
    def get_event_stats(self):
        """
        イベント統計情報を取得
        
        Returns:
            dict: イベント統計情報
        """
        stats = {
            "total_events": len(self.recent_events),
            "last_events": self.recent_events[-3:] if self.recent_events else [],
            "cooldowns": {k: f"{v:.1f}秒" for k, v in self.cooldowns.items()}
        }
        return stats

class DebugWindow:
    """デバッグ情報を表示するウィンドウ"""
    
    def __init__(self, title="デバッグビューワー", size=(800, 600)):
        """
        初期化
        
        Args:
            title (str): ウィンドウタイトル
            size (tuple): ウィンドウサイズ
        """
        self.title = title
        self.size = size
        self.window = None
        self.running = False
        self.thread = None
        self.current_image = None
        self.current_image_path = None
        self.analysis_results = {}
        
    def start(self):
        """デバッグウィンドウを開始"""
        if self.thread and self.thread.is_alive():
            print("デバッグウィンドウはすでに実行中です")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_window)
        self.thread.daemon = True
        self.thread.start()
        print("デバッグウィンドウを開始しました")
        
    def stop(self):
        """デバッグウィンドウを停止"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        print("デバッグウィンドウを停止しました")
        
    def _run_window(self):
        """ウィンドウのメインループ"""
        cv2.namedWindow(self.title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.title, self.size[0], self.size[1])
        
        blank_image = np.zeros((self.size[1], self.size[0], 3), np.uint8)
        cv2.putText(blank_image, "画像がありません", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        while self.running:
            # 表示する画像がある場合
            if self.current_image is not None:
                display_img = self.current_image.copy()
                
                # 分析結果があれば表示
                if self.current_image_path in self.analysis_results:
                    result = self.analysis_results[self.current_image_path]
                    
                    # 明るさを表示
                    if "brightness" in result:
                        brightness_text = f"明るさ: {result['brightness']:.1f}"
                        cv2.putText(display_img, brightness_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # 検出されたオブジェクトを表示
                    if "objects_detected" in result:
                        y_pos = 60
                        for obj in result["objects_detected"]:
                            cv2.putText(display_img, obj, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            y_pos += 30
                    
                    # 文字化け情報を表示
                    if "text_garbling" in result and result["text_garbling"]["potential_garbled_areas"]:
                        garble_info = result["text_garbling"]
                        garbled_areas = garble_info["potential_garbled_areas"]
                        
                        y_pos = 60
                        cv2.putText(display_img, f"文字化け検出: {len(garbled_areas)}箇所", 
                                    (display_img.shape[1] - 300, y_pos), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        for i, area in enumerate(garbled_areas):
                            y_pos += 30
                            confidence = area["confidence"]
                            area_name = area["area_name"]
                            metrics = area["metrics"]
                            
                            text = f"{i+1}. {area_name} (確信度: {confidence:.2f})"
                            cv2.putText(display_img, text, 
                                        (display_img.shape[1] - 300, y_pos), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            
                            # 詳細メトリクスも表示
                            y_pos += 20
                            detail = f"   エッジ密度: {metrics['edge_density']:.3f}"
                            cv2.putText(display_img, detail, 
                                        (display_img.shape[1] - 290, y_pos), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 100, 255), 1)
                            
                            y_pos += 20
                            detail = f"   ノイズレベル: {metrics['noise_level']:.1f}"
                            cv2.putText(display_img, detail, 
                                        (display_img.shape[1] - 290, y_pos), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 100, 255), 1)
                    
                    # 推奨事項を表示
                    if "recommendations" in result:
                        y_pos = self.size[1] - 30
                        for rec in result["recommendations"]:
                            cv2.putText(display_img, rec, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            y_pos -= 25
                
                cv2.imshow(self.title, display_img)
            else:
                cv2.imshow(self.title, blank_image)
            
            # キー入力処理
            key = cv2.waitKey(100)
            if key == 27:  # ESCキー
                self.running = False
                break
        
        cv2.destroyWindow(self.title)
    
    def show_image(self, image_path, analysis_result=None):
        """
        画像を表示
        
        Args:
            image_path (str): 表示する画像のパス
            analysis_result (dict): 分析結果
        """
        if not os.path.exists(image_path):
            print(f"画像が見つかりません: {image_path}")
            return
            
        self.current_image = cv2.imread(image_path)
        self.current_image_path = image_path
        
        if analysis_result:
            self.analysis_results[image_path] = analysis_result
            
        print(f"デバッグウィンドウに画像を表示: {image_path}")

class ImgurUploader:
    """Imgurに画像をアップロードするためのクラス"""
    
    def __init__(self, client_id=None):
        """
        初期化
        
        Args:
            client_id (str): ImgurのClient ID（なければ環境変数から取得）
        """
        # Imgur API クライアントID
        self.client_id = client_id or os.environ.get("IMGUR_CLIENT_ID", "546c25a59c58ad7")  # デモ用
        self.api_url = "https://api.imgur.com/3/image"
        
        # アップロード履歴
        self.upload_history = []
        self.max_history = 10
    
    def upload_image(self, image_path, title=None, description=None):
        """
        画像をImgurにアップロード
        
        Args:
            image_path (str): アップロードする画像のパス
            title (str): 画像のタイトル
            description (str): 画像の説明
            
        Returns:
            dict: アップロード結果、失敗した場合はNone
        """
        if not os.path.exists(image_path):
            print(f"アップロードする画像が見つかりません: {image_path}")
            return None
        
        try:
            # 画像をBase64エンコード
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 送信データの準備
            payload = {
                'image': encoded_image,
                'type': 'base64'
            }
            
            if title:
                payload['title'] = title
            
            if description:
                payload['description'] = description
            
            # ヘッダーの準備
            headers = {
                'Authorization': f'Client-ID {self.client_id}'
            }
            
            # リクエスト送信
            response = requests.post(
                self.api_url,
                data=payload,
                headers=headers
            )
            
            # レスポンスの確認
            if response.status_code == 200:
                result = response.json()
                
                # アップロード情報を履歴に追加
                upload_info = {
                    'timestamp': datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                    'local_path': image_path,
                    'url': result['data']['link'],
                    'deletehash': result['data']['deletehash']
                }
                
                self.upload_history.append(upload_info)
                
                # 履歴が上限を超えたら古いものを削除
                if len(self.upload_history) > self.max_history:
                    self.upload_history.pop(0)
                
                print(f"画像をアップロードしました: {upload_info['url']}")
                return upload_info
            else:
                print(f"Imgurアップロードエラー: {response.status_code}, {response.text}")
                return None
        
        except Exception as e:
            print(f"画像アップロードエラー: {e}")
            return None
    
    def get_latest_upload(self):
        """最新のアップロード情報を取得"""
        if not self.upload_history:
            return None
        return self.upload_history[-1]

class ScreenshotAnalyzer:
    """ゲーム画面をキャプチャして解析するクラス"""
    
    def __init__(self, capture_dir="debug_captures"):
        """
        初期化
        
        Args:
            capture_dir (str): スクリーンショットを保存するディレクトリ
        """
        self.capture_dir = capture_dir
        os.makedirs(self.capture_dir, exist_ok=True)
        
        # 分析結果のキャッシュ
        self.analysis_results = {}
        
        # デバッグ情報
        self.debug_info = {
            "last_capture_time": None,
            "capture_count": 0,
            "analysis_results": []
        }
        
        # スクリーンショットキャプチャのインターバル (秒)
        self.capture_interval = 1.0
        
        # 自動キャプチャスレッド
        self.auto_capture_thread = None
        self.auto_capture_running = False
        
        # デバッグウィンドウ
        self.debug_window = DebugWindow()
        
        # イベント管理
        self.event_manager = EventManager()
        
        # 文字化け検出のための設定
        self.text_detection_enabled = True
        self.text_areas = [
            # ゲーム画面上の日本語テキストが表示される領域（x, y, width, height）
            {'name': 'タイトル', 'rect': (100, 50, 400, 100)},  # タイトル領域
            {'name': 'メッセージ', 'rect': (200, 400, 400, 100)},  # メッセージ領域
            {'name': 'UI', 'rect': (50, 500, 300, 100)}  # UI領域
        ]
        
        # API送信設定
        self.auto_upload_enabled = False  # デフォルトでは無効化
        self.api_config = {
            # デフォルトはダミーURL。実際のエンドポイントに変更してください
            "url": "https://api.example.com/analyze-screenshot",
            "auth_token": "",  # 認証トークン（必要な場合）
            "project_id": "aos_game",  # プロジェクト識別子
            "retry_count": 3,  # 再試行回数
            "timeout": 30  # タイムアウト（秒）
        }
        
        # 送信履歴
        self.upload_history = []
        self.max_upload_history = 10
        
        # Imgurアップローダ
        self.imgur_uploader = ImgurUploader()
        self.imgur_upload_enabled = False
    
    def capture_screenshot(self, event_type="default"):
        """
        スクリーンショットを撮影して保存
        
        Args:
            event_type (str): イベントタイプ（firing, damaged, enemyなど）
            
        Returns:
            str: 保存したファイルのパス、撮影しなかった場合はNone
        """
        # イベント管理を通してイベントをチェック
        if event_type != "auto":  # 自動キャプチャはスレッドで別管理
            event_type, should_capture = self.event_manager.process_buffer()
            if not should_capture:
                return None
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{event_type}_{timestamp}.png"
        path = os.path.join(self.capture_dir, filename)
        
        # スクリーンショット撮影
        try:
            # ゲームウィンドウの情報を取得（Pygameから）
            import pygame
            
            # 現在アクティブなPygameウィンドウを取得
            if pygame.display.get_init():
                # ゲームウィンドウの位置とサイズを取得
                try:
                    # Windowsの場合
                    import win32gui
                    hwnd = pygame.display.get_wm_info()["window"]
                    rect = win32gui.GetWindowRect(hwnd)
                    x, y, width, height = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
                    
                    # ゲームウィンドウ領域だけをキャプチャ
                    screenshot = pyautogui.screenshot(region=(x, y, width, height))
                    print(f"ゲームウィンドウをキャプチャしました: {x}, {y}, {width}x{height}")
                except (ImportError, KeyError, Exception) as e:
                    print(f"ウィンドウ情報取得エラー: {e}、画面全体をキャプチャします")
                    # エラーの場合は画面全体をキャプチャ
                    screenshot = pyautogui.screenshot()
            else:
                # Pygameが初期化されていない場合は画面全体をキャプチャ
                screenshot = pyautogui.screenshot()
                print("Pygameが初期化されていないため、画面全体をキャプチャします")
            
            screenshot.save(path)
            
            # デバッグ情報を更新
            self.debug_info["last_capture_time"] = timestamp
            self.debug_info["capture_count"] += 1
            
            print(f"スクリーンショットを保存しました: {path}")
            return path
        except Exception as e:
            print(f"スクリーンショット撮影エラー: {e}")
            return None
    
    def request_screenshot(self, event_type="default"):
        """
        スクリーンショットの撮影をリクエスト（イベント登録）
        
        Args:
            event_type (str): イベントタイプ
            
        Returns:
            bool: リクエスト成功ならTrue
        """
        return self.event_manager.register_event(event_type)
    
    def detect_text_garbling(self, img):
        """
        日本語の文字化けを検出
        
        Args:
            img: 画像データ (OpenCVフォーマット)
            
        Returns:
            dict: 文字化け検出結果
        """
        result = {
            "potential_garbled_areas": [],
            "recommendations": []
        }
        
        # 画像の色分析による簡易検出
        # 文字化けは通常、特定の色パターンを持つことが多い
        for area in self.text_areas:
            # 領域を抽出
            x, y, w, h = area['rect']
            if x >= img.shape[1] or y >= img.shape[0]:
                continue
                
            # 領域がはみ出さないように調整
            w = min(w, img.shape[1] - x)
            h = min(h, img.shape[0] - y)
            
            if w <= 0 or h <= 0:
                continue
                
            roi = img[y:y+h, x:x+w]
            
            # 色の分散を計算（文字化けは通常、色のノイズが多い）
            color_variance = np.var(roi, axis=(0, 1))
            average_variance = np.mean(color_variance)
            
            # エッジ検出（文字化けは通常、鋭いエッジが多い）
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.count_nonzero(edges) / (w * h)
            
            # ノイズ分析
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            noise_level = np.mean(np.abs(gray.astype(np.float32) - blur.astype(np.float32)))
            
            # ヒューリスティックな判定
            is_garbled = False
            confidence = 0.0
            
            if edge_density > 0.1 and noise_level > 5.0 and average_variance > 100:
                is_garbled = True
                confidence = min(1.0, (edge_density * 5 + noise_level / 10 + average_variance / 1000) / 3)
            
            if is_garbled:
                result["potential_garbled_areas"].append({
                    "area_name": area['name'],
                    "rect": area['rect'],
                    "confidence": confidence,
                    "metrics": {
                        "edge_density": edge_density,
                        "noise_level": noise_level,
                        "color_variance": average_variance
                    }
                })
                
                if confidence > 0.6:
                    result["recommendations"].append(f"{area['name']}領域に文字化けの可能性があります（確信度: {confidence:.1f}）")
        
        return result
    
    def upload_screenshot(self, image_path, analysis_result=None):
        """
        スクリーンショットをAPIサーバーに送信
        
        Args:
            image_path (str): 送信する画像のパス
            analysis_result (dict): ローカル分析結果（添付する場合）
            
        Returns:
            dict: API応答、失敗した場合はNone
        """
        if not self.auto_upload_enabled:
            return None
            
        if not os.path.exists(image_path):
            print(f"送信する画像が見つかりません: {image_path}")
            return None
            
        # ファイル名から情報を抽出
        filename = os.path.basename(image_path)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 画像をBase64エンコード
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            # 送信データの準備
            payload = {
                "project_id": self.api_config["project_id"],
                "timestamp": timestamp,
                "filename": filename,
                "image": encoded_image,
                "request_type": "screenshot_analysis"
            }
            
            # ローカル分析結果がある場合は追加
            if analysis_result:
                # NumPyの配列や特殊な型をJSON化可能にする前処理
                sanitized_result = {}
                for key, value in analysis_result.items():
                    # NumPy配列はリストに変換
                    if isinstance(value, np.ndarray):
                        sanitized_result[key] = value.tolist()
                    # float32などのNumPy型はPythonのネイティブ型に変換
                    elif isinstance(value, (np.integer, np.floating)):
                        sanitized_result[key] = float(value) if isinstance(value, np.floating) else int(value)
                    # 辞書の場合は再帰的に処理
                    elif isinstance(value, dict):
                        sanitized_result[key] = self._sanitize_for_json(value)
                    # リストの場合も再帰的に処理
                    elif isinstance(value, list):
                        sanitized_result[key] = [
                            self._sanitize_for_json(item) if isinstance(item, (dict, list)) else 
                            item.tolist() if isinstance(item, np.ndarray) else
                            float(item) if isinstance(item, np.floating) else
                            int(item) if isinstance(item, np.integer) else
                            item
                            for item in value
                        ]
                    else:
                        sanitized_result[key] = value
                
                payload["local_analysis"] = sanitized_result
                
            # ヘッダーの準備
            headers = {
                "Content-Type": "application/json"
            }
            
            # 認証トークンがある場合は追加
            if self.api_config["auth_token"]:
                headers["Authorization"] = f"Bearer {self.api_config['auth_token']}"
                
            # リクエスト送信 (カスタムJSONエンコーダを使用)
            for attempt in range(self.api_config["retry_count"]):
                try:
                    response = requests.post(
                        self.api_config["url"],
                        data=json.dumps(payload, cls=NumpyJSONEncoder),
                        headers=headers,
                        timeout=self.api_config["timeout"]
                    )
                    
                    # レスポンスの確認
                    if response.status_code == 200:
                        result = response.json()
                        print(f"スクリーンショットの送信に成功しました: {filename}")
                        
                        # 送信履歴に追加
                        history_entry = {
                            "timestamp": timestamp,
                            "filename": filename,
                            "status": "success",
                            "response": result
                        }
                        self.upload_history.append(history_entry)
                        
                        # 履歴が上限を超えたら古いものを削除
                        if len(self.upload_history) > self.max_upload_history:
                            self.upload_history.pop(0)
                            
                        return result
                    else:
                        print(f"APIエラー (試行 {attempt+1}/{self.api_config['retry_count']}): {response.status_code}, {response.text}")
                        time.sleep(1)  # 再試行前に少し待機
                
                except requests.exceptions.RequestException as e:
                    print(f"リクエスト例外 (試行 {attempt+1}/{self.api_config['retry_count']}): {e}")
                    if attempt < self.api_config["retry_count"] - 1:
                        time.sleep(1)  # 再試行前に少し待機
            
            # すべての試行が失敗
            print(f"スクリーンショットの送信に失敗しました（{self.api_config['retry_count']}回試行）: {filename}")
            
            # 送信履歴に失敗を記録
            history_entry = {
                "timestamp": timestamp,
                "filename": filename,
                "status": "failed",
                "error": "Maximum retry attempts reached"
            }
            self.upload_history.append(history_entry)
            
            return None
        
        except Exception as e:
            print(f"スクリーンショット送信エラー: {e}")
            
            # 送信履歴に失敗を記録
            history_entry = {
                "timestamp": timestamp,
                "filename": filename,
                "status": "error",
                "error": str(e)
            }
            self.upload_history.append(history_entry)
            
            return None
    
    def _sanitize_for_json(self, obj):
        """
        オブジェクトをJSON化可能な形に変換（再帰処理用）
        """
        if isinstance(obj, (np.integer, np.floating)):
            return int(obj) if isinstance(obj, np.integer) else float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        else:
            return obj
    
    def analyze_screenshot(self, image_path):
        """
        スクリーンショットを分析
        
        Args:
            image_path (str): 分析する画像のパス
            
        Returns:
            dict: 分析結果
        """
        if image_path is None:
            return None
            
        # OpenCVで画像を読み込む
        img = cv2.imread(image_path)
        if img is None:
            print(f"画像の読み込みに失敗しました: {image_path}")
            return {"error": "画像読み込み失敗"}
        
        # 分析結果
        result = {
            "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
            "path": image_path,
            "objects_detected": [],
            "recommendations": []
        }
        
        # 既存の分析コード...
        # 簡単な例: 明るさの分析
        brightness = np.mean(img)
        result["brightness"] = brightness
        
        if brightness < 50:
            result["recommendations"].append("画面が暗すぎる可能性があります。明るさを調整してください。")
        
        # HSV色空間に変換して色分析
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 特定の色範囲を検出（例: 赤色の弾）
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        red_pixels = cv2.countNonZero(red_mask)
        
        result["red_pixels"] = red_pixels
        if red_pixels > 1000:
            result["objects_detected"].append("赤色の弾/オブジェクトを検出")
        
        # 青色範囲の検出（例: プレイヤー）
        lower_blue = np.array([100, 100, 100])
        upper_blue = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        blue_pixels = cv2.countNonZero(blue_mask)
        
        result["blue_pixels"] = blue_pixels
        if blue_pixels > 500:
            result["objects_detected"].append("青色のプレイヤー/オブジェクトを検出")
        
        # 緑色範囲の検出（例: 敵）
        lower_green = np.array([40, 100, 100])
        upper_green = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixels = cv2.countNonZero(green_mask)
        
        result["green_pixels"] = green_pixels
        if green_pixels > 500:
            result["objects_detected"].append("緑色の敵/オブジェクトを検出")
        
        # 文字化け検出
        if self.text_detection_enabled:
            garbling_result = self.detect_text_garbling(img)
            result["text_garbling"] = garbling_result
            
            # ガーブリング結果に基づく推奨事項を追加
            if garbling_result["recommendations"]:
                result["recommendations"].extend(garbling_result["recommendations"])
                
                # 文字化けが検出された場合は画像にマーキング
                marked_img = img.copy()
                for area in garbling_result["potential_garbled_areas"]:
                    x, y, w, h = area["rect"]
                    # 赤い枠で囲む
                    cv2.rectangle(marked_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    # ラベルを追加
                    confidence = area["confidence"]
                    label = f"{area['area_name']} ({confidence:.1f})"
                    cv2.putText(marked_img, label, (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
                # 文字化けマーキング画像を保存
                marked_path = os.path.join(self.capture_dir, 
                                        f"garbled_marked_{os.path.basename(image_path)}")
                cv2.imwrite(marked_path, marked_img)
                result["marked_image_path"] = marked_path
        
        # キャッシュに保存
        self.analysis_results[image_path] = result
        
        # デバッグ情報に追加
        summary_parts = [f"明るさ: {brightness:.1f}"]
        
        if "red_pixels" in result:
            summary_parts.append(f"赤: {red_pixels}")
        
        if "blue_pixels" in result:
            summary_parts.append(f"青: {blue_pixels}")
            
        if "green_pixels" in result:
            summary_parts.append(f"緑: {green_pixels}")
            
        if "text_garbling" in result and result["text_garbling"]["potential_garbled_areas"]:
            garbled_count = len(result["text_garbling"]["potential_garbled_areas"])
            summary_parts.append(f"文字化け: {garbled_count}箇所")
        
        self.debug_info["analysis_results"].append({
            "path": image_path,
            "timestamp": result["timestamp"],
            "summary": ", ".join(summary_parts)
        })
        
        # デバッグウィンドウが動作中なら画像を表示
        if hasattr(self, 'debug_window') and self.debug_window.running:
            # 文字化けマーキング画像がある場合はそちらを表示
            display_path = result.get("marked_image_path", image_path)
            self.debug_window.show_image(display_path, result)
        
        # Imgurへのアップロードが有効ならアップロード
        if self.imgur_upload_enabled:
            threading.Thread(
                target=self.upload_to_imgur,
                args=(image_path, result),
                daemon=True
            ).start()
        
        # 自動アップロードが有効ならAPIに送信
        if self.auto_upload_enabled:
            threading.Thread(
                target=self.upload_screenshot,
                args=(image_path, result),
                daemon=True
            ).start()
        
        return result
    
    def start_auto_capture(self, interval=1.0):
        """
        自動キャプチャを開始
        
        Args:
            interval (float): キャプチャ間隔（秒）
        """
        if self.auto_capture_thread and self.auto_capture_thread.is_alive():
            print("すでに自動キャプチャが実行中です")
            return
        
        # イベント管理のクールダウンを更新
        self.event_manager.cooldowns["auto"] = interval
        
        # キャプチャ間隔を設定
        self.capture_interval = interval
        self.auto_capture_running = True
        self.auto_capture_thread = threading.Thread(target=self._auto_capture_loop)
        self.auto_capture_thread.daemon = True
        self.auto_capture_thread.start()
        print(f"自動キャプチャを開始しました（間隔: {interval}秒）")
        
        # デバッグウィンドウを開始
        if hasattr(self, 'debug_window'):
            self.debug_window.start()
    
    def stop_auto_capture(self):
        """自動キャプチャを停止"""
        self.auto_capture_running = False
        if self.auto_capture_thread:
            self.auto_capture_thread.join(timeout=2.0)
        print("自動キャプチャを停止しました")
        
        # デバッグウィンドウを停止
        if hasattr(self, 'debug_window'):
            self.debug_window.stop()
    
    def _auto_capture_loop(self):
        """自動キャプチャのメインループ"""
        while self.auto_capture_running:
            # 自動キャプチャのクールダウンをチェック
            if self.event_manager.can_trigger("auto"):
                # クールダウン時間を更新
                self.event_manager.last_event_times["auto"] = time.time()
                
                # スクリーンショット撮影
                path = self.capture_screenshot("auto")
                if path:
                    self.analyze_screenshot(path)
            
            # 短い間隔で待機（CPU負荷軽減）
            time.sleep(0.1)

    def set_api_config(self, config):
        """
        API設定を更新
        
        Args:
            config (dict): API設定（URL、認証トークンなど）
        """
        if not isinstance(config, dict):
            return False
            
        # 設定を更新
        for key, value in config.items():
            if key in self.api_config:
                self.api_config[key] = value
                
        return True
    
    def toggle_auto_upload(self, enabled=None):
        """
        自動アップロードの有効/無効を切り替え
        
        Args:
            enabled (bool): 有効にするならTrue、無効にするならFalse、Noneなら現在の設定を反転
        """
        if enabled is None:
            self.auto_upload_enabled = not self.auto_upload_enabled
        else:
            self.auto_upload_enabled = bool(enabled)
            
        print(f"自動アップロード: {'有効' if self.auto_upload_enabled else '無効'}")
        return self.auto_upload_enabled
    
    def get_upload_stats(self):
        """
        アップロード統計情報を取得
        
        Returns:
            dict: アップロード統計情報
        """
        success_count = sum(1 for entry in self.upload_history if entry["status"] == "success")
        failed_count = sum(1 for entry in self.upload_history if entry["status"] != "success")
        
        stats = {
            "enabled": self.auto_upload_enabled,
            "total_uploads": len(self.upload_history),
            "success_count": success_count,
            "failed_count": failed_count,
            "api_url": self.api_config["url"],
            "recent_uploads": self.upload_history[-3:] if self.upload_history else []
        }
        return stats
    
    def toggle_imgur_upload(self, enabled=None):
        """
        Imgurへの自動アップロードの有効/無効を切り替え
        
        Args:
            enabled (bool): 有効にするならTrue、無効にするならFalse、Noneなら現在の設定を反転
        """
        if enabled is None:
            self.imgur_upload_enabled = not self.imgur_upload_enabled
        else:
            self.imgur_upload_enabled = bool(enabled)
            
        print(f"Imgurへの自動アップロード: {'有効' if self.imgur_upload_enabled else '無効'}")
        return self.imgur_upload_enabled
    
    def upload_to_imgur(self, image_path, analysis_result=None):
        """
        スクリーンショットをImgurにアップロード
        
        Args:
            image_path (str): アップロードする画像のパス
            analysis_result (dict): 分析結果
        
        Returns:
            dict: アップロード結果
        """
        if not self.imgur_upload_enabled:
            return None
            
        # タイトルと説明を準備
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"ゲームスクリーンショット（{timestamp}）"
        
        description = "ゲームのデバッグキャプチャ\n"
        if analysis_result:
            # 分析結果があれば追加
            if "objects_detected" in analysis_result and analysis_result["objects_detected"]:
                description += "\n検出オブジェクト:\n"
                for obj in analysis_result["objects_detected"]:
                    description += f"- {obj}\n"
            
            if "text_garbling" in analysis_result and analysis_result["text_garbling"].get("potential_garbled_areas"):
                description += "\n文字化け検出:\n"
                for area in analysis_result["text_garbling"]["potential_garbled_areas"]:
                    description += f"- {area['area_name']} (確信度: {area['confidence']:.2f})\n"
        
        # Imgurにアップロード
        return self.imgur_uploader.upload_image(image_path, title, description)
    
    def draw_debug_overlay(self, screen):
        """
        デバッグオーバーレイを描画
        
        Args:
            screen: pygame画面オブジェクト
        """
        if not pygame.font.get_init():
            return
        
        try:
            # 日本語フォントをロード
            font = pygame.font.Font("C:/Windows/Fonts/meiryo.ttc", 24)
        except:
            # フォールバック: 日本語フォントが見つからない場合はSystemフォントを使用
            font = pygame.font.SysFont(None, 24)
        
        # デバッグ情報を表示
        debug_text = [
            f"キャプチャ数: {self.debug_info['capture_count']}",
            f"最終キャプチャ: {self.debug_info['last_capture_time'] or 'なし'}"
        ]
        
        # Imgurアップロード情報を表示
        if self.imgur_upload_enabled:
            latest_upload = self.imgur_uploader.get_latest_upload()
            if latest_upload:
                debug_text.append(f"Imgurアップロード: {latest_upload['url']}")
            else:
                debug_text.append("Imgurアップロード: 準備完了")
        
        # API送信情報を表示
        if self.auto_upload_enabled:
            upload_stats = self.get_upload_stats()
            debug_text.append(f"API送信: 有効 ({upload_stats['success_count']}/{upload_stats['total_uploads']}成功)")
            
            # 最新の送信情報があれば表示
            if upload_stats["recent_uploads"]:
                latest = upload_stats["recent_uploads"][-1]
                debug_text.append(f"最新送信: {latest['status']} ({latest['filename']})")
        else:
            debug_text.append("API送信: 無効")
        
        # イベント管理の統計情報
        event_stats = self.event_manager.get_event_stats()
        if event_stats["last_events"]:
            last_event = event_stats["last_events"][-1]
            elapsed = time.time() - last_event["time"]
            debug_text.append(f"最新イベント: {last_event['type']} ({elapsed:.1f}秒前)")
        
        # 最新の分析結果があれば表示
        if self.debug_info["analysis_results"]:
            latest = self.debug_info["analysis_results"][-1]
            debug_text.append(f"最新分析: {latest['summary']}")
        
        # キー操作ガイドを追加
        debug_text.append("")
        debug_text.append("F5: スクリーンショット撮影")
        debug_text.append("F12: デバッグモード切替")
        
        # テキストをレンダリング
        y_pos = 10
        for text in debug_text:
            text_surface = font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.topleft = (10, y_pos)
            
            # 背景を描画
            bg_rect = text_rect.copy()
            bg_rect.width += 10
            bg_rect.height += 6
            bg_rect.topleft = (text_rect.left - 5, text_rect.top - 3)
            pygame.draw.rect(screen, (0, 0, 0, 128), bg_rect)
            
            # テキストを描画
            screen.blit(text_surface, text_rect)
            y_pos += 30 