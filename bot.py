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

# --- ОГРОМНЫЙ АССОРТИМЕНТ С АНИМАЦИЯМИ ---
SHOP_ITEMS = {
    # ЕДА
    "apple": {"name": "🍎 Яблоко", "price": 15, "effect": "hunger", "value": 10, "text": "🍎 *[Имя] берет яблоко...*\n\n💥 *Хрусь! Откусывает кусочек...*", "end": "✨ *Сочное и сладкое!*"},
    "burger": {"name": "🍔 Бургер", "price": 40, "effect": "hunger", "value": 30, "text": "🍔 *[Имя] впивается зубами в бургер...*\n\n💦 *Соус течет по подбородку...*", "end": "✨ *Обожаю фастфуд!*"},
    "pizza": {"name": "🍕 Пицца", "price": 80, "effect": "hunger", "value": 50, "text": "🍕 *[Имя] берет кусок пиццы...*\n\n🧀 *Сыр тянется нитями...*", "end": "✨ *Это лучший день в моей жизни!*"},
    "sushi": {"name": "🍣 Суши", "price": 100, "effect": "hunger", "value": 60, "text": "🍣 *[Имя] берет палочки...*\n\n🥢 *Опускает суши в соевый соус...*", "end": "✨ *Васаби щиплет нос, но как вкусно!*"},
    "taco": {"name": "🌮 Тако", "price": 50, "effect": "hunger", "value": 35, "text": "🌮 *[Имя] берет тако...*\n\n🌶 *Острый соус капает на пол...*", "end": "✨ *Оле! Очень остро!*"},
    "donut": {"name": "🍩 Пончик", "price": 25, "effect": "hunger", "value": 15, "text": "🍩 *[Имя] крутит пончик в руках...*\n\n🍫 *Шоколад тает на пальцах...*", "end": "✨ *Сладко! Пальчики оближешь!*"},
    "steak": {"name": "🥩 Стейк", "price": 150, "effect": "hunger", "value": 80, "text": "🥩 *[Имя] берет нож и вилку...*\n\n🔪 *Разрезает сочный стейк...*", "end": "✨ *Я чувствую себя настоящим хищником!*"},
    "salad": {"name": "🥗 Салат", "price": 30, "effect": "hunger", "value": 20, "text": "🥗 *[Имя] берет вилку...*\n\n🥬 *Хрустит свежими овощами...*", "end": "✨ *Полезно! Я буду здоровым!*"},
    "cake": {"name": "🍰 Тортик", "price": 60, "effect": "hunger", "value": 40, "text": "🍰 *[Имя] отрезает кусочек торта...*\n\n🍓 *Сверху красуется вишенка...*", "end": "✨ *Сладкий тортик! Я на вершине блаженства!*"},
    "chocolate": {"name": "🍫 Шоколад", "price": 20, "effect": "hunger", "value": 10, "text": "🍫 *[Имя] разворачивает шоколадку...*\n\n🍬 *Хрустит фольгой...*", "end": "✨ *Шоколад! Гормон счастья!*"},

    # ВОДА
    "water": {"name": "🥛 Вода", "price": 10, "effect": "thirst", "value": 15, "text": "🥛 *[Имя] наливает стакан воды...*\n\n💧 *Вода плещется...*", "end": "✨ *Водичка! Освежает!*"},
    "cola": {"name": "🥤 Кола", "price": 25, "effect": "thirst", "value": 25, "text": "🥤 *[Имя] открывает банку колы...*\n\n💨 *Пшшш! Газ вырывается наружу...*", "end": "✨ *Кола! Пузырьки в носу!*"},
    "pepsi": {"name": "🥤 Пепси", "price": 25, "effect": "thirst", "value": 25, "text": "🥤 *[Имя] открывает бутылку пепси...*\n\n💨 *Пшшш! Газ вырывается наружу...*", "end": "✨ *Пепси! Классика!*"},
    "juice": {"name": "🧃 Сок", "price": 30, "effect": "thirst", "value": 30, "text": "🧃 *[Имя] вставляет трубочку в сок...*\n\n🍹 *Буль-буль-буль...*", "end": "✨ *Сок! Витамины!*"},
    "coffee": {"name": "☕ Кофе", "price": 40, "effect": "thirst", "value": 20, "text": "☕ *[Имя] вдыхает аромат кофе...*\n\n☕ *Делает маленький глоток...*", "end": "✨ *Кофе! Я проснулся!*"},
    "tea": {"name": "🍵 Чай", "price": 20, "effect": "thirst", "value": 15, "text": "🍵 *[Имя] наливает чай...*\n\n💨 *Пар поднимается над чашкой...*", "end": "✨ *Чай! Уютно!*"},
    "energy": {"name": "⚡ Энергетик", "price": 50, "effect": "thirst", "value": 50, "text": "⚡ *[Имя] открывает энергетик...*\n\n🔋 *Буль-буль-буль...*", "end": "✨ *Я готов свернуть горы!*"},
    "milkshake": {"name": "🥤 Милкшейк", "price": 60, "effect": "thirst", "value": 40, "text": "🥤 *[Имя] пьет милкшейк через трубочку...*\n\n🥛 *Молочные усы!*", "end": "✨ *Молочный коктейль! Ням!*"},
    "lemonade": {"name": "🍋 Лимонад", "price": 35, "effect": "thirst", "value": 30, "text": "🍋 *[Имя] открывает лимонад...*\n\n💨 *Шипит!*", "end": "✨ *Лимонад! Кисло-сладко!*"},
    "smoothie": {"name": "🍹 Смузи", "price": 70, "effect": "thirst", "value": 45, "text": "🍹 *[Имя] пьет смузи через трубочку...*\n\n🍓 *Ягодные нотки!*", "end": "✨ *Смузи! Это полезно!*"},

    # МЕДИЦИНА
    "pill": {"name": "💊 Таблетка", "price": 100, "effect": "heal", "value": 1, "text": "💊 *[Имя] берет таблетку...*\n\n💧 *Запивает водой...*", "end": "✨ *Тьфу, горькая! Но теперь я здоров!*"},
    "bandage": {"name": "🩹 Бинт", "price": 50, "effect": "heal", "value": 1, "text": "🩹 *[Имя] разматывает бинт...*\n\n🤕 *Заматывает лапку...*", "end": "✨ *Бинт! Теперь заживет!*"},
    "syrup": {"name": "🧪 Сироп", "price": 80, "effect": "heal", "value": 1, "text": "🧪 *[Имя] открывает пузырек...*\n\n🥄 *Пьет сироп с ложечки...*", "end": "✨ *Сироп от кашля! Сладенький!*"},
    "vitamins": {"name": "💊 Витамины", "price": 120, "effect": "heal", "value": 1, "text": "💊 *[Имя] берет горсть витаминов...*\n\n💧 *Запивает водой...*", "end": "✨ *Витаминки! Теперь я точно не заболею!*"},
    "soap": {"name": "🧼 Мыло", "price": 40, "effect": "wash", "value": 1, "text": "🧼 *[Имя] намыливается...*\n\n🫧 *Летят мыльные пузыри...*", "end": "✨ *Я теперь чистый и пахну клубникой!*"},

    # УЮТ
    "pillow": {"name": "🛏 Подушка", "price": 100, "effect": "energy", "value": 30, "text": "🛏 *[Имя] кладет голову на подушку...*\n\n💤 *Закрывает глаза...*", "end": "✨ *Подушка! Мягкая, как облачко!*"},
    "blanket": {"name": "🛌 Одеяло", "price": 200, "effect": "energy", "value": 50, "text": "🛌 *[Имя] укрывается одеялом...*\n\n🥶 *Согревается...*", "end": "✨ *Одеяло! Так тепло и уютно!*"},
    "bed": {"name": "🛏 Кровать", "price": 500, "effect": "energy", "value": 100, "text": "🛏 *[Имя] прыгает на кровать...*\n\n☁️ *Проваливается в сон...*", "end": "✨ *Кровать! Я хочу спать тут вечно!*"},
    "lamp": {"name": "💡 Лампа", "price": 150, "effect": "energy", "value": 20, "text": "💡 *[Имя] включает лампу...*\n\n🔦 *Свет разгоняет тьму...*", "end": "✨ *Светло! Теперь не страшно!*"},
    "chair": {"name": "🪑 Кресло", "price": 300, "effect": "energy", "value": 40, "text": "🪑 *[Имя] плюхается в кресло...*\n\n🛋 *Устраивается поудобнее...*", "end": "✨ *Кресло! Удобно!*"},

    # РАЗВЛЕЧЕНИЯ
    "ball": {"name": "⚽ Мячик", "price": 70, "effect": "mood", "value": 25, "text": "⚽ *[Имя] берет мячик...*\n\n🏃 *Бежит играть...*", "end": "✨ *Мячик! Гав! Давай играть!*"},
    "toy": {"name": "🧸 Игрушка", "price": 120, "effect": "mood", "value": 40, "text": "🧸 *[Имя] обнимает игрушку...*\n\n🥰 *Улыбается...*", "end": "✨ *Игрушка! Моя любимая!*"},
    "game": {"name": "🎮 Игра", "price": 300, "effect": "mood", "value": 70, "text": "🎮 *[Имя] берет геймпад...*\n\n🎮 *Нажимает кнопки...*", "end": "✨ *Игра! Я выиграл!*"},
    "book": {"name": "📚 Книга", "price": 150, "effect": "mood", "value": 30, "text": "📚 *[Имя] открывает книгу...*\n\n🤓 *Читает строчку за строчкой...*", "end": "✨ *Книга! Как интересно!*"},
    "guitar": {"name": "🎸 Гитара", "price": 400, "effect": "mood", "value": 80, "text": "🎸 *[Имя] берет гитару...*\n\n🎶 *Играет аккорды...*", "end": "✨ *Гитара! Ля-ля-ля!*"},
    "movie": {"name": "🎬 Фильм", "price": 200, "effect": "mood", "value": 50, "text": "🎬 *[Имя] включает фильм...*\n\n🍿 *Ест попкорн...*", "end": "✨ *Фильм! Какой сюжет!*"},
    "vr": {"name": "🕶 VR-очки", "price": 800, "effect": "mood", "value": 100, "text": "🕶 *[Имя] надевает VR-очки...*\n\n🌌 *Погружается в виртуальный мир...*", "end": "✨ *VR! Я в другом мире!*"},

    # БАР
    "beer": {"name": "🍺 Пиво", "price": 60, "effect": "mood", "value": 20, "text": "🍺 *[Имя] открывает бутылку пива...*\n\n💨 *Пшшш! Пена лезет из горлышка...*", "end": "✨ *Пиво! Хи-хи, я немного опьянел!*"},
    "wine": {"name": "🍷 Вино", "price": 150, "effect": "mood", "value": 35, "text": "🍷 *[Имя] наливает вино в бокал...*\n\n🍇 *Крутит бокал, вдыхая аромат...*", "end": "✨ *Вино! Ах, какой букет!*"},
    "vodka": {"name": "🥃 Водка", "price": 200, "effect": "mood", "value": 50, "text": "🥃 *[Имя] наливает стопку водки...*\n\n🥶 *Выдыхает...*", "end": "✨ *Водка! Ой, голова кружится!*"},
    "whiskey": {"name": "🥃 Виски", "price": 300, "effect": "mood", "value": 60, "text": "🥃 *[Имя] наливает виски со льдом...*\n\n🧊 *Лед звенит в стакане...*", "end": "✨ *Виски! Я чувствую себя аристократом!*"},
    "champagne": {"name": "🍾 Шампанское", "price": 500, "effect": "mood", "value": 80, "text": "🍾 *[Имя] берет шампанское...*\n\n💨 *Пшшш! Пробка летит в потолок!*", "end": "✨ *Шампанское! Ура!*"},
    "mojito": {"name": "🍹 Мохито", "price": 250, "effect": "mood", "value": 45, "text": "🍹 *[Имя] размешивает мохито...*\n\n🌿 *Мятный листик кружится...*", "end": "✨ *Мохито! С мятой!*"},
    "cocktail": {"name": "🍸 Коктейль", "price": 220, "effect": "mood", "value": 40, "text": "🍸 *[Имя] берет коктейль...*\n\n🍒 *Вишенка на шпажке...*", "end": "✨ *Коктейль! Танцую!*"},
    "sake": {"name": "🍶 Саке", "price": 180, "effect": "mood", "value": 35, "text": "🍶 *[Имя] наливает саке в пиалу...*\n\n🏮 *Теплый рисовый напиток...*", "end": "✨ *Саке! Конничива!*"},
}

# --- ФОНОВАЯ ЗАДАЧА ---
async def background_worker():
    while True:
        try:
            now = datetime.now(TZ)
            if now.hour >= 23 or now.hour < 8:
                await asyncio.sleep(1800)
                continue

            users = load_db()
            current_time = int(time.time())
            changed = False
            
            for uid_str, user in users.items():
                if user.get('is_dead'): continue
                last_upd = user.get('last_update', current_time)
                elapsed_mins = (current_time - last_upd) / 60
                drop = int(elapsed_mins / 5)
                
                if drop > 0:
                    user['hunger'] = max(0, user['hunger'] - drop)
                    user['thirst'] = max(0, user['thirst'] - drop)
                    user['energy'] = max(0, user['energy'] - drop)
                    user['mood'] = max(0, user['mood'] - drop)
                    user['last_update'] = current_time
                    changed = True
                    
                    if user['hunger'] == 0 or user['thirst'] == 0:
                        user['is_dead'] = True
                        try: await bot.send_message(int(uid_str), f"💀 {user['pet_name']} не выдержал... Он умер от истощения.")
                        except: pass
                        continue
                        
                    if user['hunger'] < 30 or user['thirst'] < 30:
                        try: await bot.send_message(int(uid_str), f"⚠️ {user['pet_name']} голоден!\n🍔 {user['hunger']}%\n💧 {user['thirst']}%")
                        except: pass
            if changed: save_db(users)
        except Exception as e: print(f"Ошибка фона: {e}")
        await asyncio.sleep(900)

# --- СТАРТ ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    users = load_db()
    uid = str(message.from_user.id)
    if uid in users:
        if users[uid].get('is_dead'):
            return await message.answer(f"💀 {users[uid]['pet_name']} покинул этот мир.", reply_markup=get_main_keyboard())
        await message.answer(f"С возвращением! {users[uid]['pet_name']} скучал.", reply_markup=get_main_keyboard())
        return
    await message.answer("⚠️ Внимание! Персонаж создается навсегда!")
    await message.answer("Шаг 1. Введи имя:")
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
    await call.message.answer("🎉 Персонаж создан!", reply_markup=get_main_keyboard())
    await call.answer()

# --- ДЕЙСТВИЯ ---
async def sleep_timer(user_id, pet_name):
    await asyncio.sleep(60)
    users = load_db(); uid = str(user_id)
    if uid in users:
        users[uid]['energy'] = min(100, users[uid]['energy'] + 60)
        save_db(users)
        try: await bot.send_message(user_id, f"☀️ {pet_name} проснулся!\n⚡ Энергия: {draw_bar(users[uid]['energy'])}", reply_markup=get_main_keyboard())
        except: pass

@dp.message(F.text == "🍔 Покормить")
async def feed_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['hunger'] >= 100:
        return await message.answer(f"🍔 {users[uid]['pet_name']} сыт и не хочет есть!")
    users[uid]['hunger'] = min(100, users[uid]['hunger'] + 20)
    users[uid]['last_update'] = int(time.time())
    bonus = ""
    if random.random() < 0.3:
        coins = random.choice([5, 10, 20])
        users[uid]['coins'] += coins
        bonus = f"\n🪙 Ты получил {coins} монет за заботу!"
    save_db(users)
    await message.answer(f"🍔 Ты покормил {users[uid]['pet_name']}!\nСытость: {draw_bar(users[uid]['hunger'])}{bonus}")

@dp.message(F.text == "💧 Попить")
async def water_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['thirst'] >= 100:
        return await message.answer(f"💧 {users[uid]['pet_name']} не хочет пить!")
    users[uid]['thirst'] = min(100, users[uid]['thirst'] + 20)
    users[uid]['last_update'] = int(time.time())
    bonus = ""
    if random.random() < 0.3:
        coins = random.choice([5, 10, 20])
        users[uid]['coins'] += coins
        bonus = f"\n🪙 Ты получил {coins} монет за заботу!"
    save_db(users)
    await message.answer(f"💧 {users[uid]['pet_name']} попил!\nЖажда: {draw_bar(users[uid]['thirst'])}{bonus}")

@dp.message(F.text == "🛌 Поспать")
async def sleep_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['energy'] > 80:
        return await message.answer(f"☀️ {users[uid]['pet_name']} не хочет спать!")
    await message.answer(f"🛌 {users[uid]['pet_name']} лег спать. Проснется через 1 минуту ⏱")
    asyncio.create_task(sleep_timer(message.from_user.id, users[uid]['pet_name']))

@dp.message(F.text == "🎾 Поиграть")
async def play_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['mood'] >= 100:
        return await message.answer(f"🎾 {users[uid]['pet_name']} наигрался и устал!")
    users[uid]['mood'] = min(100, users[uid]['mood'] + 20)
    users[uid]['last_update'] = int(time.time())
    save_db(users)
    await message.answer(f"🎾 Ты поиграл с {users[uid]['pet_name']}!\nНастроение: {draw_bar(users[uid]['mood'])}")

@dp.message(F.text == "💬 Поговорить")
async def talk_to_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['hunger'] < 30: return await message.answer(f"🍔 {users[uid]['pet_name']}: «Я очень голоден...»")
    if users[uid]['thirst'] < 30: return await message.answer(f"💧 {users[uid]['pet_name']}: «Я хочу пить...»")
    
    char = users[uid]['pet_char']
    if char == "cute":
        starts = ["Знаешь, ", "Я тут подумал, ", "Хочу тебе сказать, ", "Мне кажется, ", "Ты в курсе, что ", "Слушай, "]
        middles = ["ты самый лучший человек на свете, ", "твоя улыбка согревает меня, ", "с тобой так тепло и уютно, ", "я так рад, что ты у меня есть, ", "ты делаешь этот мир добрее, "]
        ends = ["и я тебя очень люблю! 🤍", "и это делает меня счастливым! 🥰", "спасибо, что ты рядом! ✨", "давай обниматься! 🤗", "ты мое солнышко! ☀️"]
    elif char == "rude":
        starts = ["Слушай, ", "Ну чего тебе, ", "Опять ты, ", "Я тут лежу, а ты, ", "Может хватит уже, ", "Эй, "]
        middles = ["пристаешь ко мне со своими вопросами, ", "не даешь мне спокойно полежать, ", "мешаешь мне смотреть сны, ", "дергаешь меня без повода, ", "отвлекаешь меня от важных дел, "]
        ends = ["дай мне поспать! 😒", "иди лучше поиграй! 😤", "я вообще-то занят! 🙄", "ну ладно, привет. 😑", "отстань от меня! 😠"]
    elif char == "smart":
        starts = ["Знаешь ли ты, что ", "Интересный факт: ", "С точки зрения науки, ", "Мои наблюдения показывают, что ", "Я тут прочитал, что ", "По статистике, "]
        middles = ["осьминоги имеют три сердца, ", "медведи могут развивать скорость до 50 км/ч, ", "вода закипает при 100 градусах, ", "люди используют только 10% мозга, ", "молния бьет в землю 100 раз в секунду, "]
        ends = ["а ты знал об этом? 🧠", "и это невероятно! 🤓", "как тебе такая информация? 📚", "познавательно, не так ли? 🧐", "вот такие дела! 📖"]
    else:
        starts = ["ААА! ", "О, привет! ", "Слушай, слушай! ", "Я тут подумал... ", "Внезапно, ", "БУ! "]
        middles = ["а что если облака из ваты, ", "я нашел вчера банан, ", "а если я закрою глаза, ты исчезнешь? ", "мне кажется, я умею летать, ", "а давай построим ракету из носков, "]
        ends = ["ДАВАЙ ВЫПЬЕМ ЧАЮ! 🤪", "ЭТО ЖЕ КРУТО! 😳", "АААА! 🚀", "и тут я проснулся. 🌪", "ПОЛЕТЕЛИ НА ЛУНУ! 🌕"]

    phrase = random.choice(starts) + random.choice(middles) + random.choice(ends)
    await message.answer(f"💬 {users[uid]['pet_name']}: «{phrase}»")

@dp.message(F.text == "📊 Профиль")
async def show_profile(message: Message):
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users: return
    u = users[uid]
    birth = u.get('birth_date', int(time.time()))
    age = int(((time.time() - birth) / 86400) / 2)
    text = f"📊 **Профиль**\n\n👤 **Имя:** {u['pet_name']}\n🎂 **Возраст:** {age} лет\n🪙 **Монеты:** {u['coins']}\n\n🍔 Сытость: {draw_bar(u['hunger'])}\n💧 Жажда: {draw_bar(u['thirst'])}\n⚡ Энергия: {draw_bar(u['energy'])}\n🎾 Настроение: {draw_bar(u['mood'])}"
    await message.answer_photo(photo=u['pet_photo'], caption=text, parse_mode="Markdown")

@dp.message(F.text == "🎁 Ежедневный бонус")
async def daily_bonus(message: Message):
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    now = int(time.time())
    if now - users[uid].get('last_bonus', 0) < 86400:
        return await message.answer("⏳ Ты уже брал бонус сегодня. Возвращайся завтра!")
    users[uid]['coins'] += 100
    users[uid]['last_bonus'] = now
    save_db(users)
    await message.answer(f"🎁 **Бонус получен!** +100 🪙\nБаланс: {users[uid]['coins']}", parse_mode="Markdown")

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
    await call.message.answer(f"✅ {item['name']} добавлен в инвентарь!")
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
    
    action_text = item.get('text', "✨ *Что-то происходит...*").replace("[Имя]", users[uid]['pet_name'])
    end_text = item.get('end', "✨ *Класс!*")
    
    final_caption = f"{action_text}\n\n{end_text}\n\n🍔 Сытость: {draw_bar(users[uid]['hunger'])}\n💧 Жажда: {draw_bar(users[uid]['thirst'])}\n🎾 Настроение: {draw_bar(users[uid]['mood'])}"
    
    await call.message.answer_photo(photo=users[uid]['pet_photo'], caption=final_caption, parse_mode="Markdown")
    await call.answer()
    
    if not inv: await call.message.answer("🎒 Инвентарь пуст.")
    else:
        kb_buttons = [[InlineKeyboardButton(text=f"{SHOP_ITEMS[i]['name']} (x{c})", callback_data=f"use_{i}")] for i, c in inv.items()]
        await call.message.answer("Обновленный инвентарь:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))

# --- АДМИНКА ---
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
        [InlineKeyboardButton(text="+ 500 🪙", callback_data=f"gv_{target}_500")],
        [InlineKeyboardButton(text="✍️ Ввести свою сумму", callback_data=f"custom_give_{target}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])
    await call.message.edit_text(f"Выбери действие для ID `{target}`:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_back")
async def admin_back(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    await admin_panel(call.message)

@dp.callback_query(F.data.startswith("gv_"))
async def admin_give(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    parts = call.data.split("_"); target, amount = parts[1], int(parts[2])
    users = load_db()
    if target in users:
        users[target]['coins'] += amount
        save_db(users)
        await call.answer(f"✅ Выдано {amount} монет!")
        try: await bot.send_message(int(target), f"🎁 Вам переслано {amount} 🪙!")
        except: pass
        await admin_panel(call.message)

@dp.callback_query(F.data.startswith("custom_give_"))
async def custom_give_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID: return
    target = call.data.replace("custom_give_", "")
    await state.update_data(target_id=target)
    await state.set_state(AdminState.waiting_for_amount)
    await call.message.edit_text(f"✍️ Введи сумму монет (ID: `{target}`):", parse_mode="Markdown")
    await call.answer()

@dp.message(AdminState.waiting_for_amount)
async def custom_give_amount(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    if not message.text.isdigit(): return await message.answer("❌ Только цифры!")
    amount = int(message.text)
    data = await state.get_data()
    target = data['target_id']
    users = load_db()
    if target in users:
        users[target]['coins'] += amount
        save_db(users)
        await message.answer(f"✅ Выдано {amount} 🪙.")
        try: await bot.send_message(int(target), f"🎁 Вам переслано {amount} 🪙!")
        except: pass
    else: await message.answer("❌ Игрок не найден.")
    await state.clear()

async def main():
    asyncio.create_task(background_worker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
