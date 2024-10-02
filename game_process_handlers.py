# game_process_handlers.py

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import get_user_by_id, update_user_on_game, get_moderators, get_latest_game_set
from render_game_set import show_game_set
from constants import START_GAME, EXECUTE_TOKEN
import logging

logger = logging.getLogger(__name__)

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправляет игроку карту жетонов и уведомляет модератора.
    """
    
    game_set = get_latest_game_set()
    player_id = game_set.get('player_id')
    player_username = game_set['player_username']
    
    if not player_id:
        logger.error(f"Игрок с ID {player_id} не найден.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Игрок не найден.")
        return ConversationHandler.END

    await show_game_set(context, player_id, moderator=False)
    logger.info(f"Игроку @{player_username} ({player_id}) отправлена карта жетонов.")
    update_user_on_game(player_id, True)
    
    await context.bot.send_message(chat_id=player_id, text="Введите номер жетона, который вы собираетесь казнить:")
    context.bot_data[player_id] = {'awaiting_execute_token': True}

    return await execute_token(update, context)

async def execute_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ввод игроком номера жетона.
    """
    game_set = get_latest_game_set()
    player_id = game_set.get('player_id')
    player_username = game_set['player_username']
    moderator_id = game_set['moderator_id']
    
    user_id = player_id
    username = player_username
    text = update.message.text.strip()

    # Проверяем, ожидает ли игрок ввода номера жетона
    user_state = context.bot_data.get(player_id, {})
    if not user_state.get('awaiting_execute_token'):
        await update.message.reply_text("Вы не можете выполнять это действие сейчас.")
        return

    token_id = int(text)

    # Отправляем сообщение модератору
    if moderator_id:
        message = f"Игрок @{player_username} выбрал для казни жетон {token_id}."
        try:
            await context.bot.send_message(chat_id=moderator_id, text=message)
            logger.info(f"Модератору отправлено сообщение о выборе игрока @{username}.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение модератору: {e}")
    else:
        logger.warning("Модератор не найден для отправки сообщения.")

    await update.message.reply_text("Ваш выбор принят. Спасибо!")

    # Убираем флаг ожидания ввода номера жетона
    context.bot_data.pop(user_id, None)
    return ConversationHandler.END
