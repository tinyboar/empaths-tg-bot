# registration_handlers.py

import os
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import add_user
import logging
from constants import HANDLE_PASSWORD, GET_USERNAME, SET_UP_GAME
from game_set_handlers import set_up_game

# Получение конфигурационных данных из переменных окружения
MODERATOR_PASSWORD = os.getenv("MODERATOR_PASSWORD", "123")

# Настройка логирования
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

    add_user(username, userid)

    await update.message.reply_text(
        f"Привет, {username}! Ты успешно зарегистрирован.\n\n"
        "Если вы модератор, введите пароль. Введите /skip, чтобы пропустить."
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
        # Обновляем пользователя как модератора
        add_user(username, userid, moderator=True)
        await update.message.reply_text("Вы успешно зарегистрированы как модератор!")
        logger.info(f"Пользователь {userid} зарегистрирован как модератор.")

        # Переходим к вводу имени пользователя для игры
        await update.message.reply_text("Введите имя пользователя, с которым вы собираетесь играть:")
        return GET_USERNAME
    else:
        await update.message.reply_text("Неверный пароль. Вы зарегистрированы как обычный пользователь.")
        logger.warning(f"Неверный пароль от пользователя {userid}.")
        return ConversationHandler.END

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод имени пользователя для игры и передаёт управление в set_up_game.
    """
    player_username = update.message.text.strip()
    game_set = context.user_data.setdefault('game_set', {})
    game_set['player_username'] = player_username
    logger.info(f"Получено имя пользователя для игры: {player_username}")
    await update.message.reply_text("Имя пользователя сохранено. Теперь настройте игру.")
    
    # Вызываем set_up_game непосредственно и возвращаем его состояние
    return await set_up_game(update, context)


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает команду /skip, позволяя пользователю пропустить ввод пароля модератора.
    """
    await update.message.reply_text("Вы зарегистрированы как обычный пользователь.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает команду /cancel, отменяя процесс регистрации.
    """
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END
