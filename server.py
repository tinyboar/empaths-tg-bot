# server.py
import asyncio
import websockets
import json

NUM_PLAYERS = 16
NUM_REDS = 4

class Player:
    def __init__(self, websocket, player_id):
        self.websocket = websocket
        self.player_id = player_id
        self.role = None  # 'blue', 'red', 'demon'
        self.alive = True
        self.red_neighbors_count = 0
        self.fake_red_neighbors_count = 0

class GameState:
    def __init__(self):
        self.players = {}  # player_id: Player instance
        self.moderator = None
        self.night_phase = False
        self.game_over = False
        # Additional game state variables

    # Include all necessary methods from your GameState class
    # For example, methods to assign roles, update game state, check for game over, etc.

class GameServer:
    def __init__(self):
        self.game_state = GameState()

    async def handler(self, websocket, path):
        # Handle new client connections
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.process_message(websocket, data)
        except websockets.ConnectionClosed:
            # Handle disconnection
            pass

    async def process_message(self, websocket, data):
        action = data.get('action')
        if action == 'authenticate':
            role = data.get('role')
            if role == 'moderator':
                if self.game_state.moderator is None:
                    self.game_state.moderator = websocket
                    await websocket.send(json.dumps({'action': 'authenticated', 'role': 'moderator'}))
                    print("Модератор подключен.")
                else:
                    await websocket.send(json.dumps({'action': 'error', 'message': 'Модератор уже подключен.'}))
            elif role == 'player':
                player_id = len(self.game_state.players) + 1
                player = Player(websocket, player_id)
                self.game_state.players[player_id] = player
                await websocket.send(json.dumps({'action': 'authenticated', 'role': 'player', 'player_id': player_id}))
                print(f"Игрок {player_id} подключен.")
        elif action == 'start_game':
            # Проверяем, что сообщение пришло от модератора
            if websocket == self.game_state.moderator:
                # Отправляем модератору запрос на назначение ролей
                await websocket.send(json.dumps({'action': 'request_role_assignment'}))
                print("Игра начата модератором. Запрашиваем назначение ролей.")
            else:
                await websocket.send(json.dumps({'action': 'error', 'message': 'Только модератор может начинать игру.'}))
        elif action == 'assign_roles':
            # Обработка назначения ролей
            roles = data.get('roles')
            if roles:
                # Применяем роли к игрокам
                for player_id_str, role in roles.items():
                    player_id = int(player_id_str)
                    if player_id in self.game_state.players:
                        self.game_state.players[player_id].role = role
                print("Роли назначены игрокам.")
                # Отправляем обновление всем игрокам
                await self.send_game_state()
            else:
                await websocket.send(json.dumps({'action': 'error', 'message': 'Нет данных о ролях.'}))
        # Добавьте обработку других действий


    async def send_game_state(self):
        # Отправляем обновление состояния игры всем подключенным клиентам
        state = {
            'action': 'update',
            # Добавьте необходимые данные состояния игры
        }
        # Отправляем модератору
        if self.game_state.moderator:
            await self.game_state.moderator.send(json.dumps(state))
        # Отправляем игрокам
        for player in self.game_state.players.values():
            await player.websocket.send(json.dumps(state))

    def start(self):
        start_server = websockets.serve(self.handler, 'localhost', 12345)
        asyncio.get_event_loop().run_until_complete(start_server)
        print("Server started on ws://localhost:12345")
        asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    server = GameServer()
    server.start()
