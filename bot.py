import asyncio
import random
import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9007446269:AAHS11dx4OuNjYLZt6bTp9vwhb1Jufo2_Qw"
ADMIN_ID = 7510323045
DATA_DIR = "/app/data"
DB_FILE = os.path.join(DATA_DIR, "users.json")
TZ = ZoneInfo("Asia/Yekaterinburg") 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- АНТИСПАМ ---
last_click = {}
def is_spam(user_id):
    now = time.time()
    if user_id in last_click:
        if now - last_click[user_id] < 0.5: return True
    last_click[user_id] = now
    return False

# --- БАЗА ДАННЫХ ---
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_db(data):
    try:
        if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR, exist_ok=True)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"ОШИБКА СОХРАНЕНИЯ: {e}")

def draw_bar(value):
    if value >= 70: color = "🟩"
    elif value >= 40: color = "🟨"
    else: color = "🟥"
    filled = int(value // 10)
    return f"{color * filled}{'⬜' * (10 - filled)} {value}%"

# --- СОСТОЯНИЯ ---
class CreatePet(StatesGroup):
    name = State()
    photo = State()
    char = State()

class AdminState(StatesGroup):
    waiting_for_amount = State()
    target_id = State()

def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🍔 Покормить"), KeyboardButton(text="💧 Попить")],
        [KeyboardButton(text="🛌 Поспать"), KeyboardButton(text="🎾 Поиграть")],
        [KeyboardButton(text="📊 Профиль"), KeyboardButton(text="💬 Поговорить")],
        [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="🎁 Ежедневный бонус")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ОГРОМНЫЙ АССОРТИМЕНТ (с реакциями) ---
SHOP_ITEMS = {
    "apple": {"name": "🍎 Яблоко", "price": 15, "effect": "hunger", "value": 10, "reaction": "Хрум-хрум! Сочное яблочко! 🍎"},
    "burger": {"name": "🍔 Бургер", "price": 40, "effect": "hunger", "value": 30, "reaction": "Ммм, бургер! Обожаю фастфуд! 🍔"},
    "pizza": {"name": "🍕 Пицца", "price": 80, "effect": "hunger", "value": 50, "reaction": "Пицца! С сыром! Это лучший день! 🍕"},
    "sushi": {"name": "🍣 Суши", "price": 100, "effect": "hunger", "value": 60, "reaction": "Васаби щиплет нос, но как вкусно! 🍣"},
    "taco": {"name": "🌮 Тако", "price": 50, "effect": "hunger", "value": 35, "reaction": "Острый соус! Оле! 🌮"},
    "donut": {"name": "🍩 Пончик", "price": 25, "effect": "hunger", "value": 15, "reaction": "Сладкий пончик! Пальчики оближешь! 🍩"},
    "steak": {"name": "🥩 Стейк", "price": 150, "effect": "hunger", "value": 80, "reaction": "Мясо! Я чувствую себя хищником! 🥩"},
    "salad": {"name": "🥗 Салат", "price": 30, "effect": "hunger", "value": 20, "reaction": "Полезно! Я буду здоровым! 🥗"},
    "cake": {"name": "🍰 Тортик", "price": 60, "effect": "hunger", "value": 40, "reaction": "Сладкий тортик! Я на вершине блаженства! 🍰"},
    "chocolate": {"name": "🍫 Шоколад", "price": 20, "effect": "hunger", "value": 10, "reaction": "Шоколад! Гормон счастья! 🍫"},
    "water": {"name": "🥛 Вода", "price": 10, "effect": "thirst", "value": 15, "reaction": "Водичка! Освежает! 💧"},
    "cola": {"name": "🥤 Кола", "price": 25, "effect": "thirst", "value": 25, "reaction": "Кола! Пузырьки в носу! 🥤"},
    "pepsi": {"name": "🥤 Пепси", "price": 25, "effect": "thirst", "value": 25, "reaction": "Пепси! Классика! 🥤"},
    "juice": {"name": "🧃 Сок", "price": 30, "effect": "thirst", "value": 30, "reaction": "Сок! Витамины! 🧃"},
    "coffee": {"name": "☕ Кофе", "price": 40, "effect": "thirst", "value": 20, "reaction": "Кофе! Я проснулся! ☕"},
    "tea": {"name": "🍵 Чай", "price": 20, "effect": "thirst", "value": 15, "reaction": "Чай! Уютно! 🍵"},
    "energy": {"name": "⚡ Энергетик", "price": 50, "effect": "thirst", "value": 50, "reaction": "Энергетик! Я готов свернуть горы! ⚡"},
    "milkshake": {"name": "🥤 Милкшейк", "price": 60, "effect": "thirst", "value": 40, "reaction": "Молочный коктейль! Ням! 🥤"},
    "lemonade": {"name": "🍋 Лимонад", "price": 35, "effect": "thirst", "value": 30, "reaction": "Лимонад! Кисло-сладко! 🍋"},
    "smoothie": {"name": "🍹 Смузи", "price": 70, "effect": "thirst", "value": 45, "reaction": "Смузи! Это полезно! 🍹"},
    "pill": {"name": "💊 Таблетка", "price": 100, "effect": "heal", "value": 1, "reaction": "Тьфу, горькая! Но теперь я здоров! 💊"},
    "bandage": {"name": "🩹 Бинт", "price": 50, "effect": "heal", "value": 1, "reaction": "Бинт! Замотали лапку! 🩹"},
    "syrup": {"name": "🧪 Сироп", "price": 80, "effect": "heal", "value": 1, "reaction": "Сироп от кашля! Сладенький! 🧪"},
    "vitamins": {"name": "💊 Витамины", "price": 120, "effect": "heal", "value": 1, "reaction": "Витаминки! Теперь я точно не заболею! 💊"},
    "soap": {"name": "🧼 Мыло", "price": 40, "effect": "wash", "value": 1, "reaction": "Мыло! Я теперь чистый и пахну приятно! 🧼"},
    "pillow": {"name": "🛏 Подушка", "price": 100, "effect": "energy", "value": 30, "reaction": "Подушка! Мягкая, как облачко! 🛏"},
    "blanket": {"name": "🛌 Одеяло", "price": 200, "effect": "energy", "value": 50, "reaction": "Одеяло! Так тепло и уютно! 🛌"},
    "bed": {"name": "🛏 Кровать", "price": 500, "effect": "energy", "value": 100, "reaction": "Кровать! Я хочу спать тут вечно! 🛏"},
    "lamp": {"name": "💡 Лампа", "price": 150, "effect": "energy", "value": 20, "reaction": "Светло! Теперь не страшно! 💡"},
    "chair": {"name": "🪑 Кресло", "price": 300, "effect": "energy", "value": 40, "reaction": "Кресло! Удобно! 🪑"},
    "ball": {"name": "⚽ Мячик", "price": 70, "effect": "mood", "value": 25, "reaction": "Мячик! Гав! Давай играть! ⚽"},
    "toy": {"name": "🧸 Игрушка", "price": 120, "effect": "mood", "value": 40, "reaction": "Игрушка! Моя любимая! 🧸"},
    "game": {"name": "🎮 Игра", "price": 300, "effect": "mood", "value": 70, "reaction": "Игра! Я выиграл! 🎮"},
    "book": {"name": "📚 Книга", "price": 150, "effect": "mood", "value": 30, "reaction": "Книга! Как интересно! 📚"},
    "guitar": {"name": "🎸 Гитара", "price": 400, "effect": "mood", "value": 80, "reaction": "Гитара! Ля-ля-ля! 🎸"},
    "movie": {"name": "🎬 Фильм", "price": 200, "effect": "mood", "value": 50, "reaction": "Фильм! Какой сюжет! 🎬"},
    "vr": {"name": "🕶 VR-очки", "price": 800, "effect": "mood", "value": 100, "reaction": "VR! Я в другом мире! 🕶"},
    "beer": {"name": "🍺 Пиво", "price": 60, "effect": "mood", "value": 20, "reaction": "Пиво! Хи-хи, я немного опьянел! 🍺"},
    "wine": {"name": "🍷 Вино", "price": 150, "effect": "mood", "value": 35, "reaction": "Вино! Ах, какой букет! 🍷"},
    "vodka": {"name": "🥃 Водка", "price": 200, "effect": "mood", "value": 50, "reaction": "Водка! Ой, голова кружится! 🥃"},
    "whiskey": {"name": "🥃 Виски", "price": 300, "effect": "mood", "value": 60, "reaction": "Виски! Я чувствую себя аристократом! 🥃"},
    "champagne": {"name": "🍾 Шампанское", "price": 500, "effect": "mood", "value": 80, "reaction": "Шампанское! Ура! 🍾"},
    "mojito": {"name": "🍹 Мохито", "price": 250, "effect": "mood", "value": 45, "reaction": "Мохито! С мятой! 🍹"},
    "cocktail": {"name": "🍸 Коктейль", "price": 220, "effect": "mood", "value": 40, "reaction": "Коктейль! Танцую! 🍸"},
    "sake": {"name": "🍶 Саке", "price": 180, "effect": "mood", "value": 35, "reaction": "Саке! Конничива! 🍶"},
}

# --- ФОНОВАЯ ЗАДАЧА (Падение шкал и уведомления) ---
async def background_worker():
    while True:
        try:
            now = datetime.now(TZ)
            # Ночной режим с 23:00 до 08:00
            if now.hour >= 23 or now.hour < 8:
                await asyncio.sleep(1800)
                continue

            users = load_db()
            current_time = int(time.time())
            changed = False
            
            for uid_str, user in users.items():
                # Если персонаж мертв, пропускаем
                if user.get('is_dead'): continue
                
                last_upd = user.get('last_update', current_time)
                elapsed_mins = (current_time - last_upd) / 60
                drop = int(elapsed_mins / 5) # 1% каждые 5 минут
                
                if drop > 0:
                    user['hunger'] = max(0, user['hunger'] - drop)
                    user['thirst'] = max(0, user['thirst'] - drop)
                    user['energy'] = max(0, user['energy'] - drop)
                    user['mood'] = max(0, user['mood'] - drop)
                    user['last_update'] = current_time
                    changed = True
                    
                    # Если голод или жажда на нуле - персонаж умирает
                    if user['hunger'] == 0 or user['thirst'] == 0:
                        user['is_dead'] = True
                        try: await bot.send_message(int(uid_str), f"💀 {user['pet_name']} не выдержал... Он умер от истощения.")
                        except: pass
                        continue
                        
                    # Уведомление, если голоден
                    if user['hunger'] < 30 or user['thirst'] < 30:
                        try:
                            await bot.send_message(int(uid_str), f"⚠️ {user['pet_name']} голоден!\n🍔 Сытость: {user['hunger']}%\n💧 Жажда: {user['thirst']}%")
                        except: pass
            
            if changed: save_db(users)
        except Exception as e:
            print(f"Ошибка фона: {e}")
        await asyncio.sleep(900) # Проверка раз в 15 минут

# --- СТАРТ И СОЗДАНИЕ ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    users = load_db()
    uid = str(message.from_user.id)
    
    if uid in users:
        if users[uid].get('is_dead'):
            await message.answer(f"💀 {users[uid]['pet_name']} покинул этот мир. Напиши /start заново, чтобы создать нового.", reply_markup=get_main_keyboard())
            return
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
        "hunger": 100, "thirst": 100, "energy": 100, "mood": 100, "coins": 500,
        "inventory": {}, "last_bonus": 0, "birth_date": int(time.time()), "last_age": 0,
        "last_update": int(time.time()), "is_dead": False
    }
    save_db(users)
    await state.clear()
    await message.answer("🎉 Персонаж создан!", reply_markup=get_main_keyboard())
    await call.answer()

# --- ДЕЙСТВИЯ ---
async def sleep_timer(user_id, pet_name):
    await asyncio.sleep(60)
    users = load_db()
    uid = str(user_id)
    if uid in users:
        users[uid]['energy'] = min(100, users[uid]['energy'] + 60)
        users[uid]['last_update'] = int(time.time())
        save_db(users)
        try: await bot.send_message(user_id, f"☀️ {pet_name} проснулся!\n⚡ Энергия: {draw_bar(users[uid]['energy'])}", reply_markup=get_main_keyboard())
        except: pass

@dp.message(F.text == "🍔 Покормить")
async def feed_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    users[uid]['hunger'] = min(100, users[uid]['hunger'] + 20)
    users[uid]['last_update'] = int(time.time())
    users[uid]['coins'] += 5
    save_db(users)
    await message.answer(f"🍔 Ты покормил {users[uid]['pet_name']}!\nСытость: {draw_bar(users[uid]['hunger'])}\n🪙 +5 монет")

@dp.message(F.text == "💧 Попить")
async def water_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    users[uid]['thirst'] = min(100, users[uid]['thirst'] + 20)
    users[uid]['last_update'] = int(time.time())
    users[uid]['coins'] += 5
    save_db(users)
    await message.answer(f"💧 {users[uid]['pet_name']} попил!\nЖажда: {draw_bar(users[uid]['thirst'])}\n🪙 +5 монет")

@dp.message(F.text == "🛌 Поспать")
async def sleep_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['energy'] > 80:
        return await message.answer(f"☀️ {users[uid]['pet_name']} не хочет спать, он полон сил!")
    await message.answer(f"🛌 {users[uid]['pet_name']} лег спать. Проснется через 1 минуту ⏱")
    asyncio.create_task(sleep_timer(message.from_user.id, users[uid]['pet_name']))

@dp.message(F.text == "🎾 Поиграть")
async def play_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    users[uid]['mood'] = min(100, users[uid]['mood'] + 20)
    users[uid]['last_update'] = int(time.time())
    users[uid]['coins'] += 5
    bonus = ""
    if random.random() < 0.2:
        users[uid]['coins'] += 50; bonus = "\n🎉 Бонус! Нашел 50 монет!"
    save_db(users)
    await message.answer(f"🎾 Ты поиграл!\nНастроение: {draw_bar(users[uid]['mood'])}\n🪙 +5 монет{bonus}")

@dp.message(F.text == "💬 Поговорить")
async def talk_to_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    
    # Если голоден, жалуется
    if users[uid]['hunger'] < 30: return await message.answer(f"🍔 {users[uid]['pet_name']}: «Я очень голоден... Покорми меня».")
    if users[uid]['thirst'] < 30: return await message.answer(f"💧 {users[uid]['pet_name']}: «Я хочу пить...»")
    
    char = users[uid]['pet_char']
    if char == "cute": p = ["Ты лучший! 🤍", "Обнимаю! 🤗", "Спасибо, что ты рядом! ✨", "Ты мое солнышко ☀️"]
    elif char == "rude": p = ["Че пристал? 😒", "Дай поспать! 😤", "Опять ты? 🙄", "Иди играй!"]
    elif char == "smart": p = ["У осьминога 3 сердца! 🧠", "Медведи бегают 50 км/ч! 🤓", "Вода кипит при 100°C! 📚"]
    else: p = ["ААА! БАНАНЫ! 🤪", "Я умею летать! 🚀", "ДАВАЙ ЧАЮ! 😳", "Я инопланетянин! 👽"]
    await message.answer(f"💬 {users[uid]['pet_name']}: «{random.choice(p)}»")

@dp.message(F.text == "📊 Профиль")
async def show_profile(message: Message):
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users: return
    u = users[uid]
    
    # Считаем возраст
    birth = u.get('birth_date', int(time.time()))
    days_passed = (time.time() - birth) / 86400
    age = int(days_passed / 2)
    
    text = f"📊 **Профиль**\n\n👤 **Имя:** {u['pet_name']}\n🎭 **Характер:** {u['pet_char']}\n🎂 **Возраст:** {age} лет\n🪙 **Монеты:** {u['coins']}\n\n"
    if u.get('is_dead'): text += "💀 **СТАТУС: МЕРТВ**\n\n"
    
    text += f"🍔 Сытость: {draw_bar(u['hunger'])}\n💧 Жажда: {draw_bar(u['thirst'])}\n⚡ Энергия: {draw_bar(u['energy'])}\n🎾 Настроение: {draw_bar(u['mood'])}"
    await message.answer_photo(photo=u['pet_photo'], caption=text, parse_mode="Markdown")

@dp.message(F.text == "🎁 Ежедневный бонус")
async def daily_bonus(message: Message):
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    now = int(time.time())
    
    if now - users[uid].get('last_bonus', 0) < 86400:
        return await message.answer("⏳ Ты уже брал бонус сегодня. Возвращайся завтра!")
    
    # Проверка возраста
    birth = users[uid].get('birth_date', now)
    new_age = int(((now - birth) / 86400) / 2)
    old_age = users[uid].get('last_age', 0)
    
    age_msg = ""
    if new_age > old_age:
        age_msg = f"\n\n🎂 **С днем рождения!**\n{users[uid]['pet_name']} вырос и теперь ему **{new_age} лет**!"
        users[uid]['last_age'] = new_age
    
    users[uid]['coins'] += 100
    users[uid]['last_bonus'] = now
    save_db(users)
    await message.answer(f"🎁 **Бонус получен!** +100 🪙\nБаланс: {users[uid]['coins']}{age_msg}", parse_mode="Markdown")

# --- МАГАЗИН ---
@dp.message(F.text == "🛒 Магазин")
async def shop_menu(message: Message):
    if is_spam(message.from_user.id): return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Еда", callback_data="cat_hunger"), InlineKeyboardButton(text="💧 Вода", callback_data="cat_thirst")],
        [InlineKeyboardButton(text="💊 Медицина", callback_data="cat_heal"), InlineKeyboardButton(text="🛏 Уют", callback_data="cat_energy")],
        [InlineKeyboardButton(text="🎮 Развлечения", callback_data="cat_mood"), InlineKeyboardButton(text="🍺 Бар", callback_data="cat_bar")]
    ])
    await message.answer("🛒 **Магазин**\nВыбери категорию:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("cat_"))
async def shop_category(call: CallbackQuery):
    cat = call.data.replace("cat_", "")
    kb_buttons = []
    for item_id, item in SHOP_ITEMS.items():
        is_match = False
        if cat == "hunger" and item['effect'] == 'hunger': is_match = True
        elif cat == "thirst" and item['effect'] == 'thirst': is_match = True
        elif cat == "heal" and item['effect'] in ['heal', 'wash']: is_match = True
        elif cat == "energy" and item['effect'] == 'energy': is_match = True
        elif cat == "mood" and item['effect'] == 'mood' and item['price'] < 150: is_match = True
        elif cat == "bar" and item['effect'] == 'mood' and item['price'] >= 150: is_match = True
        
        if is_match:
            kb_buttons.append([InlineKeyboardButton(text=f"{item['name']} - {item['price']}🪙", callback_data=f"buy_{item_id}")])
            
    kb_buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_shop")])
    await call.message.edit_text("Выбери товар:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))

@dp.callback_query(F.data == "back_shop")
async def back_shop(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Еда", callback_data="cat_hunger"), InlineKeyboardButton(text="💧 Вода", callback_data="cat_thirst")],
        [InlineKeyboardButton(text="💊 Медицина", callback_data="cat_heal"), InlineKeyboardButton(text="🛏 Уют", callback_data="cat_energy")],
        [InlineKeyboardButton(text="🎮 Развлечения", callback_data="cat_mood"), InlineKeyboardButton(text="🍺 Бар", callback_data="cat_bar")]
    ])
    await call.message.edit_text("🛒 **Магазин**\nВыбери категорию:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_item(call: CallbackQuery):
    if is_spam(call.from_user.id): return await call.answer("Подожди!")
    users = load_db(); uid = str(call.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    item_id = call.data.replace("buy_", "")
    item = SHOP_ITEMS[item_id]
    if users[uid]['coins'] < item['price']: return await call.answer("Мало монет!", show_alert=True)
    
    users[uid]['coins'] -= item['price']
    inv = users[uid].get('inventory', {})
    inv[item_id] = inv.get(item_id, 0) + 1
    users[uid]['inventory'] = inv
    save_db(users)
    await call.message.answer(f"✅ {item['name']} добавлен в инвентарь!\nОстаток: {users[uid]['coins']} 🪙")
    await call.answer()

# --- ИНВЕНТАРЬ ---
@dp.message(F.text == "🎒 Инвентарь")
async def inventory(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users: return
    inv = users[uid].get('inventory', {})
    if not inv: return await message.answer("🎒 Инвентарь пуст!")
        
    kb_buttons = []
    for item_id, count in inv.items():
        item_name = SHOP_ITEMS[item_id]['name']
        kb_buttons.append([InlineKeyboardButton(text=f"{item_name} (x{count})", callback_data=f"use_{item_id}")])
    await message.answer("🎒 **Твой инвентарь**\nНажми, чтобы использовать:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))

@dp.callback_query(F.data.startswith("use_"))
async def use_item(call: CallbackQuery):
    if is_spam(call.from_user.id): return await call.answer("Подожди!")
    users = load_db(); uid = str(call.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    item_id = call.data.replace("use_", "")
    inv = users[uid].get('inventory', {})
    if item_id not in inv or inv[item_id] <= 0: return await call.answer("Нет предмета!", show_alert=True)
        
    item = SHOP_ITEMS[item_id]
    inv[item_id] -= 1
    if inv[item_id] == 0: del inv[item_id]
    users[uid]['inventory'] = inv
    
    effect = item['effect']; val = item['value']
    if effect == "hunger": users[uid]['hunger'] = min(100, users[uid]['hunger'] + val)
    elif effect == "thirst": users[uid]['thirst'] = min(100, users[uid]['thirst'] + val)
    elif effect == "energy": users[uid]['energy'] = min(100, users[uid]['energy'] + val)
    elif effect == "mood": users[uid]['mood'] = min(100, users[uid]['mood'] + val)
    elif effect == "heal": users[uid]['is_sick'] = False
    elif effect == "wash": users[uid]['is_dirty'] = False
    
    users[uid]['last_update'] = int(time.time())
    save_db(users)
    reaction = item.get('reaction', 'Вкусно!')
    await call.message.answer(f"✨ {reaction}")
    await call.answer()
    
    if not inv: await call.message.answer("🎒 Инвентарь пуст.")
    else:
        kb_buttons = [[
