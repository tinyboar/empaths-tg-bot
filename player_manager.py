# player_manager.py

import logging
from database import get_user_by_username, get_moderators, update_user_on_game

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from constants import CONFIRM_INVITE, START_GAME
from render_game_set import show_game_set

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

    if text == '1':
        player_username = context.user_data.get('player_username')
        player = get_user_by_username(player_username)
        player_userid = player['id']

        # Обновляем статус и отправляем раскладку жетонов игроку
        update_user_on_game(update.effective_user.id, True)        # Обновляем статус модератора
        update_user_on_game(player_userid, True)                   # Обновляем статус игрока

        await show_game_set(context, player_userid, moderator=False)
        logger.info(f"Игроку @{player_username} ({player_userid}) отправлена раскладка жетонов.")
        await update.message.reply_text(f"Игроку @{player_username} отправлено приглашение.")

        # Запуск команды /execute_token для выбора жетона игроком
        await context.bot.send_message(
            chat_id=player_userid,
            text="Введите команду /execute_token, чтобы выбрать жетон, который вы собираетесь казнить."
        )

        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Неверный ввод. Пожалуйста, отправьте 1, чтобы пригласить игрока, или /start, чтобы начать настройку заново."
        )
        return CONFIRM_INVITE
