# テストディレクトリ

このディレクトリには、アプリケーションのテスト関連のすべてのファイルが含まれています。

## 構造

- `unit/` - ユニットテスト
  - 個々のコンポーネントを独立してテスト
  - 例: `test_beam_rifle.py`, `test_dash_motion.py` など
  - 各ユニットの機能が仕様通りに動作することを検証

- `integration/` - 統合テスト
  - 複数のコンポーネントの連携をテスト
  - 例: プレイヤーと敵の相互作用、武器と当たり判定など
  - 複数の機能が連携して期待通りに動作することを検証
  - テスト結果やベンチマーク結果のデータを保存

- `scripts/` - テスト実行スクリプト
  - `run_single_test.py` - 単一テスト実行
  - `watch_tests.py` - ファイル変更監視
  - `run_enhanced_tests.py` - 拡張テスト実行
  - `run_auto_tests.py` - 自動テスト実行
  - `utility/` - ユーティリティスクリプト
    - `fix_imports.py` - インポート問題修正
    - `find_import_issues.py` - インポート問題検出
    - `project_reorganizer.py` - プロジェクト整理
  - `batch/` - バッチ処理ファイル

- `tools/` - テスト関連ツール
  - `analysis/` - テスト分析ツール
    - `test_report.py` - テスト結果レポート生成
    - `performance_analyzer.py` - パフォーマンス分析
  - `development/` - 開発補助ツール
    - `autonomous_test_engine.py` - 自動テスト実行エンジン
  - `advertise_mode/` - デモモード分析・改善ツール

- `helpers/` - テスト補助機能
  - モックオブジェクト
    - Pygameのモッキング
    - 外部リソースのモッキング
  - テストデータ生成
    - テスト用データの作成
  - アサーションヘルパー
    - 複雑な条件の検証を簡単にするヘルパー

- `run.py` - メインテスト実行スクリプト
  - すべてのテストの実行
  - 特定のテストの選択的実行
  - 監視モードでの実行

## 使い方

### テスト実行方法

#### 単一のテストを実行

特定のテストモジュールを実行：
```
python -m tests.run unit.test_beam_rifle
```

特定のテストクラスを実行：
```
python -m tests.run unit.test_beam_rifle.TestBeamRifle
```

特定のテストメソッドを実行：
```
python -m tests.run unit.test_beam_rifle.TestBeamRifle.test_single_shot
```

#### すべてのテストを実行

```
python -m tests.run
```

#### 監視モードでテストを実行

ファイルの変更を監視して自動的にテストを実行します：

```
python -m tests.run --watch unit
```

#### 詳細オプション

より詳細なオプションを確認：

```
python -m tests.run --help
```

実行結果を表示する詳細度の設定：
```
python -m tests.run --verbose 2  # 詳細なログを表示
python -m tests.run --quiet      # 最小限の情報のみ表示
```

### テストの作成

#### 新しいユニットテストの作成

1. `tests/unit/` ディレクトリに `test_機能名.py` ファイルを作成
2. `BaseTestCase` クラスを継承したテストクラスを定義
3. テストメソッドを作成（名前は `test_` で始める）

例：
```python
from tests.unit.test_base import BaseTestCase

class TestNewFeature(BaseTestCase):
    def setUp(self):
        super().setUp()
        # テスト固有の初期化
        
    def test_something(self):
        # テストコード
        self.assertEqual(expected, actual)
```

#### テストロガーの使用

テスト実行中のログを記録するには：

```python
from tests.unit.test_logger import TestLogger

logger = TestLogger()
logger.info("テスト情報")
logger.debug("デバッグ情報")
logger.warning("警告")
```

### テストパフォーマンスの最適化

- 重いテストは `@unittest.skip` または `@unittest.skipIf` で必要に応じてスキップ
- テストフィクスチャを再利用して初期化コストを削減
- パフォーマンス計測ツールを使用して遅いテストを特定

### テスト関連問題のトラブルシューティング

- テストが遅い場合：
  - モックオブジェクトを活用して外部依存を削減
  - `tests/tools/analysis/performance_analyzer.py` を使用して問題を特定

- テストが不安定な場合：
  - タイミング依存のテストには適切な待機時間を設定
  - 乱数を使用する場合はシードを固定

- その他の問題：
  - テストログを詳細に設定して動作を確認
  - `tests/scripts/utility/find_import_issues.py` を実行して循環参照などの問題を検出 