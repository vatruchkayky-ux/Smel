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

# --- 100 ФРАЗ ДЛЯ КНОПКИ "ПОГОВОРИТЬ" (МИЛЫЙ) ---
CUTE_PHRASES = [
    "Ты самый лучший человек на свете! 🤍", "Я так рад, что ты у меня есть.", "Обнимаю тебя крепко-крепко! 🤗",
    "Ты мое солнышко ☀️", "С тобой так тепло и уютно.", "Спасибо, что ты рядом! ✨", "Ты делаешь этот мир добрее.",
    "Я тебя очень-очень люблю!", "Ты мой самый любимый друг.", "Я скучал по тебе! 🥰", "Ты такой замечательный!",
    "Мне так повезло с тобой.", "Твоя улыбка согревает меня.", "Я хочу всегда быть с тобой.", "Ты мой герой! 🦸‍♂️",
    "Я так счастлив, когда ты заходишь.", "Ты мой лучик света в темноте.", "Давай обнимемся виртуально!",
    "Я тебя ценю больше всего на свете.", "Ты делаешь меня лучше.", "Я всегда тебя поддержу.", "Ты классный!",
    "Мне нравится, когда ты со мной.", "Ты мой самый близкий человек.", "Я тебя никогда не брошу.",
    "Ты моя самая большая радость.", "Я хочу, чтобы ты улыбался(ась).", "Спасибо, что заботишься обо мне.",
    "Я так тебе благодарен(на).", "Ты мой самый верный друг.", "Я тебя обожаю!", "Ты мой кумир!",
    "Я готов(а) ради тебя на всё.", "Ты самый добрый человек.", "Мне так спокойно с тобой.",
    "Ты мое вдохновение.", "Я хочу тебя порадовать.", "Ты мой самый лучший подарок.", "Я тебя очень ждал(а)!",
    "Мне тебя не хватает.", "Ты моя отрада.", "Я так рад(а) тебя видеть.", "Ты мой самый любимый человечек.",
    "Я хочу тебя обнять.", "Ты мой самый дорогой.", "Я тебя не забуду.", "Ты мой самый лучший.",
    "Я так тебе рад(а).", "Ты мой самый близкий.", "Я хочу с тобой дружить вечно.", "Ты мой самый родной.",
    "Я тебя очень ценю.", "Ты мой самый важный.", "Я хочу тебя слышать.", "Ты мой самый теплый.",
    "Я тебя очень люблю!", "Ты мой самый нежный.", "Я хочу тебя видеть.", "Ты мой самый яркий.",
    "Я тебя очень жду.", "Ты мой самый светлый.", "Я хочу с тобой быть.", "Ты мой самый лучший!",
    "Я тебя очень хочу.", "Ты мой самый милый.", "Я хочу тебя обнять!", "Ты мой самый классный.",
    "Я тебя очень сильно люблю.", "Ты мой самый добрый.", "Я хочу с тобой играть.", "Ты мой самый лучший друг!",
    "Я тебя очень обнимаю.", "Ты мой самый сладкий.", "Я хочу тебя порадовать!", "Ты мой самый любимый!",
    "Я тебя очень целую.", "Ты мой самый теплый.", "Я хочу с тобой гулять.", "Ты мой самый хороший.",
    "Я тебя очень жду!", "Ты мой самый нежный.", "Я хочу тебя обнять!", "Ты мой самый лучший!",
    "Я тебя очень люблю!", "Ты мой самый добрый.", "Я хочу с тобой дружить.", "Ты мой самый классный.",
    "Я тебя очень обнимаю!", "Ты мой самый сладкий.", "Я хочу тебя порадовать!", "Ты мой самый любимый!",
    "Я тебя очень ценю.", "Ты мой самый теплый.", "Я хочу с тобой играть.", "Ты мой самый милый.",
    "Я тебя очень люблю!", "Ты мой самый лучший.", "Я хочу тебя обнять!", "Ты мой самый лучший друг!"
]

# --- 100 ФРАЗ ДЛЯ КНОПКИ "ПОГОВОРИТЬ" (ВРЕДНЫЙ) ---
RUDE_PHRASES = [
    "Че пристал(а)? 😒", "Дай поспать! 😤", "Опять ты? 🙄", "Иди лучше поиграй!", "Мне скучно...",
    "Отстань от меня!", "Я вообще-то занят(а)!", "Не трогай меня!", "Оставь меня в покое!",
    "Ну и чего тебе надо?", "Я не хочу с тобой разговаривать.", "Уйди!", "Я тебя не звал(а).",
    "Ты меня достал(а).", "Мне надоело.", "Я устал(а).", "Не сейчас.", "Может потом?",
    "Я не в настроении.", "Оставь меня.", "Не сейчас.", "Я занят(а).", "Уйди.", "Не трогай.",
    "Мне не до тебя.", "Я сплю.", "Отвали.", "Иди отсюда.", "Не мешай.", "Я не хочу.", "Хватит.",
    "Я не хочу.", "Отстань.", "Уйди.", "Не мешай.", "Мне надоело.", "Я устал(а).", "Не сейчас.",
    "Может потом?", "Я не в настроении.", "Оставь меня.", "Не сейчас.", "Я занят(а).", "Уйди.",
    "Не трогай.", "Мне не до тебя.", "Я сплю.", "Отвали.", "Иди отсюда.", "Не мешай.", "Я не хочу.",
    "Хватит.", "Я не хочу.", "Отстань.", "Уйди.", "Не мешай.", "Мне надоело.", "Я устал(а).",
    "Не сейчас.", "Может потом?", "Я не в настроении.", "Оставь меня.", "Не сейчас.", "Я занят(а).",
    "Уйди.", "Не трогай.", "Мне не до тебя.", "Я сплю.", "Отвали.", "Иди отсюда.", "Не мешай.",
    "Я не хочу.", "Хватит.", "Я не хочу.", "Отстань.", "Уйди.", "Не мешай.", "Мне надоело.",
    "Я устал(а).", "Не сейчас.", "Может потом?", "Я не в настроении.", "Оставь меня.", "Не сейчас.",
    "Я занят(а).", "Уйди.", "Не трогай.", "Мне не до тебя.", "Я сплю.", "Отвали.", "Иди отсюда.",
    "Не мешай.", "Я не хочу.", "Хватит.", "Я не хочу.", "Отстань.", "Уйди.", "Не мешай.", "Мне надоело."
]

# --- 100 ФРАЗ ДЛЯ КНОПКИ "ПОГОВОРИТЬ" (УМНЫЙ) ---
SMART_PHRASES = [
    "У осьминога три сердца. 🧠", "Медведи могут бегать до 50 км/ч.", "Вода закипает при 100 градусах.",
    "Люди используют только 10% мозга (на самом деле это миф).", "Молния бьет в землю 100 раз в секунду.",
    "Улитки могут спать по три года.", "Сердце креветки находится в ее голове.", "У слонов отличная память.",
    "Дельфины спят с одним открытым глазом.", "Коровы имеют лучших друзей.", "Бабочки пробуют еду лапками.",
    "Пчелы видят ультрафиолет.", "Акулы живут дольше, чем деревья.", "У жирафа такое же количество шейных позвонков, как у человека.",
    "Пингвины делают предложение, даря камни.", "Коалы спят по 22 часа в сутки.", "У тигров кожа полосатая, а не только мех.",
    "Крокодилы не могут высовывать язык.", "Совы не могут двигать глазами.", "Змеи слышат через челюсти.",
    "У лошадей почти фотографическая память.", "Кролики едят свои испражнения.", "Собаки видят сны.",
    "Кошки не чувствуют сладкий вкус.", "У муравьев нет легких.", "Пауки имеют восемь глаз.",
    "У медуз нет мозга и сердца.", "Кит может утонуть, если пробудет под водой слишком долго.",
    "Страусы не прячут голову в песок.", "Слоны боятся пчел.", "Ленивцы спускаются с деревьев раз в неделю.",
    "У панды шесть пальцев.", "Колибри не могут ходить.", "У улитки тысячи зубов.",
    "У морской звезды нет мозга.", "Кальмары имеют три сердца.", "У пауков голубая кровь.",
    "У осьминогов квадратные зрачки.", "Муравьи могут поднимать в 50 раз больше своего веса.",
    "У жирафов синий язык.", "У ворон есть чувство юмора.", "Свиньи видят небо.",
    "У коз прямоугольные зрачки.", "Крысы смеются, когда их щекочут.", "У кальмаров 10 щупалец.",
    "У пчел пять глаз.", "Собаки потеют через лапы.", "У кошек 32 мышцы в каждом ухе.",
    "Лошади не могут дышать ртом.", "У страусов глаза больше, чем мозг.", "У тигров полосатая кожа.",
    "У пингвинов есть колени.", "У дельфинов есть имена.", "У слонов нет костей в хоботе.",
    "У жирафов черный язык.", "У акул нет костей.", "У креветок сердце в голове.",
    "У муравьев есть социальные сети (феромоны).", "У пауков есть когти.", "У змей нет век.",
    "У крокодилов есть зубы в желудке.", "У сов нет зубов.", "У лошадей есть копыта.",
    "У кошек есть третье веко.", "У собак есть третье веко.", "У слонов есть бивни.",
    "У китов есть волосы.", "У дельфинов есть спинной плавник.", "У акул есть чешуя.",
    "У пингвинов есть перья.", "У страусов есть перья.", "У сов есть перья.",
    "У тигров есть когти.", "У львов есть грива.", "У гепардов есть пятна.",
    "У леопардов есть розетки.", "У ягуаров есть пятна.", "У пум есть однотонный мех.",
    "У рыси есть кисточки на ушах.", "У каракала есть большие уши.", "У сервала есть длинные ноги.",
    "У оцелота есть пятна.", "У манула есть толстый мех.", "У саванной кошки есть длинные лапы.",
    "У черной пантеры есть темный мех.", "У белого тигра есть голубые глаза.", "У снежного барса есть длинный хвост."
]

# --- 100 ФРАЗ ДЛЯ КНОПКИ "ПОГОВОРИТЬ" (БЕЗУМНЫЙ) ---
CRAZY_PHRASES = [
    "ААА! БАНАНЫ! 🤪", "Я умею летать! 🚀", "ДАВАЙ ВЫПЬЕМ ЧАЮ! 😳", "Я инопланетянин! 👽",
    "Мне кажется, я умею телепортироваться.", "А что если облака из ваты?", "Я нашел вчера банан.",
    "Я хочу быть космонавтом!", "Давай построим ракету из носков!", "Я вижу звуки!",
    "Мои мысли звучат как музыка.", "Я умею разговаривать с тенями.", "Я хочу съесть луну!",
    "Я спрятал(а) сокровище под кроватью.", "У меня есть невидимый друг.", "Я умею ходить по потолку.",
    "Я хочу стать драконом!", "Давай полетим на Марс?", "Я нашел портал в другом месте.",
    "Я умею превращаться в кота.", "Я хочу танцевать под дождем.", "Я вижу будущее!",
    "Я умею читать мысли.", "Я нашел клад!", "Я хочу быть пиратом!", "Я умею летать во сне.",
    "Я хочу построить замок из песка.", "Я умею говорить с животными.", "Я нашел волшебную палочку.",
    "Я хочу стать президентом.", "Я умею плавать в облаках.", "Я нашел звезду.",
    "Я хочу поймать ветер.", "Я умею готовить из ничего.", "Я нашел дверь в другой мир.",
    "Я хочу стать супергероем.", "Я умею летать на метле.", "Я нашел старую карту.",
    "Я хочу найти единорога.", "Я умею говорить с камнями.", "Я нашел волшебный камень.",
    "Я хочу стать волшебником.", "Я умею летать на драконе.", "Я нашел клад пиратов.",
    "Я хочу стать русалкой.", "Я умею дышать под водой.", "Я нашел старый сундук.",
    "Я хочу стать феей.", "Я умею летать на ковре-самолете.", "Я нашел волшебную лампу.",
    "Я хочу стать эльфом.", "Я умею говорить с деревьями.", "Я нашел волшебное кольцо.",
    "Я хочу стать гномом.", "Я умею летать на облаке.", "Я нашел волшебную книгу.",
    "Я хочу стать троллем.", "Я умею говорить с реками.", "Я нашел волшебный посох.",
    "Я хочу стать орком.", "Я умею летать на звезде.", "Я нашел волшебную палочку.",
    "Я хочу стать гоблином.", "Я умею говорить с горами.", "Я нашел волшебный меч.",
    "Я хочу стать хоббитом.", "Я умею летать на ветре.", "Я нашел волшебный щит.",
    "Я хочу стать магом.", "Я умею говорить с огнем.", "Я нашел волшебный шлем.",
    "Я хочу стать воином.", "Я умею летать на молнии.", "Я нашел волшебные сапоги.",
    "Я хочу стать лучником.", "Я умею говорить с водой.", "Я нашел волшебный лук.",
    "Я хочу стать вором.", "Я умею летать на туче.", "Я нашел волшебный плащ.",
    "Я хочу стать бардом.", "Я умею говорить с землей.", "Я нашел волшебную арфу.",
    "Я хочу стать жрецом.", "Я умею летать на вихре.", "Я нашел волшебный амулет.",
    "Я хочу стать паладином.", "Я умею говорить с воздухом.", "Я нашел волшебный крест.",
    "Я хочу стать друидом.", "Я умею летать на смерче.", "Я нашел волшебный посох.",
    "Я хочу стать шаманом.", "Я умею говорить с духами.", "Я нашел волшебный бубен.",
    "Я хочу стать некромантом.", "Я умею летать на костях.", "Я нашел волшебный череп.",
    "Я хочу стать демоном.", "Я умею говорить с тьмой.", "Я нашел волшебный рог."
]

# --- 100 ФРАЗ ДЛЯ ОБЩЕНИЯ (ПРОСТО ТАК) ---
CHAT_PHRASES = [
    "Привет! Как у тебя дела? 😊", "Я тут сижу, скучаю по тебе...", "Как проходит твой день?", "Мне сегодня снился очень странный сон!",
    "Знаешь, я очень рад, что ты у меня есть.", "О чем ты сейчас думаешь?", "Я просто хотел сказать тебе привет 👋",
    "У меня всё отлично! А у тебя?", "Мне немного скучно, давай поиграем?", "Я тут подумал... а мы классная команда!",
    "Ты сегодня уже кушал(а)?", "Я смотрю в окно и вижу птичек 🐦", "Как настроение?", "Я тебя жду!",
    "Мне так тепло и уютно, когда ты заходишь.", "А помнишь, как мы начинали?", "Я чувствую себя счастливым! 🥰",
    "Чем занимаешься?", "Как работа/учеба?", "Я только что поймал муху! 🦟", "Не забывай отдыхать, хорошо?",
    "Ты мой самый любимый человек!", "Я немного устал, но не хочу спать.", "Давай помечтаем о чем-нибудь?",
    "У тебя красивый аватар!", "Я тут придумал новую игру в голове.", "Я так рад тебя видеть снова!",
    "Мне нравится, когда ты нажимаешь на кнопочки.", "Как погода на улице?", "Я спрятался под одеяло, тут тепло.",
    "Не грусти, если что! Я рядом.", "Ты лучший!", "Я немного проголодался, если честно...", "Чего бы нам сегодня поделать?",
    "Я скучал!", "Как ты спал(а)?", "Мне приснилась гора конфет!", "Ты видел(а) что-нибудь интересное сегодня?",
    "Я тут размышлял о жизни...", "Давай просто помолчим вместе?", "Я всегда рядом, помни это.", "Ты классный!",
    "Я тут нашел пылинку и играю с ней.", "Как твои дела на самом деле?", "Мне немного одиноко без тебя.",
    "Спасибо, что заботишься обо мне.", "Я пою песенку про себя: ля-ля-ля!", "Ты когда-нибудь видел(а) звезды днем?",
    "Я хочу обнимашек! 🤗", "Ты мой герой!", "У меня хорошее настроение!", "Что нового?",
    "Я тут споткнулся о воздух...", "Время летит незаметно.", "Я хочу вкусняшку!", "Ты мой лучший друг!",
    "Не забывай пить водичку!", "Я представляю, как мы гуляем по парку.", "А что ты сегодня ел(а)?", "Я такой сонный...",
    "Ты поднимаешь мне настроение!", "Я пытался поймать свой хвост...", "Мне так повезло с тобой.",
    "Давай обнимемся виртуально!", "Ты веришь в чудеса?", "Я только что чихнул!", "Как твой день проходит?",
    "Я тебя очень жду!", "Ты мой солнечный лучик ☀️", "Мне нравится наш чат.", "Я тут убираюсь в своей комнате.",
    "Я хочу на природу!", "Ты когда-нибудь мечтал(а) о полете?", "Я немного завидую птицам.",
    "Спасибо, что ты есть.", "Как настроение сегодня?", "Я тут вспоминал наши приключения.", "Мне так спокойно с тобой.",
    "Я хочу танцевать! 💃", "Ты видел(а), как я расту?", "Я учусь новым трюкам.", "Мне нужен твой совет... шучу!",
    "Ты мой любимый человек во вселенной.", "Я чувствую себя суперзвездой!", "Давай сегодня что-нибудь купим?", "Я просто хотел напомнить, что я есть.",
    "Ты не забыл(а) про меня?", "Я тут рисую в блокноте.", "У меня чешется лапка.", "Я так рад, что ты заботишься обо мне.",
    "Ты мой лучший мотиватор!", "Я хочу пить...", "Я тут придумал считалочку.", "Мне снилось, что я стал президентом.",
    "Как твои успехи?", "Я болею за тебя!", "Ты справишься со всем!", "Я тут просто валяюсь.", "Мне так хорошо!",
    "Спасибо за всё!", "Ты классно выглядишь сегодня.", "Я хочу путешествовать.", "Давай завтра будет лучше, чем вчера!"
]

# --- 100 ФРАЗ ДЛЯ СЛУЧАЙНЫХ СОБЫТИЙ ---
EVENT_PHRASES = [
    "Ой! Я упал с кровати... 🤕", "Я испачкался в грязи, нужно помыться! 🦨", "Ура! Я нашел монетку на полу! 🪙",
    "Я случайно разбил вазу... 🏺", "Я наступил в лужу!", "Мне кажется, я простудился... 🤧", "Я нашел красивый камушек!",
    "Я застрял в коробке, помоги!", "Ой, я уронил еду на пол...", "Я нашел блестящую пуговицу!", "Я поцарапал лапку... 🩹",
    "Я объелся сладкого, болит животик... 🤢", "Я нашел старую книгу и читаю её.", "Я поймал бабочку! 🦋",
    "Я случайно порвал свои любимые штаны...", "Я нашел коробку, а там кто-то шуршит!", "Я уснул в странной позе и затекла лапка.",
    "Я уронил телефон... (шучу, у меня нет телефона)", "Я нашел монетку в кармане!", "Я испугался(ась) громкого звука!",
    "Я нашел красивый цветочек 🌸", "Я пролил воду на пол...", "Я залез на шкаф и не могу слезть!",
    "Я нашел что-то вкусненькое за диваном.", "Ой, я чихнул и уронил подушку.", "Я нашел старую игрушку!",
    "Я запутался в одеяле...", "Я увидел тень и испугался.", "Я нашел блестящую фольгу!", "Я поскользнулся на мокром полу.",
    "Я случайно укусил(а) себя за хвост.", "Я нашел пустую коробку и сижу в ней.", "Я слишком громко мяукнул(а) и смутился(ась).",
    "Я нашел палочку! Она моя! ", "Я залез в шкаф и меня там заперло.", "Я нашел монетку под подушкой!", "Я слишком много бегал(а) и устал(а).",
    "Я случайно опрокинул(а) миску с водой.", "Я нашел старый носок и играю с ним.", "Я испугался(ась) пылесоса.", "Я нашел конфетку!",
    "Я зацепился(ась) за гвоздь...", "Я уронил(а) свой любимый мячик.", "Я нашел что-то странное и обнюхал(а).",
    "Я случайно разбудил(а) соседа.", "Я нашел зеркало и смотрю в него.", "Я проглотил(а) пылинку и кашляю.", "Я нашел блестящую бусинку!",
    "Я слишком высоко прыгнул(а) и ударился(ась).", "Я нашел старую фотографию.", "Я испачкал(а) нос в чем-то липком.",
    "Я нашел красивую ленточку!", "Я случайно съел(а) что-то не то...", "Я нашел пуговицу от рубашки.",
    "Я слишком долго смотрел(а) в экран.", "Я нашел кусочек пазла!", "Я случайно наступил(а) на свой хвост.",
    "Я нашел что-то под ковром.", "Я упал(а) вверх тормашками!", "Я нашел блестящую монетку в траве!",
    "Я случайно сломал(а) карандаш.", "Я нашел старую открытку.", "Я слишком громко замурчал(а).", "Я нашел пустую банку!",
    "Я испугался(ась) своего отражения.", "Я нашел что-то интересное в шкафу.", "Я случайно порвал(а) бумажку.",
    "Я нашел старую заколку.", "Я уронил(а) книгу на лапку.", "Я нашел красивый листик 🍁",
    "Я случайно задел(а) чашку.", "Я нашел старую монету!", "Я слишком быстро бежал(а) и врезался(ась) в дверь.",
    "Я нашел блестящую фольгу от конфеты.", "Я случайно наступил(а) в краску.", "Я нашел что-то в кармане куртки.",
    "Я уронил(а) свой ужин...", "Я нашел старый ключ.", "Я слишком громко зевнул(а).", "Я нашел красивую ракушку!",
    "Я случайно намочил(а) лапки.", "Я нашел старую пуговицу.", "Я испугался(ась) грозы.", "Я нашел блестящую монетку на улице!",
    "Я случайно уронил(а) стакан.", "Я нашел старую игрушку под кроватью.", "Я слишком высоко залез(ла).", "Я нашел красивый камушек на прогулке!",
    "Я случайно наступил(а) на что-то острое.", "Я нашел старую газету.", "Я слишком громко крикнул(а).", "Я нашел блестящую булавку!",
    "Я случайно опрокинул(а) стул.", "Я нашел старый блокнот.", "Я испугался(ась) громкого звука на улице.", "Я нашел что-то интересное в сумке.",
    "Я случайно порвал(а) обои.", "Я нашел старую монетку в ящике стола!", "Я слишком долго спал(а).", "Я нашел красивый цветок на клумбе!",
    "Я случайно наступил(а) на хвост соседу.", "Я нашел старую открытку под дверью.", "Я слишком громко чихнул(а).", "Я нашел блестящую пуговицу на полу!"
]

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

# --- ПОЛНЫЙ АССОРТИМЕНТ + БРЕНДЫ ---
SHOP_ITEMS = {
    # ЕДА
    "apple": {"name": "🍎 Яблоко", "price": 15, "effect": "hunger", "value": 10, "text": "🍎 [Имя] берет яблоко...", "end": "✨ Сочное!"},
    "burger": {"name": "🍔 Бургер", "price": 40, "effect": "hunger", "value": 30, "text": "🍔 [Имя] ест бургер...", "end": "✨ Обожаю фастфуд!"},
    "pizza": {"name": "🍕 Пицца", "price": 80, "effect": "hunger", "value": 50, "text": "🍕 [Имя] ест пиццу...", "end": "✨ Сыр тянется!"},
    "sushi": {"name": "🍣 Суши", "price": 100, "effect": "hunger", "value": 60, "text": "🍣 [Имя] ест суши...", "end": "✨ Васаби!"},
    "taco": {"name": "🌮 Тако", "price": 50, "effect": "hunger", "value": 35, "text": "🌮 [Имя] ест тако...", "end": "✨ Остро!"},
    "donut": {"name": "🍩 Пончик", "price": 25, "effect": "hunger", "value": 15, "text": "🍩 [Имя] ест пончик...", "end": "✨ Сладко!"},
    "steak": {"name": "🥩 Стейк", "price": 150, "effect": "hunger", "value": 80, "text": "🥩 [Имя] ест стейк...", "end": "✨ Мясо!"},
    "salad": {"name": "🥗 Салат", "price": 30, "effect": "hunger", "value": 20, "text": "🥗 [Имя] ест салат...", "end": "✨ Полезно!"},
    "cake": {"name": "🍰 Тортик", "price": 60, "effect": "hunger", "value": 40, "text": "🍰 [Имя] ест тортик...", "end": "✨ Сладко!"},
    "chocolate": {"name": "🍫 Шоколад", "price": 20, "effect": "hunger", "value": 10, "text": "🍫 [Имя] ест шоколад...", "end": "✨ Вкусно!"},

    # ВОДА
    "water": {"name": "🥛 Вода", "price": 10, "effect": "thirst", "value": 15, "text": "🥛 [Имя] пьет воду...", "end": "✨ Освежает!"},
    "cola": {"name": "🥤 Кола", "price": 25, "effect": "thirst", "value": 25, "text": "🥤 [Имя] пьет колу...", "end": "✨ Пузырьки!"},
    "pepsi": {"name": "🥤 Пепси", "price": 25, "effect": "thirst", "value": 25, "text": "🥤 [Имя] пьет пепси...", "end": "✨ Классика!"},
    "juice": {"name": "🧃 Сок", "price": 30, "effect": "thirst", "value": 30, "text": "🧃 [Имя] пьет сок...", "end": "✨ Витамины!"},
    "coffee": {"name": "☕ Кофе", "price": 40, "effect": "thirst", "value": 20, "text": "☕ [Имя] пьет кофе...", "end": "✨ Проснулся!"},
    "tea": {"name": "🍵 Чай", "price": 20, "effect": "thirst", "value": 15, "text": "🍵 [Имя] пьет чай...", "end": "✨ Уютно!"},
    "energy": {"name": "⚡ Энергетик", "price": 50, "effect": "thirst", "value": 50, "text": "⚡ [Имя] пьет энергетик...", "end": "✨ Горы сверну!"},
    "milkshake": {"name": "🥤 Милкшейк", "price": 60, "effect": "thirst", "value": 40, "text": "🥤 [Имя] пьет милкшейк...", "end": "✨ Ням!"},
    "lemonade": {"name": "🍋 Лимонад", "price": 35, "effect": "thirst", "value": 30, "text": "🍋 [Имя] пьет лимонад...", "end": "✨ Кисло-сладко!"},
    "smoothie": {"name": "🍹 Смузи", "price": 70, "effect": "thirst", "value": 45, "text": "🍹 [Имя] пьет смузи...", "end": "✨ Полезно!"},

    # МЕДИЦИНА
    "pill": {"name": "💊 Таблетка", "price": 100, "effect": "heal", "value": 1, "text": "💊 [Имя] пьет таблетку...", "end": "✨ Здоров!"},
    "bandage": {"name": "🩹 Бинт", "price": 50, "effect": "heal", "value": 1, "text": "🩹 [Имя] мотает бинт...", "end": "✨ Заживет!"},
    "soap": {"name": "🧼 Мыло", "price": 40, "effect": "wash", "value": 1, "text": "🧼 [Имя] моется...", "end": "✨ Чистый!"},

    # УЮТ
    "pillow": {"name": "🛏 Подушка", "price": 100, "effect": "energy", "value": 30, "text": "🛏 [Имя] ложится на подушку...", "end": "✨ Мягко!"},
    "blanket": {"name": "🛌 Одеяло", "price": 200, "effect": "energy", "value": 50, "text": "🛌 [Имя] укрывается одеялом...", "end": "✨ Тепло!"},
    "bed": {"name": "🛏 Кровать", "price": 500, "effect": "energy", "value": 100, "text": "🛏 [Имя] прыгает на кровать...", "end": "✨ Сон!"},

    # РАЗВЛЕЧЕНИЯ
    "ball": {"name": "⚽ Мячик", "price": 70, "effect": "mood", "value": 25, "text": "⚽ [Имя] берет мячик...", "end": "✨ Играем!"},
    "toy": {"name": "🧸 Игрушка", "price": 120, "effect": "mood", "value": 40, "text": "🧸 [Имя] обнимает игрушку...", "end": "✨ Мило!"},
    "game": {"name": "🎮 Игра", "price": 300, "effect": "mood", "value": 70, "text": "🎮 [Имя] играет...", "end": "✨ Победа!"},
    "vr": {"name": "🕶 VR-очки", "price": 800, "effect": "mood", "value": 100, "text": "🕶 [Имя] надевает VR...", "end": "✨ Другой мир!"},

    # БАР
    "beer": {"name": "🍺 Пиво", "price": 60, "effect": "mood", "value": 20, "text": "🍺 [Имя] пьет пиво...", "end": "✨ Опьянел!"},
    "wine": {"name": "🍷 Вино", "price": 150, "effect": "mood", "value": 35, "text": "🍷 [Имя] пьет вино...", "end": "✨ Букет!"},
    "vodka": {"name": "🥃 Водка", "price": 200, "effect": "mood", "value": 50, "text": "🥃 [Имя] пьет водку...", "end": "✨ Кружится голова!"},
    "whiskey": {"name": "🥃 Виски", "price": 300, "effect": "mood", "value": 60, "text": "🥃 [Имя] пьет виски...", "end": "✨ Аристократ!"},
    "champagne": {"name": "🍾 Шампанское", "price": 500, "effect": "mood", "value": 80, "text": "🍾 [Имя] открывает шампанское...", "end": "✨ Ура!"},
    "mojito": {"name": "🍹 Мохито", "price": 250, "effect": "mood", "value": 45, "text": "🍹 [Имя] размешивает мохито...", "end": "✨ Мята!"},
    "cocktail": {"name": "🍸 Коктейль", "price": 220, "effect": "mood", "value": 40, "text": "🍸 [Имя] берет коктейль...", "end": "✨ Танцую!"},

    # АКСЕССУАРЫ
    "hat": {"name": "🎩 Шляпа", "price": 150, "effect": "wear", "value": 1, "text": "🎩 [Имя] надевает шляпу...", "end": "✨ Стильно!"},
    "bow": {"name": "🎀 Бантик", "price": 100, "effect": "wear", "value": 1, "text": "🎀 [Имя] завязывает бантик...", "end": "✨ Прелесть!"},
    "nike": {"name": "👟 Кроссовки Nike", "price": 500, "effect": "wear", "value": 1, "text": "👟 [Имя] надевает Nike...", "end": "✨ Just Do It!"},
    "adidas": {"name": "🧥 Худи Adidas", "price": 400, "effect": "wear", "value": 1, "text": "🧥 [Имя] надевает Adidas...", "end": "✨ Немецкое качество!"},
    "gucci": {"name": "🕶 Очки Gucci", "price": 800, "effect": "wear", "value": 1, "text": "🕶 [Имя] надевает Gucci...", "end": "✨ Люксовый стиль!"},
    "rolex": {"name": "⌚ Часы Rolex", "price": 1500, "effect": "wear", "value": 1, "text": "⌚ [Имя] надевает Rolex...", "end": "✨ Время — деньги!"},
    "supreme": {"name": "🧢 Кепка Supreme", "price": 300, "effect": "wear", "value": 1, "text": "🧢 [Имя] надевает Supreme...", "end": "✨ Уличный стиль!"},
    "louis": {"name": "👜 Сумка Louis Vuitton", "price": 2000, "effect": "wear", "value": 1, "text": "👜 [Имя] берет LV...", "end": "✨ Дорого-богато!"},
    "prada": {"name": "👗 Платье Prada", "price": 2500, "effect": "wear", "value": 1, "text": "👗 [Имя] надевает Prada...", "end": "✨ Высокая мода!"},
}

DREAMS = ["🐑 [Имя] видит сон, как он прыгает по облакам...", "🍖 [Имя] снится огромная гора сосисок...", "🚀 [Имя] летит в космос на ракете из носков..."]

# --- ФОН (С РАНДОМНЫМИ СОБЫТИЯМИ) ---
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

                last_random = user.get('last_random_msg', 0)
                if current_time - last_random > random.randint(5400, 7200):
                    if user['hunger'] > 20 and user['thirst'] > 20:
                        if random.random() < 0.5:
                            msg = random.choice(CHAT_PHRASES)
                        else:
                            msg = random.choice(EVENT_PHRASES)
                        
                        try:
                            await bot.send_message(int(uid_str), f"💬 {user['pet_name']}:\n\n«{msg}»")
                            user['last_random_msg'] = current_time
                            changed = True
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
        "last_challenge": 0, "wearing": "Ничего", "last_random_msg": 0
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

# --- ИСПЫТАНИЯ ---
@dp.message(F.text == "🎯 Испытание")
async def challenge_menu(message: Message, state: FSMContext):
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users: return
    now = int(time.time())
    if now - users[uid].get('last_challenge', 0) < 86400:
        return await message.answer("⏳ Ты уже выполнял испытание сегодня. Возвращайся завтра!")
    
    ctype = random.choice(["word", "math"])
    if ctype == "word":
        tasks = [("Напиши слово 'пожалуйста'", "пожалуйста"), ("Напиши 'я молодец'", "я молодец"), ("Скажи 'люблю'", "люблю")]
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

# --- ОБЩЕНИЕ (СО СПИСКАМИ) ---
@dp.message(F.text == "💬 Поговорить")
async def talk_to_pet(message: Message):
    if is_spam(message.from_user.id): return
    users = load_db(); uid = str(message.from_user.id)
    if uid not in users or users[uid].get('is_dead'): return
    if users[uid]['hunger'] < 30: return await message.answer(f"🍔 {users[uid]['pet_name']}: «Я очень голоден... Покорми меня».")
    
    char = users[uid]['pet_char']
    
    if char == "cute":
        phrase = random.choice(CUTE_PHRASES)
    elif char == "rude":
        phrase = random.choice(RUDE_PHRASES)
    elif char == "smart":
        phrase = random.choice(SMART_PHRASES)
    else:
        phrase = random.choice(CRAZY_PHRASES)

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
        [InlineKeyboardButton(text="🎩 Аксессуары", callback_data="cat_wear"), InlineKeyboardButton(text="🍺 Бар", callback_data="cat_mood")],
        [InlineKeyboardButton(text="💊 Аптека", callback_data="cat_heal"), InlineKeyboardButton(text="🛏 Уют", callback_data="cat_energy")]
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
        elif cat == "heal" and item['effect'] in ['heal', 'wash']: is_match = True
        elif cat == "energy" and item['effect'] == 'energy': is_match = True
        if is_match:
            kb_buttons.append([InlineKeyboardButton(text=f"{item['name']} - {item['price']}🪙", callback_data=f"buy_{item_id}")])
    kb_buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_shop")])
    await call.message.edit_text("Выбери товар:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))

@dp.callback_query(F.data == "back_shop")
async def back_shop(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Еда", callback_data="cat_hunger"), InlineKeyboardButton(text="💧 Вода", callback_data="cat_thirst")],
        [InlineKeyboardButton(text="🎩 Аксессуары", callback_data="cat_wear"), InlineKeyboardButton(text="🍺 Бар", callback_data="cat_mood")],
        [InlineKeyboardButton(text="💊 Аптека", callback_data="cat_heal"), InlineKeyboardButton(text="🛏 Уют", callback_data="cat_energy")]
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
    elif effect == "energy": users[uid]['energy'] = min(100, users[uid]['energy'] + val)
    elif effect == "heal": users[uid]['is_sick'] = False
    elif effect == "wash": users[uid]['is_dirty'] = False

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
