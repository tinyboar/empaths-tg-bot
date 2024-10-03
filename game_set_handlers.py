# game_set_handlers.py

import random
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import (
    add_game_set,
    clear_tokens,
    add_tokens,
    update_token_alignment,
    update_token_character,
    get_latest_game_set,
    get_user_by_id,
    get_user_by_username,
    update_token_red_neighbors
    
)
import logging
from constants import GET_TOKENS_COUNT, GET_RED_COUNT, GET_RED_TOKEN_NUMBER, GET_DEMON_TOKEN_NUMBER, GET_RED_TOKEN_RED_NEIGHBORS
from render_game_set import show_game_set

from player_manager import invite_player

logger = logging.getLogger(__name__)

async def set_up_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Начинает настройку игры после ввода имени пользователя.
    """
    await update.message.reply_text("Введите количество жетонов (tokens_count):")
    return GET_TOKENS_COUNT

async def get_tokens_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод количества жетонов.
    """
    tokens_count_text = update.message.text.strip()
    if not tokens_count_text.isdigit():
        await update.message.reply_text("Пожалуйста, введите целое число для количества жетонов.")
        return GET_TOKENS_COUNT

    tokens_count = int(tokens_count_text)
    context.user_data['game_set']['tokens_count'] = tokens_count
    await update.message.reply_text("Введите количество красных жетонов (red_count):")
    return GET_RED_COUNT

async def get_red_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод количества красных жетонов и сохраняет настройки игры.
    """
    red_count_text = update.message.text.strip()
    if not red_count_text.isdigit():
        await update.message.reply_text("Пожалуйста, введите целое число для количества красных жетонов.")
        return GET_RED_COUNT

    red_count = int(red_count_text)
    tokens_count = context.user_data['game_set']['tokens_count']
    player_username = context.user_data['game_set']['player_username']
    player = get_user_by_username(player_username)
    player_id = player['id']

    moderator = update.message.from_user
    moderator_id = moderator.id
    moderator_username = moderator.username
    
    # Проверка, что red_count не превышает tokens_count
    if red_count > tokens_count:
        await update.message.reply_text("Количество красных жетонов не может превышать общее количество жетонов.")
        return GET_RED_COUNT

    # Сохраняем настройки игры в базе данных
    add_game_set(tokens_count, red_count, player_username, player_id, moderator_username, moderator_id)
    await update.message.reply_text("Настройки игры успешно сохранены!")
    logger.info(f"Игра создана: tokens_count={tokens_count}, red_count={red_count}, player_username={player_username}")

    # Очищаем таблицу tokens перед добавлением новых жетонов
    clear_tokens()

    # Создаём список жетонов: все синие по умолчанию
    tokens_list = [('blue', 'townfolk', 0) for _ in range(tokens_count)]
    add_tokens(tokens_list)
    logger.info(f"Создано {tokens_count} жетонов в таблице tokens.")

    # Показываем начальные настройки игры с серыми жетонами
    await show_game_set(context, moderator_id, moderator=True)

    # Инициализируем данные для ввода номеров красных жетонов
    context.user_data['red_count'] = red_count
    context.user_data['tokens_count'] = tokens_count
    context.user_data['selected_red_tokens'] = []
    context.user_data['current_red_token_index'] = 1  # Индекс текущего запрашиваемого красного жетона

    # Запрашиваем первый номер красного жетона
    await update.message.reply_text(f"Какие номера жетонов будут красными?")
    await update.message.reply_text(f"Выберите первый из {red_count} красных жетонов:")
    return GET_RED_TOKEN_NUMBER


async def get_red_token_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод номера красного жетона от модератора.
    """
    token_number_text = update.message.text.strip()
    if not token_number_text.isdigit():
        await update.message.reply_text("Пожалуйста, введите номер жетона в виде целого числа.")
        return GET_RED_TOKEN_NUMBER

    token_number = int(token_number_text)
    tokens_count = context.user_data['tokens_count']
    selected_red_tokens = context.user_data['selected_red_tokens']

    if token_number < 1 or token_number > tokens_count:
        await update.message.reply_text(f"Пожалуйста, введите номер жетона от 1 до {tokens_count}.")
        return GET_RED_TOKEN_NUMBER

    if token_number in selected_red_tokens:
        await update.message.reply_text(f"Жетон номер {token_number} уже выбран. Пожалуйста, выберите другой номер.")
        return GET_RED_TOKEN_NUMBER

    update_token_alignment(token_number, 'red')
    update_token_character(token_number, 'minion')
    selected_red_tokens.append(token_number)
    logger.info(f"Жетон номер {token_number} помечен как красный.")

    await update.message.reply_text(f"Жетон номер {token_number} стал красным игроком.")

    red_count = context.user_data['red_count']
    if len(selected_red_tokens) < red_count:
        context.user_data['current_red_token_index'] += 1
        ordinal = {1: "первый", 2: "второй", 3: "третий", 4: "четвёртый", 5: "пятый", 6: "шестой",
                   7: "седьмой", 8: "восьмой", 9: "девятый", 10: "десятый"}
        index = context.user_data['current_red_token_index']
        await update.message.reply_text(f"Выберите {ordinal.get(index, f'{index}-й')} из {red_count} красных жетонов:")
        return GET_RED_TOKEN_NUMBER
    else:
        await update.message.reply_text("Выберите номер жетона, который будет демоном из выбранных красных жетонов:")
        return GET_DEMON_TOKEN_NUMBER


async def get_demon_token_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод номера демона от модератора.
    """
    token_number_text = update.message.text.strip()
    if not token_number_text.isdigit():
        await update.message.reply_text("Пожалуйста, введите номер жетона в виде целого числа.")
        return GET_DEMON_TOKEN_NUMBER

    token_number = int(token_number_text)
    selected_red_tokens = context.user_data['selected_red_tokens']

    if token_number not in selected_red_tokens:
        await update.message.reply_text("Пожалуйста, введите номер жетона из выбранных красных жетонов.")
        return GET_DEMON_TOKEN_NUMBER

    # Обновляем жетон в базе данных, помечая его как демона
    from database import update_token_character
    update_token_character(token_number, 'demon')
    logger.info(f"Жетон номер {token_number} помечен как демон.")
    await update.message.reply_text(f"Жетон номер {token_number} теперь является демоном.")

    # Вызываем функцию для подсчёта красных соседей у синих жетонов
    logger.info("Подсчёт красных соседей для синих жетонов завершён.")
    player_id = update.effective_user.id
    await show_game_set(context, player_id, moderator=True)

    # Инициализируем данные для ввода red_neighbors для красных жетонов
    context.user_data['red_tokens'] = selected_red_tokens
    context.user_data['current_red_token_index'] = 0  # Начинаем с первого красного жетона

    # Запрашиваем количество соседей для первого красного жетона
    first_red_token = context.user_data['red_tokens'][0]
    await update.message.reply_text(f"Введите количество красных соседей для жетона номер {first_red_token}:")
    return GET_RED_TOKEN_RED_NEIGHBORS


async def get_red_token_red_neighbors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запрашивает у модератора количество красных соседей для каждого красного жетона.
    """
    red_tokens = context.user_data['red_tokens']
    current_index = context.user_data['current_red_token_index']
    token_number = red_tokens[current_index]

    red_neighbors_text = update.message.text.strip()
    if not red_neighbors_text.isdigit():
        await update.message.reply_text("Пожалуйста, введите целое число для количества соседей.")
        return GET_RED_TOKEN_RED_NEIGHBORS

    red_neighbors = int(red_neighbors_text)

    # Обновляем поле red_neighbors в базе данных для текущего красного жетона
    update_token_red_neighbors(token_number, red_neighbors)
    logger.info(f"Жетон {token_number}: количество соседей обновлено до {red_neighbors}")

    # Проверяем, есть ли ещё красные жетоны для обработки
    current_index += 1
    context.user_data['current_red_token_index'] = current_index

    if current_index < len(red_tokens):
        next_token_number = red_tokens[current_index]
        await update.message.reply_text(f"Введите количество красных соседей для жетона номер {next_token_number}:")
        return GET_RED_TOKEN_RED_NEIGHBORS
    else:
        player_id = update.effective_user.id
        await show_game_set(context, player_id, moderator=True)
        return await invite_player(update, context)


async def show_setup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /showsetup.
    Если вызов сделал модератор, отображает настройки игры с модераторским видом.
    Если вызов сделал игрок, отображает настройки игры с видом для игрока.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"

    game_set = get_latest_game_set()

    if not game_set:
        await update.message.reply_text("Игра не найдена или еще не начата.")
        logger.info(f"Пользователь {username} ({user_id}) попытался вызвать /showsetup, но игра не начата.")
        return

    player_id = game_set.get('player_id')
    user_data = get_user_by_id(user_id)

    if not user_data:
        await update.message.reply_text("Вы не зарегистрированы в системе.")
        logger.warning(f"Пользователь {username} ({user_id}) не найден в базе данных.")
        return

    is_moderator = user_data.get('moderator', False)

    if is_moderator:
        await show_game_set(update, context, moderator=True)
        logger.info(f"Модератор {username} ({user_id}) вызвал /showsetup.")
    else:
        if user_id == player_id:
            await show_game_set(update, context, moderator=False)
            logger.info(f"Игрок {username} ({user_id}) вызвал /showsetup.")
        else:
            await update.message.reply_text("У вас нет прав использовать эту команду.")
            logger.warning(f"Пользователь {username} ({user_id}) попытался вызвать /showsetup без прав.")
