"""
CSVエクスポートモジュール
イベントデータをCSV形式で出力する
"""
import csv
import os
from datetime import datetime
from typing import List, Dict
import config
import utils


class CSVExporter:
    """イベントデータをCSV形式でエクスポートするクラス"""
    
    def __init__(self, output_dir: str = None):
        """
        初期化
        
        Args:
            output_dir: 出力先ディレクトリ（デフォルト: configから取得）
        """
        self.output_dir = output_dir or config.OUTPUT_DIR
        self.encoding = config.CSV_ENCODING
        
        # 出力ディレクトリが存在しない場合は作成
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def export_events(self, events: List[Dict]) -> str:
        """
        イベントリストをCSVファイルにエクスポート
        
        Args:
            events: イベントデータのリスト
            
        Returns:
            str: 出力されたCSVファイルのパス
        """
        # ファイル名を生成
        filename = utils.generate_output_filename(config.OUTPUT_FILENAME_PREFIX)
        filepath = os.path.join(self.output_dir, filename)
        
        # CSVファイルに書き込み
        with open(filepath, 'w', encoding=self.encoding, newline='') as csvfile:
            fieldnames = [
                '日付',
                '開始時刻',
                '終了時刻',
                'タイトル',
                '場所',
                '説明',
                'カレンダー名'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # ヘッダーを書き込み
            writer.writeheader()
            
            # イベントデータを書き込み
            for event in events:
                start_date, start_time = utils.format_datetime_for_csv(
                    event.get('start_datetime')
                )
                end_date, end_time = utils.format_datetime_for_csv(
                    event.get('end_datetime')
                )
                
                # 日付は開始日時を使用（終了日時が異なる場合は終了日時を優先）
                date = start_date if start_date else end_date
                
                writer.writerow({
                    '日付': date,
                    '開始時刻': start_time,
                    '終了時刻': end_time,
                    'タイトル': event.get('title', ''),
                    '場所': event.get('location', ''),
                    '説明': event.get('description', ''),
                    'カレンダー名': event.get('calendar_name', '')
                })
        
        return filepath

