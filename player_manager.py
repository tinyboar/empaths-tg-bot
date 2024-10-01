# player_manager.py

import logging
from database import get_user_by_username, get_moderators, update_user_on_game

# Добавляем недостающие импорты
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def player_registration_notice(context: ContextTypes.DEFAULT_TYPE, player_username: str, player_userid: int):
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

async def player_start_game_notice(context: ContextTypes.DEFAULT_TYPE, player_username: str, player_userid: int):
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

async def invite_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обновляет поле on_game у модератора и игрока на TRUE.
    Отправляет игроку сообщение с приглашением начать игру.
    """
    # Получаем username игрока и ID модератора
    player_username = context.user_data['game_set']['player_username']
    moderator_userid = update.effective_user.id  # ID модератора

    # Получаем информацию об игроке
    player = get_user_by_username(player_username)
    if not player:
        logger.error(f"Игрок с username {player_username} не найден.")
        return

    player_userid = player['id']

    # Обновляем поле on_game у модератора и игрока
    update_user_on_game(moderator_userid, True)
    update_user_on_game(player_userid, True)
    logger.info(f"on_game обновлено для модератора {moderator_userid} и игрока {player_userid}")

    # Отправляем сообщение игроку
    message = "Модератор настроил игру. Вы готовы начать? Отправьте любое сообщение, чтобы получить раскладку жетонов"
    try:
        await context.bot.send_message(chat_id=player_userid, text=message)
        logger.info(f"Игроку @{player_username} ({player_userid}) отправлено приглашение начать игру.")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение игроку @{player_username} ({player_userid}): {e}")
