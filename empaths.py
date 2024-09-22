import arcade
import random
import math

SCREEN_WIDTH = 1600  # Увеличиваем ширину окна для двух областей
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Кровь на Часовой Башне: Эмпаты"

NUM_PLAYERS = 16
NUM_REDS = 4  # Количество красных игроков, включая демона

# Класс для хранения состояния игры
class GameState:
    def __init__(self):
        self.players = []
        self.night_phase = False  # Начинаем с дневной фазы
        self.demon = None
        self.game_over = False
        self.pending_night_kill = None  # Для хранения игрока, убитого ночью, но еще не показанного игроку
        self.init_game()

    def init_game(self):
        self.players = []
        print("Ведущий, вы хотите случайную рассадку игроков? (y/n)")
        random_seating = input().strip().lower()

        if random_seating == 'y':
            # Случайная рассадка
            roles = ['blue'] * (NUM_PLAYERS - NUM_REDS) + ['red'] * (NUM_REDS - 1) + ['demon']
            random.shuffle(roles)
            for i in range(NUM_PLAYERS):
                role = roles[i]
                if role == 'demon':
                    self.demon = i
                self.players.append(Player(role, i))
        else:
            # Вручную назначаем роли
            print("Введите 'b' для синего эмпата, 'r' для красного эмпата, 'd' для демона.")
            num_reds_assigned = 0
            for i in range(NUM_PLAYERS):
                while True:
                    role_input = input(f"Игрок {i + 1}: ").strip().lower()
                    if role_input == 'b':
                        role = 'blue'
                        break
                    elif role_input == 'r':
                        if num_reds_assigned < NUM_REDS - 1:
                            role = 'red'
                            num_reds_assigned += 1
                            break
                        else:
                            print(f"Вы уже назначили максимальное количество красных эмпатов ({NUM_REDS - 1}).")
                    elif role_input == 'd':
                        if self.demon is None:
                            role = 'demon'
                            self.demon = i
                            num_reds_assigned += 1
                            break
                        else:
                            print("Демон уже назначен. Выберите другую роль.")
                    else:
                        print("Неверный ввод. Попробуйте снова.")
                self.players.append(Player(role, i))

        # Устанавливаем количество красных соседей для эмпатов
        for player in self.players:
            player.update_neighbors(self.players)

        # Предлагаем ведущему установить случайные цифры для красных эмпатов
        print("Ведущий, вы хотите случайные цифры для красных эмпатов? (y/n)")
        random_fake_info = input().strip().lower()

        if random_fake_info == 'y':
            self.update_red_fake_info(randomize=True)
        else:
            # Вручную вводим цифры для красных эмпатов
            for i, player in enumerate(self.players):
                if player.role == 'red':
                    while True:
                        try:
                            fake_info = int(input(f"Введите цифру (0, 1 или 2) для красного эмпата {i + 1}: "))
                            if fake_info in [0, 1, 2]:
                                player.fake_red_neighbors_count = fake_info
                                break
                            else:
                                print("Нужно ввести 0, 1 или 2.")
                        except ValueError:
                            print("Пожалуйста, введите число 0, 1 или 2.")

    def update_all_blue_neighbors(self):
        for player in self.players:
            if player.alive and player.role == 'blue':
                player.update_neighbors(self.players)

    def update_red_fake_info(self, randomize=True):
        for player in self.players:
            if player.alive and player.role in ['red', 'demon']:
                if randomize:
                    player.fake_red_neighbors_count = random.randint(0, 2)
                else:
                    # Если не рандом, ведущий вводит цифры вручную
                    while True:
                        try:
                            fake_info = int(input(f"Введите цифру (0, 1 или 2) для красного эмпата {player.position + 1}: "))
                            if fake_info in [0, 1, 2]:
                                player.fake_red_neighbors_count = fake_info
                                break
                            else:
                                print("Нужно ввести 0, 1 или 2.")
                        except ValueError:
                            print("Пожалуйста, введите число 0, 1 или 2.")

    def check_game_over(self):
        alive_blues = sum(1 for player in self.players if player.alive and player.role == 'blue')
        alive_reds = sum(1 for player in self.players if player.alive and player.role in ['red', 'demon'])

        if alive_blues == 0:
            print("Все синие игроки мертвы. Красные игроки победили!")
            self.game_over = True
        elif alive_blues == 1 and alive_reds == 1 and self.players[self.demon].alive:
            print("Остались только один синий игрок и демон. Красные игроки победили!")
            self.game_over = True
        elif not self.players[self.demon].alive:
            print("Демон мертв. Синие игроки победили!")
            self.game_over = True

    def get_phase_text(self):
        if self.night_phase:
            return "Ночь: ход демона"
        else:
            return "День: ход игроков"

class Player:
    def __init__(self, role, position):
        self.role = role  # 'blue', 'red', 'demon'
        self.position = position
        self.alive = True
        self.visible_to_player = True  # Контролирует видимость на экране игрока
        self.executed = False
        self.red_neighbors_count = 0
        self.fake_red_neighbors_count = 0

    def update_neighbors(self, players):
        if self.role == 'blue':
            # Обновляем количество красных соседей
            left_index = self.position
            while True:
                left_index = (left_index - 1) % NUM_PLAYERS
                if players[left_index].alive and left_index != self.position:
                    break
                if left_index == self.position:
                    break

            right_index = self.position
            while True:
                right_index = (right_index + 1) % NUM_PLAYERS
                if players[right_index].alive and right_index != self.position:
                    break
                if right_index == self.position:
                    break

            neighbors = []
            if left_index != self.position and players[left_index].alive:
                neighbors.append(players[left_index])
            if right_index != self.position and players[right_index].alive:
                neighbors.append(players[right_index])

            self.red_neighbors_count = sum(1 for neighbor in neighbors if neighbor.role in ['red', 'demon'])

    def get_info(self):
        if self.role == 'blue':
            return f"{self.red_neighbors_count}"
        else:
            return f"{self.fake_red_neighbors_count}"


# Представление игры
class GameView(arcade.View):
    def __init__(self, game_state):
        super().__init__()
        self.game_state = game_state

        # Устанавливаем частоту обновления экрана
        self.window.set_update_rate(1 / 60)

    def on_draw(self):
        # Очищаем экран один раз
        arcade.start_render()

        # --- Рисуем область ведущего ---
        self.draw_moderator_view()

        # --- Рисуем область игрока ---
        self.draw_player_view()

    def draw_moderator_view(self):
        # Рисуем фон для области ведущего
        arcade.draw_lrtb_rectangle_filled(
            0,
            self.window.width // 2,
            self.window.height,
            0,
            arcade.color.DARK_BLUE_GRAY
        )

        # Отображаем текущую фазу игры
        phase_text = self.game_state.get_phase_text()
        arcade.draw_text(
            phase_text,
            10,
            self.window.height - 30,
            arcade.color.WHITE,
            20,
            bold=True
        )

        center_x = (self.window.width // 2) // 2
        center_y = self.window.height // 2
        radius = 250

        for i in range(NUM_PLAYERS):
            player = self.game_state.players[i]
            angle = math.radians((360 / NUM_PLAYERS) * i)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            # Цвет по роли
            if player.alive:
                if player.executed:
                    color = arcade.color.YELLOW
                elif player.role == 'blue':
                    color = arcade.color.BLUE
                elif player.role == 'red':
                    color = arcade.color.RED
                elif player.role == 'demon':
                    color = arcade.color.BLACK
                else:
                    color = arcade.color.LIGHT_GRAY
                arcade.draw_circle_filled(x, y, 20, color)

                # Отображаем информацию эмпата
                info = player.get_info()
                arcade.draw_text(info, x + 25, y - 10, arcade.color.WHITE, 12)
            else:
                # Жетон мертвого игрока
                arcade.draw_circle_filled(x, y, 20, arcade.color.GRAY)

            # Отображаем номер игрока
            arcade.draw_text(str(i + 1), x - 10, y - 10, arcade.color.WHITE, 12)

    def draw_player_view(self):
        # Рисуем фон для области игрока
        arcade.draw_lrtb_rectangle_filled(
            self.window.width // 2,
            self.window.width,
            self.window.height,
            0,
            arcade.color.ASH_GREY
        )

        # Отображаем текущую фазу игры
        phase_text = self.game_state.get_phase_text()
        arcade.draw_text(
            phase_text,
            self.window.width // 2 + 10,
            self.window.height - 30,
            arcade.color.BLACK,
            20,
            bold=True
        )

        # Корректируем центр для правой половины окна
        center_x = (self.window.width // 2) // 2 + self.window.width // 2
        center_y = self.window.height // 2
        radius = 250

        for i in range(NUM_PLAYERS):
            player = self.game_state.players[i]
            angle = math.radians((360 / NUM_PLAYERS) * i)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            # Проверяем видимость игрока на экране игрока
            if player.visible_to_player:
                if player.alive:
                    if player.executed:
                        color = arcade.color.YELLOW
                    else:
                        color = arcade.color.LIGHT_GRAY
                    arcade.draw_circle_filled(x, y, 20, color)
                else:
                    # Жетон мертвого игрока
                    arcade.draw_circle_filled(x, y, 20, arcade.color.GRAY)
            else:
                # Если игрок скрыт от игрока (например, убит ночью, но еще не открыт игроку)
                # Отображаем как живого
                if player.executed:
                    color = arcade.color.YELLOW
                else:
                    color = arcade.color.LIGHT_GRAY
                arcade.draw_circle_filled(x, y, 20, color)

            # Отображаем информацию эмпата
            info = player.get_info()
            arcade.draw_text(info, x + 25, y - 10, arcade.color.BLACK, 12)

            # Отображаем номер игрока
            arcade.draw_text(str(i + 1), x - 10, y - 10, arcade.color.BLACK, 12)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_state.game_over:
            return

        # Определяем, в какой области произошло нажатие
        if x < self.window.width // 2:
            # Левая область - действия ведущего
            self.handle_moderator_click(x, y)
        else:
            # Правая область - действия игрока
            self.handle_player_click(x, y)

    def handle_moderator_click(self, x, y):
        if self.game_state.night_phase:
            selected_player = self.get_clicked_player_moderator(x, y)
            if selected_player is not None:
                self.night_phase_actions(selected_player)
        else:
            # В дневную фазу ведущий не делает ничего
            pass

    def handle_player_click(self, x, y):
        if not self.game_state.night_phase:
            selected_player = self.get_clicked_player_player(x, y)
            if selected_player is not None:
                self.day_phase_actions(selected_player)
        else:
            # В ночную фазу игрок не может действовать
            pass

    def get_clicked_player_moderator(self, x, y):
        center_x = (self.window.width // 2) // 2
        center_y = self.window.height // 2
        radius = 250
        for i in range(NUM_PLAYERS):
            angle = (360 / NUM_PLAYERS) * i
            player_x = center_x + radius * math.cos(math.radians(angle))
            player_y = center_y + radius * math.sin(math.radians(angle))
            if arcade.get_distance(x, y, player_x, player_y) < 20:
                return i
        return None

    def get_clicked_player_player(self, x, y):
        center_x = (self.window.width // 2) // 2 + self.window.width // 2
        center_y = self.window.height // 2
        radius = 250
        for i in range(NUM_PLAYERS):
            angle = (360 / NUM_PLAYERS) * i
            player_x = center_x + radius * math.cos(math.radians(angle))
            player_y = center_y + radius * math.sin(math.radians(angle))
            if arcade.get_distance(x, y, player_x, player_y) < 20:
                return i
        return None

    def night_phase_actions(self, target):
        if 0 <= target < NUM_PLAYERS:
            player = self.game_state.players[target]
            if player.alive and target != self.game_state.demon:
                player.alive = False
                player.visible_to_player = False  # Скрываем от игрока информацию об убийстве
                self.game_state.pending_night_kill = target
                print(f"Ночью демон убил игрока {target + 1}")

                # Обновляем экран, чтобы отобразить изменения на экране ведущего
                self.window.invalid = True

                # Обновляем информацию после ночи
                self.game_state.update_all_blue_neighbors()
                self.game_state.update_red_fake_info(randomize=False)  # Ведущий вводит цифры после ночи
                self.game_state.check_game_over()
                self.game_state.night_phase = False  # Переход в дневную фазу

                # После выбора цифр для красных эмпатов открываем игроку информацию об убийстве
                killed_player = self.game_state.players[self.game_state.pending_night_kill]
                killed_player.visible_to_player = True  # Теперь игрок видит, что этот игрок мертв
                self.game_state.pending_night_kill = None

    def day_phase_actions(self, selected_player):
        player = self.game_state.players[selected_player]
        if player.alive:
            player.executed = True
            player.alive = False
            player.visible_to_player = True  # Сразу показываем игроку, что этот игрок мертв
            print(f"Днем был казнен игрок {selected_player + 1}")

            # Обновляем экран, чтобы отобразить изменения сразу
            self.window.invalid = True

            # Обновляем информацию после дня
            self.game_state.update_all_blue_neighbors()
            # Не вызываем update_red_fake_info(), так как цифры для красных эмпатов выбираются только после ночи
            self.game_state.check_game_over()
            if player.position == self.game_state.demon:
                print("Демон казнен! Синие игроки победили!")
                self.game_state.game_over = True
            else:
                self.game_state.night_phase = True  # Переход в ночную фазу

    def on_key_press(self, key, modifiers):
        pass

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_state = GameState()

    game_view = GameView(game_state)
    window.show_view(game_view)

    arcade.run()

if __name__ == "__main__":
    main()
