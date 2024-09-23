# player_client.py
import asyncio
import websockets
import arcade
import json
import threading
import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
NUM_PLAYERS = 16
CIRCLE_RADIUS = 200
TOKEN_RADIUS = 20

class PlayerClient(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Player Client")
        self.websocket = None
        self.connected = False
        self.player_id = None
        self.tokens = []  # Список жетонов для отображения
        self.empath_info = None
        self.message = "Ожидание начала игры..."
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_asyncio_loop, daemon=True).start()
        self.loop.call_soon_threadsafe(asyncio.ensure_future, self.connect())

        # Устанавливаем скорость обновления окна
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
        except Exception as e:
            print(f"Connection error: {e}")

    async def listen(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.loop.call_soon_threadsafe(self.process_message, data)
        except websockets.ConnectionClosed:
            print("Connection closed")
            
    def process_message(self, data):
        action = data.get('action')
        if action == 'authenticated':
            print("Authenticated as Player.")
        elif action == 'error':
            print(f"Error: {data.get('message')}")
        elif action == 'start_game':
            state = data.get('state')
            self.tokens = state.get('tokens', [])
            self.empath_info = state.get('empath_info', None)  # Получаем информацию об эмпатах
            self.message = "Игра началась."
            print("Received game state, starting game.")
            # Никаких дополнительных вызовов не требуется; окно обновится автоматически
        elif action == 'update_state':
            state = data.get('state')
            self.tokens = state.get('tokens', [])
            self.empath_info = state.get('empath_info', None)  # Обновляем информацию об эмпатах
            print("Received updated game state.")
            # Окно обновится автоматически при следующем кадре

    def on_update(self, delta_time):
        pass  # Если требуется логика обновления, добавьте ее здесь

    def on_draw(self):
        arcade.start_render()
        if self.tokens:
            center_x = self.width // 2
            center_y = self.height // 2
            num_tokens = len(self.tokens)
            for i, token in enumerate(self.tokens):
                angle = 2 * math.pi * i / num_tokens
                token_x = center_x + CIRCLE_RADIUS * math.cos(angle)
                token_y = center_y + CIRCLE_RADIUS * math.sin(angle)
                self.draw_token(token, token_x, token_y)
        else:
            arcade.draw_text(self.message, self.width // 2 - 100, self.height // 2,
                            arcade.color.WHITE, 14)

    def draw_token(self, token, x, y):
        color = arcade.color.GRAY if token['alive'] else arcade.color.DARK_GRAY
        arcade.draw_circle_filled(x, y, TOKEN_RADIUS, color)
        arcade.draw_text(str(token['id']), x - 5, y - 7, arcade.color.WHITE, 10)
        
        # Если эмпат, отображаем информацию о красных соседях
        if self.empath_info and token['id'] in self.empath_info:
            empath_value = self.empath_info[token['id']]
            arcade.draw_text(str(empath_value), x + 25, y - 10, arcade.color.YELLOW, 12)  # Отображаем информацию справа

    def on_mouse_press(self, x, y, button, modifiers):
        if self.tokens:
            center_x = self.width // 2
            center_y = self.height // 2
            num_tokens = len(self.tokens)
            for i, token in enumerate(self.tokens):
                angle = 2 * math.pi * i / num_tokens
                token_x = center_x + CIRCLE_RADIUS * math.cos(angle)
                token_y = center_y + CIRCLE_RADIUS * math.sin(angle)
                if arcade.get_distance(x, y, token_x, token_y) < TOKEN_RADIUS:
                    if token['alive']:
                        # Отправляем сообщение на сервер о казни жетона
                        self.send_message({'action': 'kill_token', 'token_id': token['id']})
                    break

    def send_message(self, message):
        if self.connected and self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps(message)),
                self.loop
            )

    def run(self):
        arcade.run()

if __name__ == "__main__":
    client = PlayerClient()
    client.run()
