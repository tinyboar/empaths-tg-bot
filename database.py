# database.py
import logging
import sqlite3
from db_queries import (
    CREATE_USERS_TABLE,
    CREATE_GAME_SET_TABLE,
    CREATE_TOKENS_TABLE,
    INSERT_TOKEN,
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


def add_game_set(tokens_count, red_count, player_username, player_id, moderator_username, moderator_id):
    """
    Добавляет запись в таблицу game_set.
    """
    conn = sqlite3.connect('empaths.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO game_set (tokens_count, red_count, player_username, player_id, moderator_username, moderator_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (tokens_count, red_count, player_username, player_id, moderator_username, moderator_id))
    conn.commit()
    conn.close()
    
def get_latest_game_set(db_path='empaths.db'):
    """
    Получает последние настройки игры из таблицы game_set.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT tokens_count, red_count, player_id, player_username, moderator_id, moderator_username FROM game_set ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'tokens_count': result[0],
            'red_count': result[1],
            'player_id': result[2],
            'player_username': result[3],
            'moderator_id': result[4],
            'moderator_username': result[5]
        }
    return None

def clear_tokens(db_path='empaths.db'):
    """
    Очищает таблицу tokens и сбрасывает счетчик автоинкремента.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tokens")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='tokens'")
    conn.commit()
    conn.close()
    logger.info("Таблица tokens очищена и идентификаторы сброшены.")

def clear_game_set(db_path='empaths.db'):
    """
    Очищает таблицу game_set и сбрасывает счетчик автоинкремента.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM game_set")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='game_set'")
    conn.commit()
    conn.close()
    logger.info("Таблица game_set очищена и идентификаторы сброшены.")
    
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


def get_token_by_id(token_id, db_path='empaths.db'):
    """
    Получает информацию о жетоне по ID.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, alignment, character, red_neighbors, alive FROM tokens WHERE id = ?', (token_id,))
    token = cursor.fetchone()
    conn.close()
    if token:
        return {
            'id': token[0],
            'alignment': token[1],
            'character': token[2],
            'red_neighbors': token[3],
            'alive': bool(token[3])
        }
    else:
        return None
    
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

def update_token_kill(token_id, db_path='empaths.db'):
    """
    Обновляет поле alive жетона по его id.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE tokens SET alive = 0 WHERE id = ?',
            (token_id,)  # Обратите внимание на запятую, чтобы создать кортеж
        )
        conn.commit()
        logger.info(f"Жетон с id={token_id} обновлен. alive=False")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении жетона: {e}")
    finally:
        conn.close()

def get_red_tokens(db_path='empaths.db'):
    """
    Возвращает список номеров красных жетонов из базы данных.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tokens WHERE alignment = 'red'")
    rows = cursor.fetchall()
    conn.close()
    red_token_ids = [row[0] for row in rows]
    logger.info(f"get_red_tokens: retrieved red tokens: {red_token_ids}")
    return red_token_ids



def get_alive_tokens(db_path='empaths.db'):
    """
    Возвращает список номеров живых жетонов из базы данных.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tokens WHERE alive = 1")
        rows = cursor.fetchall()
        alive_token_ids = [row[0] for row in rows]
        logger.info(f"get_alive_tokens: retrieved alive tokens: {alive_token_ids}")
    except sqlite3.Error as e:
        logger.error(f"Database error occurred: {e}")
        alive_token_ids = []
    finally:
        if conn:
            conn.close()

    return alive_token_ids


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


def reset_user_game_state(user_id):
    """
    Сбрасывает состояние on_game для указанного пользователя.
    """
    conn = sqlite3.connect('empaths.db')
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET on_game = 0 WHERE id = ?", (user_id,))
        conn.commit()
        logger.info(f"Состояние on_game для пользователя с id {user_id} успешно сброшено.")
    except Exception as e:
        logger.error(f"Ошибка при сбросе состояния on_game для пользователя с id {user_id}: {e}")
    finally:
        conn.close()
