"""
アドバタイズモードテスト

アドバタイズモードの動作を分析し,問題点を検出した後,
改善パッチを適用して再度分析し,改善効果を評価します.
"""

import os
import sys
import time
import pygame
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# 自作モジュールのインポート（パスが通っていることを前提）
try:
    from advertise_mode_analyzer import AdvertiseModeMonitor
    from advertise_mode_improver import AdvertiseModeImprover
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from advertise_mode_analyzer import AdvertiseModeMonitor
        from advertise_mode_improver import AdvertiseModeImprover
    except ImportError:
        print("エラー: 必要なモジュールが見つかりません.")
        print("advertise_mode_analyzer.py と advertise_mode_improver.py が必要です.")
        sys.exit(1)

class AdvertiseModeTest:
    """アドバタイズモードのテストを行うクラス"""
    
    def __init__(self, main_module_name="main", test_frames=300, output_dir=None, quick_mode=False):
        """初期化"""
        self.main_module_name = main_module_name
        self.test_frames = test_frames
        self.quick_mode = quick_mode
        
        # クイックモードの場合はフレーム数を制限
        if self.quick_mode and self.test_frames > 300:
            print(f"クイックモードが有効: フレーム数を {self.test_frames} から 300 に制限します")
            self.test_frames = 300
        
        # 出力ディレクトリの設定
        if output_dir:
            self.output_dir = output_dir
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = f"advertise_test_{timestamp}"
        
        # 出力ディレクトリが存在しない場合は作成
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 分析結果
        self.original_results = None
        self.improved_results = None
    
    def run_test(self):
        """テストを実行"""
        print("=== アドバタイズモードテスト開始 ===")
        start_time = time.time()
        
        # オリジナルの動作を分析
        print("\n[ステップ1] オリジナルのアドバタイズモード動作を分析中...")
        step_start = time.time()
        self.run_original_analysis()
        print(f"分析完了 (所要時間: {time.time() - step_start:.1f}秒)")
        
        # 改善パッチを適用
        print("\n[ステップ2] アドバタイズモード改善パッチを適用中...")
        step_start = time.time()
        self.apply_improvement_patch()
        print(f"パッチ適用完了 (所要時間: {time.time() - step_start:.1f}秒)")
        
        # 改善後の動作を分析
        print("\n[ステップ3] 改善後のアドバタイズモード動作を分析中...")
        step_start = time.time()
        self.run_improved_analysis()
        print(f"分析完了 (所要時間: {time.time() - step_start:.1f}秒)")
        
        # 結果の比較と評価
        print("\n[ステップ4] 分析結果の比較と評価...")
        step_start = time.time()
        self.compare_results()
        print(f"評価完了 (所要時間: {time.time() - step_start:.1f}秒)")
        
        total_time = time.time() - start_time
        print(f"\n=== アドバタイズモードテスト完了 (総所要時間: {total_time:.1f}秒) ===")
        print(f"結果は {os.path.abspath(self.output_dir)} に保存されています")
    
    def run_original_analysis(self):
        """オリジナルのアドバタイズモード動作を分析"""
        # 分析ファイルのパスを設定
        os.environ['ADVERTISE_ANALYSIS_PATH'] = os.path.join(self.output_dir, "original")
        if not os.path.exists(os.environ['ADVERTISE_ANALYSIS_PATH']):
            os.makedirs(os.environ['ADVERTISE_ANALYSIS_PATH'])
        
        # 分析モニターを作成して実行
        monitor = AdvertiseModeMonitor(
            main_module_name=self.main_module_name,
            max_frames=self.test_frames,
            headless=True,
            show_progress=True
        )
        
        # 分析を実行
        monitor.run_analysis()
        
        # 分析結果を保存
        self.original_results = monitor.analyzer.analysis_results
        
        # 結果ファイルをリネーム（わかりやすく）
        self._rename_result_files("original")
    
    def apply_improvement_patch(self):
        """アドバタイズモード改善パッチを適用"""
        # 改善クラスを作成してパッチを適用
        improver = AdvertiseModeImprover(main_module_name=self.main_module_name)
        improver.apply_patches()
    
    def run_improved_analysis(self):
        """改善後のアドバタイズモード動作を分析"""
        # 分析ファイルのパスを設定
        os.environ['ADVERTISE_ANALYSIS_PATH'] = os.path.join(self.output_dir, "improved")
        if not os.path.exists(os.environ['ADVERTISE_ANALYSIS_PATH']):
            os.makedirs(os.environ['ADVERTISE_ANALYSIS_PATH'])
        
        # 分析モニターを作成して実行
        monitor = AdvertiseModeMonitor(
            main_module_name=self.main_module_name,
            max_frames=self.test_frames,
            headless=True,
            show_progress=True
        )
        
        # 分析を実行
        monitor.run_analysis()
        
        # 分析結果を保存
        self.improved_results = monitor.analyzer.analysis_results
        
        # 結果ファイルをリネーム（わかりやすく）
        self._rename_result_files("improved")
    
    def _rename_result_files(self, prefix):
        """結果ファイルをわかりやすくリネーム"""
        try:
            # JSONファイル
            if os.path.exists("advertise_analysis_results.json"):
                new_path = os.path.join(self.output_dir, f"{prefix}_results.json")
                os.rename("advertise_analysis_results.json", new_path)
            
            # ヒートマップ画像
            if os.path.exists("advertise_analysis_heatmap.png"):
                new_path = os.path.join(self.output_dir, f"{prefix}_heatmap.png")
                os.rename("advertise_analysis_heatmap.png", new_path)
            
            # ログファイル
            for filename in os.listdir("."):
                if filename.startswith("advertise_analysis_") and filename.endswith(".log"):
                    new_path = os.path.join(self.output_dir, f"{prefix}_log.log")
                    os.rename(filename, new_path)
                    break
        except Exception as e:
            print(f"ファイルのリネーム中にエラー: {e}")
    
    def compare_results(self):
        """オリジナルと改善後の結果を比較して評価"""
        if not self.original_results or not self.improved_results:
            print("分析結果が不足しています.両方の分析を完了してください.")
            return
        
        # 比較結果を出力
        print("\n=== 分析結果の比較 ===")
        
        # 中央滞在時間比率
        orig_center = self.original_results['center_time_ratio']
        imp_center = self.improved_results['center_time_ratio']
        center_change = (imp_center - orig_center) / max(orig_center, 0.001) * 100
        print(f"中央滞在時間比率: {orig_center:.2%} -> {imp_center:.2%} ({center_change:.1f}% 変化)")
        
        # 振動比率
        orig_vibration = self.original_results['vibration_ratio']
        imp_vibration = self.improved_results['vibration_ratio']
        vibration_change = (imp_vibration - orig_vibration) / max(orig_vibration, 0.001) * 100
        print(f"振動検出比率: {orig_vibration:.2%} -> {imp_vibration:.2%} ({vibration_change:.1f}% 変化)")
        
        # 敵回避率
        orig_avoidance = self.original_results['enemy_avoidance_rate']
        imp_avoidance = self.improved_results['enemy_avoidance_rate']
        avoidance_change = (imp_avoidance - orig_avoidance) / max(orig_avoidance, 0.001) * 100
        print(f"敵回避率: {orig_avoidance:.2%} -> {imp_avoidance:.2%} ({avoidance_change:.1f}% 変化)")
        
        # 中央からの平均距離
        orig_distance = self.original_results['average_distance_from_center']
        imp_distance = self.improved_results['average_distance_from_center']
        distance_change = (imp_distance - orig_distance) / max(orig_distance, 0.001) * 100
        print(f"中央からの平均距離: {orig_distance:.1f}px -> {imp_distance:.1f}px ({distance_change:.1f}% 変化)")
        
        # 問題パターン数
        orig_problems = len(self.original_results['problematic_patterns'])
        imp_problems = len(self.improved_results['problematic_patterns'])
        print(f"検出された問題パターン数: {orig_problems} -> {imp_problems}")
        
        # 問題パターンの詳細
        print("\n[オリジナル] 検出された問題パターン:")
        for i, pattern in enumerate(self.original_results['problematic_patterns']):
            print(f"{i+1}. {pattern['type']}: {pattern['description']}")
        
        print("\n[改善後] 検出された問題パターン:")
        for i, pattern in enumerate(self.improved_results['problematic_patterns']):
            print(f"{i+1}. {pattern['type']}: {pattern['description']}")
        
        # 改善評価
        self._evaluate_improvement()
        
        # グラフによる可視化
        self._generate_comparison_graphs()
    
    def _evaluate_improvement(self):
        """改善の評価を行い,総合的な評価を出力"""
        scores = []
        
        # 中央滞在時間の改善
        if self.original_results['center_time_ratio'] > 0.3:
            # 元の中央滞在率が高すぎる場合,減少していれば改善
            if self.improved_results['center_time_ratio'] < self.original_results['center_time_ratio']:
                score_center = min(10, (self.original_results['center_time_ratio'] - self.improved_results['center_time_ratio']) / self.original_results['center_time_ratio'] * 10)
                scores.append(score_center)
                print(f"中央滞在時間の改善: {score_center:.1f}/10")
            else:
                scores.append(0)
                print("中央滞在時間の改善: 0/10 (悪化または変化なし)")
        else:
            # 元の中央滞在率が適切な場合は10点
            scores.append(10)
            print("中央滞在時間は元から適切です: 10/10")
        
        # 振動の改善
        if self.improved_results['vibration_ratio'] < self.original_results['vibration_ratio']:
            score_vibration = min(10, (self.original_results['vibration_ratio'] - self.improved_results['vibration_ratio']) / max(self.original_results['vibration_ratio'], 0.001) * 10)
            scores.append(score_vibration)
            print(f"振動の改善: {score_vibration:.1f}/10")
        else:
            scores.append(0)
            print("振動の改善: 0/10 (悪化または変化なし)")
        
        # 敵回避率の改善
        if self.improved_results['enemy_avoidance_rate'] > self.original_results['enemy_avoidance_rate']:
            score_avoidance = min(10, (self.improved_results['enemy_avoidance_rate'] - self.original_results['enemy_avoidance_rate']) / (1 - self.original_results['enemy_avoidance_rate']) * 10)
            scores.append(score_avoidance)
            print(f"敵回避率の改善: {score_avoidance:.1f}/10")
        else:
            scores.append(0)
            print("敵回避率の改善: 0/10 (悪化または変化なし)")
        
        # 問題パターン数の改善
        orig_problems = len(self.original_results['problematic_patterns'])
        imp_problems = len(self.improved_results['problematic_patterns'])
        
        if imp_problems < orig_problems:
            score_problems = min(10, (orig_problems - imp_problems) / orig_problems * 10) if orig_problems > 0 else 5
            scores.append(score_problems)
            print(f"問題パターン数の改善: {score_problems:.1f}/10")
        else:
            scores.append(0)
            print("問題パターン数の改善: 0/10 (悪化または変化なし)")
        
        # 総合評価
        if scores:
            total_score = sum(scores) / len(scores)
            print(f"\n総合改善評価: {total_score:.1f}/10")
            
            if total_score >= 7:
                print("評価: 優れた改善が見られます！敵回避と中央での振動問題が大幅に改善されています.")
            elif total_score >= 5:
                print("評価: ある程度の改善が見られます.引き続き微調整が必要かもしれません.")
            elif total_score >= 3:
                print("評価: わずかな改善が見られますが,さらなる改良が必要です.")
            else:
                print("評価: 有意な改善は見られません.アルゴリズムの再検討が必要です.")
        else:
            print("\n総合評価: 評価できるデータが不足しています.")
    
    def _generate_comparison_graphs(self):
        """比較グラフを生成して保存"""
        try:
            # データの準備
            metrics = ['中央滞在比率', '振動検出比率', '敵回避率', '中央からの距離(px/100)']
            orig_values = [
                self.original_results['center_time_ratio'],
                self.original_results['vibration_ratio'],
                self.original_results['enemy_avoidance_rate'],
                self.original_results['average_distance_from_center'] / 100
            ]
            imp_values = [
                self.improved_results['center_time_ratio'],
                self.improved_results['vibration_ratio'],
                self.improved_results['enemy_avoidance_rate'],
                self.improved_results['average_distance_from_center'] / 100
            ]
            
            # バーグラフの作成
            x = np.arange(len(metrics))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(10, 6))
            rects1 = ax.bar(x - width/2, orig_values, width, label='オリジナル', color='lightcoral')
            rects2 = ax.bar(x + width/2, imp_values, width, label='改善後', color='lightgreen')
            
            # グラフの装飾
            ax.set_title('アドバタイズモード改善の比較')
            ax.set_ylabel('値')
            ax.set_xticks(x)
            ax.set_xticklabels(metrics)
            ax.legend()
            
            # 値のラベル表示
            def autolabel(rects):
                for rect in rects:
                    height = rect.get_height()
                    ax.annotate(f'{height:.2f}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom')
            
            autolabel(rects1)
            autolabel(rects2)
            
            fig.tight_layout()
            
            # グラフの保存
            plt.savefig(os.path.join(self.output_dir, "comparison_graph.png"))
            print(f"\nグラフを保存しました: {os.path.join(self.output_dir, 'comparison_graph.png')}")
            
            plt.close()
        except Exception as e:
            print(f"グラフ生成中にエラーが発生しました: {e}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='アドバタイズモードテスト')
    parser.add_argument('--module', default='main', help='メインモジュール名')
    parser.add_argument('--frames', type=int, default=300, help='テストするフレーム数（デフォルト: 300）')
    parser.add_argument('--output', default=None, help='出力ディレクトリ')
    parser.add_argument('--quick', action='store_true', help='クイックモード（短時間実行）')
    parser.add_argument('--demo', action='store_true', help='改善後のアドバタイズモードをデモ実行')
    parser.add_argument('--visual-demo', action='store_true', help='GUI表示でデモ実行')
    
    args = parser.parse_args()
    
    # デモモードの場合
    if args.demo:
        print("改善されたアドバタイズモードをデモ実行します...")
        improver = AdvertiseModeImprover(main_module_name=args.module)
        improver.apply_patches()
        
        if args.visual_demo:
            # GUI表示でのデモ実行
            improver.run_improved_advertise_mode(duration=30)
        else:
            # ヘッドレスモードでの解析実行
            monitor = AdvertiseModeMonitor(
                main_module_name=args.module,
                max_frames=600,  # 10秒間
                headless=True,
                show_progress=True
            )
            monitor.run_analysis()
        return
    
    # テストの実行
    test = AdvertiseModeTest(
        main_module_name=args.module,
        test_frames=args.frames,
        output_dir=args.output,
        quick_mode=args.quick
    )
    
    test.run_test()


if __name__ == '__main__':
    main() 
アドバタイズモードテスト

アドバタイズモードの動作を分析し,問題点を検出した後,
改善パッチを適用して再度分析し,改善効果を評価します.
"""

import os
import sys
import time
import pygame
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# 自作モジュールのインポート（パスが通っていることを前提）
try:
    from advertise_mode_analyzer import AdvertiseModeMonitor
    from advertise_mode_improver import AdvertiseModeImprover
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from advertise_mode_analyzer import AdvertiseModeMonitor
        from advertise_mode_improver import AdvertiseModeImprover
    except ImportError:
        print("エラー: 必要なモジュールが見つかりません.")
        print("advertise_mode_analyzer.py と advertise_mode_improver.py が必要です.")
        sys.exit(1)

class AdvertiseModeTest:
    """アドバタイズモードのテストを行うクラス"""
    
    def __init__(self, main_module_name="main", test_frames=300, output_dir=None, quick_mode=False):
        """初期化"""
        self.main_module_name = main_module_name
        self.test_frames = test_frames
        self.quick_mode = quick_mode
        
        # クイックモードの場合はフレーム数を制限
        if self.quick_mode and self.test_frames > 300:
            print(f"クイックモードが有効: フレーム数を {self.test_frames} から 300 に制限します")
            self.test_frames = 300
        
        # 出力ディレクトリの設定
        if output_dir:
            self.output_dir = output_dir
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = f"advertise_test_{timestamp}"
        
        # 出力ディレクトリが存在しない場合は作成
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 分析結果
        self.original_results = None
        self.improved_results = None
    
    def run_test(self):
        """テストを実行"""
        print("=== アドバタイズモードテスト開始 ===")
        start_time = time.time()
        
        # オリジナルの動作を分析
        print("\n[ステップ1] オリジナルのアドバタイズモード動作を分析中...")
        step_start = time.time()
        self.run_original_analysis()
        print(f"分析完了 (所要時間: {time.time() - step_start:.1f}秒)")
        
        # 改善パッチを適用
        print("\n[ステップ2] アドバタイズモード改善パッチを適用中...")
        step_start = time.time()
        self.apply_improvement_patch()
        print(f"パッチ適用完了 (所要時間: {time.time() - step_start:.1f}秒)")
        
        # 改善後の動作を分析
        print("\n[ステップ3] 改善後のアドバタイズモード動作を分析中...")
        step_start = time.time()
        self.run_improved_analysis()
        print(f"分析完了 (所要時間: {time.time() - step_start:.1f}秒)")
        
        # 結果の比較と評価
        print("\n[ステップ4] 分析結果の比較と評価...")
        step_start = time.time()
        self.compare_results()
        print(f"評価完了 (所要時間: {time.time() - step_start:.1f}秒)")
        
        total_time = time.time() - start_time
        print(f"\n=== アドバタイズモードテスト完了 (総所要時間: {total_time:.1f}秒) ===")
        print(f"結果は {os.path.abspath(self.output_dir)} に保存されています")
    
    def run_original_analysis(self):
        """オリジナルのアドバタイズモード動作を分析"""
        # 分析ファイルのパスを設定
        os.environ['ADVERTISE_ANALYSIS_PATH'] = os.path.join(self.output_dir, "original")
        if not os.path.exists(os.environ['ADVERTISE_ANALYSIS_PATH']):
            os.makedirs(os.environ['ADVERTISE_ANALYSIS_PATH'])
        
        # 分析モニターを作成して実行
        monitor = AdvertiseModeMonitor(
            main_module_name=self.main_module_name,
            max_frames=self.test_frames,
            headless=True,
            show_progress=True
        )
        
        # 分析を実行
        monitor.run_analysis()
        
        # 分析結果を保存
        self.original_results = monitor.analyzer.analysis_results
        
        # 結果ファイルをリネーム（わかりやすく）
        self._rename_result_files("original")
    
    def apply_improvement_patch(self):
        """アドバタイズモード改善パッチを適用"""
        # 改善クラスを作成してパッチを適用
        improver = AdvertiseModeImprover(main_module_name=self.main_module_name)
        improver.apply_patches()
    
    def run_improved_analysis(self):
        """改善後のアドバタイズモード動作を分析"""
        # 分析ファイルのパスを設定
        os.environ['ADVERTISE_ANALYSIS_PATH'] = os.path.join(self.output_dir, "improved")
        if not os.path.exists(os.environ['ADVERTISE_ANALYSIS_PATH']):
            os.makedirs(os.environ['ADVERTISE_ANALYSIS_PATH'])
        
        # 分析モニターを作成して実行
        monitor = AdvertiseModeMonitor(
            main_module_name=self.main_module_name,
            max_frames=self.test_frames,
            headless=True,
            show_progress=True
        )
        
        # 分析を実行
        monitor.run_analysis()
        
        # 分析結果を保存
        self.improved_results = monitor.analyzer.analysis_results
        
        # 結果ファイルをリネーム（わかりやすく）
        self._rename_result_files("improved")
    
    def _rename_result_files(self, prefix):
        """結果ファイルをわかりやすくリネーム"""
        try:
            # JSONファイル
            if os.path.exists("advertise_analysis_results.json"):
                new_path = os.path.join(self.output_dir, f"{prefix}_results.json")
                os.rename("advertise_analysis_results.json", new_path)
            
            # ヒートマップ画像
            if os.path.exists("advertise_analysis_heatmap.png"):
                new_path = os.path.join(self.output_dir, f"{prefix}_heatmap.png")
                os.rename("advertise_analysis_heatmap.png", new_path)
            
            # ログファイル
            for filename in os.listdir("."):
                if filename.startswith("advertise_analysis_") and filename.endswith(".log"):
                    new_path = os.path.join(self.output_dir, f"{prefix}_log.log")
                    os.rename(filename, new_path)
                    break
        except Exception as e:
            print(f"ファイルのリネーム中にエラー: {e}")
    
    def compare_results(self):
        """オリジナルと改善後の結果を比較して評価"""
        if not self.original_results or not self.improved_results:
            print("分析結果が不足しています.両方の分析を完了してください.")
            return
        
        # 比較結果を出力
        print("\n=== 分析結果の比較 ===")
        
        # 中央滞在時間比率
        orig_center = self.original_results['center_time_ratio']
        imp_center = self.improved_results['center_time_ratio']
        center_change = (imp_center - orig_center) / max(orig_center, 0.001) * 100
        print(f"中央滞在時間比率: {orig_center:.2%} -> {imp_center:.2%} ({center_change:.1f}% 変化)")
        
        # 振動比率
        orig_vibration = self.original_results['vibration_ratio']
        imp_vibration = self.improved_results['vibration_ratio']
        vibration_change = (imp_vibration - orig_vibration) / max(orig_vibration, 0.001) * 100
        print(f"振動検出比率: {orig_vibration:.2%} -> {imp_vibration:.2%} ({vibration_change:.1f}% 変化)")
        
        # 敵回避率
        orig_avoidance = self.original_results['enemy_avoidance_rate']
        imp_avoidance = self.improved_results['enemy_avoidance_rate']
        avoidance_change = (imp_avoidance - orig_avoidance) / max(orig_avoidance, 0.001) * 100
        print(f"敵回避率: {orig_avoidance:.2%} -> {imp_avoidance:.2%} ({avoidance_change:.1f}% 変化)")
        
        # 中央からの平均距離
        orig_distance = self.original_results['average_distance_from_center']
        imp_distance = self.improved_results['average_distance_from_center']
        distance_change = (imp_distance - orig_distance) / max(orig_distance, 0.001) * 100
        print(f"中央からの平均距離: {orig_distance:.1f}px -> {imp_distance:.1f}px ({distance_change:.1f}% 変化)")
        
        # 問題パターン数
        orig_problems = len(self.original_results['problematic_patterns'])
        imp_problems = len(self.improved_results['problematic_patterns'])
        print(f"検出された問題パターン数: {orig_problems} -> {imp_problems}")
        
        # 問題パターンの詳細
        print("\n[オリジナル] 検出された問題パターン:")
        for i, pattern in enumerate(self.original_results['problematic_patterns']):
            print(f"{i+1}. {pattern['type']}: {pattern['description']}")
        
        print("\n[改善後] 検出された問題パターン:")
        for i, pattern in enumerate(self.improved_results['problematic_patterns']):
            print(f"{i+1}. {pattern['type']}: {pattern['description']}")
        
        # 改善評価
        self._evaluate_improvement()
        
        # グラフによる可視化
        self._generate_comparison_graphs()
    
    def _evaluate_improvement(self):
        """改善の評価を行い,総合的な評価を出力"""
        scores = []
        
        # 中央滞在時間の改善
        if self.original_results['center_time_ratio'] > 0.3:
            # 元の中央滞在率が高すぎる場合,減少していれば改善
            if self.improved_results['center_time_ratio'] < self.original_results['center_time_ratio']:
                score_center = min(10, (self.original_results['center_time_ratio'] - self.improved_results['center_time_ratio']) / self.original_results['center_time_ratio'] * 10)
                scores.append(score_center)
                print(f"中央滞在時間の改善: {score_center:.1f}/10")
            else:
                scores.append(0)
                print("中央滞在時間の改善: 0/10 (悪化または変化なし)")
        else:
            # 元の中央滞在率が適切な場合は10点
            scores.append(10)
            print("中央滞在時間は元から適切です: 10/10")
        
        # 振動の改善
        if self.improved_results['vibration_ratio'] < self.original_results['vibration_ratio']:
            score_vibration = min(10, (self.original_results['vibration_ratio'] - self.improved_results['vibration_ratio']) / max(self.original_results['vibration_ratio'], 0.001) * 10)
            scores.append(score_vibration)
            print(f"振動の改善: {score_vibration:.1f}/10")
        else:
            scores.append(0)
            print("振動の改善: 0/10 (悪化または変化なし)")
        
        # 敵回避率の改善
        if self.improved_results['enemy_avoidance_rate'] > self.original_results['enemy_avoidance_rate']:
            score_avoidance = min(10, (self.improved_results['enemy_avoidance_rate'] - self.original_results['enemy_avoidance_rate']) / (1 - self.original_results['enemy_avoidance_rate']) * 10)
            scores.append(score_avoidance)
            print(f"敵回避率の改善: {score_avoidance:.1f}/10")
        else:
            scores.append(0)
            print("敵回避率の改善: 0/10 (悪化または変化なし)")
        
        # 問題パターン数の改善
        orig_problems = len(self.original_results['problematic_patterns'])
        imp_problems = len(self.improved_results['problematic_patterns'])
        
        if imp_problems < orig_problems:
            score_problems = min(10, (orig_problems - imp_problems) / orig_problems * 10) if orig_problems > 0 else 5
            scores.append(score_problems)
            print(f"問題パターン数の改善: {score_problems:.1f}/10")
        else:
            scores.append(0)
            print("問題パターン数の改善: 0/10 (悪化または変化なし)")
        
        # 総合評価
        if scores:
            total_score = sum(scores) / len(scores)
            print(f"\n総合改善評価: {total_score:.1f}/10")
            
            if total_score >= 7:
                print("評価: 優れた改善が見られます！敵回避と中央での振動問題が大幅に改善されています.")
            elif total_score >= 5:
                print("評価: ある程度の改善が見られます.引き続き微調整が必要かもしれません.")
            elif total_score >= 3:
                print("評価: わずかな改善が見られますが,さらなる改良が必要です.")
            else:
                print("評価: 有意な改善は見られません.アルゴリズムの再検討が必要です.")
        else:
            print("\n総合評価: 評価できるデータが不足しています.")
    
    def _generate_comparison_graphs(self):
        """比較グラフを生成して保存"""
        try:
            # データの準備
            metrics = ['中央滞在比率', '振動検出比率', '敵回避率', '中央からの距離(px/100)']
            orig_values = [
                self.original_results['center_time_ratio'],
                self.original_results['vibration_ratio'],
                self.original_results['enemy_avoidance_rate'],
                self.original_results['average_distance_from_center'] / 100
            ]
            imp_values = [
                self.improved_results['center_time_ratio'],
                self.improved_results['vibration_ratio'],
                self.improved_results['enemy_avoidance_rate'],
                self.improved_results['average_distance_from_center'] / 100
            ]
            
            # バーグラフの作成
            x = np.arange(len(metrics))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(10, 6))
            rects1 = ax.bar(x - width/2, orig_values, width, label='オリジナル', color='lightcoral')
            rects2 = ax.bar(x + width/2, imp_values, width, label='改善後', color='lightgreen')
            
            # グラフの装飾
            ax.set_title('アドバタイズモード改善の比較')
            ax.set_ylabel('値')
            ax.set_xticks(x)
            ax.set_xticklabels(metrics)
            ax.legend()
            
            # 値のラベル表示
            def autolabel(rects):
                for rect in rects:
                    height = rect.get_height()
                    ax.annotate(f'{height:.2f}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom')
            
            autolabel(rects1)
            autolabel(rects2)
            
            fig.tight_layout()
            
            # グラフの保存
            plt.savefig(os.path.join(self.output_dir, "comparison_graph.png"))
            print(f"\nグラフを保存しました: {os.path.join(self.output_dir, 'comparison_graph.png')}")
            
            plt.close()
        except Exception as e:
            print(f"グラフ生成中にエラーが発生しました: {e}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='アドバタイズモードテスト')
    parser.add_argument('--module', default='main', help='メインモジュール名')
    parser.add_argument('--frames', type=int, default=300, help='テストするフレーム数（デフォルト: 300）')
    parser.add_argument('--output', default=None, help='出力ディレクトリ')
    parser.add_argument('--quick', action='store_true', help='クイックモード（短時間実行）')
    parser.add_argument('--demo', action='store_true', help='改善後のアドバタイズモードをデモ実行')
    parser.add_argument('--visual-demo', action='store_true', help='GUI表示でデモ実行')
    
    args = parser.parse_args()
    
    # デモモードの場合
    if args.demo:
        print("改善されたアドバタイズモードをデモ実行します...")
        improver = AdvertiseModeImprover(main_module_name=args.module)
        improver.apply_patches()
        
        if args.visual_demo:
            # GUI表示でのデモ実行
            improver.run_improved_advertise_mode(duration=30)
        else:
            # ヘッドレスモードでの解析実行
            monitor = AdvertiseModeMonitor(
                main_module_name=args.module,
                max_frames=600,  # 10秒間
                headless=True,
                show_progress=True
            )
            monitor.run_analysis()
        return
    
    # テストの実行
    test = AdvertiseModeTest(
        main_module_name=args.module,
        test_frames=args.frames,
        output_dir=args.output,
        quick_mode=args.quick
    )
    
    test.run_test()


if __name__ == '__main__':
    main() 