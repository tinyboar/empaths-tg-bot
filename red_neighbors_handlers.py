# red_neighbors_handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import update_token_red_neighbors, update_token_drunk, get_all_tokens
from render_game_set import show_game_set
from player_manager import invite_player
from constants import GET_DRUNK_TOKEN_NUMBER, SET_DRUNK_RED_NEIGHBORS

logger = logging.getLogger(__name__)

async def make_drunk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Предлагает модератору выбрать номер жетона, который будет помечен как 'пьяный'.
    """
    await update.message.reply_text("Выберите номер жетона, который хотите пометить как 'пьяный':")
    return GET_DRUNK_TOKEN_NUMBER
    
async def get_drunk_token_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод номера 'пьяного' жетона.
    """
    token_number_text = update.message.text.strip()
    if not token_number_text.isdigit():
        await update.message.reply_text("Пожалуйста, введите номер жетона в виде целого числа.")
        return GET_DRUNK_TOKEN_NUMBER

    token_number = int(token_number_text)
    context.user_data['drunk_token_number'] = token_number

    # Устанавливаем поле drunk на True для выбранного жетона
    update_token_drunk(token_number)
    logger.info(f"Жетон {token_number} помечен как 'пьяный'.")

    await update.message.reply_text("Введите количество красных соседей для этого жетона:")
    return SET_DRUNK_RED_NEIGHBORS

async def set_drunk_red_neighbors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Устанавливает значение red_neighbors для выбранного 'пьяного' жетона.
    """
    red_neighbors_text = update.message.text.strip()
    if not red_neighbors_text.isdigit():
        await update.message.reply_text("Пожалуйста, введите целое число для количества соседей.")
        return SET_DRUNK_RED_NEIGHBORS

    red_neighbors = int(red_neighbors_text)
    token_number = context.user_data['drunk_token_number']

    update_token_red_neighbors(token_number, red_neighbors)
    logger.info(f"Жетон {token_number}: количество красных соседей обновлено до {red_neighbors}")

    await update.message.reply_text(f"Жетон {token_number} теперь имеет {red_neighbors} красных соседей и помечен как 'пьяный'.")

    player_id = update.effective_user.id
    count_red_neighbors_of_blue_tokens()
    await show_game_set(context, player_id, moderator=True)

    return await invite_player(update, context)


def count_red_neighbors_of_blue_tokens():
    """
    Рассчитывает количество красных соседей для каждого синего живого жетона
    и обновляет поле red_neighbors в базе данных.
    Мёртвые жетоны и "пьяные" жетоны, для которых производится расчёт, пропускаются при обновлении.
    """
    # Получаем все жетоны из базы данных
    tokens = get_all_tokens()
    
    # Создаем словарь для удобного доступа к жетонам по их id
    tokens_dict = {
        token['id']: {
            'alignment': token['alignment'],
            'character': token['character'],
            'red_neighbors': token['red_neighbors'],
            'alive': token['alive'],
            'drunk': token.get('drunk', False)
        } for token in tokens
    }
    
    tokens_count = len(tokens)

    # Обходим каждый жетон
    for token_id in range(1, tokens_count + 1):
        token = tokens_dict.get(token_id)
        if not token:
            logger.warning(f"Жетон с id={token_id} не найден.")
            continue

        if token['alignment'] == 'blue' and token['alive']:
            # Если жетон "пьяный", оставляем информацию без изменений
            if token['drunk']:
                logger.info(f"Жетон {token_id} помечен как 'пьяный'. Информация не изменяется.")
                continue

            # Для синего живого жетона считаем количество красных соседей
            red_neighbors = 0
            
            # Находим левого живого соседа
            left_neighbor_id = token_id
            for _ in range(tokens_count - 1):  # Максимум tokens_count - 1 шагов
                left_neighbor_id = left_neighbor_id - 1 if left_neighbor_id > 1 else tokens_count
                if left_neighbor_id == token_id:
                    # Возвратились к самому себе
                    break
                left_neighbor = tokens_dict.get(left_neighbor_id)
                if left_neighbor and left_neighbor['alive']:
                    break
            else:
                left_neighbor = None

            # Находим правого живого соседа
            right_neighbor_id = token_id
            for _ in range(tokens_count - 1):
                right_neighbor_id = right_neighbor_id + 1 if right_neighbor_id < tokens_count else 1
                if right_neighbor_id == token_id:
                    # Возвратились к самому себе
                    break
                right_neighbor = tokens_dict.get(right_neighbor_id)
                if right_neighbor and right_neighbor['alive']:
                    break
            else:
                right_neighbor = None

            # Проверяем цвет соседей (включая "пьяные" жетоны)
            if left_neighbor and left_neighbor['alignment'] == 'red':
                red_neighbors += 1
            if right_neighbor and right_neighbor['alignment'] == 'red':
                red_neighbors += 1

            # Обновляем поле red_neighbors в базе данных
            update_token_red_neighbors(token_id, red_neighbors)
            logger.info(f"Жетон {token_id}: количество красных соседей обновлено до {red_neighbors}")
        else:
            # Для красных жетонов и мёртвых синих жетонов red_neighbors не обновляем
            pass
