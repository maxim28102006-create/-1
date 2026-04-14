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

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = ScheduleDatabase()

SCHOOL_NUMBER, CLASS_NAME, DAY_OF_WEEK = range(3)

DAYS_OF_WEEK = [
    "Понедельник", "Вторник", "Среда", "Четверг",
    "Пятница", "Суббота", "Вся неделя"
]

def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("📅 Мой класс"), KeyboardButton("🔍 Найти другое")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_pref = db.get_user_preference(user_id)

    if user_pref:
        school, class_name = user_pref
        message = (
            f"Привет! Рад видеть тебя снова.\n"
            f"Твой сохраненный класс: {school}-{class_name}.\n\n"
            "Нажми 'Мой класс', чтобы быстро глянуть уроки!"
        )
    else:
        message = (
            "Привет! Я бот с расписанием.\n"
            "Давай найдем твой класс. Нажми 'Найти другое' или введи /schedule."
        )

    await update.message.reply_text(message, reply_markup=get_main_menu_keyboard())

async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите номер школы (например, 1):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/cancel")]], resize_keyboard=True)
    )
    return SCHOOL_NUMBER

async def my_class_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pref = db.get_user_preference(user_id)

    if pref:
        school, class_name = pref
        context.user_data['school_number'] = school
        context.user_data['class_name'] = class_name

        keyboard = [
            [KeyboardButton(day) for day in DAYS_OF_WEEK[:3]],
            [KeyboardButton(day) for day in DAYS_OF_WEEK[3:6]],
            [KeyboardButton(DAYS_OF_WEEK[6])]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"Расписание для {school} школы, {class_name} класса.\nВыберите день:",
            reply_markup=reply_markup
        )
        return DAY_OF_WEEK
    else:
        await update.message.reply_text(
            "Ты еще не выбрал свой класс. Давай сделаем это сейчас!",
            reply_markup=get_main_menu_keyboard()
        )
        return await schedule_command(update, context)

async def get_school_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        school_number = int(update.message.text)
        context.user_data['school_number'] = school_number
        await update.message.reply_text("Введите класс (например, 9А или 10Б):")
        return CLASS_NAME
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (номер школы):")
        return SCHOOL_NUMBER

async def get_class_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    class_name = update.message.text.strip().upper()
    context.user_data['class_name'] = class_name

    user_id = update.effective_user.id
    school = context.user_data['school_number']
    db.save_user_preference(user_id, school, class_name)

    keyboard = [
        [KeyboardButton(day) for day in DAYS_OF_WEEK[:3]],
        [KeyboardButton(day) for day in DAYS_OF_WEEK[3:6]],
        [KeyboardButton(DAYS_OF_WEEK[6])]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"Запомнил: {school} школа, {class_name} класс!\nВыберите день:",
        reply_markup=reply_markup
    )
    return DAY_OF_WEEK

async def get_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day_of_week = update.message.text.strip()
    if day_of_week not in DAYS_OF_WEEK:
        await update.message.reply_text("Выберите день из меню.")
        return DAY_OF_WEEK

    school_number = context.user_data['school_number']
    class_name = context.user_data['class_name']

    lessons = db.get_schedule(school_number, class_name,
                              None if day_of_week == "Вся неделя" else day_of_week)

    if not lessons:
        await update.message.reply_text(
            "Расписание не найдено. Нажми /schedule, чтобы попробовать снова.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        schedule_text = format_schedule(lessons, school_number, class_name, day_of_week)
        await update.message.reply_text(schedule_text, reply_markup=get_main_menu_keyboard())

    context.user_data.clear()
    return ConversationHandler.END

def format_schedule(lessons, school_number, class_name, day_of_week):
    header = f"📚 Школа {school_number}, класс {class_name}\n"
    if day_of_week != "Вся неделя":
        header += f"День: {day_of_week}\n"
    header += "=" * 30 + "\n"

    schedule_text = header
    current_day = None
    for lesson in lessons:
        if day_of_week == "Вся неделя" and lesson['day_of_week'] != current_day:
            current_day = lesson['day_of_week']
            schedule_text += f"\n📅 {current_day}\n" + "-" * 20 + "\n"

        schedule_text += f"{lesson['lesson_number']}. {lesson['subject']} ({lesson['classroom'] or '???'})\n"

    return schedule_text

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Отмена.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Нет токена!")
        return

    application = Application.builder().token(token).build()

    schedule_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('schedule', schedule_command),
            MessageHandler(filters.Regex("^🔍 Найти другое$"), schedule_command),
            MessageHandler(filters.Regex("^📅 Мой класс$"), my_class_handler)
        ],
        states={
            SCHOOL_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_school_number)],
            CLASS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_class_name)],
            DAY_OF_WEEK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_schedule)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(schedule_conv_handler)

    logger.info("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
