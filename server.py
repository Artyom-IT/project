"""Сервер Telegram бота, запускаемый непосредственно"""
import logging
import os

import aiohttp
from aiogram import Bot, Dispatcher, executor, types

import exceptions
import expenses
from categories import Categories
from aiogram.utils.executor import start_webhook
from middlewares import AccessMiddleware

logging.basicConfig(level=logging.INFO)

API_TOKEN = "1623533586:AAGXBlQQb9w7Li-tUj1jtMQTY9aAewRAq5o"
# PROXY_URL = os.getenv("TELEGRAM_PROXY_URL")
# ACCESS_ID = "709563692"
PROJECT_NAME = "nameless-crag-55434"
WEBHOOK_HOST = f"https://{PROJECT_NAME}.herokuapp.com"
WEBHOOK_PATH = "/webhook/" + API_TOKEN
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT"))

print(API_TOKEN)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# dp.middleware.setup(AccessMiddleware(ACCESS_ID))


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """Отправляет приветственное сообщение и помощь по боту"""
    await message.answer(
        "Бот для учёта финансов\n\n"
        "Добавить расход: 250 такси\n"
        "Сегодняшняя статистика: /today\n"
        "За текущий месяц: /month\n"
        "Последние внесённые расходы: /expenses\n"
        "Категории трат: /categories")


async def on_startup():
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown():
    logging.warning("Shutting down..")
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bot down")


@dp.message_handler(lambda message: message.text.startswith('/del'))
async def del_expense(message: types.Message):
    """Удаляет одну запись о расходе по её идентификатору"""
    row_id = int(message.text[4:])
    expenses.delete_expense(row_id)
    answer_message = "Удалил"
    await message.answer(answer_message)


@dp.message_handler(commands=['categories'])
async def categories_list(message: types.Message):
    """Отправляет список категорий расходов"""
    categories = Categories().get_all_categories()
    answer_message = "Категории трат:\n\n* " + \
                     ("\n* ".join([c.name + ' (' + ", ".join(c.aliases) + ')' for c in categories]))
    await message.answer(answer_message)


@dp.message_handler(commands=['today'])
async def today_statistics(message: types.Message):
    """Отправляет сегодняшнюю статистику трат"""
    answer_message = expenses.get_today_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['month'])
async def month_statistics(message: types.Message):
    """Отправляет статистику трат текущего месяца"""
    answer_message = expenses.get_month_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['expenses'])
async def list_expenses(message: types.Message):
    """Отправляет последние несколько записей о расходах"""
    last_expenses = expenses.last()
    if not last_expenses:
        await message.answer("Расходы ещё не заведены")
        return

    last_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name} — нажми "
        f"/del{expense.id} для удаления"
        for expense in last_expenses]
    answer_message = "Последние сохранённые траты:\n\n* " + "\n\n* " \
        .join(last_expenses_rows)
    await message.answer(answer_message)


@dp.message_handler()
async def add_expense(message: types.Message):
    """Добавляет новый расход"""
    try:
        expense = expenses.add_expense(message.text)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f"Добавлены траты {expense.amount} руб на {expense.category_name}.\n\n"
        f"{expenses.get_today_statistics()}")
    await message.answer(answer_message)


if __name__ == "__main__":
    if "HEROKU" in list(os.environ.keys()):
        print("MAYBE WORKS")
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
    else:
        print("DONT")
        executor.start_polling(dp)
