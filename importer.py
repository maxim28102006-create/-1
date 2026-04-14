import pandas as pd
from database import ScheduleDatabase
import os


def run_import():
    file_name = "timetable.xlsx"

    # Проверяем, на месте ли файл
    if not os.path.exists(file_name):
        print(f"Ошибка! Файл {file_name} не найден в папке с проектом.")
        return

    db = ScheduleDatabase()

    try:
        # Читаем данные
        df = pd.read_excel(file_name)

        print("Начинаю загрузку данных...")

        for _, row in df.iterrows():
            db.add_lesson(
                school_number=int(row['school_number']),
                class_name=str(row['class_name']),
                day_of_week=str(row['day_of_week']),
                lesson_number=int(row['lesson_number']),
                subject=str(row['subject']),
                teacher=str(row['teacher']) if pd.notna(row['teacher']) else "",
                classroom=str(row['classroom']) if pd.notna(row['classroom']) else ""
            )

        print(f"Готово! Загружено строк: {len(df)}")

    except Exception as e:
        print(f"Произошла ошибка при чтении файла: {e}")


if __name__ == "__main__":
    run_import()
