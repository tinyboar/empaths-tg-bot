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
    get_red_token_red_neighbors,
)
from player_manager import (
    confirm_invite,
)
from game_process_handlers import (
    start_game,
    execute_token_player  # Обратите внимание на переименование функции
)
from constants import (
    HANDLE_PASSWORD,
    GET_USERNAME,
    SET_UP_GAME,
    GET_TOKENS_COUNT,
    GET_RED_COUNT,
    GET_RED_TOKEN_NUMBER,
    GET_DEMON_TOKEN_NUMBER,
    GET_RED_TOKEN_RED_NEIGHBORS,
    CONFIRM_INVITE,
    START_GAME,
    EXECUTE_TOKEN,
)

# ConversationHandler для модератора
moderator_conv_handler = ConversationHandler(
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
        CONFIRM_INVITE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_invite)
        ],
        START_GAME: [
            CommandHandler('start_game', start_game)
        ],
        # Убираем EXECUTE_TOKEN из этого ConversationHandler
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)

# Новый ConversationHandler для игрока
player_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, start_game)],
    states={
        EXECUTE_TOKEN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, execute_token_player)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True
)
