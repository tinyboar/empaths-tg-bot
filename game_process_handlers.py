# game_process_handlers.py

from telegram import Update
from telegram.ext import ContextTypes
from database import get_user_by_id, update_user_on_game
from render_game_set import show_start_game_set
import logging

logger = logging.getLogger(__name__)

async def check_player_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Проверяет, ожидает ли игрок начала игры, и вызывает start_game при получении ответа.
    """
    user = update.effective_user
    userid = user.id
    username = user.username or user.first_name or "Unknown"

    # Получаем информацию о пользователе из базы данных
    player = get_user_by_id(userid)
    if not player:
        logger.warning(f"Пользователь {username} ({userid}) не найден в базе данных.")
        return

    if player['on_game'] and not player['moderator']:
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
    await show_start_game_set(update, context)
    logger.info(f"Игроку {username} ({userid}) отправлена карта жетонов.")

    # Обновляем поле on_game у игрока
    update_user_on_game(userid, False)

    # Уведомляем модератора
    # Получаем модератора
    from database import get_moderators
    moderators = get_moderators()
    if moderators:
        moderator = moderators[0]  # Предполагаем, что модератор один
        moderator_id = moderator['id']
        message = f"{username} получил карту жетонов. Начинаем играть"
        try:
            await context.bot.send_message(chat_id=moderator_id, text=message)
            logger.info(f"Модератору {moderator['username']} ({moderator_id}) отправлено уведомление о начале игры.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение модератору {moderator['username']} ({moderator_id}): {e}")
    else:
        logger.warning("Модератор не найден для отправки уведомления о начале игры.")
