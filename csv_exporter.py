"""
CSV出力モジュール
"""
import csv
import os
from typing import List, Dict
from datetime import datetime
import config
import utils


class CSVExporter:
    """CSV出力を管理するクラス"""
    
    def __init__(self, output_dir: str = None):
        """
        初期化
        
        Args:
            output_dir: 出力ディレクトリ（デフォルト: configから取得）
        """
        self.output_dir = output_dir or config.OUTPUT_DIR
    
    def export_events(self, events: List[Dict], filename: str = None) -> str:
        """
        イベントをCSVファイルにエクスポート
        
        Args:
            events: エクスポートするイベントのリスト
            filename: 出力ファイル名（Noneの場合は自動生成）
            
        Returns:
            str: 出力されたファイルのパス
        """
        if filename is None:
            filename = utils.generate_output_filename(config.OUTPUT_FILENAME_PREFIX)
        
        filepath = os.path.join(self.output_dir, filename)
        
        # CSVヘッダー
        fieldnames = [
            "日付",
            "開始時刻",
            "終了時刻",
            "タイトル",
            "場所",
            "説明",
            "カレンダー名"
        ]
        
        # CSVファイルに書き込み
        with open(filepath, "w", encoding=config.CSV_ENCODING, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for event in events:
                # 日時を日付と時刻に分割
                start_date, start_time = utils.format_datetime_for_csv(
                    event.get("start_datetime")
                )
                end_date, end_time = utils.format_datetime_for_csv(
                    event.get("end_datetime")
                )
                
                row = {
                    "日付": start_date,
                    "開始時刻": start_time,
                    "終了時刻": end_time,
                    "タイトル": event.get("title", ""),
                    "場所": event.get("location", ""),
                    "説明": event.get("description", ""),
                    "カレンダー名": event.get("calendar_name", ""),
                }
                writer.writerow(row)
        
        return filepath

