# main.py
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
# Импортируем наши переменные из файла config.py
from config import TELEGRAM_TOKEN, RENTPROG_API_KEY

# НАСТРОЙКА API
RENTPROG_API_URL = 'https://rentprog.ru/api/v1/vehicles'

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(_name_)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_message = (
        f"Здравствуйте, {user.first_name}!\n\n"
        "Я бот компании RentGo. Я помогу вам узнать, какие автомобили сейчас свободны.\n\n"
        "Используйте команду /cars, чтобы получить список доступных авто."
    )
    await update.message.reply_text(welcome_message)

async def get_cars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔍 Ищу автомобили в базе RentGo, пожалуйста, подождите...")

    params = {'api_key': RENTPROG_API_KEY}

    try:
        response = requests.get(RENTPROG_API_URL, params=params, timeout=15)
        response.raise_for_status()

        response_data = response.json()
        cars_list = response_data.get('data')

        if not cars_list:
            await update.message.reply_text("😔 К сожалению, сейчас свободных автомобилей нет или они не найдены в базе.")
            return

        await update.message.reply_text(f"✅ Найдено доступных автомобилей: {len(cars_list)}")

        for car in cars_list:
            mark = car.get('mark', 'Бренд не указан')
            model = car.get('model', 'Модель не указана')
            year = car.get('year', '')
            price = car.get('price', '??')

            car_info = (
                f"<b>{mark} {model}</b> ({year} г.)\n\n"
                f"Статус: {car.get('status', {}).get('name', 'неизвестен')}\n"
                f"Стоимость в сутки: <b>{price} ₽</b>"
            )

            photo_url = None
            photos = car.get('photos')
            if photos and len(photos) > 0:
                photo_url = photos[0].get('url')

            if photo_url:
                await update.message.reply_photo(photo=photo_url, caption=car_info, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(text=car_info, parse_mode=ParseMode.HTML)

    except requests.exceptions.HTTPError as e:
        logger.error(f"ОШИБКА HTTP: {e}")
        await update.message.reply_text(f"❌ Сервер ответил с ошибкой: {e.response.status_code} {e.response.reason}.")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        await update.message.reply_text("❌ Что-то пошло не так.")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cars", get_cars))

    print("Бот запущен...")
    application.run_polling()

if _name_ == '_main_':
    main()
