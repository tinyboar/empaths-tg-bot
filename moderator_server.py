import asyncio
import websockets
import arcade
import arcade.gui
import json
import threading
import math
import random
import queue

NUM_PLAYERS = 16
CIRCLE_RADIUS = 200  # Радиус круга для размещения игроков
TOKEN_RADIUS = 20  # Радиус жетона

ROLE_COLORS = {
    "blue": arcade.color.BLUE,
    "red": arcade.color.RED,
    "demon": arcade.color.BLACK
}

ROLE_SEQUENCE = ["blue", "red", "demon"]  # Порядок изменения ролей
RED_EMPATH_INFO_SEQUENCE = [0, 1, 2]  # Возможные значения для информации красных эмпатов


class Player:
    def __init__(self, websocket):
        self.websocket = websocket
        self.role = "blue"  # По умолчанию 'blue'
        self.alive = True
        self.red_neighbors_count = 0
        self.fake_red_neighbors_count = 0


class GameState:
    def __init__(self):
        self.players = {}  # Хранит всех подключенных игроков
        self.initialize_players()

    def initialize_players(self):
        # Создаем объекты для всех 16 виртуальных игроков
        for player_id in range(1, NUM_PLAYERS + 1):
            player = Player(None)  # websocket=None для виртуальных игроков
            self.players[player_id] = player


class ModeratorServer(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Moderator & Server")
        self.websocket = None
        self.connected = False
        self.game_state = GameState()

        arcade.set_background_color(arcade.color.DARK_SLATE_BLUE)
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Сообщение для отображения информации
        self.message_label = arcade.gui.UILabel(
            text="Ожидание подключения игрока...",
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

        # Кнопка для генерации раскладки
        self.generate_button = arcade.gui.UIFlatButton(text="Сгенерировать раскладку", width=200)
        self.generate_button.on_click = self.on_generate_roles
        self.generate_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="bottom", align_y=50, child=self.generate_button)
        self.manager.add(self.generate_button_widget)

        # Кнопка для подтверждения ролей
        self.submit_button = arcade.gui.UIFlatButton(text="Подтвердить роли", width=200)
        self.submit_button.on_click = self.on_submit_roles
        self.submit_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="bottom", align_y=0, child=self.submit_button)
        self.manager.add(self.submit_button_widget)

        # Кнопка для подтверждения информации красных эмпатов
        self.submit_red_info_button = arcade.gui.UIFlatButton(text="Подтвердить информацию красных", width=200)
        self.submit_red_info_button.on_click = self.on_submit_red_info
        self.submit_red_info_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="bottom", align_y=0, child=self.submit_red_info_button)

        # Кнопка для начала раскладки заново
        self.reset_layout_button = arcade.gui.UIFlatButton(text="Начать раскладку заново", width=200)
        self.reset_layout_button.on_click = self.on_reset_layout
        self.reset_layout_button_widget = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="top", align_y=-50, child=self.reset_layout_button)
        self.manager.add(self.reset_layout_button_widget)
        self.manager.remove(self.reset_layout_button_widget)  # Скрываем кнопку при старте

        # Кнопка для начала игры
        self.start_game_button = arcade.gui.UIFlatButton(
            text="Начать игру", width=200
        )
        self.start_game_button.on_click = self.on_start_game
        self.start_game_button = arcade.gui.UIAnchorWidget(
            anchor_x="center_x", anchor_y="center", child=self.start_game_button)

        self.message_queue = queue.Queue()

        self.roles = {i: "blue" for i in range(1, NUM_PLAYERS + 1)}
        self.token_colors = {i: ROLE_COLORS["blue"] for i in range(1, NUM_PLAYERS + 1)}
        self.blue_player_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}
        self.red_empath_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}

        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_asyncio_loop, daemon=True).start()
        self.loop.call_soon_threadsafe(asyncio.ensure_future, self.start_websocket_server())

        # Флаг для разрешения кликов по жетонам
        self.roles_confirmed = False

    def start_asyncio_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def start_websocket_server(self):
        server = await websockets.serve(self.websocket_handler, 'localhost', 12345)
        print("WebSocket сервер запущен на ws://localhost:12345")
        await server.wait_closed()

    async def websocket_handler(self, websocket, path):
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.process_message(websocket, data)
        except websockets.ConnectionClosed:
            print("Соединение с клиентом потеряно")

    async def process_message(self, websocket, data):
        action = data.get('action')
        print(action)

        if action == 'authenticate':
            role = data.get('role')
            print(f"Роль: {role}")
            
            if role == 'moderator':
                print(f"Модератор успешно подключен.")
            
            elif role == 'player':
                player_id = len(self.connected_players) + 1
                self.connected_players[player_id] = websocket  # Сохраняем WebSocket игрока
                self.game_state.players[player_id] = Player(websocket)
                await websocket.send(json.dumps({'action': 'authenticated', 'role': 'player'}))
                print(f"Игрок {player_id} подключен.")

        elif action == 'submit_empath_info':
            empath_info = data.get('empath_info', {})
            for player_id, info in empath_info.items():
                if int(player_id) in self.game_state.players:
                    self.game_state.players[int(player_id)].red_neighbors_count = info
            print(f"Информация по эмпатам обновлена модератором: {empath_info}")
            self.manager.add(self.start_game_button)
            self.message_label.text = "Информация по эмпатам подтверждена. Нажмите 'Начать игру'."
            self.on_draw()

        elif action == 'start_game':
            print("0000000000000000")
            await self.assign_roles()
            await self.send_game_state_to_all_players()
            print("Игра начата модератором.")


    async def assign_roles(self):
        player_ids = list(self.game_state.players.keys())
        num_reds = 3
        num_demons = 1

        red_players = random.sample(player_ids, num_reds)
        for player_id in red_players:
            self.game_state.players[player_id].role = 'red'
            self.token_colors[player_id] = ROLE_COLORS["red"]
        remaining_players = [pid for pid in player_ids if pid not in red_players]
        demon_player = random.choice(remaining_players)
        self.game_state.players[demon_player].role = 'demon'
        self.token_colors[demon_player] = ROLE_COLORS["demon"]
        remaining_players.remove(demon_player)
        for player_id in remaining_players:
            self.game_state.players[player_id].role = 'blue'
            self.token_colors[player_id] = ROLE_COLORS["blue"]

    async def send_game_state_to_all_players(self):
        """Отправка состояния игры всем игрокам через их WebSocket"""
        state = {
            'tokens': [
                {
                    'id': player_id,
                    'alive': player.alive,
                    'role': player.role
                }
                for player_id, player in self.game_state.players.items()
            ],
            'empath_info': {
                str(player_id): player.red_neighbors_count  # Преобразуем ключи в строки для совместимости с JSON
                for player_id, player in self.game_state.players.items()
            },
            'day_phase': "1 день, ждем что игрок выберет кого казнить"
        }

        print(f"Отправляемое состояние игры: {json.dumps(state)}")
        for player_id, websocket in self.connected_players.items():
            await websocket.send(json.dumps({'action': 'start_game', 'state': state}))
            print(f"Сообщение 'start_game' отправлено для игрока {player_id}")
            
    def on_generate_roles(self, event):
        """Генерация ролей и эмпат информации"""
        player_ids = list(range(1, NUM_PLAYERS + 1))
        red_players = random.sample(player_ids, 3)
        demon_player = random.choice([p for p in player_ids if p not in red_players])

        # Назначаем роли
        for pid in player_ids:
            if pid in red_players:
                self.roles[pid] = "red"
                self.token_colors[pid] = ROLE_COLORS["red"]
            elif pid == demon_player:
                self.roles[pid] = "demon"
                self.token_colors[pid] = ROLE_COLORS["demon"]
            else:
                self.roles[pid] = "blue"
                self.token_colors[pid] = ROLE_COLORS["blue"]

        self.update_blue_neighbors()
        self.message_label.text = "Роли сгенерированы. Теперь нажмите 'Подтвердить роли'."

    def on_submit_roles(self, event):
        """Проверка ролей перед началом игры"""
        red_count = sum(1 for role in self.roles.values() if role == "red")
        demon_count = sum(1 for role in self.roles.values() if role == "demon")

        if red_count < 3 or demon_count < 1:
            self.message_label.text = "Ошибка: Должно быть хотя бы 3 красных и 1 демон."
            return

        self.message_label.text = "Роли подтверждены."

        # Удаляем кнопку "Подтвердить роли"
        self.manager.remove(self.submit_button_widget)

        # Добавляем кнопку "Подтвердить информацию красных"
        self.manager.add(self.submit_red_info_button_widget)

        # Устанавливаем флаг, разрешающий клики по жетонам для изменения информации эмпатов
        self.roles_confirmed = True

    def update_blue_neighbors(self):
        """Обновляем информацию для синих эмпатов"""
        for i in range(1, NUM_PLAYERS + 1):
            if self.roles[i] == "blue":
                left_neighbor = (i - 2) % NUM_PLAYERS + 1
                right_neighbor = i % NUM_PLAYERS + 1
                neighbors = [self.roles[left_neighbor], self.roles[right_neighbor]]
                self.blue_player_info[i] = neighbors.count("red") + neighbors.count("demon")

    def on_submit_red_info(self, event):
        """Обработка и отправка информации эмпатов"""
        print("on_submit_red_info вызван")  # Проверка
        
        # Проверяем, что у всех красных и демона назначена информация
        for pid in range(1, NUM_PLAYERS + 1):
            if self.roles[pid] in ["red", "demon"]:
                if self.red_empath_info[pid] not in RED_EMPATH_INFO_SEQUENCE:
                    self.message_label.text = f"Ошибка: У игрока {pid} не назначена информация."
                    return

        empath_data = {
            pid: self.red_empath_info[pid]
            for pid in range(1, NUM_PLAYERS + 1)
            if self.roles[pid] in ["red", "demon"]
        }

        print(f"Информация по эмпатам: {empath_data}")
        
        # Отправляем данные игрокам
        self.send_message({'action': 'submit_empath_info', 'empath_info': empath_data})

        # Удаляем кнопки "Подтвердить информацию красных" и "Сгенерировать раскладку"
        self.manager.remove(self.submit_red_info_button_widget)
        self.manager.remove(self.generate_button_widget)

        # Добавляем кнопку "Начать игру"
        self.manager.add(self.start_game_button)
        self.message_label.text = "Информация по эмпатам подтверждена. Нажмите 'Начать игру'."
        self.on_draw()  # Обновляем интерфейс


    def on_reset_layout(self, event):
        # Удаляем кнопку "Начать раскладку заново"
        self.manager.remove(self.reset_layout_button_widget)
        # Удаляем кнопку "Начать игру"
        self.manager.remove(self.start_game_button)

        # Добавляем кнопки "Сгенерировать раскладку" и "Подтвердить роли"
        self.manager.add(self.generate_button_widget)
        self.manager.add(self.submit_button_widget)

        # Сбрасываем роли и цвета
        self.roles = {i: "blue" for i in range(1, NUM_PLAYERS + 1)}
        self.token_colors = {i: ROLE_COLORS["blue"] for i in range(1, NUM_PLAYERS + 1)}
        self.blue_player_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}
        self.red_empath_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}

        self.update_blue_neighbors()
        self.message_label.text = "Раскладка сброшена. Сгенерируйте новую раскладку."

        # Сбрасываем флаг кликов
        self.roles_confirmed = False
        

    def on_draw(self):
        """Отрисовываем жетоны игроков на круге и отображаем информацию об эмпатах"""
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
                info_text = f"{self.red_empath_info[token_id]}"
                arcade.draw_text(info_text, token_x + 40, token_y - 10, arcade.color.YELLOW, 14)

    def draw_token(self, token_id, x, y):
        token = self.game_state.players[token_id]
        color = self.token_colors[token_id] if token.alive else arcade.color.DARK_GRAY
        arcade.draw_circle_filled(x, y, TOKEN_RADIUS, color)
        arcade.draw_text(str(token_id), x - 5, y - 7, arcade.color.WHITE, 10)

    def on_mouse_press(self, x, y, button, modifiers):
        """Обрабатываем клик мыши по жетонам"""
        center_x = self.width // 2
        center_y = self.height // 2

        for i in range(NUM_PLAYERS):
            token_id = i + 1
            token = self.game_state.players[token_id]
            angle = 2 * math.pi * i / NUM_PLAYERS
            token_x = center_x + CIRCLE_RADIUS * math.cos(angle)
            token_y = center_y + CIRCLE_RADIUS * math.sin(angle)

            distance = math.hypot(x - token_x, y - token_y)
            if distance < TOKEN_RADIUS:
                if not self.roles_confirmed:
                    # Меняем роль игрока
                    self.cycle_role(token_id)
                else:
                    # Меняем информацию эмпата только для красных и демона
                    if self.roles[token_id] in ["red", "demon"]:
                        self.cycle_red_empath_info(token_id)
                break  # Предполагаем, что клик может быть только по одному жетону

    def cycle_role(self, player_id):
        """Циклически меняем роль игрока при каждом клике."""
        current_role = self.roles[player_id]
        next_role_index = (ROLE_SEQUENCE.index(current_role) + 1) % len(ROLE_SEQUENCE)
        next_role = ROLE_SEQUENCE[next_role_index]

        self.roles[player_id] = next_role
        self.token_colors[player_id] = ROLE_COLORS[next_role]
        role_name = next_role.capitalize()
        self.message_label.text = f"Игрок {player_id}: {role_name}"

        # Обновляем информацию для синих эмпатов
        self.update_blue_neighbors()
        self.on_draw()

    def cycle_red_empath_info(self, player_id):
        """Циклически меняем информацию для красного эмпата или демона при каждом клике."""
        current_info = self.red_empath_info[player_id]
        next_info_index = (RED_EMPATH_INFO_SEQUENCE.index(current_info) + 1) % len(RED_EMPATH_INFO_SEQUENCE)
        next_info = RED_EMPATH_INFO_SEQUENCE[next_info_index]
        self.red_empath_info[player_id] = next_info

        # Обновляем текст сообщения для модератора
        self.message_label.text = f"Игрок {player_id}: Информация {next_info}"

        # Обновляем отображение жетонов
        self.on_draw()

    def on_reset_layout(self, event):
        # Удаляем кнопку "Начать раскладку заново"
        self.manager.remove(self.reset_layout_button_widget)
        # Удаляем кнопку "Начать игру"
        self.manager.remove(self.start_game_button)

        # Добавляем кнопки "Сгенерировать раскладку" и "Подтвердить роли"
        self.manager.add(self.generate_button_widget)
        self.manager.add(self.submit_button_widget)

        # Сбрасываем роли и цвета
        self.roles = {i: "blue" for i in range(1, NUM_PLAYERS + 1)}
        self.token_colors = {i: ROLE_COLORS["blue"] for i in range(1, NUM_PLAYERS + 1)}
        self.blue_player_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}
        self.red_empath_info = {i: 0 for i in range(1, NUM_PLAYERS + 1)}

        self.update_blue_neighbors()
        self.message_label.text = "Раскладка сброшена. Сгенерируйте новую раскладку."

        # Сбрасываем флаг кликов
        self.roles_confirmed = False

    def on_start_game(self, event):
        """Отправляем сигнал для старта игры"""
        self.message_label.text = "1 день, ждем что игрок выберет кого казнить."
        print("11111111111111111")

        # Отправляем сигнал для начала игры напрямую через WebSocket
        message = {'action': 'start_game'}
        self.send_message(message)

        self.manager.remove(self.reset_layout_button_widget)
        self.manager.remove(self.start_game_button)

        self.manager._do_layout()
        print("Интерфейс обновлен")

        # Обновляем интерфейс на экране
        self.on_draw()

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

    def send_message(self, message):
        print(f"Попытка отправки сообщения: {message}")
        print(f"WebSocket: {self.websocket}")
        
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps(message)),
                self.loop
            )
            print(f"Сообщение отправлено: {message}")
        else:
            print("WebSocket не подключен.")



if __name__ == "__main__":
    window = ModeratorServer()
    window.run()
