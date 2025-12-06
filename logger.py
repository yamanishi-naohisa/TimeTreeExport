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
        
        # 古いログファイルを削除（最新10個だけ保持）
        try:
            cleanup_old_logs(log_dir, max_logs=10)
        except Exception as e:
            # ログファイル削除エラーは無視（ログ出力前なのでprintを使用）
            print(f"警告: 古いログファイルの削除でエラーが発生しました: {e}")
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"ログファイル: {log_file}")
    
    return logger


def cleanup_old_logs(log_dir: Path, max_logs: int = 10, pattern: str = "timetree_export_*.log"):
    """
    古いログファイルを削除して、最新のN個だけ保持する
    
    Args:
        log_dir: ログディレクトリ
        max_logs: 保持するログファイルの最大数
        pattern: ログファイルのパターン
    """
    try:
        log_files = list(log_dir.glob(pattern))
        if len(log_files) > max_logs:
            # 更新日時でソート（新しい順）
            log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            # 古いログファイルを削除
            for old_log in log_files[max_logs:]:
                try:
                    old_log.unlink()
                except Exception as e:
                    # 削除エラーは無視（ログ出力前なのでprintを使用）
                    print(f"警告: ログファイル {old_log} の削除に失敗しました: {e}")
    except Exception as e:
        # エラーは無視（ログ出力前なのでprintを使用）
        print(f"警告: ログファイルクリーンアップでエラーが発生しました: {e}")


# グローバルロガー
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """グローバルロガーを取得（初期化されていない場合は初期化）"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger

