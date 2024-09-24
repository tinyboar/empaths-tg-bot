import asyncio
import websockets
import arcade
import arcade.gui
import json
import threading
import math
import queue
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
NUM_PLAYERS = 5
CIRCLE_RADIUS = 200  # Радиус круга для размещения игроков
TOKEN_RADIUS = 20  # Радиус жетона

ROLE_COLORS = {
    "blue": arcade.color.BLUE,
    "red": arcade.color.RED,
    "demon": arcade.color.BLACK,
    "dead": arcade.color.DARK_GRAY  # Цвет для мертвых игроков
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
            font_size=14,
            align="center"
        )
        self.message_label_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="top", align_y=-20, child=self.message_label
        )
        self.manager.add(self.message_label_widget)

        # Очередь для сообщений из сетевого потока
        self.message_queue = queue.Queue()

        # Инициализация данных игроков
        self.roles = {i: "blue" for i in range(1, NUM_PLAYERS + 1)}
        self.token_colors = {i: ROLE_COLORS["blue"] for i in range(1, NUM_PLAYERS + 1)}
        self.tokens = {i: {'id': i, 'alive': True} for i in range(1, NUM_PLAYERS + 1)}  # Жетоны с состоянием alive
        self.blue_player_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}
        self.red_empath_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}

        self.assigning_red_info = False  # Флаг для этапа выбора информации для красных эмпатов
        self.night_phase = False  # Флаг для ночной фазы

        # Инициализируем цикл событий asyncio и запускаем его в отдельном потоке
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_asyncio_loop, daemon=True).start()

        # Запускаем асинхронное подключение
        self.loop.call_soon_threadsafe(asyncio.ensure_future, self.connect())

        # Добавляем кнопку генерации раскладки
        self.generate_button = arcade.gui.UIFlatButton(text="Сгенерировать раскладку", width=200)
        self.generate_button.on_click = self.on_generate_roles
        self.generate_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="bottom", align_y=50, child=self.generate_button
        )
        self.manager.add(self.generate_button_widget)

        # Добавляем кнопку подтверждения ролей
        self.submit_button = arcade.gui.UIFlatButton(text="Подтвердить роли", width=200)
        self.submit_button.on_click = self.on_submit_roles
        self.submit_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="bottom", align_y=0, child=self.submit_button
        )
        self.manager.add(self.submit_button_widget)

        # Кнопка для подтверждения информации красных эмпатов
        self.submit_red_info_button = arcade.gui.UIFlatButton(text="Подтвердить информацию красных", width=200)
        self.submit_red_info_button.on_click = self.on_submit_red_info
        self.submit_red_info_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="bottom", align_y=0, child=self.submit_red_info_button
        )

        # Кнопка для начала игры
        self.start_game_button = arcade.gui.UIFlatButton(text="Начать игру", width=200)
        self.start_game_button.on_click = self.on_start_game
        self.start_game_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="center", child=self.start_game_button
        )

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

    def process_message(self, data):
        """Обработка сообщений от сервера"""
        action = data.get('action')
        if action == 'update_state':
            state = data.get('state', {})
            self.tokens = {t['id']: {'id': t['id'], 'alive': t['alive']} for t in state['tokens']}
            self.roles = {t['id']: t['role'] for t in state['tokens']}
            self.red_empath_info = state.get('empath_info', {})
            self.on_draw()
        elif action == 'update_message':
            self.message_label.text = data.get('text', "")
        elif action == 'token_killed':
            token_id = data.get('token_id')
            self.tokens[token_id]['alive'] = False
            self.message_label.text = f"Игрок казнил жетон {token_id}. Теперь ваша очередь убить ночью."
            self.night_phase = True  # Переключаем в ночную фазу
            self.on_draw()

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

        # Обновляем сообщение для модератора
        self.message_label.text = "Роли сгенерированы. Теперь выберите информацию для красных эмпатов."

    def on_draw(self):
        arcade.start_render()
        self.manager.draw()

        center_x = self.width // 2
        center_y = self.height // 2

        # Отрисовка всех жетонов
        for i in range(NUM_PLAYERS):
            token_id = i + 1
            angle = 2 * math.pi * i / NUM_PLAYERS
            token_x = center_x + CIRCLE_RADIUS * math.cos(angle)
            token_y = center_y + CIRCLE_RADIUS * math.sin(angle)
            self.draw_token(token_id, token_x, token_y)

            # Рисуем информацию для синих эмпатов
            if self.roles[token_id] == "blue":
                info_text = f"{self.blue_player_info[token_id]}"
                arcade.draw_text(info_text, token_x + 40, token_y - 10, arcade.color.WHITE, 14)

            # Рисуем информацию для красных эмпатов и демонов
            if self.roles[token_id] in ["red", "demon"]:
                info_text = f"{self.red_empath_info.get(token_id, 0)}"
                arcade.draw_text(info_text, token_x + 40, token_y - 10, arcade.color.YELLOW, 14)

    def draw_token(self, token_id, x, y):
        alive = self.tokens[token_id]['alive']
        color = self.token_colors[token_id] if alive else ROLE_COLORS['dead']
        arcade.draw_circle_filled(x, y, TOKEN_RADIUS, color)
        arcade.draw_text(str(token_id), x - 10, y - 10, arcade.color.WHITE, 12)

    def on_mouse_press(self, x, y, button, modifiers):
        center_x = self.width // 2
        center_y = self.height // 2

        for i in range(NUM_PLAYERS):
            token_id = i + 1
            angle = 2 * math.pi * i / NUM_PLAYERS
            token_x = center_x + CIRCLE_RADIUS * math.cos(angle)
            token_y = center_y + CIRCLE_RADIUS * math.sin(angle)

            if arcade.get_distance(x, y, token_x, token_y) < TOKEN_RADIUS:
                if self.assigning_red_info:
                    # Если мы на этапе выбора информации для красных эмпатов
                    if self.roles[token_id] in ["red", "demon"]:
                        self.cycle_red_info(token_id)
                elif self.night_phase:
                    # Ночная фаза — модератор убивает жетон ночью
                    if self.tokens[token_id]['alive']:
                        self.send_message({'action': 'night_kill', 'token_id': token_id})
                        self.tokens[token_id]['alive'] = False
                        self.on_draw()  # Обновляем отображение
                        self.night_phase = False
                else:
                    # Иначе меняем роль игрока
                    self.cycle_role(token_id)

                break  # Останавливаем цикл при обнаружении нажатия

    def cycle_role(self, player_id):
        """Циклически меняем роль игрока."""
        current_role = self.roles[player_id]
        next_role_index = (ROLE_SEQUENCE.index(current_role) + 1) % len(ROLE_SEQUENCE)
        next_role = ROLE_SEQUENCE[next_role_index]
        self.roles[player_id] = next_role
        self.token_colors[player_id] = ROLE_COLORS[next_role]
        self.update_blue_neighbors()
        self.on_draw()

    def cycle_red_info(self, player_id):
        """Циклически меняем информацию для красного эмпата."""
        current_info = self.red_empath_info.get(player_id, 0)
        next_info_index = (RED_EMPATH_INFO_SEQUENCE.index(current_info) + 1) % len(RED_EMPATH_INFO_SEQUENCE)
        next_info = RED_EMPATH_INFO_SEQUENCE[next_info_index]
        self.red_empath_info[player_id] = next_info
        self.on_draw()

    def update_blue_neighbors(self):
        """Обновляем информацию для синих эмпатов."""
        for i in range(1, NUM_PLAYERS + 1):
            if self.roles[i] == "blue":
                left_neighbor = (i - 2) % NUM_PLAYERS + 1
                right_neighbor = i % NUM_PLAYERS + 1
                neighbors = [self.roles[left_neighbor], self.roles[right_neighbor]]
                self.blue_player_info[i] = neighbors.count("red") + neighbors.count("demon")

    def on_submit_roles(self, event):
        """Переход к этапу выбора информации для красных эмпатов."""
        self.assigning_red_info = True
        self.manager.remove(self.submit_button_widget)
        self.manager.add(self.submit_red_info_button_widget)

    def on_submit_red_info(self, event):
        """Подтверждение информации для красных эмпатов."""
        self.manager.remove(self.submit_red_info_button_widget)
        self.manager.remove(self.generate_button_widget)
        self.manager.add(self.start_game_button_widget)

    def on_start_game(self, event):
        """Запуск игры с передачей информации о ролях и эмпатах."""
        print(self)
        state = {
            'roles': self.roles,  # Передаем роли игроков (синие, красные, демон)
            'empath_info': self.red_empath_info  # Передаем информацию для красных эмпатов
        }
        print("state", state)
        self.send_message({'action': 'start_game', 'state': state})
        self.message_label.text = "Ждем ход игрока."
        self.manager.remove(self.start_game_button_widget)

    def run(self):
        arcade.run()

    def send_message(self, message):
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps(message)),
                self.loop
            )
            

if __name__ == "__main__":
    client = ModeratorClient()
    client.run()
