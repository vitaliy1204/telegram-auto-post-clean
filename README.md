# Telegram Auto Post Bot

## Налаштування

1. Створи `.env` файл з такими змінними:

```
BOT_TOKEN=...
CHAT_ID=...
GOOGLE_CREDENTIALS=google_credentials.json
SPREADSHEET_NAME=...
```

2. Завантаж `google_credentials.json` у корінь проєкту.

3. Встанови залежності:

```
pip install -r requirements.txt
```

4. Запусти:

```
python main.py
```