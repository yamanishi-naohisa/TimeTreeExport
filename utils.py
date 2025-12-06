"""
ユーティリティ関数
"""
from datetime import datetime
from typing import Optional, Tuple


def get_today_start() -> datetime:
    """
    今日の開始時刻（00:00:00）を取得
    
    Returns:
        datetime: 今日の00:00:00
    """
    today = datetime.now()
    return today.replace(hour=0, minute=0, second=0, microsecond=0)


def format_datetime_for_csv(dt: Optional[datetime]) -> Tuple[str, str]:
    """
    日時をCSV用の日付と時刻に分割
    
    Args:
        dt: 日時オブジェクト
        
    Returns:
        tuple: (日付文字列 YYYY-MM-DD, 時刻文字列 HH:MM)
    """
    if dt is None:
        return "", ""
    
    date_str = dt.strftime("%Y-%m-%d")
    time_str = dt.strftime("%H:%M")
    return date_str, time_str


def generate_output_filename(prefix: str = "timetree_export") -> str:
    """
    出力ファイル名を生成
    
    Args:
        prefix: ファイル名のプレフィックス
        
    Returns:
        str: ファイル名（例: timetree_export_20240101_120000.csv）
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.csv"

