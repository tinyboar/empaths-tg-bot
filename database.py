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

def add_user(username, userid, moderator=False, on_game=False, db_path='empaths.db'):
    """
    Добавляет нового пользователя или обновляет существующего.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(INSERT_USER, (username, userid, moderator, on_game))
        conn.commit()
    except sqlite3.IntegrityError:
        # Если пользователь уже существует, обновим его данные
        cursor.execute(UPDATE_USER_USERNAME, (username, userid))
        cursor.execute(UPDATE_USER_AS_MODERATOR, (moderator, userid))
        conn.commit()
    finally:
        conn.close()

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


def add_game_set(tokens_count, red_count, player_username, db_path='empaths.db'):
    """
    Добавляет новую запись в таблицу game_set.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(INSERT_GAME_SET, (tokens_count, red_count, player_username))
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
    Получает все жетоны из таблицы tokens.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(SELECT_ALL_TOKENS)
    tokens = cursor.fetchall()
    conn.close()
    return tokens

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

