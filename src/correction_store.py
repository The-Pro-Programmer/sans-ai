import sqlite3

class CorrectionStore:
    def __init__(self, db_path="data/corrections.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT UNIQUE,
            corrected_translation TEXT
        )
        """)

    def save(self, input_text, corrected_translation):
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO corrections (input_text, corrected_translation) VALUES (?, ?)",
                (input_text, corrected_translation)
            )
            self.conn.commit()
        except Exception as e:
            print("Error saving correction:", e)

    def get(self, input_text):
        cursor = self.conn.execute(
            "SELECT corrected_translation FROM corrections WHERE input_text = ?",
            (input_text,)
        )
        result = cursor.fetchone()
        return result[0] if result else None