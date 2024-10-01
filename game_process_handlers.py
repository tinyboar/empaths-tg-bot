# game_process_handlers.py

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import get_user_by_id, update_user_on_game, get_moderators
from render_game_set import show_game_set
from constants import EXECUTE_TOKEN
import logging

logger = logging.getLogger(__name__)

async def check_player_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Проверяет, ожидает ли игрок начала игры, и вызывает start_game при получении ответа.
    """
    user = update.effective_user
    userid = user.id
    username = user.username or user.first_name or "Unknown"

    # Проверяем, ожидает ли игрок ответа
    user_state = context.bot_data.get(userid, {})
    if not user_state.get('expected_response'):
        # Игрок не ожидает ответа, игнорируем сообщение
        return

    # Удаляем флаг ожидания
    context.bot_data[userid]['expected_response'] = False

    # Получаем информацию о пользователе из базы данных
    player = get_user_by_id(userid)
    if not player:
        logger.warning(f"Пользователь {username} ({userid}) не найден в базе данных.")
        return

    if player['on_game'] and not player.get('moderator', False):
        # Игрок ответил, запускаем игру
        await start_game(update, context)
    else:
        # Игнорируем сообщения от пользователей, которые не ожидают начала игры
        pass

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет игроку карту жетонов и уведомляет модератора.
    """
    user = update.effective_user
    userid = user.id
    username = user.username or user.first_name or "Unknown"

    # Отправляем игроку карту жетонов
    await show_game_set(update, context, moderator=False)
    logger.info(f"Игроку {username} ({userid}) отправлена карта жетонов.")

    # Обновляем поле on_game у игрока
    update_user_on_game(userid, True)
    
    # Уведомляем модератора
    moderators = get_moderators()
    if moderators:
        moderator = moderators[0]  # Предполагаем, что модератор один
        moderator_id = moderator['id']
        update_user_on_game(moderator_id, True)
        message = f"{username} получил карту жетонов. Начинаем играть"
        try:
            await context.bot.send_message(chat_id=moderator_id, text=message)
            logger.info(f"Модератору {moderator['username']} ({moderator_id}) отправлено уведомление о начале игры.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение модератору {moderator['username']} ({moderator_id}): {e}")
    else:
        logger.warning("Модератор не найден для отправки уведомления о начале игры.")

async def execute_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод игроком номера жетона.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"
    text = update.message.text.strip()

    # Проверяем, является ли пользователь игроком, которого мы ожидаем
    expected_player_id = context.chat_data.get('expected_player')
    expected_state = context.chat_data.get('expected_state')

    if user_id != expected_player_id or expected_state != EXECUTE_TOKEN:
        await update.message.reply_text("Вы не можете выполнять это действие сейчас.")
        return ConversationHandler.END

    # Проверяем, что введено число
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите корректный номер жетона (целое число).")
        return EXECUTE_TOKEN

    token_id = int(text)

    # Отправляем сообщение модератору
    moderators = get_moderators()
    if moderators:
        moderator = moderators[0]
        moderator_id = moderator['id']
        message = f"Игрок {username} выбрал для казни жетон {token_id}."
        try:
            await context.bot.send_message(chat_id=moderator_id, text=message)
            logger.info(f"Модератору отправлено сообщение о выборе игрока.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение модератору: {e}")
    else:
        logger.warning("Модератор не найден для отправки сообщения.")

    await update.message.reply_text("Ваш выбор принят. Спасибо!")
    return ConversationHandler.END  # Завершаем диалог с игроком
