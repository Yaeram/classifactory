# Используем официальный образ Python для создания билда
FROM python:3.9-slim-buster

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем исходный код в контейнер
COPY . .

# Устанавливаем необходимые зависимости
RUN pip3 install requests docopt bs4 nltk


# Запускаем приложение
CMD ["python", "./__main__.py"]