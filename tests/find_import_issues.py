#!/usr/bin/env python
"""
インポートの問題と循環参照を検出するスクリプト

テストコードのインポートパスや循環参照を検出し、高負荷問題の原因を特定します。
"""

import os
import sys
import re
import time
from collections import defaultdict
import importlib
import ast
import traceback

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_root)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# test_logger.pyをインポート
try:
    from tests.unit.test_logger import get_logger, LogLevel, check_performance_issues, PerformanceMonitor
    logger = get_logger(log_level=LogLevel.INFO)
except ImportError:
    print("警告: tests.unit.test_loggerのインポートに失敗しました。基本ロガーを使用します。")
    
    # 簡易ロガー
    class SimpleLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARNING] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
        def debug(self, msg): print(f"[DEBUG] {msg}")
    
    logger = SimpleLogger()
    
    def check_performance_issues():
        return ["警告: 詳細なパフォーマンスチェックができません。test_logger.pyが見つかりません。"]
    
    class PerformanceMonitor:
        def start_monitoring(self): pass
        def stop_monitoring(self): return {'elapsed_time': 0}

class ImportAnalyzer:
    """インポートパスと循環参照を分析するクラス"""
    
    def __init__(self, root_dir=None):
        """
        初期化
        
        Args:
            root_dir: 分析対象のルートディレクトリ（省略時は現在のディレクトリ）
        """
        self.root_dir = root_dir or os.path.dirname(os.path.abspath(__file__))
        self.modules = {}
        self.import_graph = defaultdict(set)
        self.duplicate_code = {}
        self.class_definitions = {}
    
    def find_py_files(self):
        """Pythonファイルを検索"""
        py_files = []
        
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
        
        return py_files
    
    def _extract_module_name(self, filepath):
        """ファイルパスからモジュール名を抽出"""
        rel_path = os.path.relpath(filepath, os.path.dirname(self.root_dir))
        module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
        return module_path
    
    def parse_imports(self, filepath):
        """ファイル内のインポート文を解析"""
        imports = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module
                    if module:
                        imports.append(module)
        except Exception as e:
            logger.error(f"ファイル {filepath} の解析中にエラー: {str(e)}")
        
        return imports
    
    def find_circular_imports(self):
        """循環インポートを検出"""
        circular_imports = []
        
        def dfs(node, path=None):
            if path is None:
                path = []
            
            if node in path:
                cycle = path[path.index(node):] + [node]
                circular_imports.append(" -> ".join(cycle))
                return
            
            for neighbor in self.import_graph.get(node, []):
                dfs(neighbor, path + [node])
        
        for node in self.import_graph:
            dfs(node)
        
        return list(set(circular_imports))
    
    def check_duplicate_code(self, filepath):
        """ファイル内の重複コードを検出"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            chunks = {}
            duplicate_count = 0
            
            # 4行チャンクを使用して重複を検出
            for i in range(len(lines) - 3):
                chunk = '\n'.join(lines[i:i+4])
                if len(chunk.strip()) > 20:  # 意味のある重複だけカウント
                    if chunk in chunks:
                        chunks[chunk] += 1
                        duplicate_count += 1
                    else:
                        chunks[chunk] = 1
            
            # 重複クラスを検出
            class_pattern = r"class\s+(\w+)"
            classes = {}
            
            for match in re.finditer(class_pattern, content):
                class_name = match.group(1)
                if class_name in classes:
                    classes[class_name] += 1
                else:
                    classes[class_name] = 1
            
            duplicate_classes = {name: count for name, count in classes.items() if count > 1}
            
            return {
                'duplicate_chunks': duplicate_count,
                'duplicate_classes': duplicate_classes,
                'file_size': len(content)
            }
            
        except Exception as e:
            logger.error(f"ファイル {filepath} の重複チェック中にエラー: {str(e)}")
            return {
                'duplicate_chunks': 0,
                'duplicate_classes': {},
                'file_size': 0
            }
    
    def analyze(self):
        """コードベースの分析を実行"""
        logger.info(f"インポート分析を開始: {self.root_dir}")
        
        py_files = self.find_py_files()
        logger.info(f"{len(py_files)}個のPythonファイルを検出")
        
        # インポートとモジュールの解析
        for filepath in py_files:
            module_name = self._extract_module_name(filepath)
            self.modules[module_name] = filepath
            
            imports = self.parse_imports(filepath)
            for imp in imports:
                if imp in self.modules or imp.startswith('tests.'):
                    self.import_graph[module_name].add(imp)
            
            # 重複コード分析
            duplicates = self.check_duplicate_code(filepath)
            self.duplicate_code[module_name] = duplicates
        
        # 循環インポートの検出
        circular_imports = self.find_circular_imports()
        
        # 大きなファイルと重複の多いファイルを特定
        large_files = [(name, data['file_size']) 
                      for name, data in self.duplicate_code.items() 
                      if data['file_size'] > 30000]  # 30KB超
        
        duplicate_heavy = [(name, data['duplicate_chunks']) 
                          for name, data in self.duplicate_code.items() 
                          if data['duplicate_chunks'] > 100]  # 100ブロック以上の重複
        
        duplicate_classes = [(name, cls, count) 
                            for name, data in self.duplicate_code.items() 
                            for cls, count in data['duplicate_classes'].items()]
        
        # 結果を返す
        return {
            'circular_imports': circular_imports,
            'large_files': large_files,
            'duplicate_heavy': duplicate_heavy,
            'duplicate_classes': duplicate_classes,
            'total_files': len(py_files)
        }

def main():
    """メイン実行関数"""
    print("=" * 80)
    print("インポート問題と高負荷原因の分析を開始")
    print("=" * 80)
    
    # パフォーマンスモニタリング開始
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # インポート分析
    analyzer = ImportAnalyzer()
    results = analyzer.analyze()
    
    # パフォーマンス問題の検出
    issues = check_performance_issues()
    
    # 結果表示
    print("\n" + "=" * 80)
    print("分析結果のサマリー")
    print("=" * 80)
    
    print(f"検出されたPythonファイル: {results['total_files']}")
    
    if results['circular_imports']:
        print("\n循環インポート検出:")
        for cycle in results['circular_imports']:
            print(f"  {cycle}")
    else:
        print("\n循環インポートはありません")
    
    if results['large_files']:
        print("\n大きなファイル:")
        for name, size in sorted(results['large_files'], key=lambda x: x[1], reverse=True):
            print(f"  {name}: {size/1024:.1f}KB")
    
    if results['duplicate_heavy']:
        print("\n重複コードが多いファイル:")
        for name, count in sorted(results['duplicate_heavy'], key=lambda x: x[1], reverse=True):
            print(f"  {name}: {count}ブロックの重複")
    
    if results['duplicate_classes']:
        print("\n重複クラス定義:")
        for name, cls, count in results['duplicate_classes']:
            print(f"  {name}: クラス'{cls}'が{count}回定義されています")
    
    print("\nその他のパフォーマンス問題:")
    for issue in issues:
        print(f"  {issue}")
    
    # モニタリング結果
    perf_results = monitor.stop_monitoring()
    print("\nパフォーマンスモニタリング結果:")
    print(f"  実行時間: {perf_results.get('elapsed_time', 0):.2f}秒")
    
    mem_usage = perf_results.get('memory_usage')
    if mem_usage:
        print(f"  メモリ使用: {mem_usage['start']:.1f}MB -> {mem_usage['end']:.1f}MB (差分: {mem_usage['diff']:.1f}MB)")
    
    cpu_usage = perf_results.get('cpu_usage')
    if cpu_usage:
        print(f"  CPU使用率: 平均 {cpu_usage['avg']:.1f}%")
    
    print("\n推奨アクション:")
    actions = []
    
    if results['circular_imports']:
        actions.append("循環インポートを解決し、一方向の依存関係に変更する")
    
    if results['duplicate_classes']:
        actions.append("重複クラス定義を削除し、単一の定義を共有する")
    
    if results['duplicate_heavy']:
        actions.append("重複コードを関数やユーティリティクラスに抽出する")
    
    if results['large_files']:
        actions.append("大きなファイルを複数の小さなファイルに分割する")
    
    if not actions:
        actions.append("コードの品質は良好です。問題は検出されませんでした。")
    
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action}")
    
    print("=" * 80)

if __name__ == "__main__":
    main() 