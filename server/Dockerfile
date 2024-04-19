# Используем официальный образ Go для создания билда
FROM golang:1.18 AS builder

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем исходный код в контейнер
COPY . .

# Собираем Go приложение
RUN go mod tidy
RUN go build -v /app/gin_webserver.go


# Используем второй этап сборки для создания минимального образа
FROM debian:11


COPY --from=builder /app/gin_webserver /gin_webserver
COPY --from=builder /app/migrations /migrations

# Запускаем приложение
CMD ["/gin_webserver"]