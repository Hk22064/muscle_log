import sqlite3

def initialize_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Exercise (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL  -- カテゴリを追加
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TrainingLog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER,
            weight REAL,
            reps INTEGER,
            sets INTEGER,
            date TEXT,
            FOREIGN KEY (exercise_id) REFERENCES Exercise(id)
        )
    """)

    conn.commit()
    conn.close()

def get_progress_data(exercise_id):

    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, weight, reps, sets 
            FROM TrainingLog 
            WHERE exercise_id = ? 
            ORDER BY date ASC, sets ASC
        """, (exercise_id,))
        data = cursor.fetchall()
        conn.close()
        return data
    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
        return []
