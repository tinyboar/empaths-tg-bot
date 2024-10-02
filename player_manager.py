# player_manager.py

import logging
from database import get_user_by_username, get_moderators, update_user_on_game

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from constants import CONFIRM_INVITE, START_GAME
from game_process_handlers import start_game

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

async def invite_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправляет модератору сообщение с предложением пригласить игрока.
    """
    # Получаем username игрока и ID модератора
    player_username = context.user_data['game_set']['player_username']
    moderator_userid = update.effective_user.id  # ID модератора

    context.user_data['player_username'] = player_username
    message = (
        f"Пригласить @{player_username}? Отправьте /start, чтобы начать настройку заново. "
        f"Или отправьте 1, чтобы отправить игроку раскладку жетонов"
    )
    await update.message.reply_text(message)

    return CONFIRM_INVITE

async def confirm_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ответ модератора на предложение пригласить игрока.
    """
    text = update.message.text.strip()
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"

    # Проверяем, является ли пользователь модератором
    moderator = get_user_by_username(username)
    if not moderator or not moderator.get('moderator', False):
        await update.message.reply_text("Только модератор может подтвердить приглашение.")
        return ConversationHandler.END

    if text == '1':
        # Получаем username игрока
        player_username = context.user_data.get('player_username')
        if not player_username:
            await update.message.reply_text(
                "Имя пользователя игрока не найдено. Пожалуйста, начните настройку заново с помощью /start."
            )
            return ConversationHandler.END

        # Получаем информацию об игроке
        player = get_user_by_username(player_username)
        if not player:
            logger.error(f"Игрок с username {player_username} не найден.")
            await update.message.reply_text(f"Игрок с именем @{player_username} не найден.")
            return ConversationHandler.END

        player_userid = player['id']

        # Обновляем поле on_game у модератора и игрока
        update_user_on_game(user_id, True)        # ID модератора
        update_user_on_game(player_userid, True)  # ID игрока
        logger.info(f"on_game обновлено для модератора {user_id} и игрока {player_userid}")

        try:
            return await start_game(update, context, player_userid)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение игроку @{player_username} ({player_userid}): {e}")
            await update.message.reply_text(f"Не удалось отправить сообщение игроку @{player_username}.")

        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Неверный ввод. Пожалуйста, отправьте 1, чтобы пригласить игрока, или /start, чтобы начать настройку заново."
        )
        return CONFIRM_INVITE
