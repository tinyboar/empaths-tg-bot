# red_neighbors_handlers.py

import logging
from database import get_all_tokens, update_token_red_neighbors

# Настройка логирования
logger = logging.getLogger(__name__)

def count_red_neighbors_of_blue_tokens():
    """
    Рассчитывает количество красных соседей для каждого синего жетона
    и обновляет поле red_neighbors в базе данных.
    """
    # Получаем все жетоны из базы данных
    tokens = get_all_tokens()
    
    # Создаем словарь для удобного доступа к жетонам по их id
    tokens_dict = {token['id']: {'alignment': token['alignment'], 'character': token['character'], 'red_neighbors': token['red_neighbors']} for token in tokens}
    
    tokens_count = len(tokens)
    
    # Обходим каждый жетон
    for token_id in range(1, tokens_count + 1):
        token = tokens_dict.get(token_id)
        if not token:
            logger.warning(f"Жетон с id={token_id} не найден.")
            continue

        if token['alignment'] == 'blue':
            # Для синего жетона считаем количество красных соседей
            red_neighbors = 0
            
            # Находим соседей с учётом цикличности (круговая расстановка жетонов)
            left_neighbor_id = token_id - 1 if token_id > 1 else tokens_count
            right_neighbor_id = token_id + 1 if token_id < tokens_count else 1
            
            left_neighbor = tokens_dict.get(left_neighbor_id)
            right_neighbor = tokens_dict.get(right_neighbor_id)
            
            # Проверяем цвет соседей
            if left_neighbor and left_neighbor['alignment'] == 'red':
                red_neighbors += 1
            if right_neighbor and right_neighbor['alignment'] == 'red':
                red_neighbors += 1
            
            # Обновляем поле red_neighbors в базе данных
            update_token_red_neighbors(token_id, red_neighbors)
            logger.info(f"Жетон {token_id}: количество красных соседей обновлено до {red_neighbors}")
        else:
            # Для красных жетонов red_neighbors не обновляем
            pass
