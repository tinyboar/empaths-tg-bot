# game_process_handlers.py

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import get_user_by_id, update_user_on_game, get_moderators
from render_game_set import show_game_set
from constants import START_GAME, EXECUTE_TOKEN
import logging

logger = logging.getLogger(__name__)

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE, player_userid: int) -> int:
    """
    Отправляет игроку карту жетонов и уведомляет модератора.
    """
    player = get_user_by_id(player_userid)
    if not player:
        logger.error(f"Игрок с ID {player_userid} не найден.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Игрок не найден.")
        return ConversationHandler.END

    username = player['username'] or player['first_name'] or "Unknown"

    # Отправляем игроку карту жетонов
    await show_game_set(context, player_userid, moderator=False)
    logger.info(f"Игроку @{username} ({player_userid}) отправлена карта жетонов.")

    # Обновляем поле on_game у игрока
    update_user_on_game(player_userid, True)

    # Отправляем запрос на выбор жетона для казни
    await context.bot.send_message(chat_id=player_userid, text="Введите номер жетона, который вы собираетесь казнить:")

    # Устанавливаем флаг ожидания ввода номера жетона
    context.bot_data[player_userid] = {'awaiting_execute_token': True}

    return await execute_token(update, context, player_userid)

async def execute_token(update: Update, context: ContextTypes.DEFAULT_TYPE, player_userid) -> None:
    """
    Обрабатывает ввод игроком номера жетона.
    """
    
    logger.info(f"{update}")
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"
    text = update.message.text.strip()

    # Проверяем, ожидает ли игрок ввода номера жетона
    user_state = context.bot_data.get(player_userid, {})
    if not user_state.get('awaiting_execute_token'):
        await update.message.reply_text("Вы не можете выполнять это действие сейчас.")
        return

    # Проверяем, что введено число
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите корректный номер жетона (целое число).")
        return

    token_id = int(text)

    # Получаем информацию об игроке и жетоне
    player = get_user_by_id(user_id)
    if not player:
        logger.warning(f"Пользователь {username} ({user_id}) не найден в базе данных.")
        await update.message.reply_text("Ваши данные не найдены. Пожалуйста, начните игру заново.")
        return

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
