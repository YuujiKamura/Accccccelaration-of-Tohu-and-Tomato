# アクセラレーションオブ豆腐 (Acceleration of Tofu)

豆腐を操作して敵を倒す、Pythonで作られた2Dシューティングゲームです。

## 機能

- 2Dシューティングゲームプレイ
- 自動プレイ（アドバタイズモード）
- 収益化モード - [詳細](README_monetization.md)
- デバッグモード（スクリーンショット解析機能付き）

## 必要条件

- Python 3.7+
- pygame
- OpenCV (cv2)
- pyautogui
- numpy
- requests
- pywin32 (Windowsの場合)

## インストール方法

```bash
# リポジトリをクローン
git clone https://github.com/ユーザー名/acceleration-of-tofu.git
cd acceleration-of-tofu

# 依存パッケージをインストール
pip install -r requirements.txt
```

## 使い方

基本的な起動：
```bash
python run_game.py
```

デバッグモードで起動：
```bash
python run_game.py --debug
```

収益化モードで起動：
```bash
python run_game.py --monetize --monetize-hours 8.0 --monetize-rate 0.5
```

## ゲームコントロール

- **矢印キー**: 移動
- **Z**: 通常ショット
- **X**: チャージショット
- **SHIFT**: ダッシュ
- **ESC/P**: ポーズ
- **F1**: アドバタイズモード切り替え
- **F2**: 収益化モード切り替え
- **F12**: デバッグモード切り替え

## 収益化モード

睡眠中や離席中でも自動的にゲームがプレイされ、獲得スコアに応じて仮想通貨コインを獲得できる機能です。
詳細は[README_monetization.md](README_monetization.md)を参照してください。

## 実行方法

```
python run_game.py
```

または直接メインファイルを実行：

```
python main.py
```

デバッグ用の実行方法：

```
python -m src.game.core.main
```

## プロジェクト構造

プロジェクトは以下のような構造になっています：

### メインファイル
- `main.py` - ゲームのメインスクリプト
- `run_game.py` - ゲーム起動用の簡易スクリプト

### ソースコード
- `src/` - ソースコードディレクトリ
  - `game/` - ゲーム関連コード
    - `core/` - コア機能（プレイヤー、敵、弾など）
    - `ui/` - ユーザーインターフェース
    - `utils/` - ゲーム特有のユーティリティ関数
  - `common/` - 共通機能

### テスト
- `tests/` - テストコード
  - `unit/` - ユニットテスト
    - 個々のコンポーネントを独立してテスト
    - 例: `test_beam_rifle.py`, `test_dash_motion.py` など
  - `integration/` - 統合テスト
    - 複数のコンポーネントの連携をテスト
    - テスト結果とベンチマーク結果
  - `tools/` - テスト関連ツール
    - `analysis/` - パフォーマンス分析ツール
    - `development/` - 開発補助ツール
    - `advertise_mode/` - デモモード分析・改善ツール
  - `scripts/` - テスト実行スクリプト
    - `batch/` - バッチファイル
    - `utility/` - ユーティリティスクリプト
  - `helpers/` - テスト補助機能
    - モックオブジェクト
    - テストデータ生成
    - アサーションヘルパー
  - `run.py` - 統合テスト実行スクリプト

### ビルド
- `build/` - ビルド出力ディレクトリ
  - `web/` - Webブラウザ用ビルド
    - `index.html` - Webエントリーポイント
  - `version.txt` - ビルドバージョン情報

### デモモード開発
- `advertise_mode/` - デモモード開発ツール
  - `analyzer/` - デモモード分析
  - `core/` - デモモードコア機能
  - `tests/` - デモモードテスト
  - `analyzer.py` - 分析スクリプト
  - `improver.py` - 改善スクリプト

### ドキュメント
- `docs/` - ドキュメント
  - `architecture/` - アーキテクチャ図やドキュメント
  - `usage/` - 使用方法や機能説明

## テストの実行

### シンプルな実行方法

すべてのテストを実行：
```
python -m tests.run
```

特定のテストを実行：
```
python -m tests.run unit.test_beam_rifle
```

ファイル変更を監視して自動テスト実行：
```
python -m tests.run --watch unit
```

### 詳細な実行方法

より詳細なテスト実行オプションについては、テストREADMEを参照してください：
```
more tests/README.md
```

## プロジェクトの歴史と機能

このプロジェクトは、「アクセラレーションオブ豆腐」というシンプルなシューティングゲームを開発するために作成されました。
主な機能として、プレイヤーの移動、ダッシュ、ビームライフル、チャージレーザーなどがあります。

### 主要機能
- プレイヤー移動とダッシュ機能
- ビームライフルによる敵への攻撃
- チャージレーザーによる強力な一撃
- 敵の自動生成と難易度調整
- デモモード（アドバタイズモード）による自動プレイ 