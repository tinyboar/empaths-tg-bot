import asyncio
import websockets
import arcade
import arcade.gui
import json
import queue
import threading

NUM_PLAYERS = 16
NUM_REDS = 4


class ModeratorClient(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Moderator Client")
        self.websocket = None
        self.connected = False

        # Создаем менеджер GUI
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Контейнер для виджетов
        self.v_box = arcade.gui.UIBoxLayout()

        # Сообщение для отображения инструкций
        self.message_label = arcade.gui.UILabel(text="Ожидание подключения к серверу...", width=600, height=40, text_color=arcade.color.WHITE)
        self.v_box.add(self.message_label.with_space_around(bottom=20))

        # Добавляем контейнер на экран
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box
            )
        )

        # Очередь для сообщений из сетевого потока
        self.message_queue = queue.Queue()

        # Инициализируем цикл событий asyncio и запускаем его в отдельном потоке
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_asyncio_loop, daemon=True).start()

        # Запускаем асинхронное подключение
        self.loop.call_soon_threadsafe(asyncio.ensure_future, self.connect())

    def start_asyncio_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def connect(self):
        try:
            self.websocket = await websockets.connect('ws://localhost:12345')
            await self.websocket.send(json.dumps({'action': 'authenticate', 'role': 'moderator'}))
            self.connected = True
            # Отправляем сообщение в главный поток для обновления GUI
            self.message_queue.put({'action': 'update_message', 'text': "Подключено к серверу. Ожидание начала игры..."})
            # Запускаем прослушивание сообщений от сервера
            self.loop.call_soon_threadsafe(asyncio.ensure_future, self.listen())
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            self.message_queue.put({'action': 'update_message', 'text': f"Ошибка подключения: {e}"})

    async def listen(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.message_queue.put(data)
        except websockets.ConnectionClosed:
            print("Соединение закрыто")
            self.message_queue.put({'action': 'update_message', 'text': "Соединение с сервером потеряно"})

    def handle_message(self, data):
        action = data.get('action')
        if action == 'update_message':
            self.message_label.text = data.get('text', '')
        elif action == 'authenticated':
            print("Аутентификация успешна.")
            self.message_label.text = "Аутентификация успешна. Нажмите 'Начать игру'."
            # Добавляем кнопку для начала игры
            start_button = arcade.gui.UIFlatButton(text="Начать игру", width=200)
            start_button.on_click = self.on_start_game
            self.v_box.add(start_button.with_space_around(top=20))
        elif action == 'error':
            print(f"Ошибка: {data.get('message')}")
            self.message_label.text = f"Ошибка: {data.get('message')}"
        # Обработка других действий и обновлений игры
        elif action == 'update':
            # Обновление состояния игры
            self.update_game_state(data)
        elif action == 'request_role_assignment':
            # Сервер запрашивает назначение ролей
            self.assign_roles()
        # Добавьте другие необходимые обработки сообщений

    def on_start_game(self, event):
        # Отправляем на сервер команду начать игру
        if self.connected:
            self.loop.call_soon_threadsafe(asyncio.ensure_future, self.send_action('start_game', {}))
            self.message_label.text = "Игра начата. Назначьте роли игрокам."
        else:
            self.message_label.text = "Ошибка: Нет подключения к серверу."

    async def send_action(self, action, data):
        message = {'action': action}
        message.update(data)
        await self.websocket.send(json.dumps(message))

    def update_game_state(self, data):
        # Обновите состояние игры на основе данных от сервера
        pass  # Здесь вы можете обновлять интерфейс в зависимости от состояния игры

    def assign_roles(self):
        # Очищаем предыдущие виджеты
        self.v_box.clear()
        self.message_label.text = "Назначьте роли игрокам (b - синий, r - красный, d - демон):"
        self.v_box.add(self.message_label.with_space_around(bottom=20))

        self.role_inputs = []
        for i in range(1, NUM_PLAYERS + 1):
            label = arcade.gui.UILabel(text=f"Игрок {i}:", width=100)
            input_box = arcade.gui.UIInputText(text="", width=50)
            self.role_inputs.append((i, input_box))
            h_box = arcade.gui.UIBoxLayout(vertical=False)
            h_box.add(label)
            h_box.add(input_box)
            self.v_box.add(h_box.with_space_around(bottom=5))

        # Кнопка для подтверждения ролей
        submit_button = arcade.gui.UIFlatButton(text="Подтвердить роли", width=200)
        submit_button.on_click = self.on_submit_roles
        self.v_box.add(submit_button.with_space_around(top=20))

    def on_submit_roles(self, event):
        roles = {}
        num_reds_assigned = 0
        demon_assigned = False
        for player_id, input_box in self.role_inputs:
            role = input_box.text.strip().lower()
            if role == 'b':
                roles[str(player_id)] = 'blue'
            elif role == 'r':
                if num_reds_assigned < NUM_REDS - 1:
                    roles[str(player_id)] = 'red'
                    num_reds_assigned += 1
                else:
                    self.message_label.text = f"Ошибка: Превышено количество красных эмпатов (максимум {NUM_REDS - 1})."
                    return
            elif role == 'd':
                if not demon_assigned:
                    roles[str(player_id)] = 'demon'
                    demon_assigned = True
                else:
                    self.message_label.text = "Ошибка: Демон уже назначен."
                    return
            else:
                self.message_label.text = f"Ошибка: Некорректная роль для игрока {player_id}."
                return

        # Проверяем, что демон назначен
        if not demon_assigned:
            self.message_label.text = "Ошибка: Нужно назначить демона."
            return

        # Отправляем роли на сервер
        if self.connected:
            self.loop.call_soon_threadsafe(asyncio.ensure_future, self.send_action('assign_roles', {'roles': roles}))
            self.message_label.text = "Роли назначены. Ожидайте дальнейших инструкций."
            # Очистить интерфейс или перейти к следующему этапу
        else:
            self.message_label.text = "Ошибка: Нет подключения к серверу."

    def on_draw(self):
        arcade.start_render()
        # Отрисовываем интерфейс модератора
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        # Передаем события в менеджер GUI
        self.manager.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        self.manager.on_mouse_release(x, y, button, modifiers)

    def on_update(self, delta_time):
        # Обновляем менеджер GUI
        self.manager.on_update(delta_time)

        # Обрабатываем сообщения из очереди
        while not self.message_queue.empty():
            data = self.message_queue.get()
            self.handle_message(data)

    def run(self):
        arcade.run()

if __name__ == "__main__":
    client = ModeratorClient()
    client.run()
