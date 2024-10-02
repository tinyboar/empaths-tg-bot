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
    player_username = game_set.get('player_username')

    if not player_id:
        logger.error(f"Игрок с ID {player_id} не найден.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Игрок не найден.")
        return ConversationHandler.END

    # Отправляем игроку карту жетонов
    await show_game_set(context, player_id, moderator=False)
    logger.info(f"Игроку @{player_username} ({player_id}) отправлена карта жетонов.")
    
    update_user_on_game(player_id, True)

    await context.bot.send_message(chat_id=player_id, text="Введите номер жетона, который вы собираетесь казнить:", parse_mode='MarkdownV2')
    context.bot_data[player_id] = {'awaiting_execute_token': True}

    return EXECUTE_TOKEN


async def execute_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод игроком номера жетона.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"
    text = update.message.text.strip()
    
    print("000000000000000000000000")

    # Проверяем, ожидает ли игрок ввода номера жетона
    user_state = context.bot_data.get(user_id, {})
    if not user_state.get('awaiting_execute_token'):
        await update.message.reply_text("Вы не можете выполнять это действие сейчас.")
        return ConversationHandler.END

    # Проверяем, что введено число
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите корректный номер жетона (целое число).")
        return EXECUTE_TOKEN  # Остаёмся в том же состоянии

    token_id = int(text)

    # Получаем информацию об игроке и жетоне
    player = get_user_by_id(user_id)
    if not player:
        logger.warning(f"Пользователь {username} ({user_id}) не найден в базе данных.")
        await update.message.reply_text("Ваши данные не найдены. Пожалуйста, начните игру заново.")
        return ConversationHandler.END

    # Здесь можно добавить проверку, существует ли жетон с таким номером
    # и принадлежит ли он игроку, если это необходимо.

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

    # Убираем флаг ожидания ввода номера жетона
    context.bot_data.pop(user_id, None)
    return ConversationHandler.END

