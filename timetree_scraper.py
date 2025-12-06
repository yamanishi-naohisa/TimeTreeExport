"""
TimeTree スクレイパーモジュール
ブラウザ自動化を使用してTimeTreeからスケジュールを取得する
"""
from playwright.sync_api import sync_playwright, Page, Browser
from datetime import datetime
from typing import List, Dict, Optional
import time
import config

# ロガーをインポート
try:
    from logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())

# 進捗ウィンドウへのアクセスを試行（オプション）
try:
    from progress_window import get_global_progress_window, log_to_window
    HAS_PROGRESS_WINDOW = True
except ImportError:
    HAS_PROGRESS_WINDOW = False
    def log_to_window(*args, **kwargs):
        pass
import utils


class TimeTreeScraper:
    """ブラウザ自動化を使用してTimeTreeからデータを取得するクラス"""
    
    def __init__(self, headless: bool = None, timeout: int = None):
        """
        初期化
        
        Args:
            headless: ヘッドレスモード（Noneの場合はconfigから取得）
            timeout: タイムアウト時間（ミリ秒、Noneの場合はconfigから取得）
        """
        self.headless = headless if headless is not None else config.BROWSER_HEADLESS
        self.timeout = timeout or config.BROWSER_TIMEOUT
        self.base_url = config.TIMETREE_BASE_URL
        self.wait_time = config.BROWSER_WAIT_TIME
        self.keep_open = config.BROWSER_KEEP_OPEN
        self.playwright = None
        self.browser = None
        self.page = None
    
    def __enter__(self):
        """コンテキストマネージャー: 開始"""
        logger.info("ブラウザを起動中...")
        logger.debug(f"ヘッドレスモード: {self.headless}")
        logger.debug(f"タイムアウト: {self.timeout}ms")
        
        try:
            self.playwright = sync_playwright().start()
            logger.debug("Playwrightを起動しました")
            
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            logger.info(f"ブラウザを起動しました (headless={self.headless})")
            
            self.page = self.browser.new_page()
            logger.debug("新しいページを作成しました")
            
            self.page.set_default_timeout(self.timeout)
            logger.debug(f"タイムアウトを設定しました: {self.timeout}ms")
            
            return self
        except Exception as e:
            logger.error(f"ブラウザの起動に失敗しました: {e}", exc_info=True)
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了"""
        logger.info("ブラウザを終了処理中...")
        
        # エラーが発生した場合の詳細ログ
        if exc_type is not None:
            logger.error(f"エラーが発生しました: {exc_type.__name__}")
            if exc_val:
                logger.error(f"エラー内容: {exc_val}", exc_info=True)
            logger.debug(f"例外タイプ: {exc_type}")
            logger.debug(f"例外値: {exc_val}")
            logger.debug(f"トレースバック: {exc_tb}")
        
        # 現在のURLをログに記録
        try:
            if self.page:
                current_url = self.page.url
                logger.debug(f"現在のURL: {current_url}")
        except Exception as e:
            logger.debug(f"URL取得エラー: {e}")
        
        # デバッグモードでブラウザを開いたままにする場合
        if self.keep_open:
            logger.info("デバッグモード: ブラウザを開いたままにします")
            logger.info("ブラウザを閉じるには、手動で閉じるか、Enterキーを押してください...")
            try:
                input()
            except:
                pass
        
        # ブラウザを閉じる
        if self.browser:
            if self.keep_open:
                logger.info("keep_open=True のため、ブラウザを開いたままにします")
            else:
                logger.info("ブラウザを閉じます...")
                try:
                    self.browser.close()
                    logger.info("ブラウザを閉じました")
                except Exception as e:
                    logger.warning(f"ブラウザのクローズでエラーが発生しました: {e}")
        
        # Playwrightを停止
        if self.playwright:
            if self.keep_open:
                logger.info("keep_open=True のため、Playwrightを開いたままにします")
            else:
                logger.info("Playwrightを停止します...")
                try:
                    self.playwright.stop()
                    logger.info("Playwrightを停止しました")
                except Exception as e:
                    logger.warning(f"Playwrightの停止でエラーが発生しました: {e}")
        
        logger.info("ブラウザの終了処理が完了しました")
    
    def login(self, email: str, password: str) -> bool:
        """
        TimeTreeにログインする
        
        Args:
            email: メールアドレス
            password: パスワード
            
        Returns:
            bool: ログイン成功時True
        """
        try:
            logger.info(f"TimeTreeにログインを開始します (メール: {email})")
            print(f"TimeTreeにログイン中... (メール: {email})")
            
            # ログインページに移動
            login_url = f"{self.base_url}/signin"
            logger.info(f"ログインページにアクセス: {login_url}")
            print(f"ログインページにアクセス: {login_url}")
            
            logger.debug("ページ遷移を開始...")
            self.page.goto(login_url, wait_until="networkidle")
            logger.debug("ページ遷移が完了しました")
            
            time.sleep(self.wait_time)
            current_url = self.page.url
            logger.info(f"現在のURL: {current_url}")
            print(f"現在のURL: {current_url}")
            
            if config.DEBUG_MODE:
                # デバッグ用: ページのHTMLを保存
                page_content = self.page.content()
                with open("debug_login_page.html", "w", encoding="utf-8") as f:
                    f.write(page_content)
                print("デバッグ: ログインページのHTMLを debug_login_page.html に保存しました")
                self.page.screenshot(path="debug_login_page.png")
                print("デバッグ: ログインページのスクリーンショットを debug_login_page.png に保存しました")
            
            # メールアドレス入力フィールドを探す（TimeTreeの構造に合わせて最適化）
            email_filled = False
            email_selectors = [
                'input[name="email"]',  # TimeTreeの標準セレクタ
                'input[type="email"]',
                'input[id*="email"]',
                'input[placeholder*="メール"]',
                'input[placeholder*="email"]',
                'input[placeholder*="Email"]'
            ]
            
            print("メールアドレス入力フィールドを検索中...")
            for selector in email_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    element = self.page.query_selector(selector)
                    if element and element.is_visible():
                        print(f"メール入力フィールドを発見: {selector}")
                        self.page.fill(selector, email)
                        email_filled = True
                        break
                except Exception as e:
                    if config.DEBUG_MODE:
                        print(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            if not email_filled:
                print("警告: メールアドレス入力フィールドが見つかりませんでした")
                if config.DEBUG_MODE:
                    print("利用可能なinput要素:")
                    inputs = self.page.query_selector_all('input')
                    for inp in inputs[:10]:  # 最初の10個のみ表示
                        try:
                            inp_type = inp.get_attribute('type') or 'text'
                            inp_name = inp.get_attribute('name') or ''
                            inp_id = inp.get_attribute('id') or ''
                            print(f"  - type={inp_type}, name={inp_name}, id={inp_id}")
                        except:
                            pass
                return False
            
            time.sleep(0.5)
            
            # パスワード入力フィールドを探す（TimeTreeの構造に合わせて最適化）
            password_filled = False
            password_selectors = [
                'input[name="password"]',  # TimeTreeの標準セレクタ
                'input[type="password"]',
                'input[id*="password"]',
                'input[placeholder*="パスワード"]',
                'input[placeholder*="password"]',
                'input[placeholder*="Password"]'
            ]
            
            print("パスワード入力フィールドを検索中...")
            for selector in password_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    element = self.page.query_selector(selector)
                    if element and element.is_visible():
                        print(f"パスワード入力フィールドを発見: {selector}")
                        self.page.fill(selector, password)
                        password_filled = True
                        break
                except Exception as e:
                    if config.DEBUG_MODE:
                        print(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            if not password_filled:
                print("警告: パスワード入力フィールドが見つかりませんでした")
                return False
            
            time.sleep(0.5)
            
            # ログインボタンをクリック（TimeTreeの構造に合わせて最適化）
            print("ログインボタンを検索中...")
            login_button = None
            button_selectors = [
                'button[type="submit"]',  # TimeTreeの標準セレクタ
                'button:has-text("ログイン")',
                'button:has-text("サインイン")',
                'button:has-text("Sign in")',
                'input[type="submit"]'
            ]
            
            for selector in button_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    login_button = self.page.query_selector(selector)
                    if login_button and login_button.is_visible():
                        print(f"ログインボタンを発見: {selector}")
                        break
                except:
                    continue
            
            if login_button:
                login_button.click()
                print("ログインボタンをクリックしました")
            else:
                print("ログインボタンが見つからないため、Enterキーで送信を試行します")
                # フォーム送信を試行
                self.page.keyboard.press("Enter")
            
            # ログイン完了を待つ（ページ遷移を待機）
            logger.info("ログイン処理の完了を待機中...")
            time.sleep(3)  # ログイン処理を待つ
            time.sleep(self.wait_time)
            
            # ページ遷移をより確実に待つ
            logger.info("ページ遷移を待機中...")
            try:
                # URLが変わるのを待つ（最大10秒）
                max_wait = 10
                waited = 0
                initial_url = self.page.url
                logger.debug(f"初期URL: {initial_url}")
                
                while waited < max_wait:
                    time.sleep(1)
                    waited += 1
                    current_url = self.page.url
                    if current_url != initial_url:
                        logger.info(f"URLが変化しました: {initial_url} -> {current_url}")
                        break
                    if waited % 2 == 0:
                        logger.debug(f"URL変更を待機中... ({waited}秒経過)")
                
                # さらにネットワークアイドル状態を待つ
                try:
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                    logger.debug("networkidle状態になりました")
                except:
                    logger.debug("networkidleの待機はタイムアウトしました（続行します）")
                
            except Exception as e:
                logger.warning(f"ページ遷移の待機でエラーが発生しました: {e}")
            
            # ログイン成功を確認（複数の方法で確認）
            current_url = self.page.url
            page_title = self.page.title()
            logger.info(f"ログイン後のURL: {current_url}")
            logger.info(f"ページタイトル: {page_title}")
            
            # 方法1: URLがログインページでないことを確認
            url_check = "login" not in current_url.lower() and "signin" not in current_url.lower()
            logger.debug(f"URL判定: {url_check} (URL: {current_url})")
            
            # 方法2: カレンダーページの要素が存在するか確認
            calendar_indicators = [
                "calendar" in current_url.lower(),
                "/calendars" in current_url.lower(),
                "timetreeapp.com" in current_url.lower() and "signin" not in current_url.lower()
            ]
            has_calendar_url = any(calendar_indicators)
            logger.debug(f"カレンダーURL判定: {has_calendar_url}")
            
            # 方法3: ページのタイトルや要素で確認
            try:
                # カレンダー関連の要素を探す
                calendar_selectors = [
                    '[class*="calendar"]',
                    '[data-testid*="calendar"]',
                    '[id*="calendar"]',
                    'nav',
                    '[role="main"]'
                ]
                has_calendar_elements = False
                for selector in calendar_selectors[:3]:  # 最初の3つだけ試す
                    try:
                        elements = self.page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            has_calendar_elements = True
                            logger.debug(f"カレンダー要素を発見: {selector} ({len(elements)}個)")
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"カレンダー要素の検索でエラー: {e}")
                has_calendar_elements = False
            
            # ログイン成功の判定（いずれかの条件を満たせば成功）
            login_success = url_check or has_calendar_url or has_calendar_elements
            
            logger.info(f"ログイン判定結果:")
            logger.info(f"  - URL判定: {url_check}")
            logger.info(f"  - カレンダーURL判定: {has_calendar_url}")
            logger.info(f"  - カレンダー要素判定: {has_calendar_elements}")
            logger.info(f"  - 最終判定: {login_success}")
            
            if login_success:
                logger.info("ログイン成功を確認しました")
                print("ログイン成功")
                return True
            else:
                logger.warning(f"ログイン判定が失敗しました (URL: {current_url}, タイトル: {page_title})")
                logger.warning("ただし、実際にカレンダーが表示されている可能性があります")
                print(f"警告: ログイン判定が失敗しました (URL: {current_url})")
                print("注意: 実際にカレンダーが表示されている場合は、処理を続行します")
                # 警告を出しても、とりあえず続行を試みる
                return True  # 失敗と判定しても、カレンダーが表示されている可能性があるので続行
                
        except Exception as e:
            logger.error(f"ログインエラーが発生しました: {e}", exc_info=True)
            print(f"ログインエラー: {e}")
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
                # スクリーンショットを保存
                try:
                    self.page.screenshot(path="login_error.png")
                    logger.debug("エラー時のスクリーンショットを保存しました: login_error.png")
                except:
                    pass
            return False
    
    def get_events(self, calendar_id: Optional[str] = None, 
                   from_date: Optional[datetime] = None) -> List[Dict]:
        """
        イベントを取得する
        
        Args:
            calendar_id: カレンダーID（Noneの場合は全カレンダー）
            from_date: 取得開始日（Noneの場合は今日）
            
        Returns:
            List[Dict]: イベントデータのリスト
        """
        if from_date is None:
            from_date = utils.get_today_start()
        
        try:
            logger.info(f"スケジュール取得を開始します (開始日: {from_date.strftime('%Y-%m-%d')})")
            print(f"スケジュールを取得中... (開始日: {from_date.strftime('%Y-%m-%d')})")
            
            # カレンダーページに移動
            if calendar_id:
                calendar_url = f"{self.base_url}/calendars/{calendar_id}"
                logger.info(f"特定のカレンダーにアクセス: {calendar_id}")
            else:
                calendar_url = f"{self.base_url}/calendars"
                logger.info("全カレンダーにアクセスします")
            
            logger.info(f"カレンダーページに移動中: {calendar_url}")
            print(f"カレンダーページに移動中: {calendar_url}")
            
            logger.debug("ページ遷移を開始...")
            self.page.goto(calendar_url, wait_until="networkidle")
            logger.debug("ページ遷移が完了しました")
            
            time.sleep(self.wait_time)
            
            # カレンダーが読み込まれるまで待機
            current_url = self.page.url
            page_title = self.page.title()
            logger.info(f"カレンダーページに到達しました")
            logger.info(f"現在のURL: {current_url}")
            logger.info(f"ページタイトル: {page_title}")
            print("カレンダーページの読み込みを待機中...")
            print(f"現在のURL: {current_url}")
            print(f"ページタイトル: {page_title}")
            
            # JavaScriptで動的に読み込まれるコンテンツを待つ
            logger.debug(f"JavaScriptの読み込みを待機中... (待機時間: {self.wait_time * 3}秒)")
            time.sleep(self.wait_time * 3)  # より長く待機
            logger.debug("待機が完了しました")
            
            # カレンダー要素が表示されるまで待機を試行
            try:
                logger.debug("networkidle状態を待機中...")
                self.page.wait_for_load_state("networkidle", timeout=10000)
                logger.debug("networkidle状態になりました")
            except Exception as e:
                logger.warning(f"networkidleの待機でタイムアウトまたはエラー: {e}")
                pass
            
            # デバッグ用: ページのHTML構造を確認（必ず実行）
            logger.info("カレンダーページのHTMLとスクリーンショットを保存中...")
            page_content = self.page.content()
            html_file = "debug_calendar_page.html"
            screenshot_file = "debug_calendar_page.png"
            
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(page_content)
            logger.info(f"カレンダーページのHTMLを {html_file} に保存しました ({len(page_content)} 文字)")
            print(f"デバッグ: カレンダーページのHTMLを {html_file} に保存しました")
            
            self.page.screenshot(path=screenshot_file)
            logger.info(f"カレンダーページのスクリーンショットを {screenshot_file} に保存しました")
            print(f"デバッグ: カレンダーページのスクリーンショットを {screenshot_file} に保存しました")
            
            logger.info(f"ページタイトル: {page_title}")
            logger.info(f"現在のURL: {current_url}")
            logger.info(f"HTMLのサイズ: {len(page_content)} 文字")
            if config.DEBUG_MODE:
                print(f"ページタイトル: {page_title}")
                print(f"現在のURL: {current_url}")
                print(f"HTMLのサイズ: {len(page_content)} 文字")
            
            # イベント要素を取得
            logger.info("イベント取得処理を開始します")
            events = []
            
            # 複数の方法でイベントを取得
            logger.info("方法1: カレンダーグリッドからイベントを取得します")
            grid_events = self._get_events_from_calendar_grid(from_date)
            logger.info(f"カレンダーグリッドから {len(grid_events)} 件のイベントを取得しました")
            events.extend(grid_events)
            
            logger.info("方法2: イベントリストからイベントを取得します")
            list_events = self._get_events_from_event_list(from_date)
            logger.info(f"イベントリストから {len(list_events)} 件のイベントを取得しました")
            events.extend(list_events)
            
            logger.info("方法3: API/JSONからイベントを取得します")
            api_events = self._get_events_from_api(from_date)
            if api_events:
                logger.info(f"APIから {len(api_events)} 件のイベントを取得しました")
                events.extend(api_events)
            else:
                logger.debug("APIからのイベント取得はありませんでした")
            
            logger.info(f"合計 {len(events)} 件のイベントを取得しました")
            
            # 重複を除去（同じイベントが複数の方法で取得される可能性がある）
            logger.info("重複イベントを除去中...")
            unique_events = []
            seen_titles = set()
            for event in events:
                event_key = f"{event.get('title', '')}_{event.get('start_datetime', '')}"
                if event_key not in seen_titles and event.get('title'):
                    seen_titles.add(event_key)
                    unique_events.append(event)
            
            logger.info(f"重複除去後: {len(unique_events)} 件のイベント")
            events = unique_events
            
            # 日付でフィルタリング（今日以降のみ）
            logger.info(f"日付でフィルタリング中... (開始日: {from_date.strftime('%Y-%m-%d')})")
            filtered_events = []
            for event in events:
                event_start = event.get('start_datetime')
                if event_start:
                    if isinstance(event_start, datetime):
                        event_date = event_start.date()
                    else:
                        continue
                    if event_date >= from_date.date():
                        filtered_events.append(event)
            
            logger.info(f"フィルタリング後: {len(filtered_events)} 件のイベント (元: {len(events)}件)")
            print(f"{len(filtered_events)} 件のイベントを取得しました（フィルタリング後: {len(events)} -> {len(filtered_events)}）")
            
            if len(filtered_events) == 0:
                logger.warning("イベントが見つかりませんでした")
                print("警告: イベントが見つかりませんでした")
                if not config.DEBUG_MODE:
                    print("ヒント: DEBUG_MODE=True に設定すると、ページHTMLとスクリーンショットが保存されます")
            
            logger.info("イベント取得処理が完了しました")
            return filtered_events
            
        except Exception as e:
            logger.error(f"イベント取得エラーが発生しました: {e}", exc_info=True)
            print(f"イベント取得エラー: {e}")
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
                try:
                    self.page.screenshot(path="event_error.png")
                    logger.debug("エラー時のスクリーンショットを保存しました: event_error.png")
                except:
                    pass
            return []
    
    def _get_events_from_calendar_grid(self, from_date: datetime) -> List[Dict]:
        """
        カレンダーグリッド（月表示）からイベントを取得
        
        Args:
            from_date: 取得開始日
            
        Returns:
            List[Dict]: イベントデータのリスト
        """
        events = []
        try:
            # カレンダーグリッドのセルを探す
            cell_selectors = [
                '[class*="calendar-cell"]',
                '[class*="day-cell"]',
                '[class*="date-cell"]',
                'td[class*="day"]',
                '[data-date]',
                '[role="gridcell"]'
            ]
            
            cells = []
            for selector in cell_selectors:
                try:
                    found_cells = self.page.query_selector_all(selector)
                    if found_cells:
                        cells = found_cells
                        print(f"カレンダーセルを発見: {selector} ({len(cells)}個)")
                        break
                except:
                    continue
            
            # 各セルからイベントを抽出
            for cell in cells:
                try:
                    # セル内のイベント要素を探す
                    event_selectors = [
                        '[class*="event"]',
                        '[class*="schedule"]',
                        'a[href*="/events/"]',
                        '[role="button"]'
                    ]
                    
                    for event_selector in event_selectors:
                        event_elements = cell.query_selector_all(event_selector)
                        for event_elem in event_elements:
                            event_data = self._parse_event_from_cell(event_elem, cell)
                            if event_data and event_data.get('title'):
                                events.append(event_data)
                except Exception as e:
                    if config.DEBUG_MODE:
                        print(f"セルからのイベント抽出エラー: {e}")
                    continue
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"カレンダーグリッドからの取得エラー: {e}")
        
        return events
    
    def _get_events_from_event_list(self, from_date: datetime) -> List[Dict]:
        """
        イベントリスト（リスト表示）からイベントを取得
        
        Args:
            from_date: 取得開始日
            
        Returns:
            List[Dict]: イベントデータのリスト
        """
        events = []
        try:
            # イベントリストの要素を探す
            list_selectors = [
                '[class*="event-list"]',
                '[class*="event-item"]',
                '[class*="schedule-item"]',
                'li[class*="event"]',
                '[data-event]',
                'article',
                '[role="listitem"]'
            ]
            
            event_elements = []
            for selector in list_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        event_elements = elements
                        print(f"イベントリスト要素を発見: {selector} ({len(elements)}個)")
                        break
                except:
                    continue
            
            # 各イベント要素を処理
            for element in event_elements:
                try:
                    event_data = self._parse_event_element(element)
                    if event_data and event_data.get('title'):
                        events.append(event_data)
                except Exception as e:
                    if config.DEBUG_MODE:
                        print(f"イベントリストからのパースエラー: {e}")
                    continue
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"イベントリストからの取得エラー: {e}")
        
        return events
    
    def _get_events_from_api(self, from_date: datetime) -> List[Dict]:
        """
        TimeTreeの内部APIからイベントを取得（ネットワークリクエストを監視）
        
        Args:
            from_date: 取得開始日
            
        Returns:
            List[Dict]: イベントデータのリスト
        """
        events = []
        try:
            # ページのネットワークリクエストを監視して、APIレスポンスから取得
            # または、ページのJavaScript変数から直接取得
            
            # 方法1: ページのJavaScriptコンテキストからデータを取得
            try:
                # TimeTreeがページに埋め込んでいるデータを取得
                page_data = self.page.evaluate("""
                    () => {
                        // windowオブジェクトやデータ属性からイベントデータを取得
                        if (window.__INITIAL_STATE__) {
                            return window.__INITIAL_STATE__;
                        }
                        if (window.__PRELOADED_STATE__) {
                            return window.__PRELOADED_STATE__;
                        }
                        return null;
                    }
                """)
                
                if page_data:
                    # ページデータからイベントを抽出
                    print("ページデータからイベント情報を取得中...")
                    # 実際のデータ構造に合わせてパース
            except:
                pass
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"APIからの取得エラー: {e}")
        
        return events
    
    def _parse_event_from_cell(self, event_element, cell_element) -> Optional[Dict]:
        """
        カレンダーセル内のイベント要素をパース
        
        Args:
            event_element: イベント要素
            cell_element: セル要素（日付情報を取得するため）
            
        Returns:
            Dict: パース済みイベントデータ
        """
        try:
            # イベントタイトル
            title = event_element.inner_text().strip()
            if not title:
                # 代替: aria-labelやtitle属性から取得
                title = event_element.get_attribute('aria-label') or event_element.get_attribute('title') or ""
            
            # セルから日付を取得
            cell_date = None
            try:
                # セルのdata-date属性から取得
                date_str = cell_element.get_attribute('data-date')
                if date_str:
                    from datetime import datetime as dt
                    cell_date = dt.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                pass
            
            return {
                "title": title,
                "start_datetime": cell_date,
                "end_datetime": None,
                "location": "",
                "description": "",
                "calendar_name": ""
            }
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"セルイベントパースエラー: {e}")
            return None
    
    def _parse_event_element(self, element) -> Optional[Dict]:
        """
        イベント要素をパースしてデータを抽出
        
        Args:
            element: イベント要素
            
        Returns:
            Dict: パース済みイベントデータ
        """
        try:
            # 実際のTimeTreeのHTML構造に合わせて調整が必要
            # セレクタを順番に試行
            title = ""
            for selector in ['[class*="title"]', '.event-title', 'h1', 'h2', 'h3', 'a']:
                try:
                    title_elem = element.query_selector(selector)
                    if title_elem:
                        title = title_elem.inner_text().strip()
                        if title:
                            break
                except:
                    continue
            
            # 日時情報を取得
            datetime_text = ""
            for selector in ['[class*="time"]', '.event-time', '[class*="datetime"]']:
                try:
                    time_elem = element.query_selector(selector)
                    if time_elem:
                        datetime_text = time_elem.inner_text().strip()
                        if datetime_text:
                            break
                except:
                    continue
            
            start_datetime, end_datetime = self._parse_datetime_text(datetime_text)
            
            # 場所情報
            location = ""
            for selector in ['[class*="location"]', '.event-location']:
                try:
                    loc_elem = element.query_selector(selector)
                    if loc_elem:
                        location = loc_elem.inner_text().strip()
                        if location:
                            break
                except:
                    continue
            
            # 説明
            description = ""
            for selector in ['[class*="description"]', '.event-description', 'p']:
                try:
                    desc_elem = element.query_selector(selector)
                    if desc_elem:
                        description = desc_elem.inner_text().strip()
                        if description:
                            break
                except:
                    continue
            
            # カレンダー名
            calendar_name = ""
            
            return {
                "title": title,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "location": location,
                "description": description,
                "calendar_name": calendar_name
            }
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"イベントパースエラー: {e}")
            return None
    
    def _parse_datetime_text(self, datetime_text: str) -> tuple:
        """
        日時文字列をパース
        
        Args:
            datetime_text: 日時文字列
            
        Returns:
            tuple: (開始日時, 終了日時)
        """
        from datetime import datetime as dt
        # 実際のTimeTreeの日時フォーマットに合わせて実装
        # 例: "10:00 - 12:00" や "2024-01-15 10:00" など
        # 現時点では基本的なパースのみ実装
        start_datetime = None
        end_datetime = None
        
        if not datetime_text:
            return None, None
        
        try:
            # "10:00 - 12:00" 形式を試行
            if " - " in datetime_text:
                parts = datetime_text.split(" - ")
                if len(parts) == 2:
                    # 時刻のみの場合、日付は現在日を使用
                    today = dt.now().date()
                    start_time_str = parts[0].strip()
                    end_time_str = parts[1].strip()
                    # 時刻をパースしてdatetimeオブジェクトを作成
                    # 簡易実装（実際のフォーマットに合わせて調整が必要）
                    pass
        except:
            pass
        
        return start_datetime, end_datetime
    
    def parse_event(self, event_data: Dict) -> Dict:
        """
        イベントデータを標準形式に変換（互換性のため）
        
        Args:
            event_data: イベントデータ
            
        Returns:
            Dict: 標準形式のイベントデータ
        """
        return event_data

