# This file is part of empaths-tg-bot
#
# empaths-tg-bot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# empaths-tg-bot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with empaths-tg-bot. If not, see <https://www.gnu.org/licenses/>.


import logging
import os
from dotenv import load_dotenv
load_dotenv() 
from telegram.ext import (
    ApplicationBuilder,
)
from database import init_db
from conversation_handler import moderator_conv_handler, player_conv_handler
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
    application = ApplicationBuilder().token(TOKEN).read_timeout(60).write_timeout(60).build()
    application.add_handler(moderator_conv_handler)
    application.add_handler(player_conv_handler)
    application.add_error_handler(error_handler)
    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()
