# player_client.py
import asyncio
import websockets
import arcade
import json
import threading
import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CIRCLE_RADIUS = 200
TOKEN_RADIUS = 20

class PlayerClient(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Player Client")
        self.websocket = None
        self.connected = False
        self.tokens = []  # Список жетонов для отображения
        self.empath_info = {}  # Информация эмпатов, ключи как строки
        self.message = "Ожидание начала игры..."
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_asyncio_loop, daemon=True).start()
        self.loop.call_soon_threadsafe(asyncio.ensure_future, self.connect())

        self.set_update_rate(1/60)

    def start_asyncio_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def connect(self):
        try:
            self.websocket = await websockets.connect('ws://localhost:12345')
            await self.websocket.send(json.dumps({'action': 'authenticate', 'role': 'player'}))
            self.connected = True
            asyncio.ensure_future(self.listen())
            print("Игрок подключен.")
        except Exception as e:
            print(f"Connection error: {e}")

    async def listen(self):
        try:
            async for message in self.websocket:
                print("2222222222222")
                
                data = json.loads(message)
                self.loop.call_soon_threadsafe(self.process_message, data)
        except websockets.ConnectionClosed:
            print("Connection closed")

    def process_message(self, data):
        print(f"Полученные данные: {data}")  # Отладка полученных данных
        action = data.get('action')
        print(f"Получено действие: {action}")

        if action == 'authenticated':
            print("Authenticated as Player.")
        elif action == 'start_game':
            state = data.get('state', {})
            self.tokens = state.get('tokens', [])
            self.empath_info = state.get('empath_info', {})
            self.message = state.get('day_phase', "Игра началась.")  # Получаем фазу дня из состояния
            print("Получено состояние игры.")
            print(f"Tokens: {self.tokens}")
            print(f"Empath Info: {self.empath_info}")
            print(f"Day phase: {self.message}")
        elif action == 'update_state':
            state = data.get('state', {})
            self.tokens = state.get('tokens', [])
            self.empath_info = state.get('empath_info', {})
            print("Обновленное состояние игры.")
            print(f"Tokens: {self.tokens}")
            print(f"Empath Info: {self.empath_info}")


    def on_update(self, delta_time):
        pass

    def on_draw(self):
        arcade.start_render()
        
        if not self.tokens:
            # Если жетонов нет, показываем сообщение ожидания
            arcade.draw_text(self.message, self.width // 2 - 100, self.height // 2, arcade.color.WHITE, 14)
            return

        center_x = self.width // 2
        center_y = self.height // 2
        num_tokens = len(self.tokens)

        # Отрисовка всех жетонов
        for token in self.tokens:
            token_id = token['id']
            alive = token['alive']
            angle = 2 * math.pi * (token_id - 1) / num_tokens
            token_x = center_x + CIRCLE_RADIUS * math.cos(angle)
            token_y = center_y + CIRCLE_RADIUS * math.sin(angle)
            self.draw_token(token, token_x, token_y)

            # Рисуем информацию для эмпатов для всех игроков
            empath_value = self.empath_info.get(str(token_id), 0)
            arcade.draw_text(str(empath_value), token_x + 25, token_y - 10, arcade.color.YELLOW, 12)

        # Отображаем сообщение для текущей фазы игры
        arcade.draw_text(self.message, 10, 10, arcade.color.WHITE, 14)

    def draw_token(self, token, x, y):
        # Цвет жетона: светло-серый для живых, темно-серый для мертвых
        color = arcade.color.LIGHT_GRAY if token['alive'] else arcade.color.DARK_GRAY
        arcade.draw_circle_filled(x, y, TOKEN_RADIUS, color)
        arcade.draw_text(str(token['id']), x - 5, y - 7, arcade.color.WHITE, 10)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.tokens:
            center_x = self.width // 2
            center_y = self.height // 2
            num_tokens = len(self.tokens)
            for token in self.tokens:
                token_id = token['id']
                angle = 2 * math.pi * (token_id - 1) / num_tokens
                token_x = center_x + CIRCLE_RADIUS * math.cos(angle)
                token_y = center_y + CIRCLE_RADIUS * math.sin(angle)
                distance = math.hypot(x - token_x, y - token_y)
                if distance < TOKEN_RADIUS:
                    if token['alive']:
                        self.send_message({'action': 'kill_token', 'token_id': token_id})
                    break

    def send_message(self, message):
        if self.connected and self.websocket:
            print(f"Отправка сообщения: {message}")
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps(message)),
                self.loop
            )

    def run(self):
        arcade.run()

if __name__ == "__main__":
    client = PlayerClient()
    client.run()
