# VolBot AI — Инструкция по запуску бота

## ⚡ Быстрый старт (5 шагов)

### 1. Создай бота в Telegram
- Напиши @BotFather
- `/newbot` → задай имя `VolBot AI` → username `volbotai_bot`
- Скопируй токен (длинная строка вида `123456:ABC-DEF...`)

### 2. Настрой config.py
```python
BOT_TOKEN = "твой_токен_от_botfather"
ADMIN_ID  = твой_telegram_id        # узнать через @userinfobot
CHANNEL_ID = "volbotai"             # username твоего канала
USDT_ADDRESS = "твой_usdt_адрес"
```

### 3. Установи зависимости (на VPS или локально)
```bash
pip install -r requirements.txt
```

### 4. Запусти бота
```bash
python bot.py
```

### 5. Настрой бота в BotFather
```
/setcommands → вставь:
start - Главное меню
menu - Главное меню
stats - Статистика сегодня
support - Написать в поддержку

/setdescription → VolBot AI — торговый ИИ для Deriv Volatility 75. 7 дней бесплатно.
/setabouttext → Автоматическая торговля на Vol75 через MT5 · 24/7
```

---

## 🖥 Запуск на VPS (чтобы бот работал постоянно)

### Вариант A — через screen (простой)
```bash
screen -S volbot
python bot.py
# Ctrl+A, затем D — свернуть в фон
# screen -r volbot — вернуться
```

### Вариант B — через systemd (надёжный)
Создай файл `/etc/systemd/system/volbot.service`:
```ini
[Unit]
Description=VolBot AI Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/volbot
ExecStart=/usr/bin/python3 /root/volbot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
Затем:
```bash
systemctl enable volbot
systemctl start volbot
systemctl status volbot
```

---

## 👑 Команды администратора

| Команда | Что делает |
|---------|-----------|
| `/admin` | Статистика: пользователи, подписки, выручка |
| `/broadcast` | Рассылка всем пользователям |
| `/stats` | Быстрая статистика дня |

---

## 💰 Как подтверждать платежи

1. Пользователь оплачивает → нажимает "Отправить чек"
2. Тебе приходит уведомление с фото и кнопками
3. Нажимаешь ✅ Подтвердить → пользователю автоматически приходит подтверждение
4. Дальше вручную отправляешь инструкцию по подключению MT5

---

## 🔮 Что добавить в следующей версии

- [ ] База данных SQLite вместо словаря в памяти
- [ ] Автоматическая проверка оплаты через API (NOWPayments/CryptoMus)
- [ ] Авто-рассылка ежедневной статистики в 20:00
- [ ] Реферальная система с промокодами
- [ ] Интеграция с MT5 через API для live-статистики

---

## 📁 Структура файлов

```
volbot/
├── bot.py          — основной код бота
├── config.py       — настройки (токен, ID, реквизиты)
├── requirements.txt — зависимости Python
└── README.md       — эта инструкция
```
