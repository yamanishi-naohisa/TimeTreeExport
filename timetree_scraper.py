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
            try:
                # タイムアウトを設定してページ遷移
                self.page.goto(login_url, wait_until="domcontentloaded", timeout=self.timeout)
                logger.debug("ページ遷移が完了しました")
            except Exception as e:
                logger.warning(f"ページ遷移でエラーが発生しましたが、続行します: {e}")
                # 既にページが読み込まれている可能性があるので続行
            
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
            
            # ログインボタンクリック前のURLを記録
            initial_url = self.page.url
            logger.debug(f"ログインボタンクリック前のURL: {initial_url}")
            
            # ログインボタンをクリック（ナビゲーションを待機するためにコンテキストマネージャーを使用）
            if login_button:
                logger.info("ログインボタンをクリックします...")
                print("ログインボタンをクリックしました")
                try:
                    # ナビゲーション待機と同時にクリック
                    with self.page.expect_navigation(timeout=self.timeout, wait_until="domcontentloaded"):
                        login_button.click()
                    logger.debug("ナビゲーションが完了しました")
                except Exception as e:
                    logger.warning(f"ナビゲーション待機でタイムアウトまたはエラー: {e}")
                    # ナビゲーションが発生しない場合でも続行（既に遷移済みの可能性）
            else:
                print("ログインボタンが見つからないため、Enterキーで送信を試行します")
                try:
                    with self.page.expect_navigation(timeout=self.timeout, wait_until="domcontentloaded"):
                        self.page.keyboard.press("Enter")
                    logger.debug("Enterキー押下後のナビゲーションが完了しました")
                except Exception as e:
                    logger.warning(f"ナビゲーション待機でタイムアウトまたはエラー: {e}")
            
            # 追加の待機時間（JavaScriptの実行を待つ）
            logger.info("ログイン処理を待機中...")
            time.sleep(2)  # 基本待機時間
            
            # URL変更を待つ（最大10秒、0.5秒ごとにチェック）
            logger.debug("URL変更を待機中...")
            url_changed = False
            max_wait_attempts = 20  # 10秒
            for i in range(max_wait_attempts):
                try:
                    current_url = self.page.url
                    if current_url != initial_url:
                        url_changed = True
                        logger.info(f"URL変更を検出: {initial_url} -> {current_url}")
                        break
                    time.sleep(0.5)
                except KeyboardInterrupt:
                    logger.warning("URL待機中に割り込みが発生しましたが、処理を続行します")
                    break
                except Exception as e:
                    logger.debug(f"URL確認中のエラー: {e}")
            
            # ページ読み込み完了を待つ
            try:
                logger.debug("ページ読み込み完了を待機中...")
                self.page.wait_for_load_state("networkidle", timeout=10000)  # 最大10秒
                logger.debug("ページ読み込みが完了しました")
            except Exception as e:
                logger.debug(f"networkidle待機でタイムアウトまたはエラー（続行します）: {e}")
                # タイムアウトしても続行
                try:
                    self.page.wait_for_load_state("load", timeout=5000)
                    logger.debug("load状態になりました")
                except:
                    pass
            
            # ログイン成功を確認（複数の方法で確認）
            current_url = self.page.url
            page_title = self.page.title()
            logger.info(f"ログイン後のURL: {current_url}")
            logger.info(f"ページタイトル: {page_title}")
            
            # 方法1: URLがログインページから変更されているか
            url_check = (current_url != initial_url and 
                        "signin" not in current_url.lower())
            logger.debug(f"URL判定: {url_check} (初期: {initial_url}, 現在: {current_url})")
            
            # 方法2: カレンダーページのURLか確認
            calendar_url_patterns = [
                "/calendars" in current_url,
                "calendar" in current_url.lower() and "signin" not in current_url.lower(),
                "timetreeapp.com" in current_url and "signin" not in current_url.lower()
            ]
            has_calendar_url = any(calendar_url_patterns)
            logger.debug(f"カレンダーURL判定: {has_calendar_url}")
            
            # 方法3: カレンダーページの特定要素を探す（より確実な方法）
            has_calendar_elements = False
            try:
                # TimeTreeのカレンダーページに特有の要素を探す
                calendar_selectors = [
                    'a[href*="/calendars/"]',  # カレンダーリンク
                    '[class*="calendar"]',  # カレンダークラス
                    '[data-testid*="calendar"]',  # テストID
                    'nav',  # ナビゲーション要素
                    '[role="main"]',  # メインコンテンツ
                    'header',  # ヘッダー要素
                    '[class*="event"]',  # イベント要素
                ]
                
                logger.debug("カレンダー要素を検索中...")
                for selector in calendar_selectors:
                    try:
                        # 要素が表示されるまで待機（タイムアウト短縮）
                        self.page.wait_for_selector(selector, timeout=3000, state="visible")
                        elements = self.page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            has_calendar_elements = True
                            logger.info(f"カレンダー要素を発見: {selector} ({len(elements)}個)")
                            break
                    except Exception as e:
                        logger.debug(f"セレクタ {selector} で要素が見つかりませんでした: {type(e).__name__}")
                        continue
                
                # 追加チェック: ログインフォームが存在しないことを確認
                if not has_calendar_elements:
                    try:
                        login_form = self.page.query_selector('form[action*="signin"], form[method="post"]')
                        if login_form and login_form.is_visible():
                            logger.warning("ログインフォームがまだ表示されています")
                            has_calendar_elements = False
                        else:
                            # ログインフォームがない = ログイン済みの可能性が高い
                            logger.debug("ログインフォームが見つかりません（ログイン済みの可能性があります）")
                            if url_check or has_calendar_url:
                                has_calendar_elements = True  # 他の判定が成功していればOK
                    except:
                        pass
                        
            except Exception as e:
                logger.debug(f"カレンダー要素の検索でエラー: {e}")
            
            # 方法4: ページタイトルで確認
            title_check = page_title and "TimeTree" in page_title and "Sign in" not in page_title
            logger.debug(f"タイトル判定: {title_check} (タイトル: {page_title})")
            
            # ログイン成功の判定（複数の条件を組み合わせてより確実に判定）
            # headlessモードの場合はより厳密に判定
            if config.BROWSER_HEADLESS:
                # headlessモード: URL変更 + (カレンダーURL または カレンダー要素 または タイトル)
                login_success = url_check and (has_calendar_url or has_calendar_elements or title_check)
            else:
                # 表示モード: いずれかの条件を満たせば成功（ユーザー確認があるため）
                login_success = url_check or has_calendar_url or has_calendar_elements or title_check
            
            logger.info(f"ログイン判定結果:")
            logger.info(f"  - URL変更: {url_changed}")
            logger.info(f"  - URL判定: {url_check}")
            logger.info(f"  - カレンダーURL判定: {has_calendar_url}")
            logger.info(f"  - カレンダー要素判定: {has_calendar_elements}")
            logger.info(f"  - タイトル判定: {title_check}")
            logger.info(f"  - headlessモード: {config.BROWSER_HEADLESS}")
            logger.info(f"  - 最終判定: {login_success}")
            
            if login_success:
                logger.info("ログイン成功を確認しました")
                print("ログイン成功")
                return True
            else:
                # headlessモードでは失敗として扱うが、表示モードでは警告のみ
                if config.BROWSER_HEADLESS:
                    logger.error(f"ログイン判定が失敗しました (URL: {current_url}, タイトル: {page_title})")
                    print(f"エラー: ログイン判定が失敗しました (URL: {current_url})")
                    return False
                else:
                    logger.warning(f"ログイン判定が失敗しました (URL: {current_url}, タイトル: {page_title})")
                    logger.warning("ただし、実際にカレンダーが表示されている可能性があります")
                    print(f"警告: ログイン判定が失敗しました (URL: {current_url})")
                    print("注意: 実際にカレンダーが表示されている場合は、処理を続行します")
                    # ユーザー確認があるため、続行を試みる
                    return True
                
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
            try:
                # タイムアウトを設定してページ遷移（networkidleは長時間待機する可能性があるので、domcontentloadedを使用）
                self.page.goto(calendar_url, wait_until="domcontentloaded", timeout=self.timeout)
                logger.debug("ページ遷移が完了しました")
            except Exception as e:
                logger.warning(f"ページ遷移でエラーが発生しましたが、続行します: {e}")
                # 既にページが読み込まれている可能性があるので続行
                current_url = self.page.url
                if calendar_url in current_url or "calendars" in current_url:
                    logger.info(f"カレンダーページには到達しているようです (URL: {current_url})")
                else:
                    logger.warning(f"期待したURLとは異なる可能性があります (期待: {calendar_url}, 実際: {current_url})")
            
            time.sleep(self.wait_time)
            
            # リダイレクトを待ってから実際のURLを取得（待機時間を最小化）
            logger.debug("リダイレクト後のURLを確認中...")
            initial_url = self.page.url
            logger.debug(f"初期URL: {initial_url}")
            
            # リダイレクトが発生するか確認（最大3秒、0.5秒ごとにチェック）
            redirect_detected = False
            try:
                for i in range(6):  # 0.5秒 × 6回 = 3秒
                    try:
                        time.sleep(0.5)
                    except KeyboardInterrupt:
                        # 外部要因（サーバー側のタイムアウトなど）による割り込みを無視して続行
                        logger.warning(f"リダイレクト待機中に割り込みが発生しましたが、処理を続行します ({i * 0.5}秒経過)")
                        break
                    current_url = self.page.url
                    if current_url != initial_url and "/calendars/" in current_url:
                        logger.info(f"リダイレクトを検出しました: {initial_url} -> {current_url}")
                        redirect_detected = True
                        break
            except KeyboardInterrupt:
                # リダイレクト待機処理全体で割り込みが発生した場合でも続行
                logger.warning("リダイレクト待機処理中に割り込みが発生しましたが、処理を続行します")
            
            if not redirect_detected:
                current_url = self.page.url
                logger.info(f"リダイレクトは発生しませんでした。現在のURL: {current_url}")
                if current_url == initial_url and current_url.endswith("/calendars"):
                    logger.info("カレンダー一覧ページから処理を続行します")
            
            # カレンダーが読み込まれるまで待機
            current_url = self.page.url
            page_title = self.page.title()
            logger.info(f"カレンダーページに到達しました")
            logger.info(f"現在のURL: {current_url}")
            logger.info(f"ページタイトル: {page_title}")
            print("カレンダーページの読み込みを待機中...")
            print(f"現在のURL: {current_url}")
            print(f"ページタイトル: {page_title}")
            
            # URLからカレンダーIDを抽出（/calendars/{calendar_id} の形式）
            actual_calendar_id = None
            if "/calendars/" in current_url:
                try:
                    url_parts = current_url.split("/calendars/")
                    if len(url_parts) > 1:
                        calendar_part = url_parts[1].split("/")[0].split("?")[0]  # パラメータやパスを除去
                        if calendar_part:
                            actual_calendar_id = calendar_part
                            logger.info(f"URLからカレンダーIDを抽出しました: {actual_calendar_id}")
                            if calendar_id and actual_calendar_id != calendar_id:
                                logger.warning(f"指定されたカレンダーID ({calendar_id}) と実際のカレンダーID ({actual_calendar_id}) が異なります")
                except Exception as e:
                    logger.debug(f"カレンダーIDの抽出でエラー: {e}")
            
            # JavaScriptで動的に読み込まれるコンテンツを待つ（待機時間を短縮・細かく分割）
            logger.debug(f"JavaScriptの読み込みを待機中... (待機時間: {self.wait_time}秒)")
            # 待機を細かく分割して、割り込みに対応しやすくする
            sleep_interval = 0.2  # 0.2秒ごとにチェック
            total_sleep = self.wait_time
            try:
                for i in range(int(total_sleep / sleep_interval)):
                    try:
                        time.sleep(sleep_interval)
                    except KeyboardInterrupt:
                        # 外部要因（サーバー側のタイムアウトなど）による割り込みを無視して続行
                        logger.warning(f"待機中に割り込みが発生しましたが、処理を続行します ({i * sleep_interval:.1f}秒経過)")
                        # 処理を続行
                        break
                logger.debug("待機が完了しました")
            except KeyboardInterrupt:
                # 待機処理全体で割り込みが発生した場合でも続行
                logger.warning("待機処理中に割り込みが発生しましたが、処理を続行します")
                logger.debug("待機処理を中断して続行します")
            
            # カレンダー要素が表示されるまで待機を試行
            try:
                logger.debug("load状態を待機中...")
                self.page.wait_for_load_state("load", timeout=5000)  # タイムアウトを5秒に短縮
                logger.debug("load状態になりました")
            except KeyboardInterrupt:
                # 外部要因による割り込みを無視して続行
                logger.warning("load状態待機中に割り込みが発生しましたが、処理を続行します")
            except Exception as e:
                logger.debug(f"load状態の待機でタイムアウトまたはエラー（続行します）: {e}")
                pass
            
            # 追加の待機時間を削除（不要な待機を削減）
            logger.debug("カレンダーコンテンツの処理を開始します")
            
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

