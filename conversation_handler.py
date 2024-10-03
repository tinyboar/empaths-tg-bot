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
    random_red_set,
    manual_entry_red_set,
)
from player_manager import (
    confirm_invite,
)
from game_process_handlers import (
    start_game,
    execute_token_player,
    reenter_red_neighbors_for_red,
    kill_token,
    confirm_kill,
    skip_enter_neighbors,
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
    GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME,
    CONFIRM_KILL,
    RANDOM_RED_SET
)

# ConversationHandler для модератора
moderator_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start),
        CommandHandler('enter_neighbors', reenter_red_neighbors_for_red),
        CommandHandler('kill_token', kill_token),
        CommandHandler('skip_enter_neighbors', skip_enter_neighbors)
    ],
    states={
        HANDLE_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password),
            CommandHandler('skip', skip)
        ],
        GET_USERNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)
        ],
        GET_TOKENS_COUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_tokens_count)
        ],
        GET_RED_COUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_red_count)
        ],
        RANDOM_RED_SET: [
            CommandHandler('random_red_set', random_red_set),
            CommandHandler('manual_entry_red_set', manual_entry_red_set)
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
            CommandHandler('pass_turn_to_player', confirm_invite)
        ],
        START_GAME: [
            CommandHandler('start_game', start_game)
        ],
        GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, reenter_red_neighbors_for_red)
        ],
        CONFIRM_KILL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_kill)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True,
    per_chat=False,
    per_user=True
)


# ConversationHandler для игрока
player_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('execute_token', execute_token_player)  # Добавляем команду /execute_token как входную точку
    ],
    states={
        EXECUTE_TOKEN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, execute_token_player)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=False,  # Отключаем повторный вход в разговор
    per_chat=False        # Отслеживаем разговор по пользователю
)