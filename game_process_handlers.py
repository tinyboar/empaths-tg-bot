# game_process_handlers.py

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import (
    get_alive_tokens,
    update_user_on_game,
    get_moderators,
    get_latest_game_set,
    get_token_by_id,
    get_red_tokens,
    update_token_red_neighbors,
    update_token_kill,
    reset_user_game_state
)
from render_game_set import show_game_set
from constants import EXECUTE_TOKEN, GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME, CONFIRM_INVITE, CONFIRM_KILL, SKIP_ENTER_NEIGHBORS
import logging

from player_manager import invite_player
from utils import escape_html

logger = logging.getLogger(__name__)

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправляет игроку карту жетонов и уведомляет модератора.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"

    # Проверяем, является ли пользователь игроком
    game_set = get_latest_game_set()
    player_id = game_set.get('player_id')
    player_username = game_set.get('player_username')

    if user_id != player_id:
        # Если это не игрок, игнорируем сообщение
        return ConversationHandler.END

    # Отправляем карту жетонов игроку
    await show_game_set(context, player_id, moderator=False)
    logger.info(f"Игроку @{player_username} ({player_id}) отправлена карта жетонов.")
    update_user_on_game(player_id, True)

    await context.bot.send_message(
        chat_id=player_id,
        text="Введи номер жетона, который ты собираешься казнить:",
        parse_mode='MarkdownV2'
    )

    return EXECUTE_TOKEN

async def execute_token_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод игроком номера жетона.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"
    text = update.message.text.strip()

    # Проверяем, была ли введена команда /execute_token
    if text == "/execute_token":
        await update.message.reply_text("Введи номер жетона, который ты собираешься казнить:")
        return EXECUTE_TOKEN

    # Проверяем, что введено число (после команды /execute_token)
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введи корректный номер жетона (целое число).")
        return EXECUTE_TOKEN

    token_id = int(text)

    # Проверяем, существует ли жетон в базе данных
    token = get_token_by_id(token_id)
    if not token:
        await update.message.reply_text(f"Жетон с номером {token_id} не найден в базе данных. Пожалуйста, выберите существующий жетон.")
        return EXECUTE_TOKEN

    # Проверка, является ли выбранный жетон демоном
    if token['character'] == 'demon':
        # Сообщение игроку о победе
        await update.message.reply_text("🏆 Вы казнили демона, победа синего города!")

        # Сообщение модератору о победе синих
        moderators = get_moderators()
        if moderators:
            moderator = moderators[0]
            moderator_id = moderator['id']
            await context.bot.send_message(
                chat_id=moderator_id,
                text=f"💀 Игрок @{username} казнил демона. Победа синих. Нажмите /start, чтобы начать игру заново"
            )
            logger.info(f"Игрок @{username} казнил демона. Победа синих объявлена.")
            reset_user_game_state(user_id)
            reset_user_game_state(moderator_id)
        else:
            logger.warning("Модератор не найден для отправки сообщения.")

        # Завершение игры
        return ConversationHandler.END

    # Если жетон не является демоном, обновляем его статус на "убит"
    update_token_kill(token_id)
    logger.info(f"Игрок @{username} выбрал для казни жетон {token_id}, и его статус был обновлен на 'убит'.")
    await show_game_set(context, user_id, moderator=False)
    await update.message.reply_text(f"Жетон {token_id} выбран для казни и его статус обновлен. Ждем ход модератора..")

    moderators = get_moderators()
    if moderators:
        moderator = moderators[0]
        moderator_id = moderator['id']
        message = f"Игрок @{username} выбрал для казни жетон {token_id}."
        try:
            await show_game_set(context, moderator_id, moderator=True)
            await context.bot.send_message(chat_id=moderator_id, text=message)
            logger.info(f"Модератору отправлено сообщение о выборе игрока @{username}.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение модератору: {e}")
    else:
        logger.warning("Модератор не найден для отправки сообщения.")

    is_red_won = await red_won(context)
    if is_red_won:
        return ConversationHandler.END
    
    context.bot_data['awaiting_red_neighbors'] = True

    await context.bot.send_message(
        chat_id=moderator_id,
        text="/enter_neighbors, ввести соседей для красных жетонов\n\n"
        "/skip_enter_neighbors, пропустить шаг выбора соседей и перейти к выболру жетона для убийства",
        parse_mode='HTML'
    )

    return ConversationHandler.END


async def skip_enter_neighbors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Пропускает ввод количества соседей для красных жетонов и переходит к этапу выбора жетона для убийства.
    """
    await update.message.reply_text("Переходим к выбору жетона для убийства.")
    return await kill_token(update, context)


async def reenter_red_neighbors_for_red(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запрашивает у модератора количество красных соседей для каждого красного жетона.
    """
    # Проверяем, ожидается ли ввод красных соседей
    if not context.bot_data.get('awaiting_red_neighbors'):
        await update.message.reply_text("Сейчас нет необходимости вводить количество красных соседей.")
        return ConversationHandler.END

    # Если это первый вызов функции, инициализируем данные
    if 'red_tokens' not in context.user_data or not context.user_data.get('awaiting_red_neighbors_input'):
        # Получаем список красных жетонов из базы данных
        red_tokens = get_red_tokens()
        logger.info(f"Red tokens retrieved: {red_tokens}")

        if not red_tokens:
            await update.message.reply_text("Нет красных жетонов для обработки.")
            # Сбрасываем флаг, чтобы избежать повторного ввода
            context.bot_data['awaiting_red_neighbors'] = False
            return ConversationHandler.END

        context.user_data['red_tokens'] = red_tokens
        context.user_data['current_red_token_index'] = 0
        # Устанавливаем флаг, чтобы знать, что мы в процессе ввода
        context.user_data['awaiting_red_neighbors_input'] = True
        await update.message.reply_text(f"Введи количество красных соседей для жетона номер {red_tokens[0]}:")
        return GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME

    # В противном случае продолжаем запрашивать данные
    red_tokens = context.user_data['red_tokens']
    current_index = context.user_data['current_red_token_index']

    # Проверяем корректность индекса
    if current_index >= len(red_tokens):
        await update.message.reply_text("Все красные жетоны уже обработаны.")
        # Сбрасываем флаги
        context.bot_data['awaiting_red_neighbors'] = False
        context.user_data.pop('awaiting_red_neighbors_input', None)
        context.user_data.pop('red_tokens', None)
        context.user_data.pop('current_red_token_index', None)

        # Завершили ввод соседей, теперь предлагаем модератору убить жетон
        return await kill_token(update, context)

    token_number = red_tokens[current_index]

    red_neighbors_text = update.message.text.strip()
    if not red_neighbors_text.isdigit():
        await update.message.reply_text("Пожалуйста, введи целое число для количества соседей.")
        return GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME

    red_neighbors = int(red_neighbors_text)

    # Обновляем поле red_neighbors в базе данных для текущего красного жетона
    update_token_red_neighbors(token_number, red_neighbors)
    logger.info(f"Жетон {token_number}: количество соседей обновлено до {red_neighbors}")

    # Проверяем, есть ли ещё красные жетоны для обработки
    current_index += 1
    context.user_data['current_red_token_index'] = current_index

    if current_index < len(red_tokens):
        next_token_number = red_tokens[current_index]
        await update.message.reply_text(f"Введи количество красных соседей для жетона номер {next_token_number}:")
        return GET_RED_TOKEN_RED_NEIGHBORS_IN_GAME
    else:
        # Все данные введены, сохраняем изменения и отправляем обновлённую раскладку
        await update.message.reply_text("Ввод количества красных соседей завершён.")
        player_id = get_latest_game_set().get('player_id')

        # Отправляем обновлённую раскладку модератору
        await show_game_set(context, update.effective_user.id, moderator=True)

        # Сбрасываем флаги и очищаем данные
        context.bot_data['awaiting_red_neighbors'] = False
        context.user_data.pop('awaiting_red_neighbors_input', None)
        context.user_data.pop('red_tokens', None)
        context.user_data.pop('current_red_token_index', None)

        # Переход к функции kill_token для выбора жетона на убийство
        return await kill_token(update, context)

async def kill_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запрашивает у модератора выбор жетона для убийства.
    """
    await update.message.reply_text("Выбери жетон для убийства, введя его номер:")
    return CONFIRM_KILL

async def confirm_kill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод номера жетона для убийства модератором.
    """
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введи корректный номер жетона (целое число).")
        return CONFIRM_KILL  # Остаемся в этом же состоянии для повторного ввода

    token_id = int(text)

    token = get_token_by_id(token_id)
    if not token:
        await update.message.reply_text(f"Жетон с номером {token_id} не найден в базе данных. Пожалуйста, выбери существующий жетон.")
        return CONFIRM_KILL

    # Проверка, является ли жетон демоном
    if token['character'] == 'demon':
        # Сообщение игроку о том, что демона убили
        game_set = get_latest_game_set()
        player_id = game_set.get('player_id')
        
        await show_game_set(context, player_id, moderator=True)
        await context.bot.send_message(
            chat_id=player_id,
            text="🏆 Модератор зачем-то убил демона, победа синего города!"
        )

        await update.message.reply_text(
            "💀 Ты зачем-то убил демона. Что ж, это победа синего города.\n"
            "/start, чтобы начать игру заново"
        )
        logger.info(f"Модератор убил демона (жетон {token_id}). Победа синего города.")
        
        reset_user_game_state(player_id)
        moderator_id = update.effective_user.id
        reset_user_game_state(moderator_id)

        return ConversationHandler.END

    # Обновляем статус жетона на "убит"
    update_token_kill(token_id)
    logger.info(f"Жетон {token_id} выбран для убийства и помечен как убит.")
    await update.message.reply_text(f"Жетон {token_id} выбран для убийства и его статус обновлен.")
    await show_game_set(context, update.effective_user.id, moderator=True)

    # Проверяем, не закончилась ли игра победой красных
    is_red_won = await red_won(context)
    
    if is_red_won:
        return ConversationHandler.END

    return await invite_player(update, context)

async def red_won(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Проверяет, остались ли в игре два или меньше жетонов, и возвращает True, если победа красных.
    """
    alive_tokens = get_alive_tokens()  # Получаем список живых жетонов

    if len(alive_tokens) <= 2:
        # Получаем информацию о текущем игроке и модераторе
        game_set = get_latest_game_set()
        player_id = game_set.get('player_id')

        moderators = get_moderators()
        if moderators:
            moderator = moderators[0]
            moderator_id = moderator['id']

            await show_game_set(context, moderator_id, moderator=True)
            await context.bot.send_message(
                chat_id=moderator_id,
                text="🔥 В игре осталось всего 2 жетона, это победа красных!\n\n/start чтобы начать заново",
                parse_mode='HTML'
            )

            await show_game_set(context, player_id, moderator=True)
            await context.bot.send_message(
                chat_id=player_id,
                text="😞 Ты так и не убил демона, это победа красного города 🫠"
            )

            logger.info("Объявлена победа красного города, осталось 2 или меньше жетонов.")
        
        return True

    return False
