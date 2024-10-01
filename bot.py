# bot.py

import logging
import os
from dotenv import load_dotenv
load_dotenv() 
from telegram.ext import (
    ApplicationBuilder, 
    MessageHandler, 
    filters, 
    CommandHandler, 
    ConversationHandler
)
from database import init_db
from conversation_handler import conv_handler
from game_process_handlers import check_player_response, execute_token
from game_set_handlers import show_setup_handler
from telegram.ext import ContextTypes
from telegram import Update

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения.")

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
    init_db()
    application = ApplicationBuilder().token(TOKEN).build()

    # Добавляем основной ConversationHandler
    application.add_handler(conv_handler)
    
    # Добавляем отдельный MessageHandler для обработки ответов игроков
    player_response_handler = MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        check_player_response
    )
    application.add_handler(player_response_handler)

    # Добавляем обработчик для execute_token
    execute_token_handler = MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        execute_token
    )
    application.add_handler(execute_token_handler)

    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()
