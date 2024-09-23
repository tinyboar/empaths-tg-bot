# moderator_client.py

import asyncio
import websockets
import arcade
import arcade.gui
import json
import queue
import threading
import math
import random

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1090
NUM_PLAYERS = 16
CIRCLE_RADIUS = 300  # Радиус круга для размещения игроков
TOKEN_RADIUS = 40  # Радиус жетона

ROLE_COLORS = {
    "blue": arcade.color.BLUE,      # Синий игрок
    "red": arcade.color.RED,        # Красный игрок
    "demon": arcade.color.BLACK     # Демон - черный цвет
}

ROLE_SEQUENCE = ["blue", "red", "demon"]  # Порядок изменения ролей
RED_EMPATH_INFO_SEQUENCE = [0, 1, 2]  # Возможные значения для информации красных эмпатов

class ModeratorClient(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Moderator Client")
        self.websocket = None
        self.connected = False

        arcade.set_background_color(arcade.color.DARK_SLATE_BLUE)

        # Создаем менеджер GUI
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Сообщение для отображения инструкций
        self.message_label = arcade.gui.UILabel(
            text="Ожидание подключения к серверу...",
            width=800,
            height=100,
            text_color=arcade.color.WHITE,
            font_size=20,
            align="center"
        )
        self.message_label_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="top", align_y=-100, child=self.message_label
        )
        self.manager.add(self.message_label_widget)

        # Очередь для сообщений из сетевого потока
        self.message_queue = queue.Queue()

        # Инициализация данных игроков
        self.roles = {i: "blue" for i in range(1, NUM_PLAYERS + 1)}
        self.token_colors = {i: ROLE_COLORS["blue"] for i in range(1, NUM_PLAYERS + 1)}
        self.blue_player_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}
        self.red_empath_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}

        self.assigning_red_info = False  # Флаг для этапа выбора информации для красных эмпатов

        # Инициализируем цикл событий asyncio и запускаем его в отдельном потоке
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_asyncio_loop, daemon=True).start()

        # Запускаем асинхронное подключение
        self.loop.call_soon_threadsafe(asyncio.ensure_future, self.connect())

        # Добавляем кнопку генерации раскладки
        self.generate_button = arcade.gui.UIFlatButton(text="Сгенерировать раскладку", width=300)
        self.generate_button.on_click = self.on_generate_roles
        self.generate_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="bottom", align_y=50, child=self.generate_button
        )
        self.manager.add(self.generate_button_widget)

        # Добавляем кнопку подтверждения ролей
        self.submit_button = arcade.gui.UIFlatButton(text="Подтвердить роли", width=300)
        self.submit_button.on_click = self.on_submit_roles
        self.submit_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="bottom", align_y=0, child=self.submit_button
        )
        self.manager.add(self.submit_button_widget)

        # Кнопка для подтверждения информации красных эмпатов
        self.submit_red_info_button = arcade.gui.UIFlatButton(text="Подтвердить информацию красных", width=300)
        self.submit_red_info_button.on_click = self.on_submit_red_info
        self.submit_red_info_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="bottom", align_y=0, child=self.submit_red_info_button
        )

        # Кнопка для начала игры
        self.start_game_button = arcade.gui.UIFlatButton(text="Начать игру", width=300)
        self.start_game_button.on_click = self.on_start_game
        self.start_game_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="center", child=self.start_game_button
        )

        # Инициализация жетонов игроков
        self.tokens = {i: {'id': i, 'alive': True} for i in range(1, NUM_PLAYERS + 1)}
        self.night_phase = False

		

    def start_asyncio_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def connect(self):
        try:
            self.websocket = await websockets.connect("ws://localhost:12345")
            await self.websocket.send(
                json.dumps({"action": "authenticate", "role": "moderator"})
            )
            self.connected = True
            self.message_queue.put(
                {"action": "update_message", "text": "Подключено к серверу. Ожидание начала игры..."}
            )
            self.loop.call_soon_threadsafe(asyncio.ensure_future, self.listen())
        except Exception as e:
            self.message_queue.put({"action": "update_message", "text": f"Ошибка подключения: {e}"})

    async def listen(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.message_queue.put(data)
        except websockets.ConnectionClosed:
            self.message_queue.put({"action": "update_message", "text": "Соединение с сервером потеряно"})

    def on_generate_roles(self, event):
        """Случайно генерируем раскладку ролей и информации для красных эмпатов."""
        player_ids = list(range(1, NUM_PLAYERS + 1))

        # Назначаем 3 красных
        red_players = random.sample(player_ids, 3)
        for player_id in red_players:
            self.roles[player_id] = "red"
            self.token_colors[player_id] = ROLE_COLORS["red"]

        # Назначаем 1 демона
        remaining_players = [pid for pid in player_ids if pid not in red_players]
        demon_player = random.choice(remaining_players)
        self.roles[demon_player] = "demon"
        self.token_colors[demon_player] = ROLE_COLORS["demon"]

        # Оставшиеся игроки — синие эмпаты
        for player_id in player_ids:
            if player_id not in red_players and player_id != demon_player:
                self.roles[player_id] = "blue"
                self.token_colors[player_id] = ROLE_COLORS["blue"]

        # Обновляем информацию для синих эмпатов
        self.update_blue_neighbors()

        # Устанавливаем флаг для выбора информации красных эмпатов
        self.assigning_red_info = True

        # Убираем кнопку подтверждения ролей
        self.manager.remove(self.submit_button_widget)

        # Показываем кнопку для подтверждения информации красных эмпатов
        self.manager.add(self.submit_red_info_button_widget)

        # Обновляем сообщение для модератора
        self.message_label.text = "Роли сгенерированы. Теперь выберите информацию для красных эмпатов."

    def assign_roles(self):
        self.manager.clear()
        self.message_label.text = "Назначьте роли игрокам. Нажимайте на жетоны, чтобы поменять роль:"
        self.manager.add(self.message_label_widget)
        # Добавляем кнопку подтверждения ролей обратно, если она была скрыта
        self.manager.add(self.submit_button_widget)
        self.assigning_red_info = False  # На этом этапе мы не выбираем информацию для красных

    def on_draw(self):
        arcade.start_render()
        self.manager.draw()
        center_x = self.width // 2
        center_y = self.height // 2
        for i in range(NUM_PLAYERS):
            angle = 2 * math.pi * i / NUM_PLAYERS
            token_x = center_x + CIRCLE_RADIUS * math.cos(angle)
            token_y = center_y + CIRCLE_RADIUS * math.sin(angle)
            self.draw_token(i + 1, token_x, token_y)

            # Рисуем информацию для синих эмпатов
            if self.roles[i + 1] == "blue":
                info_text = f"{self.blue_player_info[i + 1]}"
                arcade.draw_text(info_text, token_x + 60, token_y - 10, arcade.color.WHITE, 14)

            # Рисуем информацию для красных эмпатов и демонов
            if self.roles[i + 1] in ["red", "demon"]:
                info_text = f"{self.red_empath_info[i + 1]}"
                arcade.draw_text(info_text, token_x + 60, token_y - 10, arcade.color.YELLOW, 14)

    def draw_token(self, token_id, x, y):
        token = self.tokens[token_id]
        color = self.token_colors[token_id] if token['alive'] else arcade.color.DARK_GRAY
        arcade.draw_circle_filled(x, y, TOKEN_RADIUS, color)
        arcade.draw_text(str(token_id), x - 10, y - 10, arcade.color.WHITE, 12)



    def on_mouse_press(self, x, y, button, modifiers):
        center_x = self.width // 2
        center_y = self.height // 2

        if self.night_phase:
            # Модератор выбирает жетон для убийства ночью
            for i in range(NUM_PLAYERS):
                token_id = i + 1
                token = self.tokens[token_id]
                if token['alive']:
                    angle = 2 * math.pi * i / NUM_PLAYERS
                    token_x = center_x + CIRCLE_RADIUS * math.cos(angle)
                    token_y = center_y + CIRCLE_RADIUS * math.sin(angle)
                    if arcade.get_distance(x, y, token_x, token_y) < TOKEN_RADIUS:
                        # Отправляем сообщение на сервер о ночном убийстве
                        self.send_message({'action': 'night_kill', 'token_id': token_id})
                        # Обновляем состояние жетона как "мертвый"
                        self.tokens[token_id]['alive'] = False
                        # Перекрашиваем жетон в серый цвет
                        self.message_label.text = f"Вы убили ночью жетон {token_id}. Ждем действия игрока."
                        self.on_draw()  # Перерисовка после изменения состояния
                        self.night_phase = False
                        break
        else:
            # Остальной код обработки нажатия на жетоны
            pass



    def cycle_role(self, player_id):
        """Циклически меняем роль игрока при каждом клике."""
        current_role = self.roles[player_id]
        next_role_index = (ROLE_SEQUENCE.index(current_role) + 1) % len(ROLE_SEQUENCE)
        next_role = ROLE_SEQUENCE[next_role_index]

        self.roles[player_id] = next_role
        self.token_colors[player_id] = ROLE_COLORS[next_role]

        # Обновляем текст сообщения для модератора
        role_name = next_role.capitalize()
        self.message_label.text = f"Игрок {player_id}: {role_name}"

        # Обновляем информацию для синих эмпатов
        self.update_blue_neighbors()

    def cycle_red_info(self, player_id):
        """Циклически меняем информацию для красного эмпата или демона при каждом клике."""
        current_info = self.red_empath_info[player_id]
        next_info_index = (RED_EMPATH_INFO_SEQUENCE.index(current_info) + 1) % len(RED_EMPATH_INFO_SEQUENCE)
        next_info = RED_EMPATH_INFO_SEQUENCE[next_info_index]
        self.red_empath_info[player_id] = next_info

        # Обновляем текст сообщения для модератора
        self.message_label.text = f"Игрок {player_id}: Информация {next_info}"

    def update_blue_neighbors(self):
        """Обновляем информацию для синих эмпатов о количестве красных соседей."""
        for i in range(1, NUM_PLAYERS + 1):
            if self.roles[i] == "blue":
                left_neighbor = (i - 2) % NUM_PLAYERS + 1
                right_neighbor = i % NUM_PLAYERS + 1
                neighbors = [self.roles[left_neighbor], self.roles[right_neighbor]]
                self.blue_player_info[i] = neighbors.count("red") + neighbors.count("demon")

    def on_submit_roles(self, event):
        # Проверка на наличие хотя бы 3 красных и 1 демона
        red_count = sum(1 for role in self.roles.values() if role == "red")
        demon_count = sum(1 for role in self.roles.values() if role == "demon")

        if red_count < 3 or demon_count < 1:
            self.message_label.text = "Ошибка: Должно быть хотя бы 3 красных и 1 демон."
            return  # Не переходим к следующему этапу

        # Устанавливаем флаг для выбора информации красных эмпатов
        self.assigning_red_info = True

        # Переходим к шагу выбора информации красных эмпатов
        self.message_label.text = "Все роли назначены. Теперь выберите информацию для красных эмпатов."
        self.manager.remove(self.submit_button_widget)
        self.manager.add(self.submit_red_info_button_widget)

    def on_submit_red_info(self, event):
        """После подтверждения информации красных показываем кнопку начала игры."""
        # Проверка, что у всех красных эмпатов назначена информация
        for player_id in self.red_empath_info:
            if self.roles[player_id] in ["red", "demon"]:
                if self.red_empath_info[player_id] not in RED_EMPATH_INFO_SEQUENCE:
                    self.message_label.text = f"Ошибка: У игрока {player_id} не назначена информация."
                    return

        # Убираем кнопки "Сгенерировать раскладку" и "Подтвердить информацию красных"
        self.manager.remove(self.generate_button_widget)
        self.manager.remove(self.submit_red_info_button_widget)

        # Очищаем менеджер
        self.manager.clear()

        # Обновляем текстовое сообщение для модератора
        self.message_label.text = "Стол разложен. Нажмите 'Начать игру'."
        self.manager.add(self.message_label_widget)

        # Добавляем кнопку "Начать игру" в центр экрана
        self.manager.add(self.start_game_button_widget)

    def on_start_game(self, event):
        # Удаляем кнопку "Начать игру" из менеджера
        self.manager.remove(self.start_game_button_widget)

        # Обновляем текстовое сообщение
        self.message_label.text = "Сейчас идет 1-й день, ждем пока игрок выберет кого казнить."

        # Отправляем сообщение на сервер о начале игры
        self.send_message({'action': 'start_game'})



    def on_update(self, delta_time):
        while not self.message_queue.empty():
            data = self.message_queue.get()
            self.handle_message(data)
        self.manager.on_update(delta_time)

    def handle_message(self, data):
        action = data.get("action")
        if action == "update_message":
            self.message_label.text = data.get("text", "")
        elif action == "authenticated":
            self.message_label.text = "Аутентификация успешна."
        elif action == "token_killed":
            token_id = data.get('token_id')
            self.message_label.text = f"Игрок казнил жетон {token_id}. Теперь ваша очередь убить ночью."
            # Обновляем состояние жетона
            self.tokens[token_id]['alive'] = False
            # Перерисовываем окно, чтобы обновить цвет жетона
            self.night_phase = True
            self.on_draw()  # Перерисовка после изменения состояния
        elif action == "night_kill":
            token_id = data.get('token_id')
            self.message_label.text = f"Ночью был убит жетон {token_id}."
            # Обновляем состояние жетона как "мертвый"
            self.tokens[token_id]['alive'] = False
            self.on_draw()  # Перерисовка после изменения состояния


    def run(self):
        arcade.run()
        
    
    def send_message(self, message):
        if self.connected and self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps(message)),
                self.loop
            )


if __name__ == "__main__":
    client = ModeratorClient()
    client.run()
