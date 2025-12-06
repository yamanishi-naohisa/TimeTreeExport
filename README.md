# TimeTreeExport

TimeTreeから今日以降のスケジュールを取得し、CSV形式でエクスポートするPythonスクリプト

## 概要

このプロジェクトは、TimeTreeのカレンダーから今日以降のスケジュールを取得し、CSV形式でエクスポートするためのツールです。

## 機能

- TimeTreeのカレンダーから今日以降のスケジュールを取得
- 取得したスケジュールをCSV形式でエクスポート
- Excel互換のUTF-8（BOM付き）形式で出力

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/yamanishi-naohisa/TimeTreeExport.git
cd TimeTreeExport
```

### 2. 仮想環境の作成と有効化

```bash
# 仮想環境の作成（推奨）
python -m venv venv

# 仮想環境の有効化
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 設定ファイルの作成

`env.example`をコピーして`.env`ファイルを作成し、認証情報を設定してください。

```bash
# Windows
copy env.example .env
# macOS/Linux
cp env.example .env
```

`.env`ファイルを編集して、TimeTreeのAPIトークンを設定：

```env
TIMETREE_ACCESS_TOKEN=your_access_token_here
```

## 使用方法

### 基本的な使用方法

```bash
python main.py
```

スクリプトを実行すると、今日以降のスケジュールが取得され、CSVファイルとして出力されます。

出力ファイル名の形式: `timetree_export_YYYYMMDD_HHMMSS.csv`

### 設定オプション

`.env`ファイルで以下の設定が可能です：

- `TIMETREE_ACCESS_TOKEN`: TimeTree APIアクセストークン（必須）
- `TIMETREE_CALENDAR_ID`: 特定のカレンダーのみ取得する場合のカレンダーID（オプション）
- `OUTPUT_DIR`: CSVファイルの出力先ディレクトリ（デフォルト: カレントディレクトリ）
- `OUTPUT_FILENAME_PREFIX`: CSVファイル名のプレフィックス（デフォルト: timetree_export）
- `DEBUG_MODE`: デバッグモードの有効化（True/False）

## 出力CSVの形式

CSVファイルには以下の列が含まれます：

- 日付（YYYY-MM-DD）
- 開始時刻（HH:MM）
- 終了時刻（HH:MM）
- タイトル
- 場所
- 説明
- カレンダー名

## 注意事項

⚠️ **重要**: TimeTreeの公式APIは2023年12月22日で終了しています。

現在の実装は仮実装です。実際のTimeTreeへのアクセス方法に応じて、以下のいずれかの方法を検討してください：

1. 非公式APIの利用（利用可能な場合）
2. カレンダー同期機能（Googleカレンダーなど）経由での取得
3. エクスポート機能の利用
4. スクレイピング（利用規約に準拠する場合）

詳細は`SPEC.md`を参照してください。

## プロジェクト構成

```
TimeTreeExport/
├── main.py              # メインスクリプト
├── config.py            # 設定管理
├── timetree_api.py      # TimeTree APIアクセス
├── csv_exporter.py      # CSV出力処理
├── utils.py             # ユーティリティ関数
├── requirements.txt     # 依存パッケージ
├── env.example          # 設定ファイル例
├── SPEC.md              # 仕様書
└── README.md            # このファイル
```

## 開発状況

- [x] プロジェクト構造の作成
- [x] 仕様書の作成
- [x] 基本的なモジュール構造の実装
- [ ] TimeTree APIアクセス方法の確定
- [ ] 実際のAPIとの統合
- [ ] エラーハンドリングの強化
- [ ] テストの実装

## ライセンス

（ライセンス情報を記載してください）

