# アドバタイズモードパッケージ

このパッケージは、ゲームのアドバタイズモード（自動デモプレイ）の機能を提供します。
プレイヤーが操作していない間に自動的にゲームをプレイするAIシステムです。

## 機能

- **自動移動**: 敵を回避しながら画面全体を効果的に使った動きを実現
- **戦略的行動**: 状況に応じて複数の戦略を切り替え、予測不能な動きを実現
- **分析ツール**: アドバタイズモードの動作を分析し、問題点を検出
- **改善機能**: 分析結果に基づいて動作を自動的に改善

## ディレクトリ構造

```
advertise_mode/
├── core/               # コア機能
│   ├── __init__.py
│   └── improver.py     # 改善ツール
├── analyzer/           # 分析ツール
│   ├── __init__.py
│   ├── analyzer.py     # 分析エンジン
│   └── monitor.py      # モニタリングツール
├── tests/              # テスト
│   ├── __init__.py
│   ├── unit_tests/     # 単体テスト
│   └── integration_tests/ # 統合テスト
├── __init__.py
├── run_tests.py        # テスト実行スクリプト
└── README.md           # このファイル
```

## 使い方

### テストの実行

```bash
# 単体テストの実行
python -m advertise_mode.run_tests test --type unit

# 統合テストの実行
python -m advertise_mode.run_tests test --type integration

# ベンチマークテストの実行
python -m advertise_mode.run_tests test --benchmark
```

### 分析と改善

```bash
# アドバタイズモードの動作を分析
python -m advertise_mode.run_tests analyze

# 改善パッチを適用
python -m advertise_mode.run_tests improve

# 分析・改善・再分析を一括実行
python -m advertise_mode.run_tests full
```

### バッチファイルを使用する場合

プロジェクトルートにある `run_advertise_tests.bat` を実行すると、メニューから各機能を選択できます。

## 開発者向け情報

### 新しいテストの追加

1. 単体テストは `tests/unit_tests/` ディレクトリに追加します。
2. 統合テストは `tests/integration_tests/` ディレクトリに追加します。
3. テストファイル名は `test_*.py` の形式にしてください。

### 改善アルゴリズムの拡張

`core/improver.py` の `AdvertiseModeImprover` クラスに新しい戦略や改善アルゴリズムを追加できます。

### 分析機能の拡張

`analyzer/analyzer.py` の `AdvertiseModeAnalyzer` クラスに新しい分析指標や可視化機能を追加できます。 