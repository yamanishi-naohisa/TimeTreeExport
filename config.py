"""
設定管理モジュール
環境変数から設定を読み込む
"""
import os
from dotenv import load_dotenv
from datetime import datetime

# .envファイルを読み込む
load_dotenv()

# TimeTree 認証設定
TIMETREE_EMAIL = os.getenv("TIMETREE_EMAIL", "")
TIMETREE_PASSWORD = os.getenv("TIMETREE_PASSWORD", "")
TIMETREE_CALENDAR_ID = os.getenv("TIMETREE_CALENDAR_ID", "")

# TimeTree Web設定
TIMETREE_BASE_URL = os.getenv("TIMETREE_BASE_URL", "https://timetreeapp.com")

# 出力設定
OUTPUT_DIR = os.getenv("OUTPUT_DIR", ".")
OUTPUT_FILENAME_PREFIX = os.getenv("OUTPUT_FILENAME_PREFIX", "timetree_export")
CSV_ENCODING = "utf-8-sig"  # Excel互換性のためBOM付きUTF-8

# フィルタ設定
FILTER_FROM_TODAY = True  # 今日以降のイベントのみ取得

# ブラウザ設定
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "False").lower() == "true"  # False=表示、True=非表示
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "30000"))  # ミリ秒
BROWSER_WAIT_TIME = int(os.getenv("BROWSER_WAIT_TIME", "2"))  # 秒（要素待機時間）
BROWSER_KEEP_OPEN = os.getenv("BROWSER_KEEP_OPEN", "False").lower() == "true"  # デバッグ用：処理終了後もブラウザを開いたままにする

# ログ設定
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

