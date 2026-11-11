import asyncio
import random
import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "9007446269:AAHS11dx4OuNjYLZt6bTp9vwhb1Jufo2_Qw"
ADMIN_ID = 7510323045

# Папка для данных на Bothost (она там точно есть)
DATA_DIR = "/app/data"
DB_FILE = os.path.join(DATA_DIR, "users.json")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- РАБОТА С БАЗОЙ ---
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_db(data):
    try:
        # Если папки нет, создаем её
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"ОШИБКА СОХРАНЕНИЯ: {e}") # Если не сохранится, мы увидим это в логах

def draw_bar(value):
    if value >= 70: color = "🟩"
    elif value >= 40: color = "🟨"
    else: color = "🟥"
    filled = int(value // 10)
    return f"{color * filled}{'⬜' * (10 - filled)} {value}%"

class CreatePet(StatesGroup):
    name = State()
    photo = State()
    char = State()

def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🍔 Покормить"), KeyboardButton(text="💧 Попить")],
        [KeyboardButton(text="🛌 Поспать"), KeyboardButton(text="🎾 Поиграть")],
        [KeyboardButton(text="📊 Профиль"), KeyboardButton(text="💬 Поговорить")],
        [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="🎒 Инвентарь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    users = load_db()
    uid = str(message.from_user.id)
    
    if uid in users:
        await message.answer(f"С возвращением! {users[uid]['pet_name']} скучал.\n🪙 Монеты: {users[uid]['coins']}", reply_markup=get_main_keyboard())
        return

    await message.answer("⚠️ Внимание! Персонаж создается навсегда!")
    await message.answer("Шаг 1. Введи имя для персонажа:")
    await state.set_state(CreatePet.name)

@dp.message(CreatePet.name)
async def process_name(message: Message, state: FSMContext):
    if len(message.text) > 15: return await message.answer("Максимум 15 символов.")
    await state.update_data(name=message.text)
    await message.answer("Шаг 2. Отправь фото:")
    await state.set_state(CreatePet.photo)

@dp.message(CreatePet.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥰 Милый", callback_data="char_cute")], 
        [InlineKeyboardButton(text="😈 Вредный", callback_data="char_rude")],
        [InlineKeyboardButton(text="🧠 Умный", callback_data="char_smart")], 
        [InlineKeyboardButton(text="🤪 Безумный", callback_data="char_crazy")]
    ])
    await message.answer("Шаг 3. Выбери характер:", reply_markup=kb)
    await state.set_state(CreatePet.char)

@dp.callback_query(CreatePet.char, F.data.startswith("char_"))
async def process_char(call: CallbackQuery, state: FSMContext):
    char = call.data.replace("char_", "")
    data = await state.get_data()
    users = load_db()
    users[str(call.from_user.id)] = {
        "pet_name": data['name'], "pet_photo": data['photo'], "pet_char": char,
        "age": 0, "hunger": 100, "thirst": 100, "energy": 100, "mood": 100, "coins": 100
    }
    save_db(users)
    await state.clear()
    await call.message.answer("🎉 Персонаж создан!", reply_markup=get_main_keyboard())
    await call.answer()

# --- ДЕЙСТВИЯ ---
@dp.message(F.text == "🍔 Покормить")
async def feed_pet(message: Message):
    users = load_db()
    uid = str(message.from_user.id)
    if uid not in users: return
    users[uid]['hunger'] = min(100, users[uid]['hunger'] + 20)
    save_db(users)
    await message.answer(f"🍔 Ты покормил {users[uid]['pet_name']}!\nСытость: {draw_bar(users[uid]['hunger'])}\n🪙 Монеты: {users[uid]['coins']}")

@dp.message(F.text == "💧 Попить")
async def water_pet(message: Message):
    users = load_db()
    uid = str(message.from_user.id)
    if uid not in users: return
    users[uid]['thirst'] = min(100, users[uid]['thirst'] + 20)
    save_db(users)
    await message.answer(f"💧 {users[uid]['pet_name']} попил!\nЖажда: {draw_bar(users[uid]['thirst'])}\n🪙 Монеты: {users[uid]['coins']}")

@dp.message(F.text == "🛌 Поспать")
async def sleep_pet(message: Message):
    users = load_db()
    uid = str(message.from_user.id)
    if uid not in users: return
    users[uid]['energy'] = min(100, users[uid]['energy'] + 30)
    save_db(users)
    await message.answer(f"⚡ {users[uid]['pet_name']} поспал!\nЭнергия: {draw_bar(users[uid]['energy'])}")

@dp.message(F.text == "🎾 Поиграть")
async def play_pet(message: Message):
    users = load_db()
    uid = str(message.from_user.id)
    if uid not in users: return
    users[uid]['mood'] = min(100, users[uid]['mood'] + 20)
    save_db(users)
    await message.answer(f"🎾 Ты поиграл!\nНастроение: {draw_bar(users[uid]['mood'])}\n🪙 Монеты: {users[uid]['coins']}")

@dp.message(F.text == "💬 Поговорить")
async def talk_to_pet(message: Message):
    users = load_db()
    uid = str(message.from_user.id)
    if uid not in users: return
    
    char = users[uid]['pet_char']
    if char == "cute":
        phrases = ["Ты самый лучший! 🤍", "Я тебя обнимаю! 🤗", "Спасибо, что ты рядом! ✨", "Ты мое солнышко ☀️"]
    elif char == "rude":
        phrases = ["Че пристал? 😒", "Дай поспать! 😤", "Опять ты? 🙄", "Иди лучше поиграй!"]
    elif char == "smart":
        phrases = ["У осьминога 3 сердца! 🧠", "Медведи бегают 50 км/ч! 🤓", "Знаешь про 10% мозга? 🧐", "Вода кипит при 100 градусах! 📚"]
    else:
        phrases = ["ААА! БАНАНЫ! 🤪", "Я умею летать! 🚀", "ДАВАЙ ЧАЮ! 😳", "Я инопланетянин! 👽"]
        
    await message.answer(f"💬 {users[uid]['pet_name']}: «{random.choice(phrases)}»")

@dp.message(F.text == "📊 Профиль")
async def show_profile(message: Message):
    users = load_db()
    uid = str(message.from_user.id)
    if uid not in users: return
    u = users[uid]
    text = f"📊 **Профиль**\n\n👤 **Имя:** {u['pet_name']}\n🎭 **Характер:** {u['pet_char']}\n🪙 **Монеты:** {u['coins']}\n\n🍔 Сытость: {draw_bar(u['hunger'])}\n💧 Жажда: {draw_bar(u['thirst'])}\n⚡ Энергия: {draw_bar(u['energy'])}\n🎾 Настроение: {draw_bar(u['mood'])}"
    await message.answer_photo(photo=u['pet_photo'], caption=text, parse_mode="Markdown")

@dp.message(F.text == "🛒 Магазин")
async def shop_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍎 Яблоко (20🪙)", callback_data="buy_apple")],
        [InlineKeyboardButton(text="🥛 Вода (10🪙)", callback_data="buy_water")],
        [InlineKeyboardButton(text="⚽ Мячик (80🪙)", callback_data="buy_ball")]
    ])
    await message.answer("🛒 **Магазин**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_item(call: CallbackQuery):
    users = load_db()
    uid = str(call.from_user.id)
    if uid not in users: return
    item = call.data.replace("buy_", "")
    prices = {"apple": 20, "water": 10, "ball": 80}
    price = prices.get(item, 0)
    
    if users[uid]['coins'] < price: return await call.answer("Мало монет!", show_alert=True)
    
    users[uid]['coins'] -= price
    if item == "apple": users[uid]['hunger'] = min(100, users[uid]['hunger'] + 15)
    elif item == "water": users[uid]['thirst'] = min(100, users[uid]['thirst'] + 20)
    elif item == "ball": users[uid]['mood'] = min(100, users[uid]['mood'] + 30)
    
    save_db(users)
    await call.message.answer(f"✅ Куплено! Остаток: {users[uid]['coins']} 🪙")
    await call.answer()

@dp.message(F.text == "🎒 Инвентарь")
async def inventory(message: Message):
    await message.answer("🎒 Твой инвентарь пока пуст. Покупай вещи в магазине!")

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID: return
    users = load_db()
    if not users: return await message.answer("Игроков нет.")
    kb_buttons = [[InlineKeyboardButton(text=f"{d['pet_name']} | 🪙 {d['coins']}", callback_data=f"adm_{u}")] for u, d in users.items()]
    await message.answer("👑 **Админка**", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))

@dp.callback_query(F.data.startswith("adm_"))
async def admin_user(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    target = call.data.replace("adm_", "")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="+ 100 🪙", callback_data=f"gv_{target}_100")],
        [InlineKeyboardButton(text="+ 500 🪙", callback_data=f"gv_{target}_500")]
    ])
    await call.message.edit_text(f"Выбери сумму:", reply_markup=kb)

@dp.callback_query(F.data.startswith("gv_"))
async def admin_give(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    parts = call.data.split("_")
    target, amount = parts[1], int(parts[2])
    users = load_db()
    if target in users:
        users[target]['coins'] += amount
        save_db(users)
        await call.answer(f"✅ Выдано {amount} монет!")
        try: await bot.send_message(int(target), f"🎁 Вам переслано {amount} 🪙!")
        except: pass
        await admin_panel(call.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
