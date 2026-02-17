import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ids_data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            is_attack INTEGER NOT NULL,
            confidence REAL NOT NULL,
            label TEXT NOT NULL,
            attack_type TEXT DEFAULT 'Unknown',
            threat_level TEXT DEFAULT 'Low',
            source_ip TEXT DEFAULT 'Edge Node'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event TEXT NOT NULL,
            details TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def log_prediction(is_attack, confidence, label, attack_type="Unknown", threat_level="Low", source_ip="Edge Node"):
    """Log a prediction to the database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO predictions (timestamp, is_attack, confidence, label, attack_type, threat_level, source_ip) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), int(is_attack), confidence, label, attack_type, threat_level, source_ip)
    )
    conn.commit()
    conn.close()

def get_attack_history(limit=50):
    """Get recent attack predictions"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM predictions WHERE is_attack = 1 ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_all_predictions(limit=100):
    """Get all recent predictions"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM predictions ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_stats():
    """Get aggregated statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE is_attack = 1")
    attacks = cursor.fetchone()[0]
    
    # Attack type distribution
    cursor.execute("""
        SELECT attack_type, COUNT(*) as count 
        FROM predictions WHERE is_attack = 1 
        GROUP BY attack_type ORDER BY count DESC
    """)
    attack_types = {row["attack_type"]: row["count"] for row in cursor.fetchall()}
    
    # Threat level distribution
    cursor.execute("""
        SELECT threat_level, COUNT(*) as count 
        FROM predictions WHERE is_attack = 1 
        GROUP BY threat_level
    """)
    threat_levels = {row["threat_level"]: row["count"] for row in cursor.fetchall()}
    
    # Hourly attack trend (last 24 entries)
    cursor.execute("""
        SELECT substr(timestamp, 1, 16) as time_bucket, COUNT(*) as count
        FROM predictions WHERE is_attack = 1
        GROUP BY time_bucket ORDER BY time_bucket DESC LIMIT 24
    """)
    hourly = [{"time": row["time_bucket"], "count": row["count"]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_predictions": total,
        "total_attacks": attacks,
        "benign_count": total - attacks,
        "detection_rate": round((attacks / total * 100), 2) if total > 0 else 0,
        "attack_types": attack_types,
        "threat_levels": threat_levels,
        "hourly_trend": list(reversed(hourly))
    }

def log_system_event(event, details=None):
    """Log a system event"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO system_log (timestamp, event, details) VALUES (?, ?, ?)",
        (datetime.now().isoformat(), event, details)
    )
    conn.commit()
    conn.close()
