"""
パフォーマンス変化の自動検出モジュール

このモジュールはテスト実行中のパフォーマンスデータを収集し、
異常な変化を検出するための機能を提供します。
"""

import os
import json
import time
import statistics
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import base64
from io import BytesIO
from collections import defaultdict

class PerformanceMetric:
    """パフォーマンス指標を表すクラス"""
    
    def __init__(self, name, value, unit="ms", context=None, timestamp=None):
        """
        初期化
        
        Args:
            name: 指標の名前
            value: 指標の値
            unit: 単位（ms, fps, MB, etc.）
            context: コンテキスト情報（任意のdict）
            timestamp: タイムスタンプ（Noneの場合は現在時刻）
        """
        self.name = name
        self.value = value
        self.unit = unit
        self.context = context or {}
        self.timestamp = timestamp or time.time()
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'context': self.context,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data):
        """辞書からインスタンスを作成"""
        return cls(
            name=data['name'],
            value=data['value'],
            unit=data['unit'],
            context=data['context'],
            timestamp=data['timestamp']
        )


class PerformanceAnalyzer:
    """パフォーマンス分析を行うクラス"""
    
    def __init__(self, data_dir="performance_data"):
        """
        初期化
        
        Args:
            data_dir: パフォーマンスデータを保存するディレクトリ
        """
        self.data_dir = data_dir
        self.metrics = []
        self.baseline = {}
        self.alerts = []
        
        # ディレクトリがなければ作成
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 履歴データを読み込む
        self._load_history()
    
    def record_metric(self, name, value, unit="ms", context=None):
        """
        パフォーマンス指標を記録
        
        Args:
            name: 指標の名前
            value: 指標の値
            unit: 単位（ms, fps, MB, etc.）
            context: コンテキスト情報（任意のdict）
            
        Returns:
            PerformanceMetric: 記録した指標
        """
        metric = PerformanceMetric(name, value, unit, context)
        self.metrics.append(metric)
        return metric
    
    def record_execution_time(self, name, func, *args, **kwargs):
        """
        関数の実行時間を記録
        
        Args:
            name: 指標の名前
            func: 測定する関数
            *args, **kwargs: 関数に渡す引数
            
        Returns:
            関数の戻り値
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # ミリ秒単位
        self.record_metric(name, execution_time, "ms", {
            'function': func.__name__,
            'args_count': len(args),
            'kwargs_count': len(kwargs)
        })
        
        return result
    
    def analyze(self, save=True):
        """
        記録された指標を分析
        
        Args:
            save: データを保存するかどうか
            
        Returns:
            dict: 分析結果
        """
        if not self.metrics:
            return {'metrics': [], 'alerts': [], 'baseline': self.baseline}
        
        # 指標ごとの統計を計算
        stats = defaultdict(lambda: {'values': [], 'avg': 0, 'median': 0, 'stddev': 0, 'min': 0, 'max': 0})
        
        for metric in self.metrics:
            stats[metric.name]['values'].append(metric.value)
        
        for name, data in stats.items():
            values = data['values']
            if values:
                data['avg'] = statistics.mean(values)
                data['median'] = statistics.median(values)
                data['stddev'] = statistics.stdev(values) if len(values) > 1 else 0
                data['min'] = min(values)
                data['max'] = max(values)
        
        # 異常検出
        self.alerts = []
        for name, data in stats.items():
            if name in self.baseline:
                baseline = self.baseline[name]
                current_avg = data['avg']
                
                # 前回のベースラインと比較
                percent_change = ((current_avg - baseline['avg']) / baseline['avg']) * 100
                
                # 20%以上の変化がある場合はアラート
                if abs(percent_change) >= 20:
                    alert = {
                        'metric': name,
                        'current_avg': current_avg,
                        'baseline_avg': baseline['avg'],
                        'percent_change': percent_change,
                        'is_regression': percent_change > 0,  # 値が増加＝パフォーマンス低下
                        'timestamp': time.time()
                    }
                    self.alerts.append(alert)
        
        # ベースラインを更新
        self.baseline = {name: {
            'avg': data['avg'],
            'median': data['median'],
            'stddev': data['stddev'],
            'timestamp': time.time()
        } for name, data in stats.items()}
        
        # 分析結果
        analysis = {
            'metrics': [metric.to_dict() for metric in self.metrics],
            'stats': {name: {k: v for k, v in data.items() if k != 'values'} for name, data in stats.items()},
            'alerts': self.alerts,
            'baseline': self.baseline
        }
        
        # データを保存
        if save:
            self._save_data(analysis)
        
        return analysis
    
    def get_history(self, metric_name=None, limit=10):
        """
        指標の履歴を取得
        
        Args:
            metric_name: 指標の名前（Noneの場合はすべて）
            limit: 取得する件数
            
        Returns:
            dict: 指標名ごとの履歴
        """
        history_file = os.path.join(self.data_dir, 'performance_history.json')
        history = {}
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = {}
        
        if metric_name:
            return history.get(metric_name, [])[-limit:]
        
        return {name: data[-limit:] for name, data in history.items()}
    
    def generate_report(self, output_file=None):
        """
        パフォーマンスレポートを生成
        
        Args:
            output_file: 出力ファイル名
            
        Returns:
            str: レポートファイルのパス
        """
        # 分析を実行
        analysis = self.analyze(save=False)
        
        # 出力ファイル名
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.data_dir, f'performance_report_{timestamp}.html')
        
        # 時系列データを取得
        history = self.get_history()
        
        # レポート用のグラフを生成
        trend_chart = self._generate_trend_chart(history)
        comparison_chart = self._generate_comparison_chart(analysis['stats'])
        
        # HTMLテンプレート
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>パフォーマンス分析レポート</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                h1, h2, h3 {{ color: #333; }}
                .alert {{ background-color: #f8d7da; color: #721c24; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .improvement {{ background-color: #d4edda; color: #155724; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .chart {{ margin: 20px 0; padding: 10px; background-color: white; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .timestamp {{ font-size: 0.8em; color: #666; text-align: right; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>パフォーマンス分析レポート</h1>
                <p class="timestamp">生成日時: {timestamp}</p>
                
                <div class="alerts">
                    <h2>検出された変化</h2>
                    {alerts_html}
                </div>
                
                <div class="chart">
                    <h2>指標の傾向</h2>
                    <img src="data:image/png;base64,{trend_chart}" alt="指標の傾向">
                </div>
                
                <div class="chart">
                    <h2>現在の指標比較</h2>
                    <img src="data:image/png;base64,{comparison_chart}" alt="現在の指標比較">
                </div>
                
                <div class="stats">
                    <h2>詳細統計</h2>
                    <table>
                        <tr>
                            <th>指標</th>
                            <th>平均値</th>
                            <th>中央値</th>
                            <th>標準偏差</th>
                            <th>最小値</th>
                            <th>最大値</th>
                        </tr>
                        {stats_rows}
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        # アラートセクションを生成
        alerts_html = ""
        if analysis['alerts']:
            for alert in analysis['alerts']:
                alert_class = "alert" if alert['is_regression'] else "improvement"
                change_text = "悪化" if alert['is_regression'] else "改善"
                
                alerts_html += f"""
                <div class="{alert_class}">
                    <h3>指標 '{alert['metric']}' が {abs(alert['percent_change']):.1f}% {change_text}</h3>
                    <p>現在の平均: {alert['current_avg']:.2f}, 前回の平均: {alert['baseline_avg']:.2f}</p>
                </div>
                """
        else:
            alerts_html = "<p>検出された変化はありません。</p>"
        
        # 統計行を生成
        stats_rows = ""
        for name, stat in analysis['stats'].items():
            stats_rows += f"""
            <tr>
                <td>{name}</td>
                <td>{stat['avg']:.2f}</td>
                <td>{stat['median']:.2f}</td>
                <td>{stat['stddev']:.2f}</td>
                <td>{stat['min']:.2f}</td>
                <td>{stat['max']:.2f}</td>
            </tr>
            """
        
        # HTMLを生成
        html = html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            alerts_html=alerts_html,
            trend_chart=trend_chart,
            comparison_chart=comparison_chart,
            stats_rows=stats_rows
        )
        
        # HTMLを保存
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_file
    
    def _load_history(self):
        """履歴データを読み込む"""
        baseline_file = os.path.join(self.data_dir, 'performance_baseline.json')
        if os.path.exists(baseline_file):
            try:
                with open(baseline_file, 'r', encoding='utf-8') as f:
                    self.baseline = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.baseline = {}
    
    def _save_data(self, analysis):
        """データを保存する"""
        # メトリクスを履歴に追加
        history_file = os.path.join(self.data_dir, 'performance_history.json')
        history = {}
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = {}
        
        # 統計を履歴に追加
        timestamp = time.time()
        for name, stat in analysis['stats'].items():
            if name not in history:
                history[name] = []
            
            history[name].append({
                'avg': stat['avg'],
                'median': stat['median'],
                'stddev': stat['stddev'],
                'timestamp': timestamp
            })
            
            # 最大100件に制限
            if len(history[name]) > 100:
                history[name] = history[name][-100:]
        
        # 履歴を保存
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
        except IOError as e:
            print(f"履歴の保存に失敗しました: {e}")
        
        # ベースラインを保存
        baseline_file = os.path.join(self.data_dir, 'performance_baseline.json')
        try:
            with open(baseline_file, 'w', encoding='utf-8') as f:
                json.dump(self.baseline, f, indent=2)
        except IOError as e:
            print(f"ベースラインの保存に失敗しました: {e}")
    
    def _generate_trend_chart(self, history):
        """指標の傾向チャートを生成"""
        if not history:
            return ""
        
        # 最大5つの指標を表示
        metrics = list(history.keys())
        if len(metrics) > 5:
            # データポイント数が多い順にソート
            metrics.sort(key=lambda m: len(history[m]), reverse=True)
            metrics = metrics[:5]
        
        # プロット用のデータを準備
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        for metric in metrics:
            data = history[metric]
            timestamps = [entry['timestamp'] for entry in data]
            values = [entry['avg'] for entry in data]
            
            # Unix時間を日付に変換
            dates = [datetime.fromtimestamp(ts) for ts in timestamps]
            
            # プロット
            ax.plot(dates, values, marker='o', label=metric)
        
        # グラフの設定
        ax.set_ylabel('値')
        ax.set_title('指標の傾向')
        ax.legend()
        
        # X軸の日付フォーマット
        fig.autofmt_xdate()
        
        # レイアウト調整
        fig.tight_layout()
        
        # 画像をBase64エンコードして返す
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(image_png).decode('utf-8')
    
    def _generate_comparison_chart(self, stats):
        """現在の指標比較チャートを生成"""
        if not stats:
            return ""
        
        # データを準備
        metrics = []
        values = []
        
        for name, stat in stats.items():
            metrics.append(name)
            values.append(stat['avg'])
        
        # ラベルが長すぎる場合は省略
        short_metrics = []
        for metric in metrics:
            if len(metric) > 20:
                short_metrics.append(f"{metric[:17]}...")
            else:
                short_metrics.append(metric)
        
        # プロット
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        bars = ax.bar(range(len(metrics)), values, color='skyblue')
        
        # グラフの設定
        ax.set_xticks(range(len(metrics)))
        ax.set_xticklabels(short_metrics, rotation=45, ha='right')
        ax.set_ylabel('値')
        ax.set_title('現在の指標比較')
        
        # バーの上に値を表示
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                    f'{values[i]:.2f}',
                    ha='center', va='bottom', rotation=0)
        
        # レイアウト調整
        fig.tight_layout()
        
        # 画像をBase64エンコードして返す
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(image_png).decode('utf-8')


# テストパフォーマンス測定用のデコレータ
def measure_performance(analyzer, name=None):
    """
    関数の実行時間を測定するデコレータ
    
    Args:
        analyzer: PerformanceAnalyzer インスタンス
        name: 指標の名前（Noneの場合は関数名）
        
    Returns:
        デコレータ関数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            metric_name = name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000  # ミリ秒単位
            analyzer.record_metric(metric_name, execution_time, "ms", {
                'function': func.__name__,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            })
            
            return result
        return wrapper
    return decorator


if __name__ == "__main__":
    # このモジュールを直接実行した場合の処理
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='パフォーマンス分析モジュール')
    parser.add_argument('--report', action='store_true',
                        help='パフォーマンスレポートを生成')
    parser.add_argument('--output', type=str, default=None,
                        help='レポート出力ファイル名')
    
    args = parser.parse_args()
    
    # アナライザーを初期化
    analyzer = PerformanceAnalyzer()
    
    if args.report:
        # レポートを生成
        output_file = analyzer.generate_report(args.output)
        print(f"パフォーマンスレポートを生成しました: {os.path.abspath(output_file)}")
    else:
        # テスト用のデータを生成
        import random
        
        print("テスト用のパフォーマンスデータを生成中...")
        
        # いくつかのテスト関数
        def test_function_1():
            time.sleep(random.uniform(0.01, 0.03))
            return sum(range(10000))
        
        def test_function_2():
            time.sleep(random.uniform(0.02, 0.05))
            return [i * i for i in range(10000)]
        
        # データを生成
        for _ in range(5):
            # 関数1の実行時間を測定
            analyzer.record_execution_time("test_function_1", test_function_1)
            
            # 関数2の実行時間を測定
            analyzer.record_execution_time("test_function_2", test_function_2)
            
            # メモリ使用量を模擬
            analyzer.record_metric("memory_usage", random.uniform(50, 100), "MB")
            
            # FPSを模擬
            analyzer.record_metric("fps", random.uniform(55, 60), "fps")
        
        # 分析を実行
        analysis = analyzer.analyze()
        
        # 結果を表示
        print("\n===== パフォーマンス分析結果 =====")
        for name, stat in analysis['stats'].items():
            print(f"{name}: 平均={stat['avg']:.2f}, 中央値={stat['median']:.2f}, 標準偏差={stat['stddev']:.2f}")
        
        if analysis['alerts']:
            print("\n検出された変化:")
            for alert in analysis['alerts']:
                change_type = "悪化" if alert['is_regression'] else "改善"
                print(f"- {alert['metric']}: {abs(alert['percent_change']):.1f}% {change_type}")
        else:
            print("\n検出された変化はありません。")
        
        # レポートを生成
        output_file = analyzer.generate_report(args.output)
        print(f"\nパフォーマンスレポートを生成しました: {os.path.abspath(output_file)}")
    
    sys.exit(0) 