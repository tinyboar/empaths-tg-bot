import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

API_TOKEN = '7623094127:AAFNpbiGouhgdB49brc76rF9SBN5z7UbDYc'

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Карта количества игроков и числа "красных"
red_distribution = {
    16: 4, 15: 4, 14: 4, 13: 4,
    12: 3, 11: 3, 10: 3, 9: 2,
    8: 2, 7: 2
}

# Класс GameState
class GameState:
    def __init__(self):
        self.moderator = None
        self.players = {}  # Хранение данных игроков
        self.num_red = 0  # Количество красных
        self.selected_red = set()  # Выбранные красные игроки
    
    def set_players_count(self, count):
        """Установка количества игроков."""
        self.players = {i: {'role': 'none', 'alive': True} for i in range(1, count + 1)}
        self.selected_red = set()
    
    def set_role(self, player_id, role):
        """Назначение роли игроку."""
        if player_id in self.players:
            self.players[player_id]['role'] = role
    
    def get_game_state(self):
        """Возвращает текущее состояние игры."""
        return {
            'players': self.players
        }

game_state = GameState()

# Обработчик для команды /start
@dp.message(Command("start"))
async def start_game(message: Message):
    game_state.moderator = message.from_user.id

    # Создание клавиатуры для выбора количества игроков
    buttons = [KeyboardButton(text=str(i)) for i in sorted(red_distribution.keys(), reverse=True)]
    keyboard = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)
    
    await message.answer("Выберите количество игроков:", reply_markup=keyboard)

# Обработчик для выбора количества игроков
@dp.message(lambda message: message.text.isdigit() and int(message.text) in red_distribution)
async def choose_players_count(message: Message):
    num_players = int(message.text)
    game_state.set_players_count(num_players)
    game_state.num_red = red_distribution[num_players]
    
    await display_tokens(message, num_players)
    
    # После выбора количества игроков, предложить выбрать роли
    await message.answer(f"Теперь выберите, кто будет 'красным'. Красных нужно выбрать: {game_state.num_red}.")
    
    # Отправляем клавиатуру с номерами игроков для выбора "красных"
    await send_red_selection_keyboard(message)

# Функция для отображения жетонов в круге
async def display_tokens(message: Message, num_players: int):
    """Отображаем круг жетонов с цветом, соответствующим роли игрока."""
    def get_player_emoji(player_id):
        role = game_state.players[player_id]['role']
        if role == 'red':
            return "🔴"
        elif role == 'blue':
            return "🔵"
        else:
            return "⚪"  # Используется, если роль еще не назначена

    lines = []
    if num_players == 16:
        positions = [
            [1, 2, 3, 4],
            [5, None, None, None, None, None, None, None, 6],
            [7, None, None, None, None, None, None, None, 8],
            [9, None, None, None, None, None, None, None, 10],
            [11, None, None, None, None, None, None, None, 12],
            [13, 14, 15, 16],
        ]
    elif num_players == 14:
        positions = [
            [1, 2, 3, 4],
            [5, None, None, None, None, 6],
            [7, None, None, None, None, 8],
            [9, None, None, None, None, 10],
            [11, None, None, None, None, 12],
            [13, 14],
        ]
    elif num_players == 12:
        positions = [
            [1, 2, 3, 4],
            [5, None, None, None, None, 6],
            [7, None, None, None, None, 8],
            [9, None, None, None, None, 10],
            [11, None, None, None, None, 12],
        ]
    elif num_players == 10:
        positions = [
            [None, 1, 2, 3],
            [4, None, None, None, 5],
            [6, None, None, None, 7],
            [None, 8, 9, 10],
        ]
    elif num_players == 8:
        positions = [
            [1, 2, 3, 4],
            [5, None, None, None, None, 6],
            [7, None, None, None, None, 8],
        ]
    elif num_players == 7:
        positions = [
            [1, 2, 3, 4],
            [5, None, None, None, None, 6],
            [7],
        ]
    else:
        # Если количество игроков меньше или не поддерживается, отображаем простой список
        token_display = "Игроки:\n" + " ".join([
            f"{get_player_emoji(pid)} {pid}" for pid in range(1, num_players + 1)
        ])
        await message.answer(token_display)
        return

    # Строим строки отображения на основе позиций
    for row in positions:
        line = ""
        for pid in row:
            if pid is None:
                line += "     "  # Пробелы для выравнивания
            else:
                emoji = get_player_emoji(pid)
                line += f"{emoji} {pid}   "
        lines.append(line.rstrip())  # Убираем лишние пробелы в конце строки

    token_display = "\n".join(lines)
    await message.answer(token_display)


# Функция для отправки клавиатуры с номерами игроков
async def send_red_selection_keyboard(message: Message):
    buttons = []
    for player_id in sorted(game_state.players.keys()):
        # Проверяем, выбран ли игрок
        if game_state.players[player_id]['role'] == 'red':
            button_text = f"✅ {player_id}"
            callback_data = f"deselect_red:{player_id}"
        else:
            button_text = f"{player_id}"
            callback_data = f"select_red:{player_id}"
        
        buttons.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    
    # Разбиваем кнопки на группы по 5
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            buttons[i:i + 5] for i in range(0, len(buttons), 5)
        ]
    )
    await message.answer("Выберите игроков, которые будут 'красными':", reply_markup=keyboard)


# Обработчик для выбора роли игроков через callback
@dp.callback_query(lambda c: c.data and c.data.startswith("select_red:"))
async def assign_role(callback: CallbackQuery):
    _, player_id_str = callback.data.split(":")
    player_id = int(player_id_str)
    
    # Проверяем, не был ли уже выбран этот игрок
    if game_state.players[player_id]['role'] != 'none':
        await callback.answer("Этот игрок уже выбран.", show_alert=True)
        return
    
    # Проверяем, осталось ли еще выбирать "красных"
    if len(game_state.selected_red) < game_state.num_red:
        game_state.set_role(player_id, 'red')
        game_state.selected_red.add(player_id)
        await callback.answer(f"Игрок {player_id} стал 'красным'.")
        
        # Обновляем сообщение с жетонами, чтобы отобразить изменения
        await display_tokens(callback.message, len(game_state.players))
        
        # Если все "красные" выбраны, назначаем остальных "синими"
        if len(game_state.selected_red) == game_state.num_red:
            assign_remaining_roles()
            await callback.message.answer(
                "Все красные выбраны. Остальные игроки назначены 'синими'.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await send_game_state(callback.message)
    else:
        # Если уже выбрано нужное количество "красных"
        await callback.answer("Все красные уже выбраны.", show_alert=True)

def assign_remaining_roles():
    """Назначает оставшихся игроков 'синими'."""
    for pid, player in game_state.players.items():
        if player['role'] == 'none':
            game_state.set_role(pid, 'blue')

# Функция для отправки состояния игры
async def send_game_state(message: Message):
    state = game_state.get_game_state()
    game_info = "\n".join([
        f"Игрок {pid}: {info['role']} (Жив: {info['alive']})" 
        for pid, info in sorted(state['players'].items())
    ])
    await message.answer(f"Текущее состояние игры:\n{game_info}")

# Обработчик для команды /role
@dp.message(Command("role"))
async def show_role(message: Message):
    player_id = message.from_user.id
    if player_id in game_state.players:
        player_role = game_state.players[player_id]['role']
        await message.answer(f"Ваша роль: {player_role}")
    else:
        await message.answer("Вы не являетесь частью игры.")

# Обработчик для команды /kill
@dp.message(Command("kill"))
async def kill_player(message: Message):
    if message.from_user.id != game_state.moderator:
        await message.answer("Только модератор может казнить.")
        return

    try:
        player_id = int(message.text.split()[1])  # Получаем ID игрока из команды
        if player_id in game_state.players and game_state.players[player_id]['alive']:
            game_state.players[player_id]['alive'] = False
            await message.answer(f"Игрок {player_id} был казнен.")
            await send_game_state(message)
        else:
            await message.answer("Невозможно казнить этого игрока.")
    except (IndexError, ValueError):
        await message.answer("Используйте: /kill <player_id>")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
