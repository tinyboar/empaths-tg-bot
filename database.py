# database.py
import logging
import sqlite3
from db_queries import (
    CREATE_USERS_TABLE,
    INSERT_USER,
    UPDATE_USER_AS_MODERATOR,
    UPDATE_USER_USERNAME,
    CREATE_GAME_SET_TABLE,
    INSERT_GAME_SET,
    UPDATE_GAME_SET,
    CREATE_TOKENS_TABLE,
    INSERT_TOKEN,
    DELETE_ALL_TOKENS,
    SELECT_ALL_TOKENS,
    UPDATE_TOKEN
)

logger = logging.getLogger(__name__)

def init_db(db_path='empaths.db'):
    """
    Инициализирует базу данных, создавая необходимые таблицы.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(CREATE_USERS_TABLE)
    cursor.execute(CREATE_GAME_SET_TABLE)
    cursor.execute(CREATE_TOKENS_TABLE)
    conn.commit()
    conn.close()

def add_user(username, userid, moderator=False, db_path='empaths.db'):
    """
    Добавляет нового пользователя в базу данных. Если пользователь уже существует, обновляет его информацию.
    Возвращает True, если пользователь новый, и False, если уже существовал.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (userid,))
    user = cursor.fetchone()
    if user:
        # Пользователь существует, обновляем информацию
        cursor.execute('UPDATE users SET username = ?, moderator = ? WHERE id = ?', (username, int(moderator), userid))
        is_new_user = False
    else:
        # Новый пользователь, добавляем в базу данных
        cursor.execute('INSERT INTO users (id, username, moderator) VALUES (?, ?, ?)', (userid, username, int(moderator)))
        is_new_user = True
    conn.commit()
    conn.close()
    return is_new_user

def get_moderators(db_path='empaths.db'):
    """
    Возвращает список модераторов из базы данных.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users WHERE moderator = 1')
    moderators = cursor.fetchall()
    conn.close()
    # Преобразуем в список словарей
    return [{'id': row[0], 'username': row[1]} for row in moderators]


def is_user_moderator(userid, db_path='empaths.db'):
    """
    Проверяет, является ли пользователь модератором.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT moderator FROM users WHERE userid = ?", (userid,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return bool(result[0])
    return False


def add_game_set(tokens_count, red_count, player_username, player_id):
    """
    Добавляет запись в таблицу game_set.
    """
    conn = sqlite3.connect('empaths.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO game_set (tokens_count, red_count, player_username, player_id)
        VALUES (?, ?, ?, ?)
    ''', (tokens_count, red_count, player_username, player_id))
    conn.commit()
    conn.close()
    
    
def get_latest_game_set(db_path='empaths.db'):
    """
    Получает последние настройки игры из таблицы game_set.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT tokens_count, red_count, player_username FROM game_set ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'tokens_count': result[0],
            'red_count': result[1],
            'player_username': result[2]
        }
    return None

def clear_tokens(db_path='empaths.db'):
    """
    Очищает таблицу tokens и сбрасывает счетчик автоинкремента.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Очищаем таблицу
    cursor.execute("DELETE FROM tokens")
    # Сбрасываем автоинкремент
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='tokens'")
    conn.commit()
    conn.close()
    logger.info("Таблица tokens очищена и идентификаторы сброшены.")


def add_tokens(tokens_list, db_path='empaths.db'):
    """
    Добавляет список жетонов в таблицу tokens.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executemany(INSERT_TOKEN, tokens_list)
    conn.commit()
    conn.close()
    logger.info(f"Добавлено {len(tokens_list)} жетонов в таблицу tokens.")

def get_all_tokens(db_path='empaths.db'):
    """
    Возвращает список всех жетонов из таблицы tokens в виде словарей.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tokens')
    tokens = cursor.fetchall()
    conn.close()
    return [dict(token) for token in tokens]

def update_token(token_id, alignment, character, red_neighbors, db_path='empaths.db'):
    """
    Обновляет жетон по его id.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(UPDATE_TOKEN, (alignment, character, red_neighbors, token_id))
    conn.commit()
    conn.close()
    logger.info(f"Жетон с id={token_id} обновлен.")
    
    

def update_token_alignment(token_id, alignment, db_path='empaths.db'):
    """
    Обновляет alignment жетона по его id.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE tokens SET alignment = ? WHERE id = ?',
        (alignment, token_id)
    )
    conn.commit()
    conn.close()
    logger.info(f"Жетон с id={token_id} обновлен. alignment={alignment}")


def update_token_character(token_id, character, db_path='empaths.db'):
    """
    Обновляет поле character жетона по его id.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE tokens SET character = ? WHERE id = ?',
        (character, token_id)
    )
    conn.commit()
    conn.close()
    logger.info(f"Жетон с id={token_id} обновлен. character={character}")


def update_token_red_neighbors(token_id, red_neighbors, db_path='empaths.db'):
    """
    Обновляет поле red_neighbors жетона по его id.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE tokens SET red_neighbors = ? WHERE id = ?',
        (red_neighbors, token_id)
    )
    conn.commit()
    conn.close()
    logger.info(f"Жетон с id={token_id} обновлен. red_neighbors={red_neighbors}")


def get_user_by_username(username, db_path='empaths.db'):
    """
    Получает информацию о пользователе по username.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, moderator, on_game FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'moderator': bool(user[2]),
            'on_game': bool(user[3])
        }
    else:
        return None

def get_user_by_id(userid, db_path='empaths.db'):
    """
    Получает информацию о пользователе по ID.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, moderator, on_game FROM users WHERE id = ?', (userid,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'moderator': bool(user[2]),
            'on_game': bool(user[3])
        }
    else:
        return None

def update_user_on_game(userid, on_game, db_path='empaths.db'):
    """
    Обновляет поле on_game у пользователя.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET on_game = ? WHERE id = ?', (int(on_game), userid))
    conn.commit()
    conn.close()


