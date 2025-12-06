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

### 3-1. Playwrightブラウザのインストール

Playwrightを使用するため、ブラウザをインストールする必要があります：

```bash
playwright install chromium
```

### 4. 設定ファイルの作成

`env.example`をコピーして`.env`ファイルを作成し、認証情報を設定してください。

```bash
# Windows
copy env.example .env
# macOS/Linux
cp env.example .env
```

`.env`ファイルを編集して、TimeTreeの認証情報を設定：

```env
TIMETREE_EMAIL=your_email@example.com
TIMETREE_PASSWORD=your_password
```

## 使用方法

### 基本的な使用方法

```bash
python main.py
```

スクリプトを実行すると、ブラウザが自動的に起動し、TimeTreeにログインして今日以降のスケジュールを取得し、CSVファイルとして出力されます。

**注意**: 初回実行時、ブラウザが表示されます（デバッグ用）。ブラウザを非表示にする場合は、`.env`ファイルで`BROWSER_HEADLESS=True`に設定してください。

出力ファイル名の形式: `timetree_export_YYYYMMDD_HHMMSS.csv`

### 設定オプション

`.env`ファイルで以下の設定が可能です：

- `TIMETREE_EMAIL`: TimeTreeのメールアドレス（必須）
- `TIMETREE_PASSWORD`: TimeTreeのパスワード（必須）
- `TIMETREE_CALENDAR_ID`: 特定のカレンダーのみ取得する場合のカレンダーID（オプション）
- `BROWSER_HEADLESS`: ブラウザを非表示にする場合True（デフォルト: False、表示モード）
- `BROWSER_TIMEOUT`: ブラウザのタイムアウト時間（ミリ秒、デフォルト: 30000）
- `BROWSER_WAIT_TIME`: 要素待機時間（秒、デフォルト: 2）
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

現在の実装は、ブラウザ自動化（Playwright）を使用してTimeTreeのWebサイトからデータを取得する方式です。

### 実装上の注意点

1. **HTML構造への依存**: 実際のTimeTreeのWebサイトのHTML構造に合わせてセレクタを調整する必要がある可能性があります。
2. **デバッグモード**: 初回使用時や問題が発生した場合は、`BROWSER_HEADLESS=False`（デフォルト）でブラウザを表示し、動作を確認してください。
3. **利用規約**: TimeTreeの利用規約を遵守してください。過度なアクセスは避けてください。
4. **認証情報の管理**: `.env`ファイルには機密情報が含まれます。Gitにコミットしないよう注意してください。

### トラブルシューティング

- イベントが取得できない場合: `DEBUG_MODE=True`に設定すると、ページのHTMLが`debug_page.html`に保存されます。このファイルを確認して、実際のHTML構造に合わせてセレクタを調整してください。
- ログインに失敗する場合: ブラウザを表示モードにして、実際のログイン画面を確認してください。TimeTreeのログイン方法が変更されている可能性があります。

詳細は`SPEC.md`を参照してください。

## プロジェクト構成

```
TimeTreeExport/
├── main.py              # メインスクリプト
├── config.py            # 設定管理
├── timetree_scraper.py  # TimeTree ブラウザ自動化スクレイパー
├── timetree_api.py      # TimeTree APIアクセス（旧実装、未使用）
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
- [x] ブラウザ自動化によるTimeTreeアクセス実装
- [x] CSVエクスポート機能の実装
- [ ] 実際のTimeTree HTML構造に合わせたセレクタの調整
- [ ] エラーハンドリングの強化
- [ ] テストの実装

## ライセンス

（ライセンス情報を記載してください）

