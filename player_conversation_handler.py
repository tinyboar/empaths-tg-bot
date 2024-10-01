# player_conversation_handler.py

from telegram.ext import ConversationHandler, MessageHandler, filters
from game_process_handlers import execute_token
from constants import EXECUTE_TOKEN

player_conv_handler = ConversationHandler(
    entry_points=[],
    states={
        EXECUTE_TOKEN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, execute_token)
        ],
    },
    fallbacks=[]
)
