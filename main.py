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
from logger import setup_logger


def main():
    """メイン処理"""
    # ロガーをセットアップ（進捗ウィンドウより前に初期化）
    logger = setup_logger()
    log_file_path = logger.handlers[-1].baseFilename if logger.handlers else "ログファイル未設定"
    
    # 進捗表示ウィンドウを起動
    progress_window = ProgressWindow("TimeTreeExport - 処理状況")
    progress_window.start()
    
    # グローバルに設定（他のモジュールからアクセス可能にする）
    from progress_window import set_global_progress_window
    set_global_progress_window(progress_window)
    
    # 少し待ってウィンドウが表示されるのを待つ
    import time
    time.sleep(0.5)
    
    logger.info("=" * 60)
    logger.info("TimeTreeExport を開始します")
    logger.info(f"ログファイル: {log_file_path}")
    logger.info("=" * 60)
    
    try:
        progress_window.update_status("初期化中...")
        progress_window.log("=" * 60)
        progress_window.log("TimeTreeExport を開始します...")
        progress_window.log("=" * 60)
        if log_file_path:
            progress_window.log(f"ログファイル: {log_file_path}")
        progress_window.log(f"ブラウザモード: {'ヘッドレス（非表示）' if config.BROWSER_HEADLESS else '表示モード（デバッグ用）'}")
        print("TimeTreeExport を開始します...")
        if log_file_path:
            print(f"ログファイル: {log_file_path}")
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
            logger.info("=" * 60)
            logger.info("TimeTreeからのデータ取得を開始します")
            logger.info("=" * 60)
            
            progress_window.update_status("TimeTreeにログイン中...")
            logger.info("TimeTreeScraperのコンテキストマネージャーに入ります (withブロック開始)")
            
            with TimeTreeScraper() as scraper:
                logger.info("TimeTreeScraperのコンテキストマネージャー内に入りました")
                
                # ログイン
                logger.info("ログイン処理を開始します")
                login_result = scraper.login(config.TIMETREE_EMAIL, config.TIMETREE_PASSWORD)
                
                if not login_result:
                    logger.warning("ログイン判定が失敗しましたが、実際にカレンダーが表示されている可能性があります")
                    logger.warning("処理を続行して、カレンダーページへのアクセスを試みます")
                    progress_window.log_warning("ログイン判定が失敗しましたが、処理を続行します...")
                    print("警告: ログイン判定が失敗しましたが、処理を続行します...")
                else:
                    logger.info("ログインに成功しました")
                    progress_window.log_success("ログイン成功")
                
                # イベントを取得
                logger.info("イベント取得処理を開始します")
                progress_window.update_status("カレンダーからスケジュールを取得中...")
                calendar_id = config.TIMETREE_CALENDAR_ID if config.TIMETREE_CALENDAR_ID else None
                logger.info(f"カレンダーID: {calendar_id if calendar_id else '全カレンダー'}")
                
                events = scraper.get_events(calendar_id=calendar_id, from_date=from_date)
                
                logger.info(f"イベント取得が完了しました。取得件数: {len(events)}件")
                event_count_msg = f"{len(events)} 件のイベントを取得しました。"
                progress_window.log_success(event_count_msg)
                print(event_count_msg)
            
            logger.info("=" * 60)
            logger.info("TimeTreeScraperのコンテキストマネージャーから出ます (withブロック終了)")
            logger.info("注意: withブロックを抜けるため、ブラウザが自動的に閉じられます")
            logger.info("=" * 60)
            progress_window.log("=" * 60)
            progress_window.log("ブラウザを閉じる前に、withブロックを抜けています")
            progress_window.log("withブロックを抜けると、自動的にブラウザが閉じられます")
            progress_window.log("=" * 60)
            
        except Exception as e:
            logger.error(f"エラーが発生しました: {e}", exc_info=True)
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
                logger.info("BROWSER_KEEP_OPEN=True のため、ブラウザを開いたままにします")
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

