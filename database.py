import sqlite3
from typing import Optional, List, Dict

class ScheduleDatabase:
    def __init__(self, db_name: str = "schedule.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_number INTEGER NOT NULL,
                    class_name TEXT NOT NULL,
                    day_of_week TEXT NOT NULL,
                    lesson_number INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    teacher TEXT,
                    classroom TEXT,
                    UNIQUE(school_number, class_name, day_of_week, lesson_number)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    school_number INTEGER NOT NULL,
                    class_name TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_user_preference(self, user_id: int, school_number: int, class_name: str):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_settings (user_id, school_number, class_name)
                    VALUES (?, ?, ?)
                """, (user_id, school_number, class_name))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def get_user_preference(self, user_id: int) -> Optional[tuple]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT school_number, class_name FROM user_settings WHERE user_id = ?
            """, (user_id,))
            return cursor.fetchone()

    def add_lesson(self, school_number: int, class_name: str, day_of_week: str,
                   lesson_number: int, subject: str, teacher: str = None,
                   classroom: str = None) -> bool:
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO schedules
                    (school_number, class_name, day_of_week, lesson_number, subject, teacher, classroom)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (school_number, class_name, day_of_week, lesson_number, subject, teacher, classroom))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def get_schedule(self, school_number: int, class_name: str,
                     day_of_week: Optional[str] = None) -> List[Dict]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            if day_of_week:
                cursor.execute("""
                    SELECT day_of_week, lesson_number, subject, teacher, classroom
                    FROM schedules
                    WHERE school_number = ? AND class_name = ? AND day_of_week = ?
                    ORDER BY lesson_number
                """, (school_number, class_name, day_of_week))
            else:
                cursor.execute("""
                    SELECT day_of_week, lesson_number, subject, teacher, classroom
                    FROM schedules
                    WHERE school_number = ? AND class_name = ?
                    ORDER BY
                        CASE day_of_week
                            WHEN 'Понедельник' THEN 1
                            WHEN 'Вторник' THEN 2
                            WHEN 'Среда' THEN 3
                            WHEN 'Четверг' THEN 4
                            WHEN 'Пятница' THEN 5
                            WHEN 'Суббота' THEN 6
                            ELSE 7
                        END,
                        lesson_number
                """, (school_number, class_name))
            rows = cursor.fetchall()
            lessons = []
            for row in rows:
                lessons.append({
                    'day_of_week': row[0],
                    'lesson_number': row[1],
                    'subject': row[2],
                    'teacher': row[3],
                    'classroom': row[4]
                })
            return lessons

    def add_sample_data(self):
        sample_schedule = [
            (1, "9А", "Понедельник", 1, "Математика", "Иванов И.И.", "201"),
            (1, "9А", "Понедельник", 2, "Русский язык", "Петрова А.С.", "105"),
            (1, "10Б", "Понедельник", 1, "Физика", "Сидоров П.П.", "301"),
        ]
        for lesson in sample_schedule:
            self.add_lesson(*lesson)

if __name__ == "__main__":
    db = ScheduleDatabase()
    db.init_database()
