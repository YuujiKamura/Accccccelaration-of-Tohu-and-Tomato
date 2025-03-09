"""
テスト依存関係分析モジュール

このモジュールは,テスト間の依存関係を分析し,効率的なテスト実行順序を
導き出すための機能を提供します.
"""

import os
import sys
import json
import time
import inspect
import unittest
from tests.unit.test_base import BaseTestCase, log_test
import importlib
from collections import defaultdict
from pathlib import Path

# 遅延インポート用のフラグ
_HAS_NETWORKX = False
_HAS_MATPLOTLIB = False

class TestDependency:
    """テスト間の依存関係を分析するクラス"""
    
    def __init__(self, data_dir="test_dependency_data"):
        """
        初期化
        
        Args:
            data_dir: 依存関係データを保存するディレクトリ
        """
        self.data_dir = data_dir
        self.dependencies = {}
        self.test_graph = None
        
        # ディレクトリがなければ作成
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 依存関係データを読み込む
        self._load_dependencies()
    
    def _load_dependencies(self):
        """依存関係データを読み込む"""
        dependency_file = os.path.join(self.data_dir, 'test_dependencies.json')
        if os.path.exists(dependency_file):
            try:
                with open(dependency_file, 'r', encoding='utf-8') as f:
                    self.dependencies = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"依存関係データの読み込みに失敗しました: {e}")
                self.dependencies = {}
    
    def _save_dependencies(self):
        """依存関係データを保存する"""
        dependency_file = os.path.join(self.data_dir, 'test_dependencies.json')
        try:
            with open(dependency_file, 'w', encoding='utf-8') as f:
                json.dump(self.dependencies, f, indent=2)
        except IOError as e:
            print(f"依存関係データの保存に失敗しました: {e}")
    
    def add_dependency(self, test_name, depends_on):
        """
        テスト間の依存関係を追加する
        
        Args:
            test_name: 依存する側のテスト名
            depends_on: 依存される側のテスト名
        """
        if test_name not in self.dependencies:
            self.dependencies[test_name] = []
        
        if depends_on not in self.dependencies[test_name]:
            self.dependencies[test_name].append(depends_on)
        
        # データを保存
        self._save_dependencies()
    
    def remove_dependency(self, test_name, depends_on):
        """
        テスト間の依存関係を削除する
        
        Args:
            test_name: 依存する側のテスト名
            depends_on: 依存される側のテスト名
        """
        if test_name in self.dependencies and depends_on in self.dependencies[test_name]:
            self.dependencies[test_name].remove(depends_on)
            
            # 依存関係が空になった場合はキーを削除
            if not self.dependencies[test_name]:
                del self.dependencies[test_name]
            
            # データを保存
            self._save_dependencies()
    
    def get_dependencies(self, test_name):
        """
        テストの依存関係を取得する
        
        Args:
            test_name: テスト名
            
        Returns:
            list: 依存するテストのリスト
        """
        return self.dependencies.get(test_name, [])
    
    def analyze_module(self, module_name):
        """
        モジュール内のテスト間の依存関係を分析する
        
        Args:
            module_name: モジュール名
            
        Returns:
            dict: テスト名と依存するテストのリスト
        """
        try:
            # モジュールをインポート
            module = importlib.import_module(module_name)
            
            # テストクラスを探す
            test_classes = []
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                    test_classes.append(obj)
            
            dependencies = {}
            
            for test_class in test_classes:
                # テストメソッドを探す
                test_methods = []
                for name, method in inspect.getmembers(test_class, predicate=inspect.isfunction):
                    if name.startswith('test_'):
                        test_methods.append(name)
                
                # テストメソッドのソースコードを解析して依存関係を検出
                for method_name in test_methods:
                    test_name = f"{module_name}.{test_class.__name__}.{method_name}"
                    
                    # メソッドのソースコードを取得
                    method = getattr(test_class, method_name)
                    source = inspect.getsource(method)
                    
                    # 依存関係メタデータを探す
                    if '# depends_on:' in source:
                        for line in source.split('\n'):
                            if '# depends_on:' in line:
                                # 依存するテスト名を抽出
                                depends_on = line.split('# depends_on:')[1].strip()
                                
                                # 依存関係を追加
                                if test_name not in dependencies:
                                    dependencies[test_name] = []
                                
                                dependencies[test_name].append(depends_on)
                                self.add_dependency(test_name, depends_on)
            
            return dependencies
            
        except ImportError as e:
            print(f"モジュールのインポートに失敗しました: {e}")
            return {}
    
    def _ensure_networkx(self):
        """NetworkXライブラリが利用可能であることを確認する"""
        global _HAS_NETWORKX
        if not _HAS_NETWORKX:
            try:
                import networkx as nx
                globals()['nx'] = nx
                _HAS_NETWORKX = True
            except ImportError:
                print("NetworkXライブラリがインストールされていません。")
                print("pip install networkx でインストールしてください。")
                return False
        return True
    
    def build_dependency_graph(self):
        """
        依存関係グラフを構築する
        
        Returns:
            nx.DiGraph: 依存関係グラフ
        """
        if not self._ensure_networkx():
            return None
        
        # グラフを初期化
        self.test_graph = nx.DiGraph()
        
        # 依存関係をグラフに追加
        for test_name, deps in self.dependencies.items():
            for dep in deps:
                self.test_graph.add_edge(dep, test_name)
        
        return self.test_graph
    
    def get_execution_order(self):
        """
        依存関係に基づいて実行順序を取得する
        
        Returns:
            list: テストの実行順序
        """
        if not self._ensure_networkx():
            print("依存関係の解析に必要なNetworkXライブラリがありません。")
            # 依存関係が解析できないので、依存関係のキーの順序だけで返す
            return list(self.dependencies.keys())
        
        # 依存関係グラフを構築
        graph = self.build_dependency_graph()
        
        try:
            # トポロジカルソートで実行順序を取得
            execution_order = list(nx.topological_sort(graph))
            return execution_order
        except nx.NetworkXUnfeasible:
            # 循環依存がある場合
            print("警告: 循環依存が検出されました.一部の依存関係は無視されます.")
            
            # 循環依存を検出
            cycles = list(nx.simple_cycles(graph))
            for cycle in cycles:
                print(f"循環依存: {' -> '.join(cycle)}")
            
            # 循環依存を解消してトポロジカルソート
            acyclic_graph = nx.DiGraph(graph)
            for cycle in cycles:
                for i in range(len(cycle) - 1):
                    if acyclic_graph.has_edge(cycle[i], cycle[i+1]):
                        acyclic_graph.remove_edge(cycle[i], cycle[i+1])
            
            return list(nx.topological_sort(acyclic_graph))
    
    def get_affected_tests(self, test_name):
        """
        指定されたテストに影響を受けるテストを取得する
        
        Args:
            test_name: テスト名
            
        Returns:
            list: 影響を受けるテストのリスト
        """
        if not self._ensure_networkx():
            # NetworkXがない場合は単純な依存関係チェック
            affected = []
            for t, deps in self.dependencies.items():
                if test_name in deps:
                    affected.append(t)
            return affected
        
        # 依存関係グラフを構築
        graph = self.build_dependency_graph()
        
        if test_name not in graph:
            return []
        
        # 影響を受けるノードを探索（BFS）
        affected_tests = set()
        queue = [test_name]
        while queue:
            current = queue.pop(0)
            for successor in graph.successors(current):
                if successor not in affected_tests:
                    affected_tests.add(successor)
                    queue.append(successor)
        
        return list(affected_tests)
    
    def visualize_dependencies(self, output_file=None):
        """
        依存関係グラフを可視化する
        
        Args:
            output_file: 出力ファイル名（デフォルトは 'test_dependencies.png'）
        """
        if not self._ensure_networkx():
            print("依存関係の可視化に必要なNetworkXライブラリがありません。")
            return
        
        # matplotlibが利用可能か確認
        global _HAS_MATPLOTLIB
        if not _HAS_MATPLOTLIB:
            try:
                import matplotlib.pyplot as plt
                globals()['plt'] = plt
                _HAS_MATPLOTLIB = True
            except ImportError:
                print("matplotlibライブラリがインストールされていません。")
                print("pip install matplotlib でインストールしてください。")
                return
        
        # デフォルトの出力ファイル名
        if output_file is None:
            output_file = os.path.join(self.data_dir, 'test_dependencies.png')
        
        # 依存関係グラフを構築
        graph = self.build_dependency_graph()
        
        if not graph or len(graph.nodes()) == 0:
            print("依存関係グラフが空です。可視化するものがありません。")
            return
        
        # フォント設定
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'Liberation Sans', 'DejaVu Sans']
        
        # グラフのレイアウトを設定
        plt.figure(figsize=(12, 8))
        
        # ノードの位置を計算（階層的レイアウト）
        pos = nx.spring_layout(graph, k=0.3, iterations=50)
        
        # ノードを描画
        nx.draw_networkx_nodes(graph, pos, node_size=500, node_color='lightblue', alpha=0.8)
        
        # エッジを描画
        nx.draw_networkx_edges(graph, pos, width=1.0, alpha=0.5, arrows=True, arrowsize=15, arrowstyle='->')
        
        # ラベルを描画
        labels = {}
        for node in graph.nodes():
            # ノード名を短くする
            # モジュール名.クラス名.メソッド名 -> クラス名.メソッド名
            parts = node.split('.')
            if len(parts) >= 3:
                labels[node] = f"{parts[-2]}.{parts[-1]}"
            else:
                labels[node] = node
        
        nx.draw_networkx_labels(graph, pos, labels, font_size=8, font_family='sans-serif')
        
        # タイトルとグリッドを設定
        plt.title('テスト依存関係グラフ', fontsize=15)
        plt.axis('off')
        
        # グラフを保存
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"依存関係グラフを {output_file} に保存しました。")
    
    def analyze_all_modules(self, directory='.', pattern='test_*.py'):
        """
        指定されたディレクトリ内のすべてのテストモジュールを分析する
        
        Args:
            directory: テストファイルがあるディレクトリ
            pattern: モジュール名のパターン
            
        Returns:
            dict: すべての依存関係
        """
        all_dependencies = {}
        
        # モジュールファイルを探す
        module_files = list(Path(directory).glob(pattern))
        
        for module_file in module_files:
            # ファイル名からモジュール名を生成
            module_name = module_file.stem
            
            print(f"モジュール {module_name} を分析中...")
            
            # モジュールを分析
            dependencies = self.analyze_module(module_name)
            all_dependencies.update(dependencies)
        
        return all_dependencies
    
    def generate_report(self, output_file=None):
        """
        依存関係レポートを生成する
        
        Args:
            output_file: 出力ファイル名
            
        Returns:
            str: レポートファイルのパス
        """
        # 出力ファイル名
        if output_file is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.data_dir, f'dependency_report_{timestamp}.txt')
        
        # 実行順序を取得
        execution_order = self.get_execution_order()
        
        # 依存関係グラフを構築
        graph = self.build_dependency_graph()
        
        # 影響度を計算（より多くのテストに影響を与えるテストほど影響度が高い）
        impact_scores = {}
        for node in graph.nodes():
            # 影響を受けるテストの数
            affected_tests = self.get_affected_tests(node)
            impact_scores[node] = len(affected_tests)
        
        # 影響度でソート
        sorted_impact = sorted(impact_scores.items(), key=lambda x: x[1], reverse=True)
        
        # レポートを生成
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("===== テスト依存関係レポート =====\n")
            f.write(f"生成日時: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("推奨実行順序:\n")
            for i, test_name in enumerate(execution_order, 1):
                f.write(f"{i}. {test_name}\n")
            
            f.write("\n影響度の高いテスト:\n")
            for i, (test_name, impact) in enumerate(sorted_impact[:20], 1):
                f.write(f"{i}. {test_name} (影響するテスト数: {impact})\n")
            
            f.write("\n詳細な依存関係:\n")
            for test_name, deps in self.dependencies.items():
                f.write(f"{test_name} は以下に依存:\n")
                for dep in deps:
                    f.write(f"  - {dep}\n")
                f.write("\n")
        
        return output_file


def setup_test_dependencies(suite, dependency_analyzer):
    """
    テストスイートの依存関係を設定する
    
    Args:
        suite: テストスイート
        dependency_analyzer: TestDependency インスタンス
        
    Returns:
        unittest.TestSuite: 依存関係を考慮したテストスイート
    """
    # 依存関係に基づく実行順序を取得
    execution_order = dependency_analyzer.get_execution_order()
    
    # スイートからテストを取得
    tests = get_tests_from_suite(suite)
    
    # テスト名とテストのマッピングを作成
    test_map = {}
    for test in tests:
        test_name = get_test_name(test)
        test_map[test_name] = test
    
    # 実行順序に従ってテストを並べ替え
    ordered_suite = unittest.TestSuite()
    
    # 実行順序に含まれるテストを追加
    for test_name in execution_order:
        if test_name in test_map:
            ordered_suite.addTest(test_map[test_name])
    
    # 実行順序に含まれないテストを追加
    for test in tests:
        test_name = get_test_name(test)
        if test_name not in execution_order:
            ordered_suite.addTest(test)
    
    return ordered_suite


def get_test_name(test):
    """
    テストの完全な名前を取得する
    
    Args:
        test: テストケースまたはテストメソッド
        
    Returns:
        str: テスト名
    """
    if hasattr(test, '_testMethodName'):
        # TestCaseインスタンスの場合
        method_name = test._testMethodName
        cls_name = test.__class__.__name__
        module_name = test.__class__.__module__
        return f"{module_name}.{cls_name}.{method_name}"
    elif isinstance(test, type) and issubclass(test, unittest.TestCase):
        # TestCaseクラスの場合
        return f"{test.__module__}.{test.__name__}"
    else:
        # その他の場合
        return str(test)


def get_tests_from_suite(suite):
    """
    スイートからすべてのテストを取得する
    
    Args:
        suite: テストスイート
        
    Returns:
        list: テストのリスト
    """
    tests = []
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            # サブスイートの場合は再帰的に処理
            tests.extend(get_tests_from_suite(test))
        else:
            # テストケースの場合はリストに追加
            tests.append(test)
    return tests


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='テスト依存関係分析ツール')
    parser.add_argument('--analyze', type=str, help='モジュールを分析して依存関係を検出する')
    parser.add_argument('--analyze-all', action='store_true', help='すべてのテストモジュールを分析する')
    parser.add_argument('--visualize', action='store_true', help='依存関係グラフを可視化する')
    parser.add_argument('--report', action='store_true', help='依存関係レポートを生成する')
    parser.add_argument('--affected', type=str, help='指定されたテストに影響を受けるテストを表示する')
    parser.add_argument('--output', type=str, default=None, help='出力ファイル名')
    
    args = parser.parse_args()
    
    # 依存関係分析クラスを初期化
    dependency = TestDependency()
    
    if args.analyze:
        # モジュールを分析
        dependencies = dependency.analyze_module(args.analyze)
        print(f"\n===== モジュール {args.analyze} の依存関係 =====")
        for test_name, deps in dependencies.items():
            print(f"{test_name} は以下に依存:")
            for dep in deps:
                print(f"  - {dep}")
    
    elif args.analyze_all:
        # すべてのモジュールを分析
        all_dependencies = dependency.analyze_all_modules()
        print("\n===== すべてのモジュールの依存関係 =====")
        print(f"依存関係の総数: {sum(len(deps) for deps in all_dependencies.values())}")
    
    elif args.visualize:
        # 依存関係グラフを可視化
        dependency.visualize_dependencies(args.output)
    
    elif args.report:
        # 依存関係レポートを生成
        output_file = dependency.generate_report(args.output)
        print(f"依存関係レポートを生成しました: {os.path.abspath(output_file)}")
    
    elif args.affected:
        # 影響を受けるテストを表示
        affected_tests = dependency.get_affected_tests(args.affected)
        print(f"\n===== テスト {args.affected} の影響を受けるテスト =====")
        for i, test in enumerate(affected_tests, 1):
            print(f"{i}. {test}")
    
    else:
        parser.print_help() 