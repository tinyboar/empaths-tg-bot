from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import get_user_by_id, update_user_on_game, get_moderators, get_latest_game_set
from render_game_set import show_game_set
from constants import START_GAME, EXECUTE_TOKEN
import logging

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
        text="Введите номер жетона, который вы собираетесь казнить:", 
        parse_mode='MarkdownV2'
    )

    # Переходим в состояние EXECUTE_TOKEN
    return EXECUTE_TOKEN

async def execute_token_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод игроком номера жетона.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "Unknown"
    text = update.message.text.strip()

    # Проверяем, что введено число
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите корректный номер жетона (целое число).")
        return EXECUTE_TOKEN  # Остаёмся в том же состоянии

    token_id = int(text)

    # Получаем информацию об игроке
    player = get_user_by_id(user_id)
    if not player:
        logger.warning(f"Пользователь {username} ({user_id}) не найден в базе данных.")
        await update.message.reply_text("Ваши данные не найдены. Пожалуйста, начните игру заново.")
        return ConversationHandler.END

    # Отправляем сообщение модератору
    moderators = get_moderators()
    if moderators:
        moderator = moderators[0]
        moderator_id = moderator['id']
        message = f"Игрок @{username} выбрал для казни жетон {token_id}."
        try:
            await context.bot.send_message(chat_id=moderator_id, text=message)
            logger.info(f"Модератору отправлено сообщение о выборе игрока @{username}.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение модератору: {e}")
    else:
        logger.warning("Модератор не найден для отправки сообщения.")

    await update.message.reply_text("Ваш выбор принят. Спасибо!")

    # Завершаем разговор
    return ConversationHandler.END
