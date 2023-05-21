FROM python:3.9

# Установка зависимостей для xvfb
RUN apt-get update && apt-get install -yq \
    curl \
    gpg \
    wget \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Установка Playwright
RUN pip install playwright

# Установка Сhromium
RUN playwright install chromium

# Копирование файлов
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.log .
COPY . .

# Установка и запуск xvfb
RUN apt-get update && apt-get install -yq \
    xvfb
ENV DISPLAY=:99

# Запуск xvfb и приложения
CMD xvfb-run --server-args="-screen 0 1024x768x24" python app.py
