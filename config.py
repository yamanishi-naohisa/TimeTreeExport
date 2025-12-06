"""
設定管理モジュール
環境変数から設定を読み込む
"""
import os
from dotenv import load_dotenv
from datetime import datetime

# .envファイルを読み込む
load_dotenv()

# TimeTree API設定
TIMETREE_ACCESS_TOKEN = os.getenv("TIMETREE_ACCESS_TOKEN", "")
TIMETREE_CALENDAR_ID = os.getenv("TIMETREE_CALENDAR_ID", "")

# API設定
TIMETREE_API_BASE_URL = os.getenv(
    "TIMETREE_API_BASE_URL", 
    "https://timetreeapis.com/v1"  # 仮のURL（実際のAPI URLに置き換え）
)

# 出力設定
OUTPUT_DIR = os.getenv("OUTPUT_DIR", ".")
OUTPUT_FILENAME_PREFIX = os.getenv("OUTPUT_FILENAME_PREFIX", "timetree_export")
CSV_ENCODING = "utf-8-sig"  # Excel互換性のためBOM付きUTF-8

# フィルタ設定
FILTER_FROM_TODAY = True  # 今日以降のイベントのみ取得

# ログ設定
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

