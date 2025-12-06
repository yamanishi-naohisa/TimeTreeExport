"""
TimeTree スクレイパーモジュール
ブラウザ自動化を使用してTimeTreeからスケジュールを取得する
"""
from playwright.sync_api import sync_playwright, Page, Browser
from datetime import datetime
from typing import List, Dict, Optional
import time
import config

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
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        self.page.set_default_timeout(self.timeout)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了"""
        # エラーが発生した場合や、デバッグモードの場合は詳細を表示
        if exc_type is not None:
            print(f"\nエラーが発生しました: {exc_type.__name__}")
            if exc_val:
                print(f"エラー内容: {exc_val}")
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
        
        # デバッグモードでブラウザを開いたままにする場合
        if self.keep_open:
            print("\nデバッグモード: ブラウザを開いたままにします。")
            print("ブラウザを閉じるには、手動で閉じるか、Enterキーを押してください...")
            try:
                input()
            except:
                pass
        
        if self.browser and not self.keep_open:
            self.browser.close()
        if self.playwright and not self.keep_open:
            self.playwright.stop()
    
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
            print(f"TimeTreeにログイン中... (メール: {email})")
            
            # ログインページに移動
            login_url = f"{self.base_url}/signin"
            print(f"ログインページにアクセス: {login_url}")
            self.page.goto(login_url, wait_until="networkidle")
            time.sleep(self.wait_time)
            print(f"現在のURL: {self.page.url}")
            
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
            time.sleep(3)  # ログイン処理を待つ
            time.sleep(self.wait_time)
            
            # ログイン成功を確認（URLがログインページでないことを確認）
            current_url = self.page.url
            if "login" not in current_url.lower():
                print("ログイン成功")
                return True
            else:
                print("警告: ログインページから遷移していない可能性があります")
                return False
                
        except Exception as e:
            print(f"ログインエラー: {e}")
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
                # スクリーンショットを保存
                self.page.screenshot(path="login_error.png")
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
            print(f"スケジュールを取得中... (開始日: {from_date.strftime('%Y-%m-%d')})")
            
            # カレンダーページに移動
            if calendar_id:
                calendar_url = f"{self.base_url}/calendars/{calendar_id}"
            else:
                calendar_url = f"{self.base_url}/calendars"
            
            self.page.goto(calendar_url, wait_until="networkidle")
            time.sleep(self.wait_time)
            
            # カレンダーが読み込まれるまで待機
            print("カレンダーページの読み込みを待機中...")
            print(f"現在のURL: {self.page.url}")
            print(f"ページタイトル: {self.page.title()}")
            
            # JavaScriptで動的に読み込まれるコンテンツを待つ
            time.sleep(self.wait_time * 3)  # より長く待機
            
            # カレンダー要素が表示されるまで待機を試行
            try:
                self.page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            
            # デバッグ用: ページのHTML構造を確認（必ず実行）
            page_content = self.page.content()
            with open("debug_calendar_page.html", "w", encoding="utf-8") as f:
                f.write(page_content)
            print("デバッグ: カレンダーページのHTMLを debug_calendar_page.html に保存しました")
            self.page.screenshot(path="debug_calendar_page.png")
            print("デバッグ: カレンダーページのスクリーンショットを debug_calendar_page.png に保存しました")
            
            if config.DEBUG_MODE:
                print(f"ページタイトル: {self.page.title()}")
                print(f"現在のURL: {self.page.url}")
                print(f"HTMLのサイズ: {len(page_content)} 文字")
            
            # イベント要素を取得
            events = []
            
            # 複数の方法でイベントを取得
            # 方法1: カレンダーグリッドから取得（月表示の場合）
            events.extend(self._get_events_from_calendar_grid(from_date))
            
            # 方法2: イベントリストから取得（リスト表示の場合）
            events.extend(self._get_events_from_event_list(from_date))
            
            # 方法3: API/JSONから取得（TimeTreeが内部で使用しているAPI）
            api_events = self._get_events_from_api(from_date)
            if api_events:
                events.extend(api_events)
            
            # 重複を除去（同じイベントが複数の方法で取得される可能性がある）
            unique_events = []
            seen_titles = set()
            for event in events:
                event_key = f"{event.get('title', '')}_{event.get('start_datetime', '')}"
                if event_key not in seen_titles and event.get('title'):
                    seen_titles.add(event_key)
                    unique_events.append(event)
            
            events = unique_events
            
            # 日付でフィルタリング（今日以降のみ）
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
            
            print(f"{len(filtered_events)} 件のイベントを取得しました（フィルタリング後: {len(events)} -> {len(filtered_events)}）")
            
            if len(filtered_events) == 0:
                print("警告: イベントが見つかりませんでした")
                if not config.DEBUG_MODE:
                    print("ヒント: DEBUG_MODE=True に設定すると、ページHTMLとスクリーンショットが保存されます")
            
            return filtered_events
            
        except Exception as e:
            print(f"イベント取得エラー: {e}")
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
                self.page.screenshot(path="event_error.png")
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

