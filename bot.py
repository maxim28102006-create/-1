"""
Telegram-бот для предоставления школьного расписания
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from database import ScheduleDatabase

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = ScheduleDatabase()

# Состояния диалога
SCHOOL_NUMBER, CLASS_NAME, DAY_OF_WEEK = range(3)

# Дни недели
DAYS_OF_WEEK = [
    "Понедельник", "Вторник", "Среда", "Четверг",
    "Пятница", "Суббота", "Вся неделя"
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_message = (
        "Привет! Я бот для предоставления школьного расписания.\n\n"
        "Доступные команды:\n"
        "/schedule - Получить расписание\n"
        "/help - Справка\n"
        "/cancel - Отменить текущую операцию"
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "Как пользоваться ботом:\n\n"
        "1. Используйте /schedule для получения расписания\n"
        "2. Введите номер школы\n"
        "3. Введите класс (например, 9А или 10Б)\n"
        "4. Выберите день недели или 'Вся неделя'\n\n"
        "Команды:\n"
        "/schedule - Получить расписание\n"
        "/help - Показать эту справку\n"
        "/cancel - Отменить текущую операцию"
    )
    await update.message.reply_text(help_text)


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса получения расписания"""
    await update.message.reply_text(
        "Введите номер школы (например, 1):"
    )
    return SCHOOL_NUMBER


async def get_school_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение номера школы"""
    try:
        school_number = int(update.message.text)
        context.user_data['school_number'] = school_number

        await update.message.reply_text(
            "Введите класс (например, 9А или 10Б):"
        )
        return CLASS_NAME
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите корректный номер школы (число):"
        )
        return SCHOOL_NUMBER


async def get_class_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение названия класса"""
    class_name = update.message.text.strip().upper()
    context.user_data['class_name'] = class_name

    # Создаем клавиатуру с днями недели
    keyboard = [
        [KeyboardButton(day) for day in DAYS_OF_WEEK[:3]],
        [KeyboardButton(day) for day in DAYS_OF_WEEK[3:6]],
        [KeyboardButton(DAYS_OF_WEEK[6])]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Выберите день недели:",
        reply_markup=reply_markup
    )
    return DAY_OF_WEEK


async def get_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение и отображение расписания"""
    day_of_week = update.message.text.strip()

    if day_of_week not in DAYS_OF_WEEK:
        await update.message.reply_text(
            "Пожалуйста, выберите день недели из предложенных вариантов."
        )
        return DAY_OF_WEEK

    school_number = context.user_data['school_number']
    class_name = context.user_data['class_name']

    # Получаем расписание из базы данных
    if day_of_week == "Вся неделя":
        lessons = db.get_schedule(school_number, class_name)
    else:
        lessons = db.get_schedule(school_number, class_name, day_of_week)

    if not lessons:
        await update.message.reply_text(
            f"К сожалению, расписание для школы {school_number}, класса {class_name} не найдено.\n\n"
            "Используйте /schedule для нового запроса."
        )
    else:
        # Форматируем расписание
        schedule_text = format_schedule(lessons, school_number, class_name, day_of_week)
        await update.message.reply_text(schedule_text)

    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END


def format_schedule(lessons, school_number, class_name, day_of_week):
    """
    Форматирование расписания для отображения

    Args:
        lessons: список уроков
        school_number: номер школы
        class_name: название класса
        day_of_week: день недели

    Returns:
        Отформатированная строка с расписанием
    """
    header = f"📚 Расписание школы {school_number}, класс {class_name}\n"
    if day_of_week != "Вся неделя":
        header += f"День: {day_of_week}\n"
    header += "=" * 40 + "\n\n"

    schedule_text = header

    current_day = None
    for lesson in lessons:
        # Если показываем расписание на всю неделю, добавляем заголовок дня
        if day_of_week == "Вся неделя" and lesson['day_of_week'] != current_day:
            current_day = lesson['day_of_week']
            schedule_text += f"\n📅 {current_day}\n"
            schedule_text += "-" * 40 + "\n"

        # Форматируем урок
        schedule_text += f"{lesson['lesson_number']}. {lesson['subject']}\n"

        if lesson['teacher']:
            schedule_text += f"   👨‍🏫 Учитель: {lesson['teacher']}\n"

        if lesson['classroom']:
            schedule_text += f"   🚪 Кабинет: {lesson['classroom']}\n"

        schedule_text += "\n"

    schedule_text += "Используйте /schedule для нового запроса."

    return schedule_text


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущей операции"""
    context.user_data.clear()
    await update.message.reply_text(
        "Операция отменена. Используйте /schedule для получения расписания."
    )
    return ConversationHandler.END


def main():
    """Запуск бота"""
    # Получаем токен бота из переменных окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в файле .env")
        return

    # Добавляем примерные данные в базу (для демонстрации)
    db.add_sample_data()

    # Создаем приложение
    application = Application.builder().token(token).build()

    # Создаем обработчик диалога для получения расписания
    schedule_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('schedule', schedule_command)],
        states={
            SCHOOL_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_school_number)],
            CLASS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_class_name)],
            DAY_OF_WEEK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_schedule)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Регистрируем обработчики
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(schedule_conv_handler)

    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
