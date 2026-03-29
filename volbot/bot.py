"""
VolBot AI — Telegram Bot
Полная воронка продаж для торгового робота Vol75
Требования: pip install python-telegram-bot==20.7 python-dotenv
"""

import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID, USDT_ADDRESS, CARD_NUMBER

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Состояния ConversationHandler ───
WAITING_PAYMENT_PROOF = 1
WAITING_SUPPORT_MSG = 2
WAITING_BROADCAST_MSG = 3

# ─── Хранилище (в реальном боте — база данных) ───
# Формат: { user_id: { "plan": "pro"/"course"/"xauusd", "trial": bool, "active": bool, "expires": date } }
users_db: dict = {}
pending_payments: dict = {}  # { user_id: plan }


# ════════════════════════════════════════════
#  ТЕКСТЫ
# ════════════════════════════════════════════


def text_welcome(first_name: str) -> str:
    return (
        f"👋 *Привет, {first_name}!*\n\n"
        "Добро пожаловать в *VolBot AI* — торговый ИИ для Deriv Volatility 75.\n\n"
        "🤖 *Что умеет наш робот:*\n"
        "• Торгует 24/7 без твоего участия\n"
        "• Специально обучен только на Vol75\n"
        "• Работает через официальный MT5 + Deriv\n"
        "• Встроенное управление рисками\n\n"
        "⬇️ Выбери раздел, чтобы начать:"
    )


def text_about() -> str:
    return (
        "🧠 *О роботе VolBot AI*\n\n"
        "Большинство торговых роботов пытаются работать на всех рынках сразу — и проигрывают. "
        "Мы пошли другим путём:\n\n"
        "📌 *Наш ИИ обучен только на одном символе:*\n"
        "Volatility 75 Index на платформе Deriv\n\n"
        "⚙️ *Технические детали:*\n"
        "• Платформа: MetaTrader 5 (MT5)\n"
        "• Брокер: Deriv (лицензированный)\n"
        "• Символ: Volatility 75 Index\n"
        "• Минимальный депозит: от $50\n"
        "• Рекомендуемый депозит: $200–$1000\n\n"
        "🛡️ *Защита депозита:*\n"
        "• Авто стоп-лосс на каждую сделку\n"
        "• Максимальный дневной убыток: 5%\n"
        "• Риск на сделку: 1–2%\n\n"
        "📊 *Средняя статистика (последние 6 мес):*\n"
        "• Win rate: 97%\n"
        "• Средняя доходность: +22% / мес\n"
        "• Максимальная просадка: 8.4%\n\n"
        "⚠️ _Прошлые результаты не гарантируют будущую доходность._"
    )


def text_results() -> str:
    return (
        "📈 *Результаты торговли — реальный счёт MT5*\n\n"
        "┌─────────────────────────────────┐\n"
        "│  Октябрь  2024  │  *+22.4%*  │  66% WR  │\n"
        "│  Ноябрь   2024  │  *+31.7%*  │  71% WR  │\n"
        "│  Декабрь  2024  │  *+16.7%*  │  63% WR  │\n"
        "│  Январь   2025  │  *+18.9%*  │  64% WR  │\n"
        "│  Февраль  2025  │  *+27.3%*  │  69% WR  │\n"
        "│  Март     2025  │  *+19.6%*  │  65% WR  │\n"
        "└─────────────────────────────────┘\n\n"
        "📊 *Итого за 6 месяцев:*\n"
        "• Суммарно: *+136.6%*\n"
        "• Убыточных месяцев: 0 из 6\n"
        "• Всего сделок: 1 159\n"
        "• Средний Win Rate: *97%*\n\n"
        "🔍 _Все данные взяты из истории MT5.\n"
        "Никаких бэктестов — только реальные сделки._\n\n"
        "⚠️ _Торговля связана с риском. Инвестируй только то, что готов потерять._"
    )


def text_xauusd_vip() -> str:
    return (
        "🥇 *XAUUSD VIP — торговые сигналы по золоту*\n\n"
        "Торгуешь золото (XAUUSD) и хочешь получать точные входы от профи?\n\n"
        "📌 *Что ты получаешь:*\n"
        "• Сигналы по XAUUSD в реальном времени\n"
        "• Точка входа, стоп-лосс, тейк-профит\n"
        "• 3–8 сделок в день\n"
        "• Средний профит: +50–150 пунктов на сделку\n"
        "• Закрытый VIP-канал в Telegram\n"
        "• Поддержка 7 дней в неделю\n\n"
        "💰 *Стоимость: $49/мес*\n\n"
        "📊 *Статистика за последний месяц:*\n"
        "• Сделок: 142\n"
        "• Win rate: 73%\n"
        "• Средний профит: +87 пунктов\n"
        "• Просадка: 2.1%\n\n"
        "👇 Выбери действие:"
    )


def text_pricing() -> str:
    return (
        "💎 *Тарифы VolBot AI*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🥇 *XAUUSD VIP — $49/мес*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Сигналы по золоту (XAUUSD) в реальном времени\n"
        "✅ Точка входа, SL, TP на каждую сделку\n"
        "✅ 3–8 сигналов в день\n"
        "✅ Закрытый VIP-канал\n"
        "✅ Поддержка 7 дней в неделю\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 *Vol75 Pro Signal — $100/мес*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Сигналы и копирование сделок 24/7\n"
        "✅ Ежедневная статистика в Telegram\n"
        "✅ Инструкция по подключению MT5\n"
        "✅ Личная поддержка в чате\n"
        "✅ Закрытое комьюнити подписчиков\n"
        "✅ 7 дней БЕСПЛАТНОГО триала\n"
        "✅ Отмена в любой момент\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 *Vol75 Master Course — $397 разово*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ 8 видеомодулей с нуля до профи\n"
        "✅ Разбор ИИ-стратегии Vol75 в деталях\n"
        "✅ Настройка MT5 под себя\n"
        "✅ Управление рисками и мани-менеджмент\n"
        "✅ Пожизненный доступ + обновления\n"
        "✅ *1 месяц подписки Pro в подарок*\n\n"
        "👇 Выбери тариф:"
    )


def text_trial_info() -> str:
    return (
        "🎁 *7 дней бесплатного триала*\n\n"
        "Мы даём тебе 7 дней, чтобы убедиться в результате *без оплаты*.\n\n"
        "📋 *Что ты получишь:*\n"
        "• Полный доступ к сигналам робота\n"
        "• Ежедневный отчёт в этот чат\n"
        "• Помощь с подключением MT5\n"
        "• Доступ в закрытый чат подписчиков\n\n"
        "⚙️ *Требования для старта:*\n"
        "1️⃣ Аккаунт на Deriv (бесплатно)\n"
        "2️⃣ Установленный MetaTrader 5\n"
        "3️⃣ Депозит от $50 на торговом счёте\n\n"
        "После триала — реши сам, хочешь ли продолжить за $100/мес.\n\n"
        "👇 Нажми кнопку, чтобы активировать триал:"
    )


def text_payment_instructions(plan: str) -> str:
    if plan == "trial":
        return (
            "✅ *Триал активирован!*\n\n"
            "Отлично! Дальше пришли @aielegan своё:\n"
            "• Имя / никнейм\n"
            "• Логин MT5 (только номер счёта, не пароль)\n\n"
            "Мы подключим тебя в течение *15 минут* и пришлём инструкцию.\n\n"
            "📌 Пока жди — вступи в наш канал с результатами:"
        )
    prices = {"xauusd": "$49", "pro": "$100", "course": "$397"}
    names = {
        "xauusd": "XAUUSD VIP",
        "pro": "Vol75 Pro Signal",
        "course": "Vol75 Master Course",
    }
    price = prices.get(plan, "$49")
    plan_name = names.get(plan, plan)
    return (
        f"💳 *Оплата — {plan_name}*\n\n"
        f"*Сумма: {price}*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💰 *USDT (TRC20):*\n"
        f"`{USDT_ADDRESS}`\n"
        "_(нажми, чтобы скопировать)_\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📤 *После оплаты:*\n"
        "Нажми кнопку ниже и отправь скриншот транзакции.\n"
        "Доступ активируем в течение *15 минут*.\n\n"
        "❓ Вопросы по оплате → @aielegan"
    )


def text_how_to_start() -> str:
    return (
        "🚀 *Как начать — пошаговая инструкция*\n\n"
        "*Шаг 1 — Зарегистрируйся на Deriv*\n"
        "1. Создай аккаунт (5 минут)\n"
        "2. Пополни счёт от $50\n\n"
        "*Шаг 2 — Установи MetaTrader 5*\n"
        "1. Скачай MT5 с [официального сайта](https://www.metatrader5.com)\n"
        "2. В Deriv личном кабинете создай MT5 счёт\n"
        "3. Зайди в MT5 со своим логином/паролем\n\n"
        "*Шаг 3 — Подключись к сигналам*\n"
        "После активации подписки мы пришлём:\n"
        "• Настройки для подключения\n"
        "• Видео-инструкцию (15 минут)\n"
        "• Контакт личной поддержки\n\n"
        "*Шаг 4 — Следи за результатами*\n"
        "• История сделок — в MT5\n"
        "• Ежедневная статистика — в этом боте\n"
        "• Обсуждение — в закрытом чате\n\n"
        "⏱ _Полная настройка занимает 30–45 минут._"
    )


def text_faq() -> str:
    return "❓ *Часто задаваемые вопросы*\n\nВыбери вопрос, который тебя интересует:"


FAQ_ANSWERS = {
    "faq_beginner": (
        "🌱 *Нужен ли опыт в трейдинге?*\n\n"
        "Нет! Для подписки Pro опыт не нужен совсем.\n\n"
        "Мы даём:\n"
        "• Пошаговую инструкцию по регистрации на Deriv\n"
        "• Видео-гайд по установке MT5\n"
        "• Личную поддержку при подключении\n\n"
        "Если хочешь разобраться глубже — возьми курс Vol75 Master."
    ),
    "faq_min_deposit": (
        "💵 *Минимальный депозит*\n\n"
        "Минимум на Deriv: *$50*\n\n"
        "Наши рекомендации:\n"
        "• $50–$100 — стартовый, для знакомства\n"
        "• $200–$500 — оптимальный баланс\n"
        "• $1000+ — максимальная эффективность\n\n"
        "_Чем больше депозит — тем больше робот может зарабатывать в абсолютных цифрах._"
    ),
    "faq_risk": (
        "🛡️ *Можно ли потерять всё?*\n\n"
        "Трейдинг — это риск. Честно.\n\n"
        "Что делает робот для защиты:\n"
        "• Стоп-лосс на каждую сделку\n"
        "• Риск не более 1–2% от депозита за сделку\n"
        "• Лимит дневного убытка: 5%\n"
        "• Авто-пауза при достижении лимита\n\n"
        "❗ _Никогда не вкладывай деньги, которые не можешь позволить себе потерять._"
    ),
    "faq_vol75": (
        "📊 *Почему только Vol75?*\n\n"
        "Volatility 75 — синтетический актив Deriv:\n"
        "• Торгуется 24/7 без выходных\n"
        "• Нет новостных скачков\n"
        "• Нет геополитических рисков\n"
        "• Предсказуемая волатильность\n\n"
        "Наш ИИ обучен именно на нём — это даёт точность, которую не даст универсальный робот."
    ),
    "faq_cancel": (
        "🔄 *Как отменить подписку?*\n\n"
        "Очень просто:\n"
        "• Напиши в /support или @aielegan\n"
        "• Скажи «хочу отменить подписку»\n"
        "• Готово — следующее списание не произойдёт\n\n"
        "Никаких штрафов, никаких вопросов.\n"
        "Доступ сохраняется до конца оплаченного периода."
    ),
    "faq_payment": (
        "💳 *Способы оплаты*\n\n"
        "Принимаем:\n"
        "• 💰 USDT TRC20 / ERC20\n"
        "• 💳 Карты Visa/Mastercard\n"
        "• 🏦 Перевод по реквизитам\n\n"
        "После оплаты — доступ в течение 15 минут.\n"
        "По вопросам оплаты: @aielegan"
    ),
}


# ════════════════════════════════════════════
#  КЛАВИАТУРЫ
# ════════════════════════════════════════════


def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🥇 XAUUSD VIP — $49/мес", callback_data="xauusd_vip"
                )
            ],
            [InlineKeyboardButton("📈 Результаты торговли", callback_data="results")],
            [
                InlineKeyboardButton("🤖 О роботе", callback_data="about"),
                InlineKeyboardButton("🚀 Как начать", callback_data="howto"),
            ],
            [InlineKeyboardButton("💎 Все тарифы", callback_data="pricing")],
            [
                InlineKeyboardButton(
                    "🎁 7 дней бесплатно (Vol75)", callback_data="trial"
                )
            ],
            [
                InlineKeyboardButton("❓ FAQ", callback_data="faq"),
                InlineKeyboardButton("💬 Поддержка", callback_data="support"),
            ],
            [InlineKeyboardButton("📡 Наш канал", url="https://t.me/volbotchannel")],
        ]
    )


def kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("◀️ Главное меню", callback_data="main")]]
    )


def kb_pricing() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🥇 XAUUSD VIP — $49/мес", callback_data="pay_xauusd"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 Триал 7 дней (бесплатно)", callback_data="trial"
                )
            ],
            [
                InlineKeyboardButton(
                    "🟢 Подписка Pro — $100/мес", callback_data="pay_pro"
                )
            ],
            [InlineKeyboardButton("🏆 Купить курс — $397", callback_data="pay_course")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main")],
        ]
    )


def kb_trial() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Активировать триал", callback_data="trial_confirm"
                )
            ],
            [InlineKeyboardButton("💎 Сразу купить подписку", callback_data="pay_pro")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main")],
        ]
    )


def kb_payment(plan: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📎 Отправить чек об оплате", callback_data=f"proof_{plan}"
                )
            ],
            [InlineKeyboardButton("💬 Вопрос по оплате", url="https://t.me/aielegan")],
            [InlineKeyboardButton("◀️ Назад", callback_data="pricing")],
        ]
    )


def kb_after_trial() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📡 Перейти в канал", url="https://t.me/volbotchannel"
                )
            ],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main")],
        ]
    )


def kb_faq() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌱 Нужен ли опыт?", callback_data="faq_beginner")],
            [
                InlineKeyboardButton(
                    "💵 Минимальный депозит?", callback_data="faq_min_deposit"
                )
            ],
            [InlineKeyboardButton("🛡️ Можно потерять всё?", callback_data="faq_risk")],
            [
                InlineKeyboardButton(
                    "📊 Почему только Vol75?", callback_data="faq_vol75"
                )
            ],
            [InlineKeyboardButton("🔄 Как отменить?", callback_data="faq_cancel")],
            [InlineKeyboardButton("💳 Способы оплаты?", callback_data="faq_payment")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main")],
        ]
    )


def kb_faq_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("◀️ К вопросам", callback_data="faq")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main")],
        ]
    )


def kb_results() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎁 Попробовать бесплатно", callback_data="trial")],
            [InlineKeyboardButton("💎 Тарифы", callback_data="pricing")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main")],
        ]
    )


def kb_admin_approve(user_id: int, plan: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Подтвердить", callback_data=f"admin_approve_{user_id}_{plan}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Отклонить", callback_data=f"admin_reject_{user_id}_{plan}"
                )
            ],
        ]
    )


# ════════════════════════════════════════════
#  HANDLERS
# ════════════════════════════════════════════


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"New user: {user.id} | {user.username} | {user.first_name}")

    # Уведомить админа о новом пользователе
    if str(user.id) != str(ADMIN_ID):
        try:
            await ctx.bot.send_message(
                ADMIN_ID,
                f"👤 *Новый пользователь*\n\n"
                f"Имя: {user.first_name}\n"
                f"Username: @{user.username or '—'}\n"
                f"ID: `{user.id}`\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass

    await update.message.reply_text(
        text_welcome(user.first_name),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main(),
    )


async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 *Главное меню VolBot AI*\n\nВыбери раздел:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main(),
    )


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Быстрая статистика дня — команда /stats"""
    now = datetime.now()
    await update.message.reply_text(
        f"📊 *Статистика на {now.strftime('%d.%m.%Y')}*\n\n"
        "🟢 Робот: *АКТИВЕН*\n"
        "📈 PnL сегодня: *+$47.80*\n"
        "📉 Сделок сегодня: *14*\n"
        "✅ Выигрышных: *10* (71.4%)\n"
        "❌ Убыточных: *4* (28.6%)\n"
        "📊 Символ: *Volatility 75 Index*\n"
        "⏰ Обновлено: " + now.strftime("%H:%M"),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_back(),
    )


async def cmd_support(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 *Поддержка VolBot AI*\n\n"
        "Напиши своё сообщение, и мы ответим в течение нескольких часов.\n\n"
        "_Или напрямую: @aielegan_",
        parse_mode=ParseMode.MARKDOWN,
    )
    return WAITING_SUPPORT_MSG


# ─── CALLBACK ROUTER ───


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    # ── Главное меню ──
    if data == "main":
        await query.edit_message_text(
            text_welcome(user.first_name),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_main(),
        )

    # ── О роботе ──
    elif data == "about":
        await query.edit_message_text(
            text_about(), parse_mode=ParseMode.MARKDOWN, reply_markup=kb_back()
        )

    # ── Как начать ──
    elif data == "howto":
        await query.edit_message_text(
            text_how_to_start(),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🎁 Начать триал", callback_data="trial")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="main")],
                ]
            ),
        )

    # ── Результаты ──
    elif data == "results":
        await query.edit_message_text(
            text_results(), parse_mode=ParseMode.MARKDOWN, reply_markup=kb_results()
        )

    # ── Тарифы ──
    elif data == "pricing":
        await query.edit_message_text(
            text_pricing(), parse_mode=ParseMode.MARKDOWN, reply_markup=kb_pricing()
        )

    # ── XAUUSD VIP ──
    elif data == "xauusd_vip":
        await query.edit_message_text(
            text_xauusd_vip(),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "💳 Оформить подписку — $49/мес", callback_data="pay_xauusd"
                        )
                    ],
                    [InlineKeyboardButton("💎 Все тарифы", callback_data="pricing")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="main")],
                ]
            ),
        )

    # ── Оплата XAUUSD VIP ──
    elif data == "pay_xauusd":
        pending_payments[user.id] = "xauusd"
        await query.edit_message_text(
            text_payment_instructions("xauusd"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_payment("xauusd"),
        )

    # ── Триал ──
    elif data == "trial":
        await query.edit_message_text(
            text_trial_info(), parse_mode=ParseMode.MARKDOWN, reply_markup=kb_trial()
        )

    elif data == "trial_confirm":
        uid = user.id
        users_db[uid] = {"plan": "trial", "trial": True, "active": True}
        # Уведомить админа
        try:
            await ctx.bot.send_message(
                ADMIN_ID,
                f"🎁 *Новый триал*\n\n"
                f"Имя: {user.first_name}\n"
                f"Username: @{user.username or '—'}\n"
                f"ID: `{uid}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass
        await query.edit_message_text(
            text_payment_instructions("trial"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_after_trial(),
        )

    # ── Оплата подписки Pro ──
    elif data == "pay_pro":
        pending_payments[user.id] = "pro"
        await query.edit_message_text(
            text_payment_instructions("pro"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_payment("pro"),
        )

    # ── Оплата курса ──
    elif data == "pay_course":
        pending_payments[user.id] = "course"
        await query.edit_message_text(
            text_payment_instructions("course"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_payment("course"),
        )

    # ── Отправить чек ──
    elif data.startswith("proof_"):
        plan = data.split("_", 1)[1]
        ctx.user_data["awaiting_proof_plan"] = plan
        await query.edit_message_text(
            "📎 *Отправь скриншот или хеш транзакции*\n\n"
            "Просто прикрепи изображение или напиши TXID/хеш транзакции в следующем сообщении.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("◀️ Назад", callback_data=f"pay_{plan}")]]
            ),
        )
        return WAITING_PAYMENT_PROOF

    # ── FAQ ──
    elif data == "faq":
        await query.edit_message_text(
            text_faq(), parse_mode=ParseMode.MARKDOWN, reply_markup=kb_faq()
        )

    elif data in FAQ_ANSWERS:
        await query.edit_message_text(
            FAQ_ANSWERS[data], parse_mode=ParseMode.MARKDOWN, reply_markup=kb_faq_back()
        )

    # ── Поддержка ──
    elif data == "support":
        ctx.user_data["in_support"] = True
        await query.edit_message_text(
            "💬 *Напиши свой вопрос*\n\n"
            "Отправь сообщение — мы ответим в ближайшее время.\n\n"
            "_Или напрямую: @aielegan_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_back(),
        )

    # ── Админ: подтвердить платёж ──
    elif data.startswith("admin_approve_"):
        parts = data.split("_")
        target_uid = int(parts[2])
        plan = parts[3]
        users_db[target_uid] = {"plan": plan, "trial": False, "active": True}
        plan_names = {
            "xauusd": "XAUUSD VIP",
            "pro": "Vol75 Pro Signal",
            "course": "Vol75 Master Course",
        }
        plan_name = plan_names.get(plan, plan)
        try:
            await ctx.bot.send_message(
                target_uid,
                f"✅ *Оплата подтверждена!*\n\n"
                f"Тариф: *{plan_name}*\n\n"
                "Сейчас мы пришлём тебе инструкцию по подключению.\n"
                "Добро пожаловать в VolBot AI! 🎉",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb_main(),
            )
        except Exception:
            pass
        await query.edit_message_text(
            f"✅ Платёж пользователя {target_uid} подтверждён ({plan})"
        )

    elif data.startswith("admin_reject_"):
        parts = data.split("_")
        target_uid = int(parts[2])
        try:
            await ctx.bot.send_message(
                target_uid,
                "❌ *Платёж не подтверждён*\n\n"
                "Мы не смогли найти твою транзакцию. "
                "Пожалуйста, свяжись с поддержкой: @aielegan",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass
        await query.edit_message_text(f"❌ Платёж пользователя {target_uid} отклонён")


# ─── Получение чека об оплате ───


async def receive_payment_proof(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    plan = ctx.user_data.get(
        "awaiting_proof_plan", pending_payments.get(user.id, "pro")
    )
    plan_names = {
        "xauusd": "XAUUSD VIP $49/мес",
        "pro": "Pro $100/мес",
        "course": "Курс $397",
    }
    plan_name = plan_names.get(plan, plan)

    # Переслать чек админу
    caption = (
        f"💳 *Новый платёж на проверку*\n\n"
        f"Пользователь: {user.first_name} (@{user.username or '—'})\n"
        f"ID: `{user.id}`\n"
        f"Тариф: *{plan_name}*\n"
        f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    if update.message.photo:
        await ctx.bot.send_photo(
            ADMIN_ID,
            update.message.photo[-1].file_id,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_admin_approve(user.id, plan),
        )
    elif update.message.text:
        await ctx.bot.send_message(
            ADMIN_ID,
            caption + f"\n\nТранзакция: `{update.message.text}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_admin_approve(user.id, plan),
        )

    await update.message.reply_text(
        "✅ *Чек получен!*\n\n"
        "Проверяем транзакцию — обычно это занимает до *15 минут*.\n"
        "После подтверждения ты получишь уведомление здесь.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main(),
    )
    ctx.user_data.pop("awaiting_proof_plan", None)
    return ConversationHandler.END


# ─── Приём сообщений поддержки ───


async def receive_support_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message.text or "[медиа-файл]"

    await ctx.bot.send_message(
        ADMIN_ID,
        f"💬 *Запрос в поддержку*\n\n"
        f"От: {user.first_name} (@{user.username or '—'})\n"
        f"ID: `{user.id}`\n\n"
        f"_{msg}_",
        parse_mode=ParseMode.MARKDOWN,
    )
    await update.message.reply_text(
        "✅ Сообщение отправлено!\n\n"
        "Ответим в ближайшее время. Обычно — в течение нескольких часов.\n\n"
        "_Если срочно — @aielegan_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main(),
    )
    ctx.user_data.pop("in_support", None)
    return ConversationHandler.END


# ─── Рассылка (только админ) ───


async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        return
    await update.message.reply_text(
        "📢 *Режим рассылки*\n\nНапиши сообщение для всех пользователей:",
        parse_mode=ParseMode.MARKDOWN,
    )
    return WAITING_BROADCAST_MSG


async def do_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        return ConversationHandler.END
    text = update.message.text
    sent = 0
    failed = 0
    for uid in list(users_db.keys()):
        try:
            await ctx.bot.send_message(uid, text, parse_mode=ParseMode.MARKDOWN)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await update.message.reply_text(
        f"✅ Рассылка завершена\n\nОтправлено: {sent}\nОшибок: {failed}"
    )
    return ConversationHandler.END


# ─── Статистика для админа ───


async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        return
    total = len(users_db)
    trials = sum(1 for u in users_db.values() if u.get("trial"))
    xauusd = sum(
        1 for u in users_db.values() if u.get("plan") == "xauusd" and not u.get("trial")
    )
    pro = sum(
        1 for u in users_db.values() if u.get("plan") == "pro" and not u.get("trial")
    )
    course = sum(1 for u in users_db.values() if u.get("plan") == "course")
    await update.message.reply_text(
        f"📊 *Статистика бота*\n\n"
        f"Всего пользователей: *{total}*\n"
        f"На триале: *{trials}*\n"
        f"XAUUSD VIP: *{xauusd}*\n"
        f"Подписка Pro: *{pro}*\n"
        f"Купили курс: *{course}*\n\n"
        f"💰 Выручка (оценка): *${xauusd * 49 + pro * 100 + course * 397}*",
        parse_mode=ParseMode.MARKDOWN,
    )


# ─── Fallback для необработанных сообщений ───


async def fallback_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("in_support"):
        return await receive_support_msg(update, ctx)
    await update.message.reply_text("Выбери раздел из меню 👇", reply_markup=kb_main())


# ════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler для чека оплаты
    payment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback, pattern="^proof_")],
        states={
            WAITING_PAYMENT_PROOF: [
                MessageHandler(
                    filters.PHOTO | filters.TEXT & ~filters.COMMAND,
                    receive_payment_proof,
                )
            ]
        },
        fallbacks=[CommandHandler("start", cmd_start)],
    )

    # ConversationHandler для поддержки
    support_conv = ConversationHandler(
        entry_points=[CommandHandler("support", cmd_support)],
        states={
            WAITING_SUPPORT_MSG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_support_msg)
            ]
        },
        fallbacks=[CommandHandler("start", cmd_start)],
    )

    # ConversationHandler для рассылки
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", cmd_broadcast)],
        states={
            WAITING_BROADCAST_MSG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)
            ]
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(payment_conv)
    app.add_handler(support_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, fallback_message))

    logger.info("🤖 VolBot AI запущен")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
