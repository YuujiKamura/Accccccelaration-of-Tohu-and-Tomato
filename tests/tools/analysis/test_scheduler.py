"""
テスト実行スケジューラ

このモジュールはテストを定期的に実行し、結果を保存するための機能を提供します。
"""

import os
import sys
import time
import json
import datetime
import subprocess
import logging
import argparse
import schedule
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("test_scheduler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_scheduler")

class TestScheduler:
    """テスト実行のスケジューリングを行うクラス"""
    
    def __init__(self, config_file="scheduler_config.json"):
        """
        初期化
        
        Args:
            config_file: 設定ファイル名
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.test_history = []
        
        # 履歴ファイル
        self.history_file = self.config.get("history_file", "scheduler_history.json")
        
        # 履歴を読み込む
        self._load_history()
    
    def _load_config(self):
        """設定を読み込む"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
                # デフォルト設定を返す
                return self._get_default_config()
        else:
            # デフォルト設定
            config = self._get_default_config()
            
            # 設定を保存
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                logger.info(f"デフォルト設定を保存しました: {self.config_file}")
            except Exception as e:
                logger.error(f"設定ファイルの保存に失敗しました: {e}")
            
            return config
    
    def _get_default_config(self):
        """デフォルト設定を取得"""
        return {
            "schedules": [
                {
                    "name": "日次テスト",
                    "schedule": "daily",
                    "time": "02:00",
                    "command": "python run_tests.py --analyze --report",
                    "enabled": True
                },
                {
                    "name": "週次パフォーマンステスト",
                    "schedule": "weekly",
                    "day": "monday",
                    "time": "03:00",
                    "command": "python run_tests.py --analyze --report --filter performance",
                    "enabled": True
                }
            ],
            "notification": {
                "enabled": False,
                "email": "",
                "slack_webhook": ""
            },
            "history_file": "scheduler_history.json",
            "report_dir": "test_reports"
        }
    
    def _load_history(self):
        """履歴を読み込む"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.test_history = json.load(f)
            except Exception as e:
                logger.error(f"履歴ファイルの読み込みに失敗しました: {e}")
                self.test_history = []
        else:
            self.test_history = []
    
    def _save_history(self):
        """履歴を保存する"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_history, f, indent=2)
        except Exception as e:
            logger.error(f"履歴ファイルの保存に失敗しました: {e}")
    
    def run_test(self, name, command):
        """
        テストを実行する
        
        Args:
            name: テスト名
            command: 実行コマンド
        """
        logger.info(f"テスト実行: {name}")
        logger.info(f"コマンド: {command}")
        
        start_time = time.time()
        
        try:
            # レポートディレクトリを作成
            report_dir = self.config.get("report_dir", "test_reports")
            os.makedirs(report_dir, exist_ok=True)
            
            # 現在時刻
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # ログファイル
            log_file = os.path.join(report_dir, f"{name.lower().replace(' ', '_')}_{timestamp}.log")
            
            # コマンドを実行
            with open(log_file, 'w', encoding='utf-8') as f:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # リアルタイムでログを出力
                for line in process.stdout:
                    f.write(line)
                    logger.info(line.strip())
                
                return_code = process.wait()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 履歴に追加
            self.test_history.append({
                "name": name,
                "command": command,
                "timestamp": timestamp,
                "duration": duration,
                "return_code": return_code,
                "log_file": log_file,
                "success": return_code == 0
            })
            
            # 履歴を保存
            self._save_history()
            
            # 終了メッセージ
            if return_code == 0:
                logger.info(f"テスト成功: {name} (所要時間: {duration:.2f}秒)")
            else:
                logger.error(f"テスト失敗: {name} (所要時間: {duration:.2f}秒, 終了コード: {return_code})")
            
            # 通知
            self._send_notification(name, return_code == 0, duration, log_file)
            
        except Exception as e:
            logger.error(f"テスト実行中にエラーが発生しました: {e}")
            
            # 履歴に追加
            self.test_history.append({
                "name": name,
                "command": command,
                "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                "duration": time.time() - start_time,
                "return_code": -1,
                "error": str(e),
                "success": False
            })
            
            # 履歴を保存
            self._save_history()
            
            # 通知
            self._send_notification(name, False, time.time() - start_time, None, str(e))
    
    def _send_notification(self, name, success, duration, log_file, error=None):
        """
        通知を送信する
        
        Args:
            name: テスト名
            success: 成功したかどうか
            duration: 所要時間
            log_file: ログファイル
            error: エラーメッセージ
        """
        notification = self.config.get("notification", {})
        if not notification.get("enabled", False):
            return
        
        # ここに通知ロジックを実装
        # 例: Slack, Eメールなど
        pass
    
    def setup_schedules(self):
        """スケジュールを設定する"""
        schedules = self.config.get("schedules", [])
        
        for schedule_config in schedules:
            if not schedule_config.get("enabled", True):
                continue
            
            name = schedule_config.get("name", "名称なし")
            schedule_type = schedule_config.get("schedule")
            command = schedule_config.get("command")
            
            if not command:
                logger.warning(f"コマンドが指定されていないため、スキップします: {name}")
                continue
            
            # スケジュールのタイプに応じて設定
            if schedule_type == "daily":
                time_str = schedule_config.get("time", "00:00")
                logger.info(f"日次スケジュール設定: {name} @ {time_str}")
                schedule.every().day.at(time_str).do(self.run_test, name=name, command=command)
                
            elif schedule_type == "weekly":
                day = schedule_config.get("day", "monday").lower()
                time_str = schedule_config.get("time", "00:00")
                logger.info(f"週次スケジュール設定: {name} @ {day} {time_str}")
                
                if day == "monday":
                    schedule.every().monday.at(time_str).do(self.run_test, name=name, command=command)
                elif day == "tuesday":
                    schedule.every().tuesday.at(time_str).do(self.run_test, name=name, command=command)
                elif day == "wednesday":
                    schedule.every().wednesday.at(time_str).do(self.run_test, name=name, command=command)
                elif day == "thursday":
                    schedule.every().thursday.at(time_str).do(self.run_test, name=name, command=command)
                elif day == "friday":
                    schedule.every().friday.at(time_str).do(self.run_test, name=name, command=command)
                elif day == "saturday":
                    schedule.every().saturday.at(time_str).do(self.run_test, name=name, command=command)
                elif day == "sunday":
                    schedule.every().sunday.at(time_str).do(self.run_test, name=name, command=command)
                
            elif schedule_type == "hourly":
                minutes = schedule_config.get("minutes", 0)
                logger.info(f"時間ごとスケジュール設定: {name} (毎時 {minutes} 分)")
                schedule.every().hour.at(f":{minutes:02d}").do(self.run_test, name=name, command=command)
                
            elif schedule_type == "interval":
                hours = schedule_config.get("hours", 0)
                minutes = schedule_config.get("minutes", 0)
                seconds = schedule_config.get("seconds", 0)
                total_seconds = hours * 3600 + minutes * 60 + seconds
                
                if total_seconds <= 0:
                    logger.warning(f"間隔が0以下のため、スキップします: {name}")
                    continue
                
                logger.info(f"間隔スケジュール設定: {name} (間隔: {hours}時間 {minutes}分 {seconds}秒)")
                schedule.every(total_seconds).seconds.do(self.run_test, name=name, command=command)
            
            else:
                logger.warning(f"不明なスケジュールタイプ: {schedule_type} ({name})")
    
    def run_once(self, name=None):
        """
        すべての有効なテストを一度だけ実行する
        
        Args:
            name: 特定のテスト名（Noneの場合はすべて）
        """
        schedules = self.config.get("schedules", [])
        
        for schedule_config in schedules:
            if not schedule_config.get("enabled", True):
                continue
            
            schedule_name = schedule_config.get("name", "名称なし")
            
            if name and name != schedule_name:
                continue
            
            command = schedule_config.get("command")
            if command:
                self.run_test(schedule_name, command)
    
    def start(self):
        """スケジューラを開始する"""
        self.setup_schedules()
        
        logger.info("スケジューラを開始しました")
        logger.info("Ctrl+Cで終了してください")
        
        try:
            while True:
                # スケジュールを実行
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("スケジューラを終了します")
    
    def list_schedules(self):
        """スケジュールを一覧表示する"""
        schedules = self.config.get("schedules", [])
        
        print("\n===== スケジュール一覧 =====")
        for i, schedule_config in enumerate(schedules, 1):
            name = schedule_config.get("name", "名称なし")
            schedule_type = schedule_config.get("schedule", "不明")
            enabled = "有効" if schedule_config.get("enabled", True) else "無効"
            command = schedule_config.get("command", "")
            
            # スケジュール詳細
            details = ""
            if schedule_type == "daily":
                time_str = schedule_config.get("time", "00:00")
                details = f"毎日 {time_str}"
            elif schedule_type == "weekly":
                day = schedule_config.get("day", "monday")
                time_str = schedule_config.get("time", "00:00")
                day_ja = {
                    "monday": "月曜日",
                    "tuesday": "火曜日",
                    "wednesday": "水曜日",
                    "thursday": "木曜日",
                    "friday": "金曜日",
                    "saturday": "土曜日",
                    "sunday": "日曜日"
                }.get(day.lower(), day)
                details = f"毎週 {day_ja} {time_str}"
            elif schedule_type == "hourly":
                minutes = schedule_config.get("minutes", 0)
                details = f"毎時 {minutes} 分"
            elif schedule_type == "interval":
                hours = schedule_config.get("hours", 0)
                minutes = schedule_config.get("minutes", 0)
                seconds = schedule_config.get("seconds", 0)
                details = f"間隔: {hours}時間 {minutes}分 {seconds}秒"
            
            print(f"{i}. {name} ({enabled})")
            print(f"   スケジュール: {details}")
            print(f"   コマンド: {command}")
            print()
    
    def list_history(self, limit=10):
        """
        実行履歴を一覧表示する
        
        Args:
            limit: 表示する件数
        """
        if not self.test_history:
            print("実行履歴がありません")
            return
        
        # 最新順にソート
        sorted_history = sorted(self.test_history, key=lambda x: x.get("timestamp", ""), reverse=True)
        
        print(f"\n===== 実行履歴 (最新{min(limit, len(sorted_history))}件) =====")
        for i, history in enumerate(sorted_history[:limit], 1):
            name = history.get("name", "名称なし")
            timestamp = history.get("timestamp", "")
            duration = history.get("duration", 0)
            success = "成功" if history.get("success", False) else "失敗"
            return_code = history.get("return_code", -1)
            
            # タイムスタンプをフォーマット
            formatted_timestamp = timestamp
            if len(timestamp) == 15:  # YYYYMMdd_HHMMSS
                try:
                    dt = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            
            print(f"{i}. {name} ({success})")
            print(f"   実行日時: {formatted_timestamp}")
            print(f"   所要時間: {duration:.2f}秒")
            print(f"   終了コード: {return_code}")
            
            if not history.get("success", False):
                error = history.get("error", "")
                if error:
                    print(f"   エラー: {error}")
            
            log_file = history.get("log_file", "")
            if log_file and os.path.exists(log_file):
                print(f"   ログファイル: {log_file}")
            
            print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='テスト実行スケジューラ')
    parser.add_argument('--run', action='store_true', help='スケジューラを開始')
    parser.add_argument('--run-once', action='store_true', help='すべてのテストを一度だけ実行')
    parser.add_argument('--list', action='store_true', help='スケジュール一覧を表示')
    parser.add_argument('--history', action='store_true', help='実行履歴を表示')
    parser.add_argument('--name', type=str, help='特定のテスト名を指定')
    parser.add_argument('--config', type=str, default='scheduler_config.json', help='設定ファイル名')
    
    args = parser.parse_args()
    
    # スケジューラを初期化
    scheduler = TestScheduler(args.config)
    
    if args.run:
        # スケジューラを開始
        scheduler.start()
    elif args.run_once:
        # すべてのテストを一度だけ実行
        scheduler.run_once(args.name)
    elif args.list:
        # スケジュール一覧を表示
        scheduler.list_schedules()
    elif args.history:
        # 実行履歴を表示
        scheduler.list_history()
    else:
        # 引数がない場合はヘルプを表示
        parser.print_help() 