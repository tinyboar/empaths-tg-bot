# registration_handlers.py

import os
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import add_user, get_user_by_username
import logging
from constants import HANDLE_PASSWORD, GET_USERNAME, SET_UP_GAME
from game_set_handlers import set_up_game
from player_manager import (
    player_registration_notice,
    player_start_game_notice
)

MODERATOR_PASSWORD = os.getenv("MODERATOR_PASSWORD")
if not MODERATOR_PASSWORD:
    raise ValueError("Переменная окружения MODERATOR_PASSWORD не установлена.")

logger = logging.getLogger(__name__)

def extract_user_info(user) -> tuple:
    """
    Извлекает username и user id из объекта пользователя Telegram.
    """
    username = user.username or user.first_name or "Unknown"
    userid = user.id
    return username, userid

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /start.
    """
    context.user_data.clear()

    user = update.effective_user
    username, userid = extract_user_info(user)

    # Сохраняем пользователя в базе данных и получаем флаг is_new_user
    is_new_user = add_user(username, userid)
    context.user_data['is_new_user'] = is_new_user

    await update.message.reply_text(
        f"Привет, {username}! Ты успешно зарегистрирован.\n\n"
        "Если вы модератор, введите пароль. Чтобы продолжить как игрок нажми /skip"
    )

    return HANDLE_PASSWORD

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Проверяет введённый пароль и продолжает диалог при успешном вводе.
    """
    password = update.message.text
    user = update.effective_user
    username, userid = extract_user_info(user)

    if password == MODERATOR_PASSWORD:
        add_user(username, userid, moderator=True)
        await update.message.reply_text("Вы успешно зарегистрированы как модератор!")
        logger.info(f"Пользователь {userid} зарегистрирован как модератор.")

        await update.message.reply_text("Введите имя пользователя, с которым вы собираетесь играть(например @username):")
        return GET_USERNAME
    else:
        await update.message.reply_text(
            "Пароль модератора неверный. Введите пароль ещё раз или введите /skip, чтобы продолжить как игрок."
        )
        logger.warning(f"Неверный пароль от пользователя {userid}.")
        return HANDLE_PASSWORD

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод имени пользователя для игры и передаёт управление в set_up_game.
    """
    player_username_input = update.message.text.strip()
    # Удаляем ведущий '@', если он есть
    player_username = player_username_input.lstrip('@')
    
    # Проверка, что имя пользователя не пустое
    if not player_username:
        await update.message.reply_text("Имя пользователя не может быть пустым. Пожалуйста, введите имя пользователя:")
        return GET_USERNAME
    
    # Дополнительная валидация имени пользователя (по желанию)
    if not player_username.isalnum():
        await update.message.reply_text("Имя пользователя должно содержать только буквы и цифры. Пожалуйста, введите корректное имя пользователя:")
        return GET_USERNAME
    
    game_set = context.user_data.setdefault('game_set', {})
    game_set['player_username'] = player_username
    logger.info(f"Получено имя пользователя для игры: {player_username}")
    await update.message.reply_text("Имя пользователя сохранено. Теперь настройте игру.")
    
    player = get_user_by_username(player_username)
    player_id = player['id']

    await context.bot.send_message(
        chat_id=player_id,
        text=(f"Модератор @{update.effective_user.username} выбрал тебя для игры.")
    )
    
    return await set_up_game(update, context)

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает команду /skip, позволяя пользователю пропустить ввод пароля модератора.
    """
    user = update.effective_user
    username, userid = extract_user_info(user)
    is_new_user = context.user_data.get('is_new_user', False)

    await update.message.reply_text("Вы зарегистрированы как обычный пользователь. Модератор настроит игру и пригласит вас.")

    if is_new_user:
        await player_registration_notice(context, username, userid)
        await player_start_game_notice(context, username, userid)
        logger.info(f"Новый игрок зарегистрирован: @{username} ({userid})")
    else:
        await player_start_game_notice(context, username, userid)
        logger.info(f"Пользователь @{username} ({userid}) нажал кнопку старта и ожидает начало игры.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает команду /cancel, отменяя процесс регистрации.
    """
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END
