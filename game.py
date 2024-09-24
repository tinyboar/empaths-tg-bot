# game.py
import random

NUM_PLAYERS = 14

class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.role = "blue"
        self.alive = True
        self.red_neighbors_count = 0
        self.fake_red_neighbors_count = 0

class GameState:
    def __init__(self):
        self.moderator = None
        self.players = {}  # Хранение данных игроков
    
    def set_players_count(self, count):
        """Установка количества игроков."""
        self.players = {i: {'role': None, 'alive': True} for i in range(1, count + 1)}

    def assign_roles(self, num_players, num_red):
        """Распределение ролей."""
        player_ids = list(self.players.keys())
        
        # Назначаем "красных"
        red_players = random.sample(player_ids, num_red)
        for pid in red_players:
            self.players[pid]['role'] = 'red'
            player_ids.remove(pid)
        
        # Назначаем одного демона
        demon_player = random.choice(player_ids)
        self.players[demon_player]['role'] = 'demon'
        player_ids.remove(demon_player)
        
        # Оставшиеся игроки - синие эмпаты
        for pid in player_ids:
            self.players[pid]['role'] = 'blue'
    
    def get_game_state(self):
        """Возвращает текущее состояние игры."""
        return {
            'players': self.players
        }

