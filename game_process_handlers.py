from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import (
    get_user_by_id,
    update_user_on_game,
    get_moderators,
    get_latest_game_set,
    get_user_by_id,
    get_red_tokens,
    update_token_red_neighbors
    
)

from render_game_set import show_game_set
from constants import START_GAME, EXECUTE_TOKEN, GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME
import logging

logger = logging.getLogger(__name__)

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправляет игроку карту жетонов и уведомляет модератора.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"

    # Проверяем, является ли пользователь игроком
    game_set = get_latest_game_set()
    player_id = game_set.get('player_id')
    player_username = game_set.get('player_username')

    if user_id != player_id:
        # Если это не игрок, игнорируем сообщение
        return ConversationHandler.END

    # Отправляем карту жетонов игроку
    await show_game_set(context, player_id, moderator=False)
    logger.info(f"Игроку @{player_username} ({player_id}) отправлена карта жетонов.")
    update_user_on_game(player_id, True)

    await context.bot.send_message(
        chat_id=player_id, 
        text="Введите номер жетона, который вы собираетесь казнить:", 
        parse_mode='MarkdownV2'
    )

    # Переходим в состояние EXECUTE_TOKEN
    return EXECUTE_TOKEN

# game_process_handlers.py

async def execute_token_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод игроком номера жетона.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"
    text = update.message.text.strip()

    # Проверяем, что введено число
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите корректный номер жетона (целое число).")
        return EXECUTE_TOKEN  # Остаёмся в том же состоянии

    token_id = int(text)

    # Получаем информацию об игроке
    player = get_user_by_id(user_id)
    if not player:
        logger.warning(f"Пользователь {username} ({user_id}) не найден в базе данных.")
        await update.message.reply_text("Ваши данные не найдены. Пожалуйста, начните игру заново.")
        return ConversationHandler.END

    # Отправляем сообщение модератору
    moderators = get_moderators()
    if moderators:
        moderator = moderators[0]
        moderator_id = moderator['id']
        message = f"Игрок @{username} выбрал для казни жетон {token_id}."
        try:
            await context.bot.send_message(chat_id=moderator_id, text=message)
            logger.info(f"Модератору отправлено сообщение о выборе игрока @{username}.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение модератору: {e}")
    else:
        logger.warning("Модератор не найден для отправки сообщения.")

    await update.message.reply_text("Ваш выбор принят. Спасибо!")
    context.bot_data['awaiting_red_neighbors'] = True
    
    await context.bot.send_message(
        chat_id=moderator_id,
        text="Игрок сделал свой выбор. Отправьте 'Ввести соседей', чтобы продолжить игру."
    )
    
    return ConversationHandler.END



async def reenter_red_neighbors_for_red(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запрашивает у модератора количество красных соседей для каждого красного жетона.
    """
    
    # Проверяем, ожидается ли ввод красных соседей
    if not context.bot_data.get('awaiting_red_neighbors'):
        await update.message.reply_text("Сейчас нет необходимости вводить количество красных соседей.")
        return ConversationHandler.END
    
    # Если это первый вызов функции, инициализируем данные
    if 'red_tokens' not in context.user_data:
        # Получаем список красных жетонов из базы данных
        red_tokens = get_red_tokens()
        context.user_data['red_tokens'] = red_tokens
        context.user_data['current_red_token_index'] = 0
        await update.message.reply_text(f"Введите количество красных соседей для жетона номер {red_tokens[0]}:")
        return GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME


    # В противном случае продолжаем запрашивать данные
    red_tokens = context.user_data['red_tokens']
    current_index = context.user_data['current_red_token_index']
    token_number = red_tokens[current_index]

    red_neighbors_text = update.message.text.strip()
    if not red_neighbors_text.isdigit():
        await update.message.reply_text("Пожалуйста, введите целое число для количества соседей.")
        return GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME

    red_neighbors = int(red_neighbors_text)

    # Обновляем поле red_neighbors в базе данных для текущего красного жетона
    update_token_red_neighbors(token_number, red_neighbors)
    logger.info(f"Жетон {token_number}: количество соседей обновлено до {red_neighbors}")

    # Проверяем, есть ли ещё красные жетоны для обработки
    current_index += 1
    context.user_data['current_red_token_index'] = current_index

    if current_index < len(red_tokens):
        next_token_number = red_tokens[current_index]
        await update.message.reply_text(f"Введите количество красных соседей для жетона номер {next_token_number}:")
        return GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME
    else:
        # Все данные введены, сохраняем изменения и отправляем обновлённую раскладку
        await update.message.reply_text("Ввод количества красных соседей завершён.")
        player_id = get_latest_game_set().get('player_id')

        # Отправляем обновлённую раскладку модератору
        await show_game_set(context, update.effective_user.id, moderator=True)
        # Отправляем обновлённую раскладку игроку
        await show_game_set(context, player_id, moderator=False)
        context.bot_data['awaiting_red_neighbors'] = False

        # Завершаем разговор
        return ConversationHandler.END
