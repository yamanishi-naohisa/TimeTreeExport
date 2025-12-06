"""
ログ出力モジュール
ファイルとコンソール、進捗ウィンドウにログを出力する
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import config

# 進捗ウィンドウへのアクセスを試行
try:
    from progress_window import get_global_progress_window
    HAS_PROGRESS_WINDOW = True
except ImportError:
    HAS_PROGRESS_WINDOW = False


class ProgressWindowHandler(logging.Handler):
    """進捗ウィンドウにログを出力するハンドラー"""
    
    def emit(self, record):
        """ログレコードを進捗ウィンドウに出力"""
        try:
            if HAS_PROGRESS_WINDOW:
                progress_window = get_global_progress_window()
                if progress_window:
                    log_message = self.format(record)
                    if record.levelno >= logging.ERROR:
                        progress_window.log_error(log_message)
                    elif record.levelno >= logging.WARNING:
                        progress_window.log_warning(log_message)
                    elif record.levelno >= logging.INFO:
                        progress_window.log(log_message)
        except Exception:
            pass  # 進捗ウィンドウが利用できない場合は無視


def setup_logger(log_file: Optional[str] = None) -> logging.Logger:
    """
    ロガーをセットアップ
    
    Args:
        log_file: ログファイルのパス（Noneの場合は自動生成）
        
    Returns:
        logging.Logger: セットアップ済みロガー
    """
    # ロガーを作成
    logger = logging.getLogger('TimeTreeExport')
    logger.setLevel(logging.DEBUG)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # ログフォーマット
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # 進捗ウィンドウハンドラー
    if HAS_PROGRESS_WINDOW:
        progress_handler = ProgressWindowHandler()
        progress_handler.setLevel(logging.INFO)
        progress_handler.setFormatter(simple_formatter)
        logger.addHandler(progress_handler)
    
    # ファイルハンドラー
    if log_file is None:
        log_dir = Path(config.OUTPUT_DIR)
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"timetree_export_{timestamp}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"ログファイル: {log_file}")
    
    return logger


# グローバルロガー
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """グローバルロガーを取得（初期化されていない場合は初期化）"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger

