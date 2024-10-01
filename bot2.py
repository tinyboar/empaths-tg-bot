# bot.py

import logging
import os
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
from database import init_db
from conversation_handler import conv_handler
from telegram.ext import ContextTypes
from telegram import Update

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение конфигурационных данных из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения.")

# Конфигурация логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка при обработке вашего запроса.")

def main():
    # Инициализация базы данных
    init_db()

    # Создание приложения бота
    application = ApplicationBuilder().token(TOKEN).build()

    # Добавляем общий ConversationHandler в приложение
    application.add_handler(conv_handler)

    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()
