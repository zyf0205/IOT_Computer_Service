import sqlite3
from config import DB_NAME


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dev_id TEXT,
            temperature INTEGER,
            humidity INTEGER,
            server_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()
    print(f"[数据库] 初始化完成: {DB_NAME}")


def save_sensor_data(dev_id, temperature, humidity, device_time):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO sensor_data (dev_id, temperature, humidity, server_time) VALUES (?, ?, ?, ?)",
            (dev_id, temperature, humidity, device_time),
        )

        conn.commit()
        conn.close()
        return True, None

    except Exception as e:
        return False, str(e)
