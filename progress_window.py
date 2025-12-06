"""
進捗表示ウィンドウモジュール
処理状況をビジュアルに表示するGUIウィンドウ
"""
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread, Event
import queue
import sys
from typing import Optional


class ProgressWindow:
    """処理状況を表示するウィンドウ"""
    
    def __init__(self, title: str = "TimeTreeExport - 処理状況"):
        """
        初期化
        
        Args:
            title: ウィンドウタイトル
        """
        self.title = title
        self.root: Optional[tk.Tk] = None
        self.text_widget: Optional[scrolledtext.ScrolledText] = None
        self.status_label: Optional[tk.Label] = None
        self.message_queue = queue.Queue()
        self.is_running = Event()
        self.thread: Optional[Thread] = None
        
    def _create_window(self):
        """ウィンドウを作成"""
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # ステータスラベル
        self.status_label = tk.Label(
            self.root,
            text="準備中...",
            font=("Arial", 12, "bold"),
            anchor="w",
            bg="#f0f0f0",
            padx=10,
            pady=5
        )
        self.status_label.pack(fill=tk.X)
        
        # ログ表示エリア
        self.text_widget = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#ffffff",
            fg="#000000",
            state=tk.DISABLED
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 閉じるボタン
        close_button = tk.Button(
            self.root,
            text="閉じる",
            command=self.close,
            bg="#d32f2f",
            fg="white",
            font=("Arial", 10),
            padx=20,
            pady=5
        )
        close_button.pack(pady=5)
        
        # ウィンドウを閉じる時の処理
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        
        # メッセージキューを処理
        self.root.after(100, self._process_queue)
        
    def _process_queue(self):
        """メッセージキューを処理して表示を更新"""
        try:
            while True:
                try:
                    message = self.message_queue.get_nowait()
                    if message is None:  # 終了シグナル
                        return
                    
                    if isinstance(message, dict):
                        msg_type = message.get("type", "log")
                        content = message.get("content", "")
                        
                        if msg_type == "status":
                            self._update_status(content)
                        elif msg_type == "log":
                            self._append_log(content)
                        elif msg_type == "success":
                            self._append_log(content, tag="success")
                        elif msg_type == "error":
                            self._append_log(content, tag="error")
                        elif msg_type == "warning":
                            self._append_log(content, tag="warning")
                except queue.Empty:
                    break
        except Exception as e:
            print(f"メッセージ処理エラー: {e}")
        
        if self.root:
            self.root.after(100, self._process_queue)
    
    def _update_status(self, status: str):
        """ステータスラベルを更新"""
        if self.status_label:
            self.status_label.config(text=status)
    
    def _append_log(self, message: str, tag: str = "log"):
        """ログメッセージを追加"""
        if not self.text_widget:
            return
        
        self.text_widget.config(state=tk.NORMAL)
        
        # タグに応じて色を設定
        tag_configs = {
            "success": {"foreground": "#2e7d32", "font": ("Consolas", 9, "bold")},
            "error": {"foreground": "#d32f2f", "font": ("Consolas", 9, "bold")},
            "warning": {"foreground": "#f57c00", "font": ("Consolas", 9, "bold")},
            "log": {"foreground": "#000000"}
        }
        
        # タグを登録
        if tag not in self.text_widget.tag_names():
            self.text_widget.tag_config(tag, **tag_configs.get(tag, tag_configs["log"]))
        
        # メッセージを追加
        self.text_widget.insert(tk.END, message + "\n", tag)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)
        
        # ウィンドウを更新
        self.root.update_idletasks()
    
    def start(self):
        """ウィンドウを表示開始"""
        self.is_running.set()
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        """ウィンドウのメインループを実行"""
        self._create_window()
        if self.root:
            self.root.mainloop()
    
    def update_status(self, status: str):
        """ステータスを更新（スレッドセーフ）"""
        self.message_queue.put({"type": "status", "content": status})
    
    def log(self, message: str):
        """ログメッセージを追加（スレッドセーフ）"""
        self.message_queue.put({"type": "log", "content": message})
    
    def log_success(self, message: str):
        """成功メッセージを追加（スレッドセーフ）"""
        self.message_queue.put({"type": "success", "content": f"✓ {message}"})
    
    def log_error(self, message: str):
        """エラーメッセージを追加（スレッドセーフ）"""
        self.message_queue.put({"type": "error", "content": f"✗ {message}"})
    
    def log_warning(self, message: str):
        """警告メッセージを追加（スレッドセーフ）"""
        self.message_queue.put({"type": "warning", "content": f"⚠ {message}"})
    
    def close(self):
        """ウィンドウを閉じる"""
        self.is_running.clear()
        if self.root:
            self.root.quit()
            self.root.destroy()
        self.message_queue.put(None)  # 終了シグナル
    
    def wait_for_close(self):
        """ウィンドウが閉じられるまで待機"""
        if self.thread:
            self.thread.join()


# グローバルな進捗ウィンドウインスタンス（他のモジュールからアクセス可能）
_global_progress_window: Optional[ProgressWindow] = None


def set_global_progress_window(progress_window: ProgressWindow):
    """グローバルな進捗ウィンドウを設定"""
    global _global_progress_window
    _global_progress_window = progress_window


def get_global_progress_window() -> Optional[ProgressWindow]:
    """グローバルな進捗ウィンドウを取得"""
    return _global_progress_window


def log_to_window(message: str, msg_type: str = "log"):
    """
    グローバルな進捗ウィンドウにログを出力
    
    Args:
        message: ログメッセージ
        msg_type: メッセージタイプ（log, success, error, warning）
    """
    global _global_progress_window
    if _global_progress_window:
        if msg_type == "success":
            _global_progress_window.log_success(message)
        elif msg_type == "error":
            _global_progress_window.log_error(message)
        elif msg_type == "warning":
            _global_progress_window.log_warning(message)
        else:
            _global_progress_window.log(message)

