import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Optional, Any


class CacheService:
    """SQLite-based caching service for FDA data"""
    
    def __init__(self, db_path: str = "data/cache.db", ttl_hours: int = 24):
        self.db_path = db_path
        self.ttl_hours = ttl_hours
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        # Create data directory if it doesn't exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drug_name TEXT UNIQUE NOT NULL,
                    data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def get(self, drug_name: str) -> Optional[dict]:
        """Get cached data for a drug"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data, timestamp FROM cache WHERE drug_name = ?",
                (drug_name.lower(),)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            data_json, timestamp_str = row
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # Check if cache is still valid
            if datetime.now() - timestamp > timedelta(hours=self.ttl_hours):
                # Cache expired, delete it
                self.delete(drug_name)
                return None
            
            return json.loads(data_json)
    
    def set(self, drug_name: str, data: dict) -> None:
        """Cache data for a drug"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO cache (drug_name, data) VALUES (?, ?)",
                (drug_name.lower(), json.dumps(data))
            )
            conn.commit()
    
    def delete(self, drug_name: str) -> None:
        """Delete cached data for a drug"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache WHERE drug_name = ?", (drug_name.lower(),))
            conn.commit()
    
    def clear(self) -> None:
        """Clear all cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache")
            conn.commit()
    
    def get_cache_age(self, drug_name: str) -> Optional[int]:
        """Get cache age in seconds"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp FROM cache WHERE drug_name = ?",
                (drug_name.lower(),)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            timestamp = datetime.fromisoformat(row[0])
            age_seconds = int((datetime.now() - timestamp).total_seconds())
            return age_seconds
