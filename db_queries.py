# db_queries.py

CREATE_USERS_TABLE = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(255),
    userid INTEGER UNIQUE,
    moderator BOOLEAN NOT NULL DEFAULT 0,
    on_game BOOLEAN NOT NULL DEFAULT 0
)
'''

INSERT_USER = '''
INSERT INTO users (username, userid, moderator, on_game)
VALUES (?, ?, ?, ?)
'''

UPDATE_USER_AS_MODERATOR = '''
UPDATE users
SET moderator = ?
WHERE userid = ?
'''

UPDATE_USER_USERNAME = '''
UPDATE users
SET username = ?
WHERE userid = ?
'''

# Обновление CREATE_GAME_SET_TABLE, чтобы включить player_username
CREATE_GAME_SET_TABLE = '''
CREATE TABLE IF NOT EXISTS game_set (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tokens_count INTEGER,
    red_count INTEGER,
    player_username VARCHAR(255),
    player_id INTEGER
)
'''

INSERT_GAME_SET = '''
INSERT INTO game_set (tokens_count, red_count, player_username)
VALUES (?, ?, ?)
'''

UPDATE_GAME_SET = '''
UPDATE game_set
SET tokens_count = ?, red_count = ?, player_username = ?
WHERE id = ?
'''


# Создание таблицы tokens с обновленным столбцом alignment
CREATE_TOKENS_TABLE = '''
CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alignment TEXT CHECK(alignment IN ('blue', 'red')),
    character TEXT CHECK(character IN ('townfolk', 'minion', 'demon')),
    red_neighbors INTEGER DEFAULT 0,
    alive BOOLEAN NOT NULL DEFAULT 1
)
'''

# Вставка нового жетона
INSERT_TOKEN = '''
INSERT INTO tokens (alignment, character, red_neighbors)
VALUES (?, ?, ?)
'''

# Очистка таблицы tokens
DELETE_ALL_TOKENS = '''
DELETE FROM tokens
'''

# Получение всех жетонов
SELECT_ALL_TOKENS = '''
SELECT id, alignment, character, red_neighbors FROM tokens
'''

# Обновление жетона
UPDATE_TOKEN = '''
UPDATE tokens
SET alignment = ?, character = ?, red_neighbors = ?
WHERE id = ?
'''