"""
TimeTreeExport メインスクリプト
TimeTreeから今日以降のスケジュールを取得し、CSV形式でエクスポートする
"""
import sys
from datetime import datetime
import config
from timetree_scraper import TimeTreeScraper
from csv_exporter import CSVExporter
import utils
from progress_window import ProgressWindow


def main():
    """メイン処理"""
    # 進捗表示ウィンドウを起動
    progress_window = ProgressWindow("TimeTreeExport - 処理状況")
    progress_window.start()
    
    # グローバルに設定（他のモジュールからアクセス可能にする）
    from progress_window import set_global_progress_window
    set_global_progress_window(progress_window)
    
    # 少し待ってウィンドウが表示されるのを待つ
    import time
    time.sleep(0.5)
    
    try:
        progress_window.update_status("初期化中...")
        progress_window.log("=" * 60)
        progress_window.log("TimeTreeExport を開始します...")
        progress_window.log("=" * 60)
        progress_window.log(f"ブラウザモード: {'ヘッドレス（非表示）' if config.BROWSER_HEADLESS else '表示モード（デバッグ用）'}")
        print("TimeTreeExport を開始します...")
        print(f"ブラウザモード: {'ヘッドレス（非表示）' if config.BROWSER_HEADLESS else '表示モード（デバッグ用）'}")
        
        # 設定の確認
        if not config.TIMETREE_EMAIL or not config.TIMETREE_PASSWORD:
            error_msg = "エラー: TIMETREE_EMAIL または TIMETREE_PASSWORD が設定されていません。\n.env ファイルに認証情報を設定してください。"
            progress_window.log_error(error_msg)
            print(error_msg)
            progress_window.update_status("エラー: 認証情報が設定されていません")
            time.sleep(3)  # エラーメッセージを表示する時間
            progress_window.close()
            sys.exit(1)
        
        # 取得開始日を設定
        from_date = None
        if config.FILTER_FROM_TODAY:
            from_date = utils.get_today_start()
            date_msg = f"取得期間: {from_date.strftime('%Y-%m-%d')} 以降"
            progress_window.log(date_msg)
            print(date_msg)
        
        # ブラウザ自動化を使用してTimeTreeからデータを取得
        scraper = None
        events = []
        try:
            progress_window.update_status("TimeTreeにログイン中...")
            with TimeTreeScraper() as scraper:
                # ログイン
                if not scraper.login(config.TIMETREE_EMAIL, config.TIMETREE_PASSWORD):
                    error_msg = "エラー: ログインに失敗しました。"
                    progress_window.log_error(error_msg)
                    print(error_msg)
                    progress_window.update_status("ログイン失敗")
                    if config.BROWSER_KEEP_OPEN:
                        progress_window.log_warning("ブラウザを開いたままにしてデバッグを続けます...")
                        print("ブラウザを開いたままにしてデバッグを続けます...")
                        time.sleep(5)
                    else:
                        time.sleep(3)
                        progress_window.close()
                        sys.exit(1)
                else:
                    progress_window.log_success("ログイン成功")
                
                # イベントを取得
                progress_window.update_status("カレンダーからスケジュールを取得中...")
                calendar_id = config.TIMETREE_CALENDAR_ID if config.TIMETREE_CALENDAR_ID else None
                events = scraper.get_events(calendar_id=calendar_id, from_date=from_date)
                
                event_count_msg = f"{len(events)} 件のイベントを取得しました。"
                progress_window.log_success(event_count_msg)
                print(event_count_msg)
        except Exception as e:
            error_msg = f"エラーが発生しました: {e}"
            progress_window.log_error(error_msg)
            print(f"\n{error_msg}")
            progress_window.update_status(f"エラー: {type(e).__name__}")
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
            if config.BROWSER_KEEP_OPEN and scraper:
                progress_window.log_warning("ブラウザを開いたままにしてデバッグを続けます...")
                print("ブラウザを開いたままにしてデバッグを続けます...")
                time.sleep(5)
        
        if len(events) == 0:
            warning_msg = "エクスポートするイベントがありません。\n注意: 実際のTimeTreeのHTML構造に合わせてセレクタを調整する必要がある可能性があります。"
            progress_window.log_warning(warning_msg)
            print(warning_msg)
            progress_window.update_status("イベントが見つかりませんでした")
            time.sleep(5)
            progress_window.close()
            return
        
        # CSVにエクスポート
        progress_window.update_status("CSVファイルにエクスポート中...")
        progress_window.log("CSVファイルにエクスポート中...")
        print("CSVファイルにエクスポート中...")
        exporter = CSVExporter(output_dir=config.OUTPUT_DIR)
        output_path = exporter.export_events(events)
        
        success_msg = f"エクスポート完了: {output_path}"
        progress_window.log_success(success_msg)
        print(success_msg)
        progress_window.update_status("エクスポート完了")
        
        progress_window.log("=" * 60)
        progress_window.log("すべての処理が完了しました！")
        progress_window.log("=" * 60)
        
        # 5秒後に自動的に閉じる
        time.sleep(5)
        progress_window.close()
        
    except KeyboardInterrupt:
        progress_window.log_warning("\n処理が中断されました。")
        print("\n処理が中断されました。")
        progress_window.update_status("処理が中断されました")
        time.sleep(2)
        progress_window.close()
        sys.exit(1)
    except Exception as e:
        error_msg = f"エラーが発生しました: {e}"
        progress_window.log_error(error_msg)
        print(error_msg)
        progress_window.update_status(f"エラー: {type(e).__name__}")
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        time.sleep(5)
        progress_window.close()
        sys.exit(1)


if __name__ == "__main__":
    main()

