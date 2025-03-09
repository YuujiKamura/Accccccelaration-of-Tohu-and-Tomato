"""
アドバタイズモードのテスト結果可視化ツール

テスト結果やアドバタイズモードの行動パターンを視覚的に表示します。
グラフ、ヒートマップ、時系列分析などの可視化機能を提供します。
"""

import os
import sys
import json
import math
import argparse
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.colors import LinearSegmentedColormap

# パスの追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_test_results(results_dir):
    """
    指定したディレクトリからテスト結果を読み込む
    
    Args:
        results_dir: テスト結果が格納されているディレクトリパス
    
    Returns:
        dict: 読み込んだテスト結果のデータ
    """
    result_file = os.path.join(results_dir, 'test_results.json')
    if not os.path.exists(result_file):
        print(f"エラー: テスト結果ファイルが見つかりません: {result_file}")
        return None
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"エラー: テスト結果の読み込みに失敗しました: {e}")
        return None


def load_analysis_results(results_dir):
    """
    指定したディレクトリから分析結果を読み込む
    
    Args:
        results_dir: 分析結果が格納されているディレクトリパス
    
    Returns:
        list: 読み込んだ分析結果のデータリスト
    """
    analysis_files = []
    for file in os.listdir(results_dir):
        if file.startswith('analysis_') and file.endswith('.json'):
            analysis_files.append(os.path.join(results_dir, file))
    
    if not analysis_files:
        print(f"エラー: 分析結果ファイルが見つかりません: {results_dir}")
        return None
    
    analysis_results = []
    for file in analysis_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                analysis_results.append(json.load(f))
        except Exception as e:
            print(f"エラー: 分析結果の読み込みに失敗しました ({file}): {e}")
    
    return analysis_results


def load_benchmark_results(results_dir):
    """
    指定したディレクトリからベンチマーク結果を読み込む
    
    Args:
        results_dir: ベンチマーク結果が格納されているディレクトリパス
    
    Returns:
        list: 読み込んだベンチマーク結果のデータリスト
    """
    benchmark_files = []
    for file in os.listdir(results_dir):
        if file.startswith('benchmark_') and file.endswith('.json'):
            benchmark_files.append(os.path.join(results_dir, file))
    
    if not benchmark_files:
        print(f"エラー: ベンチマーク結果ファイルが見つかりません: {results_dir}")
        return None
    
    benchmark_results = []
    for file in benchmark_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                benchmark_results.append(json.load(f))
        except Exception as e:
            print(f"エラー: ベンチマーク結果の読み込みに失敗しました ({file}): {e}")
    
    return benchmark_results


def create_movement_heatmap(positions, title, output_file=None, resolution=(80, 60)):
    """
    位置データからヒートマップを作成
    
    Args:
        positions: 位置データのリスト [(x1, y1), (x2, y2), ...]
        title: ヒートマップのタイトル
        output_file: 保存先ファイルパス（Noneの場合は表示のみ）
        resolution: ヒートマップの解像度 (width, height)
    """
    # ヒートマップのサイズ設定
    width, height = 800, 600  # 画面サイズ
    grid_width, grid_height = resolution
    
    # ヒートマップデータの初期化
    heatmap_data = np.zeros((grid_height, grid_width))
    
    # 位置データからヒートマップデータを作成
    for x, y in positions:
        # 座標が範囲内かチェック
        if 0 <= x < width and 0 <= y < height:
            # 座標をグリッドインデックスに変換
            grid_x = min(int(x * grid_width / width), grid_width - 1)
            grid_y = min(int(y * grid_height / height), grid_height - 1)
            heatmap_data[grid_y, grid_x] += 1
    
    # 図の作成
    plt.figure(figsize=(10, 8))
    
    # カスタムカラーマップの作成（青から赤へのグラデーション）
    colors = [(0, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0), (1, 0, 0)]
    cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)
    
    # ヒートマップの描画
    plt.imshow(heatmap_data, cmap=cmap, interpolation='gaussian')
    plt.colorbar(label='滞在頻度')
    
    # タイトルと軸ラベルの設定
    plt.title(title)
    plt.xlabel('X座標')
    plt.ylabel('Y座標')
    
    # グリッド線の設定
    plt.grid(False)
    
    # 画面中央のマーク
    center_x = grid_width // 2
    center_y = grid_height // 2
    center_radius = min(grid_width, grid_height) // 10
    
    # 中央の円を描画（点線）
    circle = plt.Circle((center_x, center_y), center_radius, fill=False, linestyle='--', color='white')
    plt.gca().add_patch(circle)
    
    # 結果を保存または表示
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"ヒートマップを保存しました: {output_file}")
    else:
        plt.show()
    
    plt.close()


def create_trajectory_plot(positions, title, output_file=None):
    """
    位置データから軌跡プロットを作成
    
    Args:
        positions: 位置データのリスト [(x1, y1), (x2, y2), ...]
        title: プロットのタイトル
        output_file: 保存先ファイルパス（Noneの場合は表示のみ）
    """
    # データを配列に変換
    x_values = [pos[0] for pos in positions]
    y_values = [pos[1] for pos in positions]
    
    # 図の作成
    plt.figure(figsize=(10, 8))
    
    # 画面境界の設定
    plt.xlim(0, 800)
    plt.ylim(0, 600)
    
    # 軌跡の描画
    plt.plot(x_values, y_values, '-', linewidth=0.8, alpha=0.7)
    
    # 移動方向を示す矢印を追加
    arrow_interval = max(1, len(positions) // 20)  # 矢印の数
    for i in range(0, len(positions) - 1, arrow_interval):
        if i + 1 < len(positions):
            dx = positions[i+1][0] - positions[i][0]
            dy = positions[i+1][1] - positions[i][1]
            
            # 矢印の長さが十分にある場合のみ描画
            if math.sqrt(dx**2 + dy**2) > 5:
                plt.arrow(positions[i][0], positions[i][1], dx, dy, 
                         head_width=10, head_length=10, fc='blue', ec='blue', alpha=0.7)
    
    # 開始位置と終了位置をマーク
    plt.plot(x_values[0], y_values[0], 'go', markersize=8, label='開始位置')
    plt.plot(x_values[-1], y_values[-1], 'ro', markersize=8, label='終了位置')
    
    # タイトルと軸ラベルの設定
    plt.title(title)
    plt.xlabel('X座標')
    plt.ylabel('Y座標')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # 画面中央を円でマーク
    center_x, center_y = 400, 300
    center_circle = plt.Circle((center_x, center_y), 50, fill=False, linestyle='--', color='gray')
    plt.gca().add_patch(center_circle)
    
    # 結果を保存または表示
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"軌跡プロットを保存しました: {output_file}")
    else:
        plt.show()
    
    plt.close()


def create_comparison_plot(benchmark_result, title, output_file=None):
    """
    ベンチマーク結果から比較プロットを作成
    
    Args:
        benchmark_result: ベンチマーク結果データ
        title: プロットのタイトル
        output_file: 保存先ファイルパス（Noneの場合は表示のみ）
    """
    # データの取得
    original_positions = benchmark_result['original_positions']
    improved_positions = benchmark_result['improved_positions']
    
    # 元のデータと改善版データのx, y座標を抽出
    original_x = [pos[0] for pos in original_positions]
    original_y = [pos[1] for pos in original_positions]
    improved_x = [pos[0] for pos in improved_positions]
    improved_y = [pos[1] for pos in improved_positions]
    
    # 図の作成
    plt.figure(figsize=(12, 10))
    
    # 画面境界の設定
    plt.xlim(0, 800)
    plt.ylim(0, 600)
    
    # 元の軌跡をプロット
    plt.plot(original_x, original_y, 'b-', linewidth=1.0, alpha=0.7, label='オリジナル')
    
    # 改善版の軌跡をプロット
    plt.plot(improved_x, improved_y, 'r-', linewidth=1.0, alpha=0.7, label='改善版')
    
    # 開始位置をマーク
    plt.plot(original_x[0], original_y[0], 'bo', markersize=8)
    plt.plot(improved_x[0], improved_y[0], 'ro', markersize=8)
    
    # 画面中央を円でマーク
    center_x, center_y = 400, 300
    center_circle = plt.Circle((center_x, center_y), 50, fill=False, linestyle='--', color='gray')
    plt.gca().add_patch(center_circle)
    
    # タイトルと軸ラベルの設定
    plt.title(title)
    plt.xlabel('X座標')
    plt.ylabel('Y座標')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # 結果を保存または表示
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"比較プロットを保存しました: {output_file}")
    else:
        plt.show()
    
    plt.close()


def create_metrics_chart(analysis_results, title, output_file=None):
    """
    分析結果から評価指標チャートを作成
    
    Args:
        analysis_results: 分析結果データのリスト
        title: チャートのタイトル
        output_file: 保存先ファイルパス（Noneの場合は表示のみ）
    """
    if not analysis_results:
        print("エラー: 分析結果がありません")
        return
    
    # 評価指標を取得
    metrics = ['center_time_ratio', 'vibration_ratio', 'enemy_avoidance_rate']
    metric_labels = ['中央滞在率', '振動検出率', '敵回避率']
    
    # データを抽出
    values = []
    for metric in metrics:
        metric_values = [result.get(metric, 0) for result in analysis_results]
        values.append(np.mean(metric_values))  # 平均値を使用
    
    # チャートの作成
    plt.figure(figsize=(10, 6))
    
    # バーチャートの描画
    x = np.arange(len(metric_labels))
    bars = plt.bar(x, values, width=0.6)
    
    # バーの色を設定
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    for i, bar in enumerate(bars):
        bar.set_color(colors[i % len(colors)])
    
    # タイトルと軸ラベルの設定
    plt.title(title)
    plt.xlabel('評価指標')
    plt.ylabel('値')
    plt.ylim(0, 1.0)
    
    # X軸の目盛りラベルを設定
    plt.xticks(x, metric_labels)
    
    # 値のラベルを追加
    for i, v in enumerate(values):
        plt.text(i, v + 0.02, f'{v:.2%}', ha='center')
    
    # グリッド線の設定
    plt.grid(axis='y', alpha=0.3)
    
    # 結果を保存または表示
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"評価指標チャートを保存しました: {output_file}")
    else:
        plt.show()
    
    plt.close()


def visualize_test_results(results_dir, output_dir=None):
    """
    テスト結果を可視化
    
    Args:
        results_dir: テスト結果が格納されているディレクトリパス
        output_dir: 可視化結果の保存先ディレクトリ
    """
    # 出力ディレクトリの設定
    if not output_dir:
        output_dir = f"visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 出力ディレクトリが存在しない場合は作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 分析結果の読み込み
    analysis_results = load_analysis_results(results_dir)
    if analysis_results:
        # 評価指標チャートの作成
        metrics_chart_file = os.path.join(output_dir, 'metrics_chart.png')
        create_metrics_chart(analysis_results, 'アドバタイズモード評価指標', metrics_chart_file)
        
        # 最新の分析結果からヒートマップを作成
        latest_result = analysis_results[-1]
        if 'position_history' in latest_result:
            positions = latest_result['position_history']
            
            # ヒートマップの作成
            heatmap_file = os.path.join(output_dir, 'movement_heatmap.png')
            create_movement_heatmap(positions, 'アドバタイズモード移動ヒートマップ', heatmap_file)
            
            # 軌跡プロットの作成
            trajectory_file = os.path.join(output_dir, 'movement_trajectory.png')
            create_trajectory_plot(positions, 'アドバタイズモード移動軌跡', trajectory_file)
    
    # ベンチマーク結果の読み込み
    benchmark_results = load_benchmark_results(results_dir)
    if benchmark_results:
        for i, result in enumerate(benchmark_results):
            # 比較プロットの作成
            comparison_file = os.path.join(output_dir, f'comparison_plot_{i+1}.png')
            enemy_count = result.get('enemy_count', 'unknown')
            frames = result.get('frames', 'unknown')
            create_comparison_plot(result, f'オリジナルと改善版の比較 ({enemy_count}敵, {frames}フレーム)', comparison_file)
    
    print(f"可視化が完了しました。結果は {os.path.abspath(output_dir)} に保存されました。")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='アドバタイズモードのテスト結果可視化ツール')
    
    parser.add_argument('--results', '-r', type=str, required=True,
                        help='テスト結果が格納されているディレクトリパス')
    
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='可視化結果の保存先ディレクトリ（デフォルトは自動生成）')
    
    args = parser.parse_args()
    
    # 指定されたディレクトリが存在するか確認
    if not os.path.exists(args.results) or not os.path.isdir(args.results):
        print(f"エラー: 指定されたディレクトリが存在しません: {args.results}")
        return 1
    
    # テスト結果の可視化
    visualize_test_results(args.results, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 
アドバタイズモードのテスト結果可視化ツール

テスト結果やアドバタイズモードの行動パターンを視覚的に表示します。
グラフ、ヒートマップ、時系列分析などの可視化機能を提供します。
"""

import os
import sys
import json
import math
import argparse
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.colors import LinearSegmentedColormap

# パスの追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_test_results(results_dir):
    """
    指定したディレクトリからテスト結果を読み込む
    
    Args:
        results_dir: テスト結果が格納されているディレクトリパス
    
    Returns:
        dict: 読み込んだテスト結果のデータ
    """
    result_file = os.path.join(results_dir, 'test_results.json')
    if not os.path.exists(result_file):
        print(f"エラー: テスト結果ファイルが見つかりません: {result_file}")
        return None
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"エラー: テスト結果の読み込みに失敗しました: {e}")
        return None


def load_analysis_results(results_dir):
    """
    指定したディレクトリから分析結果を読み込む
    
    Args:
        results_dir: 分析結果が格納されているディレクトリパス
    
    Returns:
        list: 読み込んだ分析結果のデータリスト
    """
    analysis_files = []
    for file in os.listdir(results_dir):
        if file.startswith('analysis_') and file.endswith('.json'):
            analysis_files.append(os.path.join(results_dir, file))
    
    if not analysis_files:
        print(f"エラー: 分析結果ファイルが見つかりません: {results_dir}")
        return None
    
    analysis_results = []
    for file in analysis_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                analysis_results.append(json.load(f))
        except Exception as e:
            print(f"エラー: 分析結果の読み込みに失敗しました ({file}): {e}")
    
    return analysis_results


def load_benchmark_results(results_dir):
    """
    指定したディレクトリからベンチマーク結果を読み込む
    
    Args:
        results_dir: ベンチマーク結果が格納されているディレクトリパス
    
    Returns:
        list: 読み込んだベンチマーク結果のデータリスト
    """
    benchmark_files = []
    for file in os.listdir(results_dir):
        if file.startswith('benchmark_') and file.endswith('.json'):
            benchmark_files.append(os.path.join(results_dir, file))
    
    if not benchmark_files:
        print(f"エラー: ベンチマーク結果ファイルが見つかりません: {results_dir}")
        return None
    
    benchmark_results = []
    for file in benchmark_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                benchmark_results.append(json.load(f))
        except Exception as e:
            print(f"エラー: ベンチマーク結果の読み込みに失敗しました ({file}): {e}")
    
    return benchmark_results


def create_movement_heatmap(positions, title, output_file=None, resolution=(80, 60)):
    """
    位置データからヒートマップを作成
    
    Args:
        positions: 位置データのリスト [(x1, y1), (x2, y2), ...]
        title: ヒートマップのタイトル
        output_file: 保存先ファイルパス（Noneの場合は表示のみ）
        resolution: ヒートマップの解像度 (width, height)
    """
    # ヒートマップのサイズ設定
    width, height = 800, 600  # 画面サイズ
    grid_width, grid_height = resolution
    
    # ヒートマップデータの初期化
    heatmap_data = np.zeros((grid_height, grid_width))
    
    # 位置データからヒートマップデータを作成
    for x, y in positions:
        # 座標が範囲内かチェック
        if 0 <= x < width and 0 <= y < height:
            # 座標をグリッドインデックスに変換
            grid_x = min(int(x * grid_width / width), grid_width - 1)
            grid_y = min(int(y * grid_height / height), grid_height - 1)
            heatmap_data[grid_y, grid_x] += 1
    
    # 図の作成
    plt.figure(figsize=(10, 8))
    
    # カスタムカラーマップの作成（青から赤へのグラデーション）
    colors = [(0, 0, 1), (0, 1, 1), (0, 1, 0), (1, 1, 0), (1, 0, 0)]
    cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)
    
    # ヒートマップの描画
    plt.imshow(heatmap_data, cmap=cmap, interpolation='gaussian')
    plt.colorbar(label='滞在頻度')
    
    # タイトルと軸ラベルの設定
    plt.title(title)
    plt.xlabel('X座標')
    plt.ylabel('Y座標')
    
    # グリッド線の設定
    plt.grid(False)
    
    # 画面中央のマーク
    center_x = grid_width // 2
    center_y = grid_height // 2
    center_radius = min(grid_width, grid_height) // 10
    
    # 中央の円を描画（点線）
    circle = plt.Circle((center_x, center_y), center_radius, fill=False, linestyle='--', color='white')
    plt.gca().add_patch(circle)
    
    # 結果を保存または表示
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"ヒートマップを保存しました: {output_file}")
    else:
        plt.show()
    
    plt.close()


def create_trajectory_plot(positions, title, output_file=None):
    """
    位置データから軌跡プロットを作成
    
    Args:
        positions: 位置データのリスト [(x1, y1), (x2, y2), ...]
        title: プロットのタイトル
        output_file: 保存先ファイルパス（Noneの場合は表示のみ）
    """
    # データを配列に変換
    x_values = [pos[0] for pos in positions]
    y_values = [pos[1] for pos in positions]
    
    # 図の作成
    plt.figure(figsize=(10, 8))
    
    # 画面境界の設定
    plt.xlim(0, 800)
    plt.ylim(0, 600)
    
    # 軌跡の描画
    plt.plot(x_values, y_values, '-', linewidth=0.8, alpha=0.7)
    
    # 移動方向を示す矢印を追加
    arrow_interval = max(1, len(positions) // 20)  # 矢印の数
    for i in range(0, len(positions) - 1, arrow_interval):
        if i + 1 < len(positions):
            dx = positions[i+1][0] - positions[i][0]
            dy = positions[i+1][1] - positions[i][1]
            
            # 矢印の長さが十分にある場合のみ描画
            if math.sqrt(dx**2 + dy**2) > 5:
                plt.arrow(positions[i][0], positions[i][1], dx, dy, 
                         head_width=10, head_length=10, fc='blue', ec='blue', alpha=0.7)
    
    # 開始位置と終了位置をマーク
    plt.plot(x_values[0], y_values[0], 'go', markersize=8, label='開始位置')
    plt.plot(x_values[-1], y_values[-1], 'ro', markersize=8, label='終了位置')
    
    # タイトルと軸ラベルの設定
    plt.title(title)
    plt.xlabel('X座標')
    plt.ylabel('Y座標')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # 画面中央を円でマーク
    center_x, center_y = 400, 300
    center_circle = plt.Circle((center_x, center_y), 50, fill=False, linestyle='--', color='gray')
    plt.gca().add_patch(center_circle)
    
    # 結果を保存または表示
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"軌跡プロットを保存しました: {output_file}")
    else:
        plt.show()
    
    plt.close()


def create_comparison_plot(benchmark_result, title, output_file=None):
    """
    ベンチマーク結果から比較プロットを作成
    
    Args:
        benchmark_result: ベンチマーク結果データ
        title: プロットのタイトル
        output_file: 保存先ファイルパス（Noneの場合は表示のみ）
    """
    # データの取得
    original_positions = benchmark_result['original_positions']
    improved_positions = benchmark_result['improved_positions']
    
    # 元のデータと改善版データのx, y座標を抽出
    original_x = [pos[0] for pos in original_positions]
    original_y = [pos[1] for pos in original_positions]
    improved_x = [pos[0] for pos in improved_positions]
    improved_y = [pos[1] for pos in improved_positions]
    
    # 図の作成
    plt.figure(figsize=(12, 10))
    
    # 画面境界の設定
    plt.xlim(0, 800)
    plt.ylim(0, 600)
    
    # 元の軌跡をプロット
    plt.plot(original_x, original_y, 'b-', linewidth=1.0, alpha=0.7, label='オリジナル')
    
    # 改善版の軌跡をプロット
    plt.plot(improved_x, improved_y, 'r-', linewidth=1.0, alpha=0.7, label='改善版')
    
    # 開始位置をマーク
    plt.plot(original_x[0], original_y[0], 'bo', markersize=8)
    plt.plot(improved_x[0], improved_y[0], 'ro', markersize=8)
    
    # 画面中央を円でマーク
    center_x, center_y = 400, 300
    center_circle = plt.Circle((center_x, center_y), 50, fill=False, linestyle='--', color='gray')
    plt.gca().add_patch(center_circle)
    
    # タイトルと軸ラベルの設定
    plt.title(title)
    plt.xlabel('X座標')
    plt.ylabel('Y座標')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # 結果を保存または表示
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"比較プロットを保存しました: {output_file}")
    else:
        plt.show()
    
    plt.close()


def create_metrics_chart(analysis_results, title, output_file=None):
    """
    分析結果から評価指標チャートを作成
    
    Args:
        analysis_results: 分析結果データのリスト
        title: チャートのタイトル
        output_file: 保存先ファイルパス（Noneの場合は表示のみ）
    """
    if not analysis_results:
        print("エラー: 分析結果がありません")
        return
    
    # 評価指標を取得
    metrics = ['center_time_ratio', 'vibration_ratio', 'enemy_avoidance_rate']
    metric_labels = ['中央滞在率', '振動検出率', '敵回避率']
    
    # データを抽出
    values = []
    for metric in metrics:
        metric_values = [result.get(metric, 0) for result in analysis_results]
        values.append(np.mean(metric_values))  # 平均値を使用
    
    # チャートの作成
    plt.figure(figsize=(10, 6))
    
    # バーチャートの描画
    x = np.arange(len(metric_labels))
    bars = plt.bar(x, values, width=0.6)
    
    # バーの色を設定
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    for i, bar in enumerate(bars):
        bar.set_color(colors[i % len(colors)])
    
    # タイトルと軸ラベルの設定
    plt.title(title)
    plt.xlabel('評価指標')
    plt.ylabel('値')
    plt.ylim(0, 1.0)
    
    # X軸の目盛りラベルを設定
    plt.xticks(x, metric_labels)
    
    # 値のラベルを追加
    for i, v in enumerate(values):
        plt.text(i, v + 0.02, f'{v:.2%}', ha='center')
    
    # グリッド線の設定
    plt.grid(axis='y', alpha=0.3)
    
    # 結果を保存または表示
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"評価指標チャートを保存しました: {output_file}")
    else:
        plt.show()
    
    plt.close()


def visualize_test_results(results_dir, output_dir=None):
    """
    テスト結果を可視化
    
    Args:
        results_dir: テスト結果が格納されているディレクトリパス
        output_dir: 可視化結果の保存先ディレクトリ
    """
    # 出力ディレクトリの設定
    if not output_dir:
        output_dir = f"visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 出力ディレクトリが存在しない場合は作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 分析結果の読み込み
    analysis_results = load_analysis_results(results_dir)
    if analysis_results:
        # 評価指標チャートの作成
        metrics_chart_file = os.path.join(output_dir, 'metrics_chart.png')
        create_metrics_chart(analysis_results, 'アドバタイズモード評価指標', metrics_chart_file)
        
        # 最新の分析結果からヒートマップを作成
        latest_result = analysis_results[-1]
        if 'position_history' in latest_result:
            positions = latest_result['position_history']
            
            # ヒートマップの作成
            heatmap_file = os.path.join(output_dir, 'movement_heatmap.png')
            create_movement_heatmap(positions, 'アドバタイズモード移動ヒートマップ', heatmap_file)
            
            # 軌跡プロットの作成
            trajectory_file = os.path.join(output_dir, 'movement_trajectory.png')
            create_trajectory_plot(positions, 'アドバタイズモード移動軌跡', trajectory_file)
    
    # ベンチマーク結果の読み込み
    benchmark_results = load_benchmark_results(results_dir)
    if benchmark_results:
        for i, result in enumerate(benchmark_results):
            # 比較プロットの作成
            comparison_file = os.path.join(output_dir, f'comparison_plot_{i+1}.png')
            enemy_count = result.get('enemy_count', 'unknown')
            frames = result.get('frames', 'unknown')
            create_comparison_plot(result, f'オリジナルと改善版の比較 ({enemy_count}敵, {frames}フレーム)', comparison_file)
    
    print(f"可視化が完了しました。結果は {os.path.abspath(output_dir)} に保存されました。")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='アドバタイズモードのテスト結果可視化ツール')
    
    parser.add_argument('--results', '-r', type=str, required=True,
                        help='テスト結果が格納されているディレクトリパス')
    
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='可視化結果の保存先ディレクトリ（デフォルトは自動生成）')
    
    args = parser.parse_args()
    
    # 指定されたディレクトリが存在するか確認
    if not os.path.exists(args.results) or not os.path.isdir(args.results):
        print(f"エラー: 指定されたディレクトリが存在しません: {args.results}")
        return 1
    
    # テスト結果の可視化
    visualize_test_results(args.results, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 