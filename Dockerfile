# Истифодаи симои Python
FROM python:3.11-slim

# Насби ffmpeg дар система
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Танзими папкаи корӣ
WORKDIR /app

# Нусхабардории файлҳо
COPY . .

# Насби китобхонаҳо
RUN pip install --no-cache-dir -r requirements.txt

# Ба кор даровардани бот
CMD ["python", "main.py"]
