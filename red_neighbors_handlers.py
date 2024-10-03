# red_neighbors_handlers.py

import logging
from database import get_all_tokens, update_token_red_neighbors

logger = logging.getLogger(__name__)

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
