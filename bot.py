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

def draw_text_bar(value):
    return f"{value}%"

def get_stats_text(user):
    age = int(((time.time() - user.get('birth_date', time.time())) / 86400) / 2)
    lvl = user.get('level', 1)
    xp = user.get('xp', 0)
    xp_needed = lvl * 100
    
    text = (
        f"👤 **{user['pet_name']}**\n"
        f"🎂 Возраст: {age} лет | ⭐ Уровень: {lvl}\n"
        f"🪙 Монеты: {user['coins']}\n"
        f"📈 Опыт: {xp}/{xp_needed}\n"
        f"👗 Надето: {user.get('wearing', 'Ничего')}\n\n"
        f"🍔 Сытость: {draw_text_bar(user['hunger'])}\n"
        f"💧 Жажда: {draw_text_bar(user['thirst'])}\n"
        f"⚡ Энергия: {draw_text_bar(user['energy'])}\n"
        f"🎾 Настроение: {draw_text_bar(user['mood'])}"
    )
    return text

def add_xp(user, amount):
    if 'xp' not in user: user['xp'] = 0
    if 'level' not in user: user['level'] = 1
    user['xp'] += amount
    while user['xp'] >= user['level'] * 100:
        user['xp'] -= user['level'] * 100
        user['level'] += 1
        user['coins'] += 50
    return user['level']

# --- СОСТОЯНИЯ ---
class CreatePet(StatesGroup):
    name = State()
    photo = State()
    char = State()

class AdminState(StatesGroup):
    waiting_for_amount = State()
    target_id = State()

class ChallengeState(StatesGroup):
    waiting_for_answer = State()

def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="🛌 Поспать"), KeyboardButton(text="🎾 Поиграть")],
        [KeyboardButton(text="📊 Профиль"), KeyboardButton(text="💬 Поговорить")],
        [KeyboardButton(text="🎁 Бонус"), KeyboardButton(text="🎮 Мини-игра")],
        [KeyboardButton(text="🎯 Испытание")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ТОВАРЫ (ЕДА, ВОДА, БРЕНДОВАЯ ОДЕЖДА) ---
SHOP_ITEMS = {
    # Еда и вода
    "apple": {"name": "🍎 Яблоко", "price": 15, "effect": "hunger", "value": 10, "text": "🍎 [Имя] берет яблоко...", "end": "✨ Сочное!"},
    "burger": {"name": "🍔 Бургер", "price": 40, "effect": "hunger", "value": 30, "text": "🍔 [Имя] ест бургер...", "end": "✨ Обожаю фастфуд!"},
    "water": {"name": "🥛 Вода", "price": 10, "effect": "thirst", "value": 15, "text": "🥛 [Имя] пьет воду...", "end": "✨ Освежает!"},
    "cola": {"name": "🥤 Кола", "price": 25, "effect": "thirst", "value": 25, "text": "🥤 [Имя] пьет колу...", "end": "✨ Пузырьки!"},
    "beer": {"name": "🍺 Пиво", "price": 60, "effect": "mood", "value": 20, "text": "🍺 [Имя] пьет пиво...", "end": "✨ Опьянел!"},
    
    # Брендовая одежда (Аксессуары)
    "nike": {"name": "👟 Кроссовки Nike", "price": 500, "effect": "wear", "value": 1, "text": "👟 [Имя] надевает кроссовки Nike...", "end": "✨ Just Do It!"},
    "adidas": {"name": "🧥 Худи Adidas", "price": 400, "effect": "wear", "value": 1, "text": "🧥 [Имя] надевает худи Adidas...", "end": "✨ Немецкое качество!"},
    "gucci": {"name": "🕶 Очки Gucci", "price": 800, "effect": "wear", "value": 1, "text": "🕶 [Имя] надевает очки Gucci...", "end": "✨ Люксовый стиль!"},
    "rolex": {"name": "⌚ Часы Rolex", "price": 1500, "effect": "wear", "value": 1, "text": "⌚ [Имя] надевает Rolex...", "end": "✨ Время — деньги!"},
    "supreme": {"name": "🧢 Кепка Supreme", "price": 300, "effect": "wear", "value": 1, "text": "🧢 [Имя] надевает кепку Supreme...", "end": "✨ Уличный стиль!"},
    "louis": {"name": "👜 Сумка Louis Vuitton", "price": 2000, "effect": "wear", "value": 1, "text": "👜 [Имя] берет сумку LV...", "end": "✨ Дорого-богато!"},
    "prada": {"name": "👗 Платье Prada", "price": 2500, "effect": "wear", "value": 1, "text": "👗 [Имя] надевает платье Prada...", "end": "✨ Высокая мода!"},
}

DREAMS = ["🐑 [Имя] видит сон, как он прыгает по облакам...", "🍖 [Имя] снится огромная гора сосисок...", "🚀 [Имя] летит в космос на ракете из носков..."]

# --- ФОН ---
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
                drop = int(elapsed_mins / 30)
                if drop > 0:
                    old_hunger = user['hunger']
                    user['hunger'] = max(0, user['hunger'] - drop)
                    user['thirst'] = max(0, user['thirst'] - drop)
                    user['energy'] = max(0, user['energy'] - drop)
                    user['mood'] = max(0, user['mood'] - drop)
                    user['last_update'] = current_time
                    changed = True
                    if user['hunger'] == 0 or user['thirst'] == 0:
                        user['is_dead'] = True
                        try: await bot.send_message(int(uid_str), f"💀 {user['pet_name']} не выдержал...")
                        except: pass
                        continue
                    if user['hunger'] <= 20 and old_hunger > 20:
                        try: await bot.send_message(int(uid_str), f"⚠️ {user['pet_name']} голоден! Купи еду.")
                        except: pass
            if changed: save_db(users)
        except Exception as e: print(f"Ошибка фона: {e}")
        await asyncio.sleep(900)

# --- СТАРТ ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    users = load_db(); uid = str(message.from_user.id)
    if uid in users:
        if users[uid].get('is_dead'): 
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🕯 Воскресить (5000 🪙)", callback_data="revive_pet")]])
            return await message.answer_photo(
                photo=users[uid]['pet_photo'], 
                caption=f"💀 **{users[uid]['pet_name']} покинул этот мир...**\n\nВоскрешение стоит 5000 монет.\nТвой баланс: {users[uid]['coins']} 🪙", 
                reply_markup=kb, parse_mode="Markdown"
            )
        return await message.answer(f"С возвращением! {users[uid]['pet_name']} скучал.", reply_markup=get_main_keyboard())
    
    text = (
        "👋 **Добро пожаловать в игру!**\n\n"
        "Здесь ты сможешь завести своего собственного персонажа, заботиться о нем и прокачивать его.\n\n"
        "📜 **Что можно делать:**\n"
        "🛒 Покупать еду и воду в магазине.\n"
        "🎒 Использовать предметы и надевать брендовые вещи.\n"
        "🎾 Играть и спать.\n"
        "🎮 Играть в мини-игры.\n"
        "🎯 Проходить испытания.\n"
        "⭐ Повышать уровень.\n\n"
        "⚠️ **Важно:** Персонаж создается навсегда!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Погнали! 🚀", callback_data="start_create")]])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "revive_pet")
async def revive_pet(call: CallbackQuery):
    users = load_db(); uid = str(call.from_user.id)
    if uid not in users: return
    user = users[uid]
    
    if not user.get('is_dead'): return await call.answer("Твой персонаж жив!", show_alert=True)
    price = 5000
    if user['coins'] < price:
        return await call.answer(f"Не хватает монет! Нужно {price} 🪙, а у тебя {user['coins']} 🪙.", show_alert=True)
        
    user['coins'] -= price
    user['is_dead'] = False
    user['hunger'] = 100; user['thirst'] = 100; user['energy'] = 100; user['mood'] = 100
    save_db(users)
    
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer_photo(photo=user['pet_photo'], caption="🕯 **Успешное воскрешение!**\nТвой персонаж снова с тобой и полон сил!", parse_mode="Markdown")
    await call.answer("Успешно воскрешён!")

@dp.callback_query(F.data == "start_create")
async def start_create(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Шаг 1. Введи имя для своего персонажа:")
    await state.set_state(CreatePet.name)
    await call.answer()

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
        [InlineKeyboardButton(text="🥰 Милый", callback_data="char_cute")], [InlineKeyboardButton(text="😈 Вредный", callback_data="char_rude")],
        [InlineKeyboardButton(text="🧠 Умный", callback_data="char_smart")], [InlineKeyboardButton(text="🤪 Безумный", callback_data="char_crazy")]
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
        "last_update": int(time.time()), "is_dead": False, "xp": 0, "level": 1,
        "last_challenge": 0, "wearing": "Ничего"
    }
    save_db(users)
    await state.clear()
    await call.message.answer("🎉 Персонаж создан!", reply_markup=get_main_keyboard())
    await call.answer()

# --- ДЕЙСТВИЯ ---
async def send_card(message_or_call, user, action_text=""):
    stats = get_stats_text(user)
    caption = f"{action_text}\n\n{stats}"
    await bot.send_photo(message_or_call.from_user.id, photo=user['pet_photo'], caption=caption, parse_mode="Markdown")

async def sleep_timer(user_id, pet_name):
    await asyncio.sleep(60)
    users = load_db(); uid = str(user_id)
    if uid in users:
        users[uid]['energy'] = min(100, users[uid]['energy'] + 60)
        users[uid]['last_update'] = int(time.time())
        save_db(users)
        dream = random.choice(DREAMS).replace("[Имя]", pet_name)
        class FakeMsg: pass
        fake = FakeMsg(); fake.from_user = type('obj', (object,), {'id': int(user_id)})
        await send_card(fake, users[uid], f"☀️ {pet_name} проснулся!\nСон: {dream}")

@dp.message(F.text == "🎾 Поиграть")
async def play_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['mood'] >= 100: return await message.answer(f"🎾 {users[uid]['pet_name']} наигрался!")
    users[uid]['mood'] = min(100, users[uid]['mood'] + 20)
    users[uid]['last_update'] = int(time.time())
    add_xp(users[uid], 10)
    save_db(users)
    await send_card(message, users[uid], f"🎾 *Ты поиграл с {users[uid]['pet_name']}!*")

@dp.message(F.text == "🛌 Поспать")
async def sleep_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['energy'] > 80: return await message.answer(f"☀️ {users[uid]['pet_name']} не хочет спать!")
    await message.answer(f"🛌 {users[uid]['pet_name']} лег спать. Проснется через 1 минуту ⏱")
    asyncio.create_task(sleep_timer(message.from_user.id, users[uid]['pet_name']))

@dp.message(F.text == "📊 Профиль")
async def show_profile(message: Message):
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users: return
    await send_card(message, users[uid], "📊 *Паспорт персонажа*")

# --- МИНИ-ИГРЫ ---
@dp.message(F.text == "🎮 Мини-игра")
async def mini_game(message: Message):
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    
    game = random.choice(["guess", "coin", "rps"])
    users[uid]['current_game'] = game
    save_db(users)
    
    if game == "guess":
        users[uid]['game_secret'] = random.randint(1, 5)
        save_db(users)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1", callback_data="guess_1"), InlineKeyboardButton(text="2", callback_data="guess_2")],
            [InlineKeyboardButton(text="3", callback_data="guess_3"), InlineKeyboardButton(text="4", callback_data="guess_4")],
            [InlineKeyboardButton(text="5", callback_data="guess_5")]
        ])
        await message.answer(f"🎮 **Мини-игра: Угадай число!**\n{users[uid]['pet_name']} загадал число от 1 до 5.\nПриз: 50 монет и 20 XP", reply_markup=kb)
    elif game == "coin":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Орёл 🦅", callback_data="coin_eagle"), InlineKeyboardButton(text="Решка 🪙", callback_data="coin_tails")]
        ])
        await message.answer(f"🎮 **Мини-игра: Орёл или Решка!**\nЧто выпадет?\nПриз: 50 монет и 20 XP", reply_markup=kb)
    elif game == "rps":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Камень 🪨", callback_data="rps_rock"), InlineKeyboardButton(text="Ножницы ✂️", callback_data="rps_scissors")],
            [InlineKeyboardButton(text="Бумага 📄", callback_data="rps_paper")]
        ])
        await message.answer(f"🎮 **Мини-игра: Камень, Ножницы, Бумага!**\nТвой ход:\nПриз: 50 монет и 20 XP", reply_markup=kb)

@dp.callback_query(F.data.startswith("guess_"))
async def guess_number(call: CallbackQuery):
    users = load_db(); uid = str(call.from_user.id)
    if uid not in users or users[uid].get('current_game') != "guess": return
    guess = int(call.data.replace("guess_", ""))
    secret = users[uid].get('game_secret', 0)
    if guess == secret:
        users[uid]['coins'] += 50
        add_xp(users[uid], 20)
        del users[uid]['current_game']
        save_db(users)
        await call.message.edit_text(f"🎉 **Угадал!**\n🪙 +50 монет\n📈 +20 XP")
    else:
        await call.answer(f"Мимо! Было {secret}", show_alert=True)
        del users[uid]['current_game']
        save_db(users)
        await call.message.edit_text(f"❌ **Не угадал.** Было {secret}.")

@dp.callback_query(F.data.startswith("coin_"))
async def coin_game(call: CallbackQuery):
    users = load_db(); uid = str(call.from_user.id)
    if uid not in users or users[uid].get('current_game') != "coin": return
    choice = call.data.replace("coin_", "")
    result = random.choice(["eagle", "tails"])
    if choice == result:
        users[uid]['coins'] += 50
        add_xp(users[uid], 20)
        save_db(users)
        await call.message.edit_text(f"🦅 Выпал **{ 'Орёл' if result == 'eagle' else 'Решка' }**!\n🎉 Ты угадал!\n🪙 +50 монет\n📈 +20 XP")
    else:
        await call.answer(f"Выпал {'Орёл' if result == 'eagle' else 'Решка'}! Не угадал.", show_alert=True)
        await call.message.edit_text(f"🪙 Выпал **{ 'Орёл' if result == 'eagle' else 'Решка' }**.\n❌ Ты не угадал.")
    del users[uid]['current_game']
    save_db(users)

@dp.callback_query(F.data.startswith("rps_"))
async def rps_game(call: CallbackQuery):
    users = load_db(); uid = str(call.from_user.id)
    if uid not in users or users[uid].get('current_game') != "rps": return
    choice = call.data.replace("rps_", "")
    bot_choice = random.choice(["rock", "scissors", "paper"])
    names = {"rock": "🪨 Камень", "scissors": "✂️ Ножницы", "paper": "📄 Бумага"}
    win = (choice == "rock" and bot_choice == "scissors") or (choice == "scissors" and bot_choice == "paper") or (choice == "paper" and bot_choice == "rock")
    draw = (choice == bot_choice)
    res_text = f"Ты: {names[choice]}\nБот: {names[bot_choice]}\n\n"
    if win:
        users[uid]['coins'] += 50
        add_xp(users[uid], 20)
        res_text += "🎉 **Ты победил!**\n🪙 +50 монет\n📈 +20 XP"
    elif draw:
        res_text += "🤝 **Ничья!**\nПопробуй еще раз."
    else:
        res_text += "❌ **Ты проиграл.**"
    del users[uid]['current_game']
    save_db(users)
    await call.message.edit_text(res_text)

# --- ИСПЫТАНИЯ (НОВЫЕ) ---
@dp.message(F.text == "🎯 Испытание")
async def challenge_menu(message: Message, state: FSMContext):
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users: return
    now = int(time.time())
    if now - users[uid].get('last_challenge', 0) < 86400:
        return await message.answer("⏳ Ты уже выполнял испытание сегодня. Возвращайся завтра!")
    
    # Выбираем тип испытания
    ctype = random.choice(["word", "math"])
    
    if ctype == "word":
        tasks = [
            ("Напиши слово 'пожалуйста'", "пожалуйста"),
            ("Напиши 'я молодец'", "я молодец"),
            ("Скажи 'люблю'", "люблю")
        ]
        task_text, answer = random.choice(tasks)
        await state.update_data(answer=answer)
        await message.answer(f"🎯 **Испытание!**\n{users[uid]['pet_name']} просит тебя: *{task_text}*\n\nНапиши это сообщением в чат. Награда: 100 монет и 50 XP!", parse_mode="Markdown")
        await state.set_state(ChallengeState.waiting_for_answer)
    else:
        a, b = random.randint(1, 10), random.randint(1, 10)
        ans = str(a + b)
        await state.update_data(answer=ans)
        await message.answer(f"🎯 **Испытание!**\nРеши пример: *{a} + {b} = ?*\n\nНапиши ответ в чат. Награда: 100 монет и 50 XP!", parse_mode="Markdown")
        await state.set_state(ChallengeState.waiting_for_answer)

@dp.message(ChallengeState.waiting_for_answer)
async def check_challenge(message: Message, state: FSMContext):
    data = await state.get_data()
    correct = data.get('answer', '').lower()
    user_ans = message.text.lower().strip()
    
    users = load_db(); uid = str(message.from_user.id)
    if not users or uid not in users: return
    
    if user_ans == correct:
        users[uid]['coins'] += 100
        add_xp(users[uid], 50)
        users[uid]['last_challenge'] = int(time.time())
        save_db(users)
        await message.answer("✅ **Верно! Испытание пройдено.**\n🪙 +100 монет\n📈 +50 XP", reply_markup=get_main_keyboard())
    else:
        await message.answer(f"❌ **Неверно.** Попробуй завтра!", reply_markup=get_main_keyboard())
        users[uid]['last_challenge'] = int(time.time())
        save_db(users)
        
    await state.clear()

# --- ОБЩЕНИЕ ---
@dp.message(F.text == "💬 Поговорить")
async def talk_to_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['hunger'] < 30: return await message.answer(f"🍔 {users[uid]['pet_name']}: «Я очень голоден... Покорми меня».")
    
    char = users[uid]['pet_char']
    if char == "cute":
        s = ["Знаешь, ", "Я тут подумал, ", "Хочу тебе сказать, ", "Мне кажется, ", "Ты в курсе, что "]
        m = ["ты самый лучший человек на свете, ", "твоя улыбка согревает меня, ", "с тобой так тепло и уютно, ", "я так рад, что ты у меня есть, "]
        e = ["и я тебя очень люблю! 🤍", "и это делает меня счастливым! 🥰", "спасибо, что ты рядом! ✨", "давай обниматься! 🤗"]
    elif char == "rude":
        s = ["Слушай, ", "Ну чего тебе, ", "Опять ты, ", "Может хватит уже, "]
        m = ["пристаешь ко мне со своими вопросами, ", "не даешь мне спокойно полежать, ", "мешаешь мне спать, "]
        e = ["дай мне поспать! 😒", "иди лучше поиграй! 😤", "я вообще-то занят! 🙄"]
    elif char == "smart":
        s = ["Знаешь ли ты, что ", "Интересный факт: ", "С точки зрения науки, "]
        m = ["осьминоги имеют три сердца, ", "медведи бегают 50 км/ч, ", "вода закипает при 100 градусах, "]
        e = ["а ты знал об этом? 🧠", "и это невероятно! 🤓", "познавательно, не так ли? 🧐"]
    else:
        s = ["ААА! ", "Слушай, слушай! ", "Внезапно, ", "БУ! "]
        m = ["а что если облака из ваты, ", "я нашел вчера банан, ", "мне кажется, я умею летать, "]
        e = ["ДАВАЙ ВЫПЬЕМ ЧАЮ! 🤪", "ЭТО ЖЕ КРУТО! 😳", "АААА! 🚀"]

    phrase = random.choice(s) + random.choice(m) + random.choice(e)
    await message.answer(f"💬 {users[uid]['pet_name']}: «{phrase}»")

@dp.message(F.text == "🎁 Бонус")
async def daily_bonus(message: Message):
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    now = int(time.time())
    if now - users[uid].get('last_bonus', 0) < 86400:
        return await message.answer("⏳ Ты уже брал бонус сегодня!")
    users[uid]['coins'] += 100
    users[uid]['last_bonus'] = now
    save_db(users)
    await message.answer(f"🎁 **Бонус!** +100 🪙\nБаланс: {users[uid]['coins']}")

# --- МАГАЗИН И ИНВЕНТАРЬ ---
@dp.message(F.text == "🛒 Магазин")
async def shop_menu(message: Message):
    if is_spam(message.from_user.id): return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Еда", callback_data="cat_hunger"), InlineKeyboardButton(text="💧 Вода", callback_data="cat_thirst")],
        [InlineKeyboardButton(text="👟 Брендовая одежда", callback_data="cat_wear")]
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
        elif cat == "wear" and item['effect'] == 'wear': is_match = True
        elif cat == "mood" and item['effect'] == 'mood': is_match = True
        if is_match:
            kb_buttons.append([InlineKeyboardButton(text=f"{item['name']} - {item['price']}🪙", callback_data=f"buy_{item_id}")])
    kb_buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_shop")])
    await call.message.edit_text("Выбери товар:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))

@dp.callback_query(F.data == "back_shop")
async def back_shop(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Еда", callback_data="cat_hunger"), InlineKeyboardButton(text="💧 Вода", callback_data="cat_thirst")],
        [InlineKeyboardButton(text="👟 Брендовая одежда", callback_data="cat_wear")]
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
        kb_buttons.append([InlineKeyboardButton(text=f"Использовать {item_name} (x{count})", callback_data=f"use_{item_id}")])
    await message.answer("🎒 **Твой инвентарь**\nНажми, чтобы использовать/надеть:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))

@dp.callback_query(F.data.startswith("use_"))
async def use_item(call: CallbackQuery):
    if is_spam(call.from_user.id): return await call.answer("Подожди!")
    users = load_db(); uid = str(call.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    item_id = call.data.replace("use_", "")
    inv = users[uid].get('inventory', {})
    if item_id not in inv or inv[item_id] <= 0: return await call.answer("Нет предмета!", show_alert=True)
    item = SHOP_ITEMS[item_id]
    
    if item['effect'] == 'wear':
        users[uid]['wearing'] = item['name']
        save_db(users)
        await send_card(call, users[uid], f"✨ *Ты надел на {users[uid]['pet_name']} {item['name']}!*")
        await call.answer()
        return

    inv[item_id] -= 1
    if inv[item_id] == 0: del inv[item_id]
    users[uid]['inventory'] = inv
    effect = item['effect']; val = item['value']
    if effect == "hunger": users[uid]['hunger'] = min(100, users[uid]['hunger'] + val)
    elif effect == "thirst": users[uid]['thirst'] = min(100, users[uid]['thirst'] + val)
    elif effect == "mood": users[uid]['mood'] = min(100, users[uid]['mood'] + val)

    users[uid]['last_update'] = int(time.time())
    add_xp(users[uid], 5)
    save_db(users)
    
    action_text = item.get('text', "✨ *Что-то происходит...*").replace("[Имя]", users[uid]['pet_name'])
    end_text = item.get('end', "✨ *Класс!*")
    await send_card(call, users[uid], f"{action_text}\n{end_text}")
    await call.answer()

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
    users = load_db()
    is_dead = users.get(target, {}).get('is_dead', False)
    revive_btn = [InlineKeyboardButton(text="🕯 Воскресить", callback_data=f"rev_{target}")] if is_dead else []
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="+ 100 🪙", callback_data=f"gv_{target}_100")],
        [InlineKeyboardButton(text="+ 500 🪙", callback_data=f"gv_{target}_500")],
        [InlineKeyboardButton(text="✍️ Ввести сумму", callback_data=f"custom_give_{target}")],
        *([revive_btn] if revive_btn else []),
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])
    await call.message.edit_text(f"Действие для ID `{target}`:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("rev_"))
async def admin_revive(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    target = call.data.replace("rev_", "")
    users = load_db()
    if target in users:
        users[target]['is_dead'] = False
        users[target]['hunger'] = 100
        users[target]['thirst'] = 100
        users[target]['energy'] = 100
        users[target]['mood'] = 100
        save_db(users)
        await call.answer("✅ Успешно воскрешен!")
        await admin_user(call)

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
