# render_game_set.py

import os
import re
import logging
from PIL import Image, ImageDraw, ImageFont
import math
import io
from telegram import Update
from telegram.ext import ContextTypes
from database import get_latest_game_set, get_all_tokens
from distributions import POSITIONS_MAP

# Настройка логирования
logger = logging.getLogger(__name__)

# Путь к шрифтам
FONT_PATH = os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf')

def escape_markdown_v2(text: str) -> str:
    """
    Экранирует специальные символы для MarkdownV2.
    """
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

async def show_start_game_set(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает начальные настройки игры, включая визуализацию карты жетонов.
    Все жетоны отображаются серыми.
    """
    game_set = get_latest_game_set()

    if game_set:
        tokens_count = game_set['tokens_count']
        red_count = game_set['red_count']
        player_username = game_set['player_username']

        # Получаем карту распределения жетонов по количеству жетонов
        token_map = POSITIONS_MAP.get(tokens_count)

        if not token_map:
            message = "Карта распределения жетонов для данного количества жетонов не найдена."
            escaped_message = escape_markdown_v2(message)
            await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
            logger.warning(f"Карта распределения жетонов для tokens_count={tokens_count} не найдена.")
            return

        # Создаём список цветов жетонов: все серые
        tokens_colors = ['grey'] * tokens_count

        # Рассчитываем позиции жетонов по кругу
        image_size = 500  # Размер изображения
        center = image_size // 2
        radius = image_size // 2 - 50  # Радиус круга, на котором будут расположены жетоны
        angle_between_tokens = 360 / tokens_count

        # Создаем новое изображение
        image = Image.new('RGB', (image_size, image_size), color='white')
        draw = ImageDraw.Draw(image)

        # Проверяем наличие шрифта
        if not os.path.isfile(FONT_PATH):
            message = f"Файл шрифта не найден по пути '{FONT_PATH}'."
            escaped_message = escape_markdown_v2(message)
            await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
            logger.error(f"Файл шрифта не найден по пути '{FONT_PATH}'.")
            return

        # Загружаем шрифт
        font_size = 20
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except Exception as e:
            message = "Не удалось загрузить шрифт."
            escaped_message = escape_markdown_v2(message)
            await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
            logger.error(f"Ошибка при загрузке шрифта: {e}")
            return

        for i in range(tokens_count):
            angle_deg = angle_between_tokens * i - 90  # Смещаем на 90 градусов, чтобы первый жетон был сверху
            angle_rad = math.radians(angle_deg)

            # Позиция жетона
            x = center + radius * math.cos(angle_rad)
            y = center + radius * math.sin(angle_rad)

            # Цвет жетона: всегда серый
            token_color = 'grey'

            # Рисуем жетон (круг)
            token_radius = 20
            left_up_point = (x - token_radius, y - token_radius)
            right_down_point = (x + token_radius, y + token_radius)
            draw.ellipse([left_up_point, right_down_point], fill=token_color, outline='black')

            # Номер жетона внутри круга
            token_number = str(i + 1)
            number_width, number_height = draw.textsize(token_number, font=font)
            number_x = x - number_width / 2
            number_y = y - number_height / 2
            draw.text((number_x, number_y), token_number, fill='black', font=font)

            # Цифра 0 справа от жетона
            zero_text = '0'
            zero_width, zero_height = draw.textsize(zero_text, font=font)
            zero_x = x + token_radius + 5  # 5 пикселей отступ
            zero_y = y - zero_height / 2
            draw.text((zero_x, zero_y), zero_text, fill='black', font=font)

        # Сохраняем изображение в байтовый поток
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)

        # Экранирование и форматирование информации об игре
        escaped_player_username = escape_markdown_v2(player_username)
        game_info = (
            f"**Текущие настройки игры:**\n"
            f"**Игрок:** {escaped_player_username}\n"
            f"**Количество жетонов \\(tokens_count\\):** {tokens_count}\n"
            f"**Количество красных жетонов \\(red_count\\):** {red_count}\n\n"
            f"**Карта распределения жетонов:**"
        )

        # Отправляем информацию и изображение
        await update.message.reply_text(game_info, parse_mode='MarkdownV2')
        await update.message.reply_photo(photo=image_bytes, caption="Карта распределения жетонов")
        logger.info("Показаны начальные настройки игры с картой жетонов.")
    else:
        message = "Настройки игры не найдены."
        escaped_message = escape_markdown_v2(message)
        await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
        logger.warning("Настройки игры не найдены.")


async def show_start_game_set_with_red_(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает настройки игры после выбора демона, включая визуализацию карты жетонов.
    Красные жетоны отображаются красным цветом, демон отображается фиолетовым цветом.
    """
    game_set = get_latest_game_set()

    if game_set:
        tokens_count = game_set['tokens_count']
        red_count = game_set['red_count']
        player_username = game_set['player_username']

        # Получаем карту распределения жетонов по количеству жетонов
        token_map = POSITIONS_MAP.get(tokens_count)

        if not token_map:
            message = "Карта распределения жетонов для данного количества жетонов не найдена."
            escaped_message = escape_markdown_v2(message)
            await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
            logger.warning(f"Карта распределения жетонов для tokens_count={tokens_count} не найдена.")
            return

        # Получаем список жетонов из базы данных
        tokens_data = get_all_tokens()

        # Сортируем жетоны по id для соответствия порядку
        tokens_data.sort(key=lambda x: x[0])  # x[0] это id жетона

        # Получаем список цветов жетонов и информацию о демоне
        tokens_colors = []
        demon_token_id = None

        for token in tokens_data:
            token_id, alignment, character, _ = token
            if character == 'demon':
                tokens_colors.append('purple')  # Демон отображается фиолетовым цветом
                demon_token_id = token_id
            elif alignment == 'red':
                tokens_colors.append('red')  # Красные жетоны
            else:
                tokens_colors.append('lightblue')  # Синие жетоны отображаются светло-синим цветом

        # Рассчитываем позиции жетонов по кругу
        image_size = 500  # Размер изображения
        center = image_size // 2
        radius = image_size // 2 - 50  # Радиус круга, на котором будут расположены жетоны
        angle_between_tokens = 360 / tokens_count

        # Создаем новое изображение
        image = Image.new('RGB', (image_size, image_size), color='white')
        draw = ImageDraw.Draw(image)

        # Проверяем наличие шрифта
        if not os.path.isfile(FONT_PATH):
            message = f"Файл шрифта не найден по пути '{FONT_PATH}'."
            escaped_message = escape_markdown_v2(message)
            await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
            logger.error(f"Файл шрифта не найден по пути '{FONT_PATH}'.")
            return

        # Загружаем шрифт
        font_size = 20
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except Exception as e:
            message = "Не удалось загрузить шрифт."
            escaped_message = escape_markdown_v2(message)
            await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
            logger.error(f"Ошибка при загрузке шрифта: {e}")
            return

        for i in range(tokens_count):
            angle_deg = angle_between_tokens * i - 90  # Смещаем на 90 градусов, чтобы первый жетон был сверху
            angle_rad = math.radians(angle_deg)

            # Позиция жетона
            x = center + radius * math.cos(angle_rad)
            y = center + radius * math.sin(angle_rad)

            # Цвет жетона
            token_color = tokens_colors[i]

            # Рисуем жетон (круг)
            token_radius = 20
            left_up_point = (x - token_radius, y - token_radius)
            right_down_point = (x + token_radius, y + token_radius)
            draw.ellipse([left_up_point, right_down_point], fill=token_color, outline='black')

            # Номер жетона внутри круга
            token_number = str(i + 1)
            number_width, number_height = draw.textsize(token_number, font=font)
            number_x = x - number_width / 2
            number_y = y - number_height / 2
            draw.text((number_x, number_y), token_number, fill='black', font=font)

            # Цифра 0 справа от жетона
            zero_text = '0'
            zero_width, zero_height = draw.textsize(zero_text, font=font)
            zero_x = x + token_radius + 5  # 5 пикселей отступ
            zero_y = y - zero_height / 2
            draw.text((zero_x, zero_y), zero_text, fill='black', font=font)

        # Сохраняем изображение в байтовый поток
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)

        # Экранирование и форматирование информации об игре
        escaped_player_username = escape_markdown_v2(player_username)
        game_info = (
            f"**Текущие настройки игры:**\n"
            f"**Игрок:** {escaped_player_username}\n"
            f"**Количество жетонов \\(tokens_count\\):** {tokens_count}\n"
            f"**Количество красных жетонов \\(red_count\\):** {red_count}\n\n"
            f"**Карта распределения жетонов:**"
        )

        # Отправляем информацию и изображение
        await update.message.reply_text(game_info, parse_mode='MarkdownV2')
        await update.message.reply_photo(photo=image_bytes, caption="Карта распределения жетонов")
        logger.info("Показаны настройки игры с красными жетонами и демоном.")
    else:
        message = "Настройки игры не найдены."
        escaped_message = escape_markdown_v2(message)
        await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
        logger.warning("Настройки игры не найдены.")



async def show_start_game_set_with_red_neighbors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает настройки игры, включая визуализацию карты жетонов.
    Отображает цвета жетонов и значения red_neighbors из базы данных.
    """
    game_set = get_latest_game_set()

    if game_set:
        tokens_count = game_set['tokens_count']
        red_count = game_set['red_count']
        player_username = game_set['player_username']

        # Получаем карту распределения жетонов по количеству жетонов
        token_map = POSITIONS_MAP.get(tokens_count)

        if not token_map:
            message = "Карта распределения жетонов для данного количества жетонов не найдена."
            escaped_message = escape_markdown_v2(message)
            await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
            logger.warning(f"Карта распределения жетонов для tokens_count={tokens_count} не найдена.")
            return

        # Получаем список жетонов из базы данных
        tokens_data = get_all_tokens()

        # Сортируем жетоны по id для соответствия порядку
        tokens_data.sort(key=lambda x: x[0])  # x[0] это id жетона

        # Получаем список цветов жетонов и информацию о демоне
        tokens_colors = []
        red_neighbors_list = []
        for token in tokens_data:
            token_id, alignment, character, red_neighbors = token
            red_neighbors_list.append(red_neighbors)
            if character == 'demon':
                tokens_colors.append('purple')  # Демон отображается фиолетовым цветом
            elif alignment == 'red':
                tokens_colors.append('red')  # Красные жетоны
            elif alignment == 'blue':
                tokens_colors.append('lightblue')  # Синие жетоны
            else:
                tokens_colors.append('grey')  # Неизвестные жетоны (на случай ошибки)

        # Рассчитываем позиции жетонов по кругу
        image_size = 500  # Размер изображения
        center = image_size // 2
        radius = image_size // 2 - 50  # Радиус круга, на котором будут расположены жетоны
        angle_between_tokens = 360 / tokens_count

        # Создаем новое изображение
        image = Image.new('RGB', (image_size, image_size), color='white')
        draw = ImageDraw.Draw(image)

        # Проверяем наличие шрифта
        if not os.path.isfile(FONT_PATH):
            message = f"Файл шрифта не найден по пути '{FONT_PATH}'."
            escaped_message = escape_markdown_v2(message)
            await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
            logger.error(f"Файл шрифта не найден по пути '{FONT_PATH}'.")
            return

        # Загружаем шрифт
        font_size = 20
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except Exception as e:
            message = "Не удалось загрузить шрифт."
            escaped_message = escape_markdown_v2(message)
            await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
            logger.error(f"Ошибка при загрузке шрифта: {e}")
            return

        for i in range(tokens_count):
            angle_deg = angle_between_tokens * i - 90  # Смещаем на 90 градусов, чтобы первый жетон был сверху
            angle_rad = math.radians(angle_deg)

            # Позиция жетона
            x = center + radius * math.cos(angle_rad)
            y = center + radius * math.sin(angle_rad)

            # Цвет жетона
            token_color = tokens_colors[i]

            # Рисуем жетон (круг)
            token_radius = 20
            left_up_point = (x - token_radius, y - token_radius)
            right_down_point = (x + token_radius, y + token_radius)
            draw.ellipse([left_up_point, right_down_point], fill=token_color, outline='black')

            # Номер жетона внутри круга
            token_number = str(i + 1)
            number_width, number_height = draw.textsize(token_number, font=font)
            number_x = x - number_width / 2
            number_y = y - number_height / 2
            draw.text((number_x, number_y), token_number, fill='black', font=font)

            # Значение red_neighbors справа от жетона
            red_neighbors = red_neighbors_list[i]
            red_neighbors_text = str(red_neighbors)
            rn_width, rn_height = draw.textsize(red_neighbors_text, font=font)
            rn_x = x + token_radius + 5  # 5 пикселей отступ
            rn_y = y - rn_height / 2
            draw.text((rn_x, rn_y), red_neighbors_text, fill='black', font=font)

        # Сохраняем изображение в байтовый поток
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)

        # Экранирование и форматирование информации об игре
        escaped_player_username = escape_markdown_v2(player_username)
        game_info = (
            f"**Текущие настройки игры:**\n"
            f"**Игрок:** {escaped_player_username}\n"
            f"**Количество жетонов \\(tokens_count\\):** {tokens_count}\n"
            f"**Количество красных жетонов \\(red_count\\):** {red_count}\n\n"
            f"**Карта распределения жетонов с количеством красных соседей:**"
        )

        # Отправляем информацию и изображение
        await update.message.reply_text(game_info, parse_mode='MarkdownV2')
        await update.message.reply_photo(photo=image_bytes, caption="Карта с красными соседями")
        logger.info("Показаны настройки игры с отображением red_neighbors.")
    else:
        message = "Настройки игры не найдены."
        escaped_message = escape_markdown_v2(message)
        await update.message.reply_text(escaped_message, parse_mode='MarkdownV2')
        logger.warning("Настройки игры не найдены.")
