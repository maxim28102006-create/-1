"""
Модуль для работы с базой данных расписаний
"""
import sqlite3
from typing import Optional, List, Dict


class ScheduleDatabase:
    """Класс для работы с базой данных расписаний"""

    def __init__(self, db_name: str = "schedule.db"):
        """
        Инициализация базы данных

        Args:
            db_name: имя файла базы данных
        """
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Создание таблиц в базе данных"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Таблица для расписаний
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

            conn.commit()

    def add_lesson(self, school_number: int, class_name: str, day_of_week: str,
                   lesson_number: int, subject: str, teacher: str = None,
                   classroom: str = None) -> bool:
        """
        Добавление урока в расписание

        Args:
            school_number: номер школы
            class_name: название класса (например, "9А")
            day_of_week: день недели (Понедельник, Вторник, и т.д.)
            lesson_number: номер урока
            subject: название предмета
            teacher: ФИО учителя (необязательно)
            classroom: номер кабинета (необязательно)

        Returns:
            True если успешно добавлено, False в случае ошибки
        """
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
            print(f"Ошибка при добавлении урока: {e}")
            return False

    def get_schedule(self, school_number: int, class_name: str,
                     day_of_week: Optional[str] = None) -> List[Dict]:
        """
        Получение расписания для класса

        Args:
            school_number: номер школы
            class_name: название класса
            day_of_week: день недели (если не указан, возвращается расписание на всю неделю)

        Returns:
            Список уроков в виде словарей
        """
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
        """Добавление примерных данных для тестирования"""
        sample_schedule = [
            # Школа 1, класс 9А
            (1, "9А", "Понедельник", 1, "Математика", "Иванов И.И.", "201"),
            (1, "9А", "Понедельник", 2, "Русский язык", "Петрова А.С.", "105"),
            (1, "9А", "Понедельник", 3, "Физика", "Сидоров П.П.", "301"),
            (1, "9А", "Понедельник", 4, "История", "Смирнова Е.А.", "208"),
            (1, "9А", "Вторник", 1, "Английский язык", "Козлова М.В.", "112"),
            (1, "9А", "Вторник", 2, "Химия", "Морозов Д.К.", "302"),
            (1, "9А", "Вторник", 3, "Литература", "Петрова А.С.", "105"),
            (1, "9А", "Вторник", 4, "Геометрия", "Иванов И.И.", "201"),

            # Школа 1, класс 10Б
            (1, "10Б", "Понедельник", 1, "Физика", "Сидоров П.П.", "301"),
            (1, "10Б", "Понедельник", 2, "Математика", "Иванов И.И.", "201"),
            (1, "10Б", "Понедельник", 3, "Информатика", "Новиков А.А.", "115"),
        ]

        for lesson in sample_schedule:
            self.add_lesson(*lesson)

        print("Примерные данные добавлены в базу данных")


if __name__ == "__main__":
    # Тестирование
    db = ScheduleDatabase()
    db.add_sample_data()

    print("\nРасписание для школы 1, класса 9А:")
    schedule = db.get_schedule(1, "9А")
    for lesson in schedule:
        print(f"{lesson['day_of_week']}, урок {lesson['lesson_number']}: {lesson['subject']}")
