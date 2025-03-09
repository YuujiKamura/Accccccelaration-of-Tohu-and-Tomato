"""
テスト結果の詳細分析と可視化

このモジュールは、テスト実行結果を詳細に分析し、
HTML形式のグラフィカルレポートを生成します。
"""

import json
import os
import datetime
import time
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import base64
from io import BytesIO
import unittest
from collections import defaultdict, Counter

class TestResultAnalyzer:
    """テスト結果を分析するクラス"""
    
    def __init__(self, results_dir="test_results"):
        """
        初期化
        
        Args:
            results_dir: テスト結果を保存するディレクトリ
        """
        self.results_dir = results_dir
        self.current_results = None
        self.history = []
        
        # ディレクトリがなければ作成
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            
        # 履歴を読み込む
        self._load_history()
    
    def analyze_test_result(self, test_result):
        """
        テスト結果を分析する
        
        Args:
            test_result: unittestのTestResult オブジェクト
            
        Returns:
            dict: 分析結果
        """
        # 現在時刻
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # テスト実行時間を計算
        start_time = getattr(test_result, 'start_time', None)
        stop_time = getattr(test_result, 'stop_time', None)
        
        if start_time and stop_time:
            run_time = stop_time - start_time
        else:
            run_time = None
        
        # 結果を取得
        tests_run = test_result.testsRun
        failures = len(test_result.failures)
        errors = len(test_result.errors)
        skipped = len(getattr(test_result, 'skipped', []))
        successes = tests_run - failures - errors - skipped
        
        # モジュールごとの成功率を計算
        module_stats = self._analyze_modules(test_result)
        
        # パフォーマンステストの結果を取得
        performance_stats = self._analyze_performance(test_result)
        
        # 結果をまとめる
        analysis = {
            'timestamp': timestamp,
            'tests_run': tests_run,
            'successes': successes,
            'failures': failures,
            'errors': errors,
            'skipped': skipped,
            'success_rate': (successes / tests_run * 100) if tests_run > 0 else 0,
            'run_time': run_time,
            'modules': module_stats,
            'performance': performance_stats,
            'failures_details': self._format_failures(test_result.failures),
            'errors_details': self._format_failures(test_result.errors)
        }
        
        # 現在の結果を保存
        self.current_results = analysis
        
        # 履歴に追加
        self.history.append(analysis)
        
        # 履歴を保存
        self._save_history()
        
        return analysis
    
    def _analyze_modules(self, test_result):
        """モジュールごとのテスト結果を分析"""
        module_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0, 'error': 0})
        
        # すべての実行されたテストを取得
        all_tests = []
        for test, _ in getattr(test_result, 'errors', []):
            all_tests.append((test, 'error'))
        for test, _ in getattr(test_result, 'failures', []):
            all_tests.append((test, 'failure'))
        for test, _ in getattr(test_result, 'skipped', []):
            all_tests.append((test, 'skipped'))
            
        # 成功したテストを推定（試行回数から失敗、エラー、スキップを引く）
        total_known = len(all_tests)
        if test_result.testsRun > total_known:
            # 不明なテストはすべて成功と仮定
            unknown_success = test_result.testsRun - total_known
            # モジュール名が不明なので "unknown" としておく
            module_stats["unknown"]['total'] += unknown_success
            module_stats["unknown"]['success'] += unknown_success
        
        # 既知のテスト結果を集計
        for test, result_type in all_tests:
            module_name = test.__class__.__module__
            module_stats[module_name]['total'] += 1
            if result_type == 'error':
                module_stats[module_name]['error'] += 1
            elif result_type == 'failure':
                module_stats[module_name]['failure'] += 1
            elif result_type == 'skipped':
                pass  # スキップは特に集計しない
        
        # 成功数を計算
        for stats in module_stats.values():
            stats['success'] = stats['total'] - stats['failure'] - stats['error']
        
        return dict(module_stats)
    
    def _analyze_performance(self, test_result):
        """パフォーマンステスト結果を分析"""
        performance_stats = {}
        
        # test_performanceモジュールのテスト結果を探す
        for test_case, _ in getattr(test_result, 'errors', []) + getattr(test_result, 'failures', []):
            if 'TestPerformance' in str(test_case):
                # パフォーマンステストの詳細な情報がない場合は空の結果を返す
                return performance_stats
        
        # 実行時間の情報を持つテストを探す（この実装は仮定に基づく）
        # 実際には、パフォーマンス情報を収集する仕組みが必要
        return performance_stats
    
    def _format_failures(self, failures):
        """失敗とエラーの詳細をフォーマット"""
        formatted = []
        for test, error in failures:
            formatted.append({
                'test': str(test),
                'message': error.split('\n')[0] if error else "",
                'details': error
            })
        return formatted
    
    def _load_history(self):
        """テスト履歴を読み込む"""
        history_file = os.path.join(self.results_dir, 'test_history.json')
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []
        else:
            self.history = []
    
    def _save_history(self):
        """テスト履歴を保存する"""
        history_file = os.path.join(self.results_dir, 'test_history.json')
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2)
        except IOError as e:
            print(f"履歴の保存に失敗しました: {e}")
    
    def generate_html_report(self, output_file=None):
        """HTML形式のレポートを生成"""
        if not self.current_results:
            raise ValueError("レポート生成前にテスト結果を分析する必要があります")
        
        if output_file is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.results_dir, f'test_report_{timestamp}.html')
        
        # 分析結果を取得
        analysis = self.current_results
        
        # グラフを生成
        success_rate_chart = self._generate_success_rate_chart()
        modules_chart = self._generate_modules_chart(analysis['modules'])
        history_chart = self._generate_history_chart()
        
        # HTMLテンプレート
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>テスト結果レポート</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                h1, h2, h3 {{ color: #333; }}
                .summary {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
                .summary-card {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; width: 18%; text-align: center; }}
                .success {{ background-color: #d4edda; color: #155724; }}
                .failure {{ background-color: #f8d7da; color: #721c24; }}
                .error {{ background-color: #f5c6cb; color: #721c24; }}
                .skipped {{ background-color: #fff3cd; color: #856404; }}
                .chart {{ margin: 20px 0; padding: 10px; background-color: white; border-radius: 5px; }}
                .modules {{ margin-top: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .failures {{ margin-top: 20px; }}
                .failure-item {{ background-color: #f8d7da; padding: 10px; margin-bottom: 10px; border-radius: 5px; }}
                .failure-message {{ font-weight: bold; color: #721c24; }}
                .failure-details {{ white-space: pre-wrap; margin-top: 10px; font-family: monospace; font-size: 0.9em; background-color: #f5f5f5; padding: 10px; border-radius: 3px; }}
                .timestamp {{ font-size: 0.8em; color: #666; text-align: right; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>テスト結果レポート</h1>
                <p class="timestamp">生成日時: {timestamp}</p>
                
                <div class="summary">
                    <div class="summary-card">
                        <h3>実行テスト数</h3>
                        <p>{tests_run}</p>
                    </div>
                    <div class="summary-card success">
                        <h3>成功</h3>
                        <p>{successes}</p>
                    </div>
                    <div class="summary-card failure">
                        <h3>失敗</h3>
                        <p>{failures}</p>
                    </div>
                    <div class="summary-card error">
                        <h3>エラー</h3>
                        <p>{errors}</p>
                    </div>
                    <div class="summary-card skipped">
                        <h3>スキップ</h3>
                        <p>{skipped}</p>
                    </div>
                </div>
                
                <div class="chart">
                    <h2>成功率</h2>
                    <img src="data:image/png;base64,{success_rate_chart}" alt="成功率">
                </div>
                
                <div class="chart">
                    <h2>モジュール別成功率</h2>
                    <img src="data:image/png;base64,{modules_chart}" alt="モジュール別成功率">
                </div>
                
                <div class="chart">
                    <h2>履歴トレンド</h2>
                    <img src="data:image/png;base64,{history_chart}" alt="履歴トレンド">
                </div>
                
                <div class="modules">
                    <h2>モジュール別詳細</h2>
                    <table>
                        <tr>
                            <th>モジュール</th>
                            <th>テスト数</th>
                            <th>成功</th>
                            <th>失敗</th>
                            <th>エラー</th>
                            <th>成功率</th>
                        </tr>
                        {module_rows}
                    </table>
                </div>
                
                {failures_section}
                
                {errors_section}
            </div>
        </body>
        </html>
        """
        
        # モジュール別詳細行を生成
        module_rows = ""
        for module, stats in analysis['modules'].items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            module_rows += f"""
            <tr>
                <td>{module}</td>
                <td>{stats['total']}</td>
                <td>{stats['success']}</td>
                <td>{stats['failure']}</td>
                <td>{stats['error']}</td>
                <td>{success_rate:.1f}%</td>
            </tr>
            """
        
        # 失敗セクションを生成
        failures_section = ""
        if analysis['failures']:
            failures_section = "<div class='failures'><h2>失敗の詳細</h2>"
            for failure in analysis['failures_details']:
                failures_section += f"""
                <div class="failure-item">
                    <div class="failure-message">{failure['test']}</div>
                    <div class="failure-message">{failure['message']}</div>
                    <div class="failure-details">{failure['details']}</div>
                </div>
                """
            failures_section += "</div>"
        
        # エラーセクションを生成
        errors_section = ""
        if analysis['errors']:
            errors_section = "<div class='failures'><h2>エラーの詳細</h2>"
            for error in analysis['errors_details']:
                errors_section += f"""
                <div class="failure-item">
                    <div class="failure-message">{error['test']}</div>
                    <div class="failure-message">{error['message']}</div>
                    <div class="failure-details">{error['details']}</div>
                </div>
                """
            errors_section += "</div>"
        
        # HTMLを生成
        html = html_template.format(
            timestamp=analysis['timestamp'],
            tests_run=analysis['tests_run'],
            successes=analysis['successes'],
            failures=analysis['failures'],
            errors=analysis['errors'],
            skipped=analysis['skipped'],
            success_rate_chart=success_rate_chart,
            modules_chart=modules_chart,
            history_chart=history_chart,
            module_rows=module_rows,
            failures_section=failures_section,
            errors_section=errors_section
        )
        
        # HTMLを保存
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_file
    
    def _generate_success_rate_chart(self):
        """成功率のチャートを生成"""
        if not self.current_results:
            return ""
        
        # データを取得
        labels = ['成功', '失敗', 'エラー', 'スキップ']
        values = [
            self.current_results['successes'],
            self.current_results['failures'],
            self.current_results['errors'],
            self.current_results['skipped']
        ]
        colors = ['#4CAF50', '#F44336', '#FF9800', '#FFC107']
        
        # グラフを生成
        fig = Figure(figsize=(8, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels, 
            colors=colors,
            autopct='%1.1f%%', 
            startangle=90,
            explode=(0.1, 0.1, 0.1, 0.1)
        )
        ax.axis('equal')
        
        # ラベルの色を設定
        for text in texts:
            text.set_color('black')
        for autotext in autotexts:
            autotext.set_color('white')
        
        # 画像をBase64エンコードして返す
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(image_png).decode('utf-8')
    
    def _generate_modules_chart(self, modules):
        """モジュール別成功率のチャートを生成"""
        if not modules:
            return ""
        
        # データを準備
        labels = []
        success_rates = []
        
        for module, stats in modules.items():
            if stats['total'] > 0:
                labels.append(module)
                success_rates.append(stats['success'] / stats['total'] * 100)
        
        # ラベルが長すぎる場合は省略
        short_labels = []
        for label in labels:
            if len(label) > 20:
                parts = label.split('.')
                if len(parts) > 1:
                    short_labels.append(f"...{parts[-1]}")
                else:
                    short_labels.append(f"{label[:17]}...")
            else:
                short_labels.append(label)
        
        # グラフを生成
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        bars = ax.bar(range(len(labels)), success_rates, color='#4CAF50')
        
        # グラフの設定
        ax.set_ylim(0, 100)
        ax.set_ylabel('成功率 (%)')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(short_labels, rotation=45, ha='right')
        
        # バーの上に値を表示
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 1,
                    f'{success_rates[i]:.1f}%',
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
    
    def _generate_history_chart(self):
        """テスト履歴のトレンドチャートを生成"""
        if not self.history:
            return ""
        
        # データを準備（最新の10件のみ使用）
        history = self.history[-10:] if len(self.history) > 10 else self.history
        
        timestamps = []
        success_rates = []
        runs = []
        
        for record in history:
            timestamp = record.get('timestamp', '')
            if timestamp:
                # 日付部分のみ使用
                timestamps.append(timestamp.split(' ')[0])
            else:
                timestamps.append('')
            
            success_rates.append(record.get('success_rate', 0))
            runs.append(record.get('tests_run', 0))
        
        # グラフを生成
        fig = Figure(figsize=(10, 5))
        canvas = FigureCanvas(fig)
        
        # 成功率のグラフ
        ax1 = fig.add_subplot(111)
        ax1.plot(timestamps, success_rates, 'g-', marker='o', label='成功率')
        ax1.set_ylim(0, 100)
        ax1.set_ylabel('成功率 (%)')
        ax1.tick_params('y', colors='g')
        
        # テスト数のグラフ（2軸目）
        ax2 = ax1.twinx()
        ax2.plot(timestamps, runs, 'b--', marker='s', label='テスト数')
        ax2.set_ylabel('テスト数')
        ax2.tick_params('y', colors='b')
        
        # X軸ラベルの設定
        plt.xticks(rotation=45)
        
        # 凡例の設定
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # レイアウト調整
        fig.tight_layout()
        
        # 画像をBase64エンコードして返す
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(image_png).decode('utf-8')


# テスト結果分析用のTestResultクラス拡張
class AnalyzableTestResult(unittest.TextTestResult):
    """テスト結果を分析可能な形式で出力するクラス"""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.start_time = time.time()
        self.performance_results = {}
    
    def stopTest(self, test):
        """各テスト終了時に呼ばれる"""
        super().stopTest(test)
        
        # パフォーマンステストの場合、結果を記録
        if 'TestPerformance' in test.__class__.__name__:
            # ここで本来はテストからパフォーマンス情報を取得する
            # 実際の実装では、テスト側で性能データを記録する仕組みが必要
            pass
    
    def stopTestRun(self):
        """テスト実行終了時に呼ばれる"""
        super().stopTestRun()
        self.stop_time = time.time()


def create_test_runner(verbosity=2, analyzer=None, output_file=None):
    """テスト実行とレポート生成を行うランナーを作成"""
    # 分析クラスを初期化
    if analyzer is None:
        analyzer = TestResultAnalyzer()
    
    # カスタム結果クラスを使用するランナー
    class AnalyzingTextTestRunner(unittest.TextTestRunner):
        def __init__(self, **kwargs):
            kwargs['resultclass'] = AnalyzableTestResult
            super().__init__(**kwargs)
            self.analyzer = analyzer
            self.output_file = output_file
        
        def run(self, test):
            """テストを実行して結果を分析"""
            # テスト実行
            result = super().run(test)
            
            # 結果を分析
            self.analyzer.analyze_test_result(result)
            
            # レポート生成
            if self.output_file:
                report_file = self.analyzer.generate_html_report(self.output_file)
                print(f"\nHTMLレポートが生成されました: {os.path.abspath(report_file)}")
            else:
                report_file = self.analyzer.generate_html_report()
                print(f"\nHTMLレポートが生成されました: {os.path.abspath(report_file)}")
            
            return result
    
    # ランナーを作成して返す
    return AnalyzingTextTestRunner(verbosity=verbosity)


if __name__ == "__main__":
    # このモジュールを直接実行した場合の処理
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='テスト結果を分析してレポートを生成')
    parser.add_argument('--test-script', type=str, default='run_tests.py',
                        help='実行するテストスクリプト')
    parser.add_argument('--output', type=str, default=None,
                        help='レポート出力ファイル名')
    parser.add_argument('--history-only', action='store_true',
                        help='履歴データのみからレポートを生成')
    
    args = parser.parse_args()
    
    # 分析クラスを初期化
    analyzer = TestResultAnalyzer()
    
    if args.history_only:
        # 履歴データのみからレポートを生成
        if not analyzer.history:
            print("履歴データがありません。テストを実行してください。")
            sys.exit(1)
        
        analyzer.current_results = analyzer.history[-1]
        report_file = analyzer.generate_html_report(args.output)
        print(f"履歴データからレポートを生成しました: {os.path.abspath(report_file)}")
    else:
        # テストを実行してレポートを生成
        import subprocess
        
        # テストスクリプトを実行
        print(f"{args.test_script} を実行中...")
        result = subprocess.run([sys.executable, args.test_script])
        
        # 履歴を再読込
        analyzer._load_history()
        
        if not analyzer.history:
            print("テスト結果が記録されていません。")
            sys.exit(1)
        
        # 最新の結果でレポートを生成
        analyzer.current_results = analyzer.history[-1]
        report_file = analyzer.generate_html_report(args.output)
        print(f"テスト結果からレポートを生成しました: {os.path.abspath(report_file)}")
    
    sys.exit(0) 