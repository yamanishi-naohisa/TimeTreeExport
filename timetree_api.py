"""
TimeTree APIアクセスモジュール
"""
import requests
from datetime import datetime
from typing import List, Dict, Optional
import config
import utils


class TimeTreeAPI:
    """TimeTree APIへのアクセスを管理するクラス"""
    
    def __init__(self, access_token: str, base_url: str = None):
        """
        初期化
        
        Args:
            access_token: TimeTree APIアクセストークン
            base_url: APIベースURL（デフォルト: configから取得）
        """
        self.access_token = access_token
        self.base_url = base_url or config.TIMETREE_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_events(self, calendar_id: Optional[str] = None, 
                   from_date: Optional[datetime] = None) -> List[Dict]:
        """
        イベントを取得
        
        Args:
            calendar_id: カレンダーID（Noneの場合は全カレンダー）
            from_date: 取得開始日（Noneの場合は今日）
            
        Returns:
            List[Dict]: イベントのリスト
            
        Note:
            このメソッドは仮実装です。
            TimeTreeの実際のAPI仕様に合わせて実装を変更してください。
        """
        if from_date is None:
            from_date = utils.get_today_start()
        
        # TODO: 実際のAPIエンドポイントに合わせて実装
        # 現在は仮の実装
        url = f"{self.base_url}/calendars"
        if calendar_id:
            url = f"{self.base_url}/calendars/{calendar_id}/events"
        else:
            url = f"{self.base_url}/events"
        
        params = {
            "from": from_date.isoformat(),
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # TODO: 実際のAPIレスポンス構造に合わせてパース
            events = data.get("data", [])
            return events
            
        except requests.exceptions.RequestException as e:
            print(f"APIアクセスエラー: {e}")
            if config.DEBUG_MODE:
                print(f"URL: {url}")
                print(f"Response: {response.text if 'response' in locals() else 'N/A'}")
            raise
    
    def parse_event(self, event_data: Dict) -> Dict:
        """
        イベントデータをパースして標準形式に変換
        
        Args:
            event_data: APIから取得した生のイベントデータ
            
        Returns:
            Dict: パース済みイベントデータ
        """
        # TODO: 実際のAPIレスポンス構造に合わせて実装
        return {
            "title": event_data.get("title", ""),
            "start_datetime": self._parse_datetime(event_data.get("start_at")),
            "end_datetime": self._parse_datetime(event_data.get("end_at")),
            "location": event_data.get("location", ""),
            "description": event_data.get("description", ""),
            "calendar_name": event_data.get("calendar", {}).get("name", ""),
        }
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """
        日時文字列をdatetimeオブジェクトに変換
        
        Args:
            datetime_str: ISO形式の日時文字列
            
        Returns:
            datetime: 変換されたdatetimeオブジェクト
        """
        if not datetime_str:
            return None
        
        try:
            # ISO形式の日時文字列をパース
            return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

