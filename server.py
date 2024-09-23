# server.py
import asyncio
import websockets
import json
import random

NUM_PLAYERS = 16

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
        self.initialize_players()  # Инициализируем виртуальных игроков

    def initialize_players(self):
        # Создаем объекты для всех 16 виртуальных игроков
        for player_id in range(1, NUM_PLAYERS + 1):
            player = Player(None, player_id)  # websocket=None для виртуальных игроков
            self.players[player_id] = player


    def get_game_state_for_player(self, player_id):
        # Возвращаем информацию о состоянии игры для конкретного игрока
        player = self.players[player_id]
        state = {
            'player_id': player_id,
            'tokens': [{'id': p_id} for p_id in self.players],
        }
        # Добавляем эмпатическую информацию
        if player.role == 'blue':
            state['empath_info'] = player.red_neighbors_count
        elif player.role in ['red', 'demon']:
            state['empath_info'] = player.fake_red_neighbors_count
        else:
            state['empath_info'] = None
        return state

class GameServer:
    def __init__(self):
        self.game_state = GameState()

    async def handler(self, websocket, path):
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.process_message(websocket, data)
        except websockets.ConnectionClosed:
            # Обработка отключения
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
            elif role == 'player':  # Исправленный блок
                if not hasattr(self, 'player_websocket'):
                    self.player_websocket = websocket
                    await websocket.send(json.dumps({'action': 'authenticated', 'role': 'player'}))
                    print("Игрок подключен.")
                else:
                    await websocket.send(json.dumps({'action': 'error', 'message': 'Игрок уже подключен.'}))
        elif action == 'start_game':
            if websocket == self.game_state.moderator:
                await self.assign_roles()
                await self.send_game_state_to_player()
                print("Игра начата модератором. Отправляем состояние игры игроку.")
            else:
                await websocket.send(json.dumps({'action': 'error', 'message': 'Только модератор может начинать игру.'}))
        elif action == 'kill_token':
                token_id = data.get('token_id')
                if token_id in self.game_state.players and self.game_state.players[token_id].alive:
                    self.game_state.players[token_id].alive = False
                    print(f"Игрок казнил жетон {token_id}")
                    # Пересчитываем информацию для эмпатов
                    self.calculate_empath_info()
                    # Отправляем обновленное состояние игры игроку
                    await self.send_game_state_to_player()
                    # Уведомляем модератора о казни жетона
                    await self.game_state.moderator.send(json.dumps({'action': 'token_killed', 'token_id': token_id}))
        elif action == 'night_kill':
            token_id = data.get('token_id')
            if websocket == self.game_state.moderator:
                if token_id in self.game_state.players and self.game_state.players[token_id].alive:
                    self.game_state.players[token_id].alive = False
                    print(f"Модератор убил ночью жетон {token_id}")
                    # Отправляем обновленное состояние игры игроку
                    await self.send_game_state_to_player()
                else:
                    await websocket.send(json.dumps({'action': 'error', 'message': 'Невозможно убить выбранный жетон.'}))
            else:
                await websocket.send(json.dumps({'action': 'error', 'message': 'Только модератор может убивать ночью.'}))


    async def assign_roles(self):
        player_ids = list(self.game_state.players.keys())
        num_reds = 3
        num_demons = 1

        red_players = random.sample(player_ids, num_reds)
        for player_id in red_players:
            self.game_state.players[player_id].role = 'red'
        remaining_players = [pid for pid in player_ids if pid not in red_players]
        demon_player = random.choice(remaining_players)
        self.game_state.players[demon_player].role = 'demon'
        remaining_players.remove(demon_player)
        for player_id in remaining_players:
            self.game_state.players[player_id].role = 'blue'

        # Рассчитываем информацию для эмпатов
        self.calculate_empath_info()


    def calculate_empath_info(self):
        """Рассчитываем количество красных соседей для синих эмпатов."""
        for player_id, player in self.game_state.players.items():
            if player.role == 'blue':
                # Рассчитываем соседей для каждого синего эмпата
                left_neighbor_id = (player_id - 2) % NUM_PLAYERS + 1
                right_neighbor_id = player_id % NUM_PLAYERS + 1
                neighbors = [
                    self.game_state.players[left_neighbor_id].role,
                    self.game_state.players[right_neighbor_id].role
                ]
                # Считаем количество красных и демонов среди соседей
                player.red_neighbors_count = neighbors.count('red') + neighbors.count('demon')


    async def send_game_state_to_player(self):
        state = {
            'tokens': [
                {
                    'id': player.player_id,
                    'alive': player.alive
                }
                for player in self.game_state.players.values()
            ],
            'empath_info': {
                player.player_id: player.red_neighbors_count
                for player in self.game_state.players.values() if player.role == 'blue'
            }
        }
        await self.player_websocket.send(json.dumps({'action': 'start_game', 'state': state}))


    async def broadcast_start_game(self):
        # Рассылка сообщения о начале игры всем игрокам
        for player_id, player in self.game_state.players.items():
            state = self.game_state.get_game_state_for_player(player_id)
            message = {'action': 'start_game', 'state': state}
            await player.websocket.send(json.dumps(message))
            print(f"Отправлено сообщение start_game игроку {player_id}")

    def start(self):
        start_server = websockets.serve(self.handler, 'localhost', 12345)
        asyncio.get_event_loop().run_until_complete(start_server)
        print("Server started on ws://localhost:12345")
        asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    server = GameServer()
    server.start()
