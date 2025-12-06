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
                progress_window.update_status("TimeTreeにログイン中...")
                
                # headlessモードかどうかで処理を分岐
                if config.BROWSER_HEADLESS:
                    # headlessモード: 自動判定のみ（ユーザー確認なし）
                    logger.info("headlessモードでログインします（自動判定のみ）")
                    progress_window.log("headlessモード: ログインを自動判定します...")
                    
                    try:
                        login_success = scraper.login(config.TIMETREE_EMAIL, config.TIMETREE_PASSWORD)
                        
                        if login_success:
                            logger.info("ログイン成功を確認しました（自動判定）")
                            progress_window.log_success("ログイン成功を確認しました（自動判定）")
                            progress_window.update_status("ログイン成功 - イベント取得を開始します...")
                        else:
                            error_msg = "ログイン判定が失敗しました"
                            logger.error(error_msg)
                            progress_window.log_error(error_msg)
                            progress_window.update_status("ログイン失敗")
                            print(error_msg)
                            progress_window.close()
                            sys.exit(1)
                            
                    except Exception as e:
                        error_msg = f"ログイン処理でエラーが発生しました: {e}"
                        logger.error(error_msg, exc_info=True)
                        progress_window.log_error(error_msg)
                        progress_window.update_status("ログイン失敗")
                        print(error_msg)
                        progress_window.close()
                        sys.exit(1)
                else:
                    # 表示モード: ユーザー確認あり
                    progress_window.log("")
                    progress_window.log("=" * 60)
                    progress_window.log("ログイン処理を開始します。")
                    progress_window.log("ブラウザでログインが完了し、カレンダーが表示されたら")
                    progress_window.log("「ログイン成功」ボタンをクリックしてください。")
                    progress_window.log("=" * 60)
                    
                    # 確認ボタンを事前に表示（ログイン処理開始前に）
                    confirmation_event = progress_window.prepare_confirmation(
                        "ブラウザでログインが完了し、カレンダーが表示されたら「ログイン成功」ボタンをクリックしてください。",
                        "ログイン成功"
                    )
                    
                    # ボタンが表示されるまで少し待つ
                    time.sleep(0.5)
                    
                    try:
                        # ログイン処理を実行（自動判定は参考程度）
                        login_success = scraper.login(config.TIMETREE_EMAIL, config.TIMETREE_PASSWORD)
                        
                        if login_success:
                            logger.info("ログイン自動判定が成功しました")
                            progress_window.log("ログイン自動判定が成功しました。")
                        else:
                            logger.warning("ログイン自動判定が失敗しましたが、ユーザー確認で続行可能です")
                            progress_window.log_warning("ログイン自動判定が失敗しましたが、ブラウザで確認してください。")
                        
                        logger.info("ユーザーの確認を待機します...")
                        progress_window.log("ログイン成功ボタンのクリックを待機中です...")
                        progress_window.log("プログレスウィンドウを閉じないでください。ブラウザは開いたままです。")
                        
                        # ユーザーが確認ボタンをクリックするまで待機（ログイン処理中でも押せる）
                        try:
                            confirmed = confirmation_event.wait(timeout=300)  # 最大5分
                            
                            if confirmed:
                                logger.info("ユーザーがログイン成功を確認しました")
                                progress_window.log_success("ログイン成功を確認しました")
                                progress_window.update_status("ログイン成功 - イベント取得を開始します...")
                            else:
                                logger.warning("ユーザー確認がタイムアウトしましたが、処理を続行します")
                                progress_window.log_warning("確認がタイムアウトしましたが、処理を続行します...")
                        except KeyboardInterrupt:
                            # ログイン確認待機中にキャンセルされた場合でも、ブラウザは開いたままにする
                            logger.warning("ログイン確認待機中に割り込みが発生しました")
                            logger.info("ユーザーがログイン成功を確認したとみなして処理を続行します")
                            try:
                                progress_window.log_warning("割り込みが発生しましたが、処理を続行します...")
                            except:
                                pass  # プログレスウィンドウが閉じられている可能性がある
                            confirmed = True  # 続行する
                            
                    except Exception as e:
                        error_msg = f"ログイン処理でエラーが発生しました: {e}"
                        logger.error(error_msg, exc_info=True)
                        progress_window.log_error(error_msg)
                        progress_window.update_status("ログイン失敗")
                        print(error_msg)
                        if config.BROWSER_KEEP_OPEN:
                            progress_window.log_warning("ブラウザを開いたままにしてデバッグを続けます...")
                            logger.info("BROWSER_KEEP_OPEN=True のため、ブラウザを開いたままにします")
                            time.sleep(5)
                        else:
                            logger.info("3秒待機後、スクリプトを終了します")
                            time.sleep(3)
                            progress_window.close()
                            sys.exit(1)
                
                # イベントを取得
                logger.info("イベント取得処理を開始します")
                progress_window.update_status("カレンダーからスケジュールを取得中...")
                calendar_id = config.TIMETREE_CALENDAR_ID if config.TIMETREE_CALENDAR_ID else None
                logger.info(f"カレンダーID: {calendar_id if calendar_id else '全カレンダー'}")
                
                try:
                    events = scraper.get_events(calendar_id=calendar_id, from_date=from_date)
                    
                    logger.info(f"イベント取得が完了しました。取得件数: {len(events)}件")
                    event_count_msg = f"{len(events)} 件のイベントを取得しました。"
                    progress_window.log_success(event_count_msg)
                    print(event_count_msg)
                except Exception as e:
                    error_msg = f"イベント取得でエラーが発生しました: {e}"
                    logger.error(error_msg, exc_info=True)
                    progress_window.log_error(error_msg)
                    progress_window.update_status("イベント取得エラー")
                    print(error_msg)
                    events = []  # 空のリストを返して処理を続行
            
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

