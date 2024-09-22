import arcade
import random
import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Кровь на Часовой Башне: Эмпаты"

NUM_PLAYERS = 16
NUM_REDS = 4  # Количество красных игроков, включая демона

class Player:
    def __init__(self, role, position):
        self.role = role  # 'blue', 'red', 'demon'
        self.position = position
        self.alive = True
        self.red_neighbors_count = 0  # Количество красных соседей
        self.fake_red_neighbors_count = random.randint(0, 2)  # Ложное значение

    def update_neighbors(self, players):
        if self.role == 'blue':
            # Находим ближайшего живого соседа слева
            left_index = self.position
            while True:
                left_index = (left_index - 1) % NUM_PLAYERS
                if players[left_index].alive and left_index != self.position:
                    break
                if left_index == self.position:
                    # Больше нет живых игроков
                    break

            # Находим ближайшего живого соседа справа
            right_index = self.position
            while True:
                right_index = (right_index + 1) % NUM_PLAYERS
                if players[right_index].alive and right_index != self.position:
                    break
                if right_index == self.position:
                    # Больше нет живых игроков
                    break

            neighbors = []
            if left_index != self.position and players[left_index].alive:
                neighbors.append(players[left_index])
            if right_index != self.position and players[right_index].alive:
                neighbors.append(players[right_index])

            self.red_neighbors_count = sum(1 for neighbor in neighbors if neighbor.role in ['red', 'demon'])
        else:
            pass  # Для красных игроков ничего не делаем

    def get_info(self):
        if self.role == 'blue':
            return f"Эмпат говорит: 'У меня {self.red_neighbors_count} красных соседа(ей)!'"
        else:
            return f"Эмпат говорит: 'У меня {self.fake_red_neighbors_count} красных соседа(ей)!'"  # Ложная информация

class BloodOnTheClocktowerGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.players = []
        self.red_positions = []
        self.night_phase = True
        self.demon = None
        self.init_game()

    def init_game(self):
        self.players = []
        self.red_positions = random.sample(range(NUM_PLAYERS), NUM_REDS)
        for i in range(NUM_PLAYERS):
            if i in self.red_positions[:-1]:
                role = 'red'
            elif i == self.red_positions[-1]:
                role = 'demon'
                self.demon = i
            else:
                role = 'blue'

            self.players.append(Player(role, i))

        # Устанавливаем количество красных соседей для эмпатов
        for player in self.players:
            player.update_neighbors(self.players)

    def on_draw(self):
        arcade.start_render()  # Начинаем рисование
        self.draw_table()      # Вызываем метод отрисовки

    def draw_table(self):
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        radius = 200
        for i in range(NUM_PLAYERS):
            angle = math.radians((360 / NUM_PLAYERS) * i)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            if self.players[i].alive:
                color = arcade.color.BLUE if self.players[i].role == 'blue' else arcade.color.RED
                arcade.draw_circle_filled(x, y, 20, color)

                if self.players[i].role == 'demon':
                    arcade.draw_circle_filled(x, y, 10, arcade.color.BLACK)

                # Отображаем количество красных соседей
                if self.players[i].role == 'blue':
                    arcade.draw_text(str(self.players[i].red_neighbors_count), x + 25, y - 10, arcade.color.WHITE, 12)
                else:
                    # Ложная информация для красных игроков
                    arcade.draw_text(str(self.players[i].fake_red_neighbors_count), x + 25, y - 10, arcade.color.WHITE, 12)

            else:
                arcade.draw_circle_filled(x, y, 20, arcade.color.GRAY)

            arcade.draw_text(str(i + 1), x - 10, y - 10, arcade.color.WHITE, 12)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.night_phase:
            # В первую ночь демон не убивает, только казнят
            print("Первый ход: игроки должны казнить.")
            self.select_execution(x, y)
        else:
            # В ночной фазе демон убивает игрока (после первой казни)
            self.demon_kills(x, y)

    def select_execution(self, x, y):
        selected_player = self.get_clicked_player(x, y)
        if selected_player is not None and self.players[selected_player].alive:
            self.players[selected_player].alive = False
            print(f"Днем был казнен игрок {selected_player + 1}")

            # Обновляем информацию у всех синих игроков
            self.update_all_blue_neighbors()

            # Обновляем ложные значения для красных игроков
            self.update_red_fake_info()

            # Проверяем, казнен ли демон
            if selected_player == self.demon:
                print("Демон казнен! Синие игроки победили!")
                arcade.exit()  # Останавливаем игру
            else:
                self.check_game_over()  # Проверяем условия окончания игры
                self.night_phase = False  # Переход в ночную фазу

    def demon_kills(self, x, y):
        killed_player = self.get_clicked_player(x, y)
        if killed_player is not None and self.players[killed_player].alive:
            # Демон не может убить себя
            if killed_player == self.demon:
                print("Демон не может убить себя!")
                return

            self.players[killed_player].alive = False
            print(f"Ночью демон убил игрока {killed_player + 1}")

            # Обновляем информацию у всех синих игроков
            self.update_all_blue_neighbors()

            # Обновляем ложные значения для красных игроков
            self.update_red_fake_info()

            # Проверяем, убит ли демон (на всякий случай)
            if killed_player == self.demon:
                print("Демон убит! Синие игроки победили!")
                arcade.exit()  # Останавливаем игру
            else:
                self.check_game_over()  # Проверяем условия окончания игры
                self.night_phase = True  # Переход в дневную фазу

    def check_game_over(self):
        alive_blues = sum(1 for player in self.players if player.alive and player.role == 'blue')
        alive_reds = sum(1 for player in self.players if player.alive and player.role in ['red', 'demon'])

        # Если остался один синий и демон
        if alive_blues == 1 and alive_reds == 1 and self.players[self.demon].alive:
            print("Остались только один синий игрок и демон. Красные игроки победили!")
            arcade.exit()  # Останавливаем игру

        # Можно добавить дополнительные условия окончания игры, если необходимо

    def update_all_blue_neighbors(self):
        # Обновляем информацию о красных соседях у всех синих игроков
        for player in self.players:
            if player.alive and player.role == 'blue':
                player.update_neighbors(self.players)

    def update_red_fake_info(self):
        # Обновляем ложную информацию для красных игроков
        for player in self.players:
            if player.alive and player.role == 'red':
                player.fake_red_neighbors_count = random.randint(0, 2)

    def get_clicked_player(self, x, y):
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        radius = 200
        for i in range(NUM_PLAYERS):
            angle = (360 / NUM_PLAYERS) * i
            player_x = center_x + radius * math.cos(math.radians(angle))
            player_y = center_y + radius * math.sin(math.radians(angle))
            if arcade.get_distance(x, y, player_x, player_y) < 20:
                return i
        return None

if __name__ == "__main__":
    game = BloodOnTheClocktowerGame()
    arcade.run()
