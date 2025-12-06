"""
TimeTreeExport メインスクリプト
TimeTreeから今日以降のスケジュールを取得し、CSV形式でエクスポートする
"""
import sys
from datetime import datetime
import config
from timetree_api import TimeTreeAPI
from csv_exporter import CSVExporter
import utils


def main():
    """メイン処理"""
    print("TimeTreeExport を開始します...")
    
    # 設定の確認
    if not config.TIMETREE_ACCESS_TOKEN:
        print("エラー: TIMETREE_ACCESS_TOKEN が設定されていません。")
        print(".env ファイルに認証情報を設定してください。")
        sys.exit(1)
    
    try:
        # TimeTree APIクライアントの初期化
        api = TimeTreeAPI(
            access_token=config.TIMETREE_ACCESS_TOKEN,
            base_url=config.TIMETREE_API_BASE_URL
        )
        
        # 取得開始日を設定
        from_date = None
        if config.FILTER_FROM_TODAY:
            from_date = utils.get_today_start()
            print(f"取得期間: {from_date.strftime('%Y-%m-%d')} 以降")
        
        # イベントを取得
        print("スケジュールを取得中...")
        calendar_id = config.TIMETREE_CALENDAR_ID if config.TIMETREE_CALENDAR_ID else None
        events_data = api.get_events(calendar_id=calendar_id, from_date=from_date)
        
        # イベントデータをパース
        events = []
        for event_data in events_data:
            parsed_event = api.parse_event(event_data)
            events.append(parsed_event)
        
        print(f"{len(events)} 件のイベントを取得しました。")
        
        if len(events) == 0:
            print("エクスポートするイベントがありません。")
            return
        
        # CSVにエクスポート
        print("CSVファイルにエクスポート中...")
        exporter = CSVExporter(output_dir=config.OUTPUT_DIR)
        output_path = exporter.export_events(events)
        
        print(f"エクスポート完了: {output_path}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

