FROM python:3.11-slim

# Установка зависимостей, включая SQLite, компилятор GCC, и необходимые библиотеки для Pillow
RUN apt-get update && apt-get install -y \
    sqlite3 \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Инициализация базы данных
RUN python -c "from database import init_db; init_db()"

CMD ["python", "bot.py"]
