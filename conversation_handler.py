from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from registration_handlers import (
    start,
    handle_password,
    get_username,
    skip,
    cancel
)
from game_set_handlers import (
    set_up_game,
    get_tokens_count,
    get_red_count,
    get_red_token_number,
    get_demon_token_number,
    get_red_token_red_neighbors
)
from constants import (
    HANDLE_PASSWORD,
    GET_USERNAME,
    SET_UP_GAME,
    GET_TOKENS_COUNT,
    GET_RED_COUNT,
    GET_RED_TOKEN_NUMBER,
    GET_DEMON_TOKEN_NUMBER,
    GET_RED_TOKEN_RED_NEIGHBORS
)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        HANDLE_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password),
            CommandHandler('skip', skip)
        ],
        GET_USERNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)
        ],
        SET_UP_GAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, set_up_game)
        ],
        GET_TOKENS_COUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_tokens_count)
        ],
        GET_RED_COUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_red_count)
        ],
        GET_RED_TOKEN_NUMBER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_red_token_number)
        ],
        GET_DEMON_TOKEN_NUMBER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_demon_token_number)
        ],
        GET_RED_TOKEN_RED_NEIGHBORS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_red_token_red_neighbors)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
