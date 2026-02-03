from typing import List, Dict
from datetime import datetime
import json
from pathlib import Path

class HistoryService:
    def __init__(self, storage_path: str = "data/history.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(exist_ok=True)
        self._ensure_file()
    
    def _ensure_file(self):
        if not self.storage_path.exists():
            self.storage_path.write_text("[]")
    
    def add_entry(self, query: str, response: str, model: str) -> Dict:
        history = self._load_history()
        entry = {
            "id": str(len(history) + 1),
            "query": query,
            "response": response,
            "model": model,
            "timestamp": datetime.utcnow().isoformat()
        }
        history.append(entry)
        self._save_history(history)
        return entry
    
    def get_history(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        history = self._load_history()
        return list(reversed(history))[offset:offset + limit]
    
    def clear_history(self) -> bool:
        self._save_history([])
        return True
    
    def _load_history(self) -> List[Dict]:
        try:
            return json.loads(self.storage_path.read_text())
        except Exception:
            return []
    
    def _save_history(self, history: List[Dict]):
        self.storage_path.write_text(json.dumps(history, indent=2))
