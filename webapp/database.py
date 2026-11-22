# webapp/database.py

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# ডেটাবেস ফাইলটি webapp ফোল্ডারেই সেভ হবে
DB_PATH = Path(__file__).parent / "health_monitoring.db"

def get_db_connection():
    """ডেটাবেস কানেকশন তৈরি করা"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # ডেটাকে ডিকশনারি এর মতো এক্সেস করার জন্য
    return conn

def init_db():
    """ডেটাবেস এবং টেবিল তৈরি করা (যদি না থাকে)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # predictions টেবিল তৈরি করা
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_type TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ইনডেক্স তৈরি করা যাতে কুয়েরি দ্রুত হয়
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_machine_type ON predictions(machine_type)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON predictions(timestamp)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully at:", DB_PATH)

def save_prediction(machine_type: str, machine_id: str, status: str, details: dict):
    """API থেকে পাওয়া প্রেডিকশন ডেটাবেসে সেভ করা"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # details ডিকশনারিকে JSON স্ট্রিং এ কনভার্ট করে সেভ করা
    details_json = json.dumps(details)
    
    cursor.execute('''
        INSERT INTO predictions (machine_type, machine_id, status, details)
        VALUES (?, ?, ?, ?)
    ''', (machine_type, machine_id, status, details_json))
    
    conn.commit()
    conn.close()

def get_recent_predictions(machine_type: str, limit: int = 50):
    """ড্যাশবোর্ডের জন্য সাম্প্রতিক প্রেডিকশনগুলো নিয়ে আসা"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, machine_type, machine_id, status, details, timestamp
        FROM predictions
        WHERE machine_type = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (machine_type, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Row objects কে ডিকশনারি লিস্টে কনভার্ট করা
    predictions = []
    for row in rows:
        pred = dict(row)
        pred['details'] = json.loads(pred['details'])  # JSON কে আবার ডিকশনারিতে রূপান্তর
        predictions.append(pred)
        
    return predictions

# সার্ভার চালু হওয়ার সময় ডেটাবেস ইনিশিয়ালাইজ করা
init_db()