# player_manager.py

import logging
from database import get_moderators

logger = logging.getLogger(__name__)

async def player_registration_notice(context, player_username, player_userid):
    """
    Отправляет уведомление модератору(ам) о том, что зарегистрировался новый игрок.
    """
    moderators = get_moderators()
    if not moderators:
        logger.warning("Модераторы не найдены для уведомления о регистрации нового игрока.")
        return

    message = f"Зарегистрирован новый пользователь @{player_username}."

    for moderator in moderators:
        moderator_id = moderator['id']
        try:
            await context.bot.send_message(chat_id=moderator_id, text=message)
            logger.info(f"Уведомлен модератор {moderator['username']} ({moderator_id}) о новом игроке @{player_username}.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение модератору {moderator['username']} ({moderator_id}): {e}")

async def player_start_game_notice(context, player_username, player_userid):
    """
    Отправляет уведомление модератору(ам) о том, что пользователь нажал /start и ожидает начало игры.
    """
    moderators = get_moderators()
    if not moderators:
        logger.warning("Модераторы не найдены для уведомления о начале игры пользователем.")
        return

    message = f"Пользователь @{player_username} нажал кнопку старта и ожидает начало игры."

    for moderator in moderators:
        moderator_id = moderator['id']
        try:
            await context.bot.send_message(chat_id=moderator_id, text=message)
            logger.info(f"Уведомлен модератор {moderator['username']} ({moderator_id}) о начале игры пользователем @{player_username}.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение модератору {moderator['username']} ({moderator_id}): {e}")
