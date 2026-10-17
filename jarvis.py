import os
import sys
import socket
import zipfile

os.system("")


# ==========================================
# ПУТИ ДЛЯ EXE
# ==========================================

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def is_frozen():
    return getattr(sys, 'frozen', False)


if is_frozen():
    APP_DATA = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "JARVIS")
else:
    APP_DATA = os.path.dirname(os.path.abspath(__file__))

os.makedirs(APP_DATA, exist_ok=True)

CACHE_DIR = os.path.join(APP_DATA, "voice_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Папки пользователя — в домашней директории
JARVIS_HOME = os.path.join(os.path.expanduser("~"), "JARVIS")
os.makedirs(JARVIS_HOME, exist_ok=True)

PICTURES_DIR = os.path.join(JARVIS_HOME, "Screenshots")
os.makedirs(PICTURES_DIR, exist_ok=True)

PHOTOS_DIR = os.path.join(JARVIS_HOME, "Photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

RECORDINGS_DIR = os.path.join(JARVIS_HOME, "Recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

OCR_DIR = os.path.join(JARVIS_HOME, "OCR")
os.makedirs(OCR_DIR, exist_ok=True)

LAUNCH_COUNT_FILE = os.path.join(APP_DATA, "launch_count.txt")

NOTES_FILE = os.path.join(APP_DATA, "my_notes.json")
APPS_FILE = os.path.join(APP_DATA, "my_apps.json")
PASSWORDS_FILE = os.path.join(APP_DATA, "passwords.json")
CONFIG_FILE = os.path.join(APP_DATA, "config.json")
ICON_PATH = resource_path("icon.ico")


# ==========================================
# ИМПОРТЫ
# ==========================================

import speech_recognition as sr
import webbrowser
import subprocess
import pyautogui
import time
import ctypes
import json
import urllib.parse
import requests
import threading
import random
import pyperclip
import psutil
import winsound
import secrets
import string
import re
import asyncio
import hashlib
import edge_tts
import pytesseract
from PIL import Image, ImageGrab
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from colorama import init

init(autoreset=True, strip=True)

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient,
    QLinearGradient, QFont, QPainterPath
)
import math


# ==========================================
# ЦВЕТА
# ==========================================

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    CYAN    = "\033[38;5;51m"
    BLUE    = "\033[38;5;33m"
    GREEN   = "\033[38;5;46m"
    YELLOW  = "\033[38;5;226m"
    RED     = "\033[38;5;196m"
    MAGENTA = "\033[38;5;201m"
    WHITE   = "\033[38;5;255m"
    GRAY    = "\033[38;5;240m"
    ORANGE  = "\033[38;5;208m"
    PURPLE  = "\033[38;5;99m"


# ==========================================
# ПРОВЕРКА БИБЛИОТЕК
# ==========================================

try:
    import cv2
    CV2_AVAILABLE = True
except:
    CV2_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except:
    NUMPY_AVAILABLE = False

SCREEN_RECORD_AVAILABLE = CV2_AVAILABLE and NUMPY_AVAILABLE

try:
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except:
    MUTAGEN_AVAILABLE = False

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except:
    MEDIAPIPE_AVAILABLE = False


# === TESSERACT ===
tess_path = resource_path(os.path.join("tesseract", "tesseract.exe"))
if os.path.exists(tess_path):
    pytesseract.pytesseract.tesseract_cmd = tess_path
    os.environ["TESSDATA_PREFIX"] = resource_path(os.path.join("tesseract", "tessdata"))
    OCR_AVAILABLE = True
else:
    import shutil
    sys_tess = shutil.which("tesseract")
    if sys_tess:
        pytesseract.pytesseract.tesseract_cmd = sys_tess
        OCR_AVAILABLE = True
    else:
        OCR_AVAILABLE = False


# === VOSK ===
try:
    from vosk import Model, KaldiRecognizer
    import pyaudio
    PYAUDIO_AVAILABLE = True
    VOSK_AVAILABLE = True
except:
    PYAUDIO_AVAILABLE = False
    VOSK_AVAILABLE = False

VOSK_MODEL_PATH = resource_path("vosk-model-small-ru-0.22")
if VOSK_AVAILABLE and os.path.exists(VOSK_MODEL_PATH):
    try:
        vosk_model = Model(VOSK_MODEL_PATH)
    except:
        VOSK_AVAILABLE = False


# ==========================================
# ГЛОБАЛЬНЫЕ
# ==========================================

VOICE = "ru-RU-DmitryNeural"
VOICE_AVAILABLE = True
VOICE_ENABLED = True
speak_lock = threading.Lock()
gui = None
IS_SPEAKING = False
MIC_LOCK = threading.Lock()
CAMERA_LOCK = threading.Lock()
camera_busy = False


# ==========================================
# СЛОВАРИ КОМАНД
# ==========================================

SIMPLE_COMMANDS = {
    "time": ["время", "который час", "сколько времени", "текущее время",
             "время сейчас", "часы", "сколько время"],
    "screenshot": ["скриншот", "скрин", "снимок экрана", "скрин экрана",
                   "сделай скриншот", "снимок"],
    "volume_up": ["громче", "прибавь звук", "увеличь громкость", "громкость выше",
                  "сделай громче", "прибавь громкость", "громче звук"],
    "volume_down": ["тише", "убавь звук", "уменьши громкость", "громкость ниже",
                    "сделай тише", "убавь громкость", "тише звук"],
    "play_pause": ["пауза", "продолжи", "играй", "стоп музыка", "плей",
                   "плей пауза", "пауза музыка", "продолжи музыку"],
    "system_status": ["статус системы", "статус", "состояние системы",
                      "загрузка системы", "статус пк", "проверь систему"],
    "disk_space": ["свободное место", "сколько места", "место на диске",
                   "свободно на диске", "диск место", "сколько свободно"],
    "top_processes": ["топ процессов", "процессы", "загрузка процессов",
                      "что грузит цпу", "топ программ", "нагрузка на цпу"],
    "diagnostics": ["диагностика", "полная диагностика", "проверка системы",
                    "проверь всё", "диагностика пк", "полная проверка"],
    "ping": ["пинг", "проверь пинг", "пинг до гугла", "пинг гугла",
             "проверь интернет", "пинг 8.8.8.8"],
    "speedtest": ["скорость интернета", "тест скорости", "спидтест",
                  "проверь скорость", "скорость сети"],
    "temp": ["температура", "температура цпу", "температура процессора",
             "нагрев", "сколько градусов", "температура пк"],
    "battery": ["батарея", "заряд", "заряд батареи", "статус батареи",
                "сколько заряда", "уровень заряда"],
    "overheat": ["перегрев", "проверь перегрев", "не перегрелся ли",
                 "температура в норме", "перегревается"],
    "memory_leak": ["утечка памяти", "топ по памяти", "что жрёт память",
                    "топ процессов по рам", "память процессы"],
    "cache_clear": ["сбрось кэш", "очисти кэш", "сброс кэша",
                    "очисти временные", "почисти кэш"],
    "update_check": ["обнови себя", "проверь обновления", "обновления питона",
                     "проверь пакеты", "обнови пакеты"],
    "my_network": ["моя сеть", "мой айпи", "мой ip", "покажи сеть",
                   "информация о сети", "сетевые настройки"],
    "who_is_online": ["кто в сети", "устройства в сети", "локальная сеть",
                      "кто подключён", "сканируй сеть"],
    "dns_change": ["смени днс", "смени dns", "сменить днс",
                   "днс гугл", "днс клаудфлер"],
    "internet_off": ["отключи интернет", "выключи интернет", "нет интернета"],
    "internet_on": ["включи интернет", "верни интернет", "дай интернет"],
    "find_file": ["найди файл", "поиск файла", "где файл", "найти файл"],
    "big_files": ["что занимает место", "большие файлы", "топ файлов",
                  "самые большие файлы", "топ по размеру"],
    "duplicates": ["дубликаты", "найди дубликаты", "повторы файлов",
                   "одинаковые файлы"],
    "old_files": ["старые файлы", "старая папка", "файлы не изменялись",
                  "давно не открывал", "старьё"],
    "sort_downloads": ["сортируй загрузки", "сортировка загрузок",
                       "разбери загрузки", "порядок в загрузках"],
    "make_archive": ["в архив", "создай архив", "упакуй папку", "заархивируй"],
    "unpack_archive": ["из архива", "распакуй архив", "разархивируй"],
    "encrypt_file": ["зашифруй", "зашифруй файл", "шифрование", "закодируй файл"],
    "decrypt_file": ["расшифруй", "расшифруй файл", "дешифрование", "раскодируй"],
    "hide_folder": ["скрытая папка", "скрой папку", "сделай скрытой"],
    "show_notes": ["покажи заметки", "список заметок", "мои заметки", "заметки",
                   "все заметки", "что в заметках"],
    "show_reminders": ["покажи напоминания", "список напоминаний", "напоминания",
                       "мои напоминания", "активные напоминания"],
    "currency": ["курс", "курс доллара", "курс валют", "доллар", "евро",
                 "сколько стоит доллар", "валюты"],
    "weather": ["погода", "погода на улице", "какая погода", "погода сегодня",
                "погода сейчас", "прогноз погоды"],
    "joke": ["шутка", "расскажи шутку", "пошути", "анекдот", "рассмеши"],
    "fact": ["факт", "интересный факт", "расскажи факт", "факты",
             "интересное", "расскажи что-нибудь"],
    "password_generate": ["сгенерируй пароль", "пароль", "создай пароль",
                          "новый пароль", "случайный пароль"],
    "dice": ["брось кубик", "кубик", "кинь кубик", "дай кубик", "брось кость"],
    "lock": ["заблокируй компьютер", "заблокируй", "блокировка", "лок",
             "заблокируй пк", "заблокируй экран"],
    "sleep": ["спящий режим", "сон", "усни", "спать", "спящий", "режим сна"],
    "shutdown": ["выключи компьютер", "выключи", "завершение работы", "шатдаун",
                 "выключи пк", "выключение", "вырубай"],
    "restart": ["перезагрузи компьютер", "перезагрузка", "рестарт", "перезагрузи",
                "перезагрузи пк", "ребут"],
    "help": ["помощь", "что ты умеешь", "список команд", "команды",
             "что можешь", "помоги", "хелп"],
    "help_full": ["расширенная помощь", "полная помощь", "все команды",
                  "подробная помощь", "полный список команд"],
    "quiet_hour_on": ["тихий час", "замолчи", "тихо", "молчать", "тихий режим",
                      "выключи голос", "не говори", "тишина"],
    "quiet_hour_off": ["включи голос", "говори", "включи звук", "верни голос",
                       "разговаривай", "включи речь", "говори снова"],
    "history": ["история", "история команд", "что я делал", "последние команды",
                "покажи историю"],
    "repeat_last": ["повтор", "повтори", "повтор последнего", "что ты сказал"],
    "undo_last": ["отмени последнее", "отмена", "отмени", "верни как было"],
    "forgot": ["я забыл что хотел", "забыл", "что я хотел", "напомни что я делал"],
}

SITE_VARIANTS = {
    "вк": ["вк", "в контакте", "вконтакте", "вк контакте", "vk", "в ка", "вконтакт"],
    "ютуб": ["ютуб", "ю туп", "youtube", "ютюб", "ю туб", "ютуп", "ютубе", "ютуба"],
    "яндекс": ["яндекс", "ендекс", "я ндекс", "yandex", "яндек", "янекс", "индекс"],
    "гугл": ["гугл", "гугал", "google", "гугль", "гугле", "гугла", "гугол", "гугел"],
    "телеграм": ["телеграм", "телега", "telegram", "телеграмм", "теле гам", "тг"],
    "github": ["github", "гитхаб", "гит хаб", "гитхабе", "гитхаба", "гидхаб"],
    "реддит": ["реддит", "reddit", "редит", "ред ит", "реддите", "реддита"],
    "аниме": ["аниме", "anime", "анимего", "аниме го", "анимешка", "анимешку"],
    "стим": ["стим", "сти", "ским", "steam", "стимь", "стин", "стимо", "стиму", "стэм"],
    "гта": ["гта", "гэта", "гташка", "gta", "сан андреас", "гту", "гта 5", "гташку"],
    "майнкрафт": ["майн", "майнкрафт", "minecraft", "майк", "маенкрафт", "майне"],
    "дота": ["дота", "dota", "доту", "доточка", "дота2", "доте", "дотка"],
    "дискорд": ["дискорд", "discord", "дискорде", "дискорда", "дис", "диска"],
    "вотсап": ["вотсап", "whatsapp", "ватсап", "вотсапе", "вотсапа", "вацап"],
    "инстаграм": ["инстаграм", "instagram", "инста", "инсте", "инсту"],
    "тикток": ["тикток", "tiktok", "тик ток", "тиктоке", "тик тока"],
    "нетфликс": ["нетфликс", "netflix", "нетфликсе", "нетфликса"],
    "твич": ["твич", "twitch", "твиче", "твича"],
    "озон": ["озон", "ozon", "озоне", "озона"],
    "вайлдберриз": ["вайлдберриз", "wildberries", "вайлд"],
    "алиэкспресс": ["алиэкспресс", "aliexpress", "али"],
    "почта": ["почта", "mail", "почте", "почту"],
    "карты": ["карты", "maps", "карте", "карту"],
    "погода": ["погода", "weather", "погоде", "погоду"],
    "новости": ["новости", "news", "новостях", "новостей"],
    "переводчик": ["переводчик", "translate", "перевод"],
}

APP_VARIANTS = {
    "блокнот": ["блокнот", "блакнот", "блок нот", "notepad", "нотепад"],
    "калькулятор": ["калькулятор", "кальк", "калк", "calc"],
    "проводник": ["проводник", "explorer", "эксплорер"],
    "диспетчер": ["диспетчер", "диспетчер задач", "taskmgr", "таск менеджер"],
    "командная строка": ["командная строка", "командную строку", "cmd", "консоль", "терминал"],
    "панель управления": ["панель управления", "панель", "control"],
    "word": ["ворд", "word", "ворде"],
    "excel": ["эксель", "excel", "экселе"],
    "powerpoint": ["поверпоинт", "powerpoint", "пауэрпоинт"],
    "photoshop": ["фотошоп", "photoshop", "фотошопе"],
    "telegram desktop": ["телеграм десктоп", "telegram desktop"],
    "discord desktop": ["дискорд десктоп", "discord desktop"],
    "steam desktop": ["стим десктоп", "steam desktop"],
    "notepad++": ["нотепад плюс плюс", "notepad++"],
    "vs code": ["вс код", "vs code", "визуал студио код"],
    "pycharm": ["пайчарм", "pycharm", "пай чарм"],
    "sublime": ["саблайм", "sublime", "саблайм текст"],
    "7zip": ["семь зип", "7zip", "7 зип"],
    "winrar": ["винрар", "winrar", "вин рар"],
}


# ==========================================
# ФРАЗЫ ДЛЯ ПРЕДЗАГРУЗКИ
# ==========================================

PRELOAD_PHRASES = [
    "Доброе утро, сэр. Джарвис готов к работе.",
    "Искусственный интеллект активен.",
    "Обращайтесь ко мне по имени: Джарвис.",
    "Добро пожаловать, сэр. Я Джарвис.",
    "До свидания, сэр.",
    "Слушаю вас, сэр.",
    "Понял, сэр.",
    "Выполняю, сэр.",
    "Готово, сэр.",
    "Хорошо, сэр.",
    "Тихий час включён, сэр. Я буду молчать.",
    "Тихий час выключен, сэр. Я снова говорю.",
    "Открываю вк, сэр.",
    "Открываю ютуб, сэр.",
    "Открываю яндекс, сэр.",
    "Открываю гугл, сэр.",
    "Открываю телеграм, сэр.",
    "Открываю github, сэр.",
    "Открываю реддит, сэр.",
    "Открываю аниме, сэр.",
    "Открываю стим, сэр.",
    "Какой сайт открыть, сэр?",
    "Открываю сайт, сэр.",
    "Открываю браузер, сэр.",
    "Открываю блокнот, сэр.",
    "Открываю калькулятор, сэр.",
    "Открываю проводник, сэр.",
    "Какое приложение открыть, сэр?",
    "Приложение не найдено, сэр.",
    "Приложение запущено, сэр.",
    "Слушаюсь, сэр.",
    "Конечно, сэр.",
    "Уже делаю, сэр.",
    "Один момент, сэр.",
    "Секунду, сэр.",
    "Будет сделано, сэр.",
    "Принято, сэр.",
    "Так точно, сэр.",
    "Есть, сэр.",
    "Всё готово, сэр.",
    "Задача выполнена, сэр.",
    "Сделано, сэр.",
    "Выключаю систему, сэр. До свидания.",
    "Перезагружаю, сэр.",
    "Приятного отдыха, сэр.",
    "Компьютер заблокирован, сэр.",
    "Вы уверены, сэр? Скажите да.",
    "Действие отменено, сэр.",
    "Подтверждено, сэр.",
    "Отменено, сэр.",
    "Громкость увеличена, сэр.",
    "Громкость уменьшена, сэр.",
    "Звук выключен, сэр.",
    "Звук включён, сэр.",
    "Скриншот сохранён, сэр.",
    "Делаю снимок, сэр.",
    "Фото сохранено, сэр.",
    "Название заметки, сэр?",
    "Текст заметки, сэр?",
    "Заметка сохранена, сэр.",
    "Заметка не найдена, сэр.",
    "Какую заметку прочитать, сэр?",
    "Нет заметок, сэр.",
    "Список заметок на экране, сэр.",
    "Отменяю, сэр.",
    "Пароль сгенерирован, сэр.",
    "Пароль скопирован в буфер, сэр.",
    "Генерирую пароль, сэр.",
    "Бросаю кубик, сэр.",
    "Рассказываю шутку, сэр.",
    "Вот интересный факт, сэр.",
    "Запрашиваю статус системы, сэр.",
    "Не удалось выполнить, сэр.",
    "Ошибка, сэр.",
    "Не понял команду, сэр.",
    "Прошу прощения, сэр.",
    "Повторите, пожалуйста, сэр.",
    "Слушаю вас, сэр. Говорите текст.",
    "Текст вставлен, сэр.",
    "Уведомление отправлено на телефон, сэр.",
    "Ночной режим включён, сэр.",
    "Дневной режим включён, сэр.",
    "Яркость снижена, сэр.",
    "Яркость восстановлена, сэр.",
    "Сигнал отправлен на телефон, сэр. Ищите!",
    "Скриншот отправлен на телефон, сэр.",
    "Фото отправлено на телефон, сэр.",
    "Статус отправлен на телефон, сэр.",
    "Время отправлено на телефон, сэр.",
    "Погода отправлена на телефон, сэр.",
    "Курс отправлен на телефон, сэр.",
    "Открываю новую вкладку, сэр.",
    "Закрываю вкладку, сэр.",
    "Обновляю страницу, сэр.",
    "Иду назад, сэр.",
    "Иду вперёд, сэр.",
    "Переключаю вкладку, сэр.",
    "Сворачиваю браузер, сэр.",
    "Программа закрыта, сэр.",
    "Не удалось найти программу, сэр.",
    "Напоминание установлено, сэр.",
    "Напоминаю, сэр!",
    "Список напоминаний, сэр.",
    "Напоминаний нет, сэр.",
    "Запускаю игру, сэр.",
    "Запускаю стим, сэр.",
    "Запускаю гта, сэр.",
    "Запускаю майнкрафт, сэр.",
    "Запускаю доту, сэр.",
    "Игра запущена, сэр. Приятной игры.",
    "Свободное место на дисках, сэр.",
    "Топ процессов по ЦПУ, сэр.",
    "Делаю скриншот и распознаю текст, сэр.",
    "Текст скопирован в буфер, сэр.",
    "Текст на экране не найден, сэр.",
    "Управление жестами включено, сэр.",
    "Управление жестами выключено, сэр.",
    "Детектор хлопка включён, сэр.",
    "Детектор хлопка выключен, сэр.",
    "Дыхание включено, сэр.",
    "Дыхание выключено, сэр.",
    "Распознаю текст с камеры, сэр.",
    "Наведите камеру на текст, сэр.",
    "Читаю текст с камеры, сэр.",
    "Показываю расширенную помощь, сэр.",
]


# ==========================================
# ГОЛОС — ГИБРИД (edge-tts → gTTS)
# ==========================================

def get_cache_path(text):
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, f"{text_hash}.mp3")


def generate_voice(text, output_path):
    async def generate():
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_path)
    asyncio.run(generate())


def get_mp3_duration(mp3_path):
    try:
        if MUTAGEN_AVAILABLE:
            return MP3(mp3_path).info.length
    except:
        pass
    try:
        size = os.path.getsize(mp3_path)
        return max(1.5, size / 16000)
    except:
        return 3.0


def play_mp3(mp3_path):
    duration = get_mp3_duration(mp3_path) + 0.5
    play_cmd = (
        f'powershell -Command "'
        f'Add-Type -AssemblyName presentationCore; '
        f'$player = New-Object System.Windows.Media.MediaPlayer; '
        f'$player.Open([Uri]\'{mp3_path}\'); '
        f'$player.Play(); '
        f'Start-Sleep -Seconds {duration}; '
        f'$player.Stop(); '
        f'$player.Close()"'
    )
    subprocess.run(play_cmd, shell=True, capture_output=True)


def speak_gtts(text):
    """Русский голос Google TTS (требует интернет)."""
    try:
        from gtts import gTTS
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp.close()
        tts = gTTS(text=text, lang='ru')
        tts.save(tmp.name)
        play_mp3(tmp.name)
        try:
            os.remove(tmp.name)
        except:
            pass
    except Exception as e:
        print_error(f"gTTS ошибка: {e}")


def say(text):
    global IS_SPEAKING
    print_jarvis(text)
    if gui:
        gui.set_jarvis_response(text)
        gui.set_speaking(True)
    if not VOICE_ENABLED or not VOICE_AVAILABLE:
        if gui:
            gui.set_speaking(False)
        return
    try:
        cache_file = get_cache_path(text)
        with speak_lock:
            IS_SPEAKING = True
            if os.path.exists(cache_file) and os.path.getsize(cache_file) > 100:
                play_mp3(cache_file)
            else:
                print_info("🔊 Озвучиваю через Google TTS...")
                speak_gtts(text)
    except Exception as e:
        print_error(f"Ошибка голоса: {e}")
    finally:
        IS_SPEAKING = False
        if gui:
            gui.set_speaking(False)


def preload_phrases():
    print_info(f"Предзагрузка {len(PRELOAD_PHRASES)} фраз...")
    loaded = 0
    skipped = 0
    failed = 0
    for i, phrase in enumerate(PRELOAD_PHRASES, 1):
        cache_file = get_cache_path(phrase)
        if os.path.exists(cache_file) and os.path.getsize(cache_file) > 100:
            skipped += 1
            continue
        try:
            generate_voice(phrase, cache_file)
            loaded += 1
        except:
            failed += 1
        if i % 20 == 0:
            print_info(f"  ... {i}/{len(PRELOAD_PHRASES)}")
    print_success(f"Загружено: {loaded} новых, {skipped} из кэша, {failed} ошибок")


# ==========================================
# КАМЕРА
# ==========================================

def open_camera():
    global camera_busy
    if camera_busy:
        print_warning("Камера занята другим модулем")
        return None
    camera_busy = True
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            cap.release()
            camera_busy = False
            return None
        return cap
    except Exception as e:
        print_error(f"Ошибка камеры: {e}")
        camera_busy = False
        return None


def close_camera(cap):
    global camera_busy
    try:
        if cap:
            cap.release()
    except:
        pass
    camera_busy = False

# ==========================================
# КОНСОЛЬНЫЕ ФУНКЦИИ
# ==========================================

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print()
    print(f"{C.CYAN}╔{'═' * 78}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}{C.MAGENTA}{'█' * 78}{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}{C.MAGENTA}██{C.RESET}  {C.WHITE}{'J  A  R  V  I  S':^70}{C.RESET}  {C.MAGENTA}██{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}{C.MAGENTA}██{C.RESET}  {C.GRAY}{'Искусственный интеллект · Голосовой ассистент':^70}{C.RESET}  {C.MAGENTA}██{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}{C.MAGENTA}{'█' * 78}{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 78}╣{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {C.GREEN}●{C.RESET} Система запущена  {C.CYAN}│{C.RESET}  {C.GREEN}●{C.RESET} Голос активен  {C.CYAN}│{C.RESET}  {C.GREEN}●{C.RESET} Все модули в норме{' ' * 8}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╚{'═' * 78}╝{C.RESET}")
    print()


def _bar(value, width=20):
    filled = int(value / 100 * width)
    empty = width - filled
    if value < 50:
        color = C.GREEN
    elif value < 80:
        color = C.YELLOW
    else:
        color = C.RED
    return f"{color}{'█' * filled}{C.GRAY}{'░' * empty}{C.RESET}"


def print_status_bar(ollama_available=False):
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    try:
        disk = psutil.disk_usage('/').percent
    except:
        disk = 0

    voice_status = f"{C.GREEN}● ON{C.RESET}" if VOICE_ENABLED else f"{C.RED}● OFF{C.RESET}"
    vosk_status = f"{C.GREEN}VOSK{C.RESET}" if VOSK_AVAILABLE else f"{C.YELLOW}GOOGLE{C.RESET}"
    ocr_status = f"{C.GREEN}●{C.RESET}" if OCR_AVAILABLE else f"{C.RED}○{C.RESET}"
    ai_status = f"{C.GREEN}●{C.RESET}" if ollama_available else f"{C.RED}○{C.RESET}"

    print(f"{C.CYAN}┌{'─' * 78}┐{C.RESET}")
    print(f"{C.CYAN}│{C.RESET}  {C.WHITE}⚡ CPU{C.RESET}  {_bar(cpu)}  {C.WHITE}{cpu:5.1f}%{C.RESET}   "
          f"{C.WHITE}💾 RAM{C.RESET}  {_bar(ram)}  {C.WHITE}{ram:5.1f}%{C.RESET}   "
          f"{C.WHITE}💽 DISK{C.RESET}  {_bar(disk, 10)}  {C.WHITE}{disk:5.1f}%{C.RESET}  {C.CYAN}│{C.RESET}")
    print(f"{C.CYAN}│{C.RESET}  {C.WHITE}🔊 ГОЛОС{C.RESET} {voice_status}   "
          f"{C.WHITE}🎤 ВВОД{C.RESET} {vosk_status}   "
          f"{C.WHITE}👁 OCR{C.RESET} {ocr_status}   "
          f"{C.WHITE}🤖 ИИ{C.RESET} {ai_status}"
          f"{' ' * 26}{C.CYAN}│{C.RESET}")
    print(f"{C.CYAN}└{'─' * 78}┘{C.RESET}")


def print_user(text):
    print(f"\n  🎤 Вы: {text}")
    try:
        if gui and hasattr(gui, 'append_log'):
            gui.append_log(f"🎤 Вы: {text}")
    except:
        pass


def print_jarvis(text):
    print(f"  🤖 Джарвис: {text}")
    try:
        if gui and hasattr(gui, 'append_log'):
            gui.append_log(f"🤖 Джарвис: {text}")
    except:
        pass


def print_success(text):
    print(f"  ✓ {text}")
    try:
        if gui and hasattr(gui, 'append_log'):
            gui.append_log(f"✓ {text}")
    except:
        pass


def print_warning(text):
    print(f"  ⚠ {text}")
    try:
        if gui and hasattr(gui, 'append_log'):
            gui.append_log(f"⚠ {text}")
    except:
        pass


def print_error(text):
    print(f"  ✗ {text}")
    try:
        if gui and hasattr(gui, 'append_log'):
            gui.append_log(f"✗ {text}")
    except:
        pass


def print_info(text):
    print(f"  ℹ {text}")
    try:
        if gui and hasattr(gui, 'append_log'):
            gui.append_log(f"ℹ {text}")
    except:
        pass

def print_waiting():
    print(f"\n  {C.GRAY}┌{'─' * 72}┐{C.RESET}")
    print(f"  {C.GRAY}│{C.RESET}  {C.CYAN}◉{C.RESET}  {C.WHITE}Ожидаю команду, сэр...{C.RESET}{' ' * 46}{C.GRAY}│{C.RESET}")
    print(f"  {C.GRAY}└{'─' * 72}┘{C.RESET}")


def print_thinking():
    print(f"  {C.ORANGE}  ◌  Обрабатываю...{C.RESET}")


# ==========================================
# ТЕЛЕФОН
# ==========================================

class PhoneControl:
    def __init__(self):
        self.user_id = ""
        self.user_key = ""
        self._load_config()

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self.user_id = cfg.get("pushall_user_id", "")
                self.user_key = cfg.get("pushall_user_key", "")
            except:
                pass

    def _save_config(self):
        if not os.path.exists(CONFIG_FILE):
            template = {
                "pushall_user_id": "",
                "pushall_user_key": "",
                "_comment": "Получите ключи на https://pushall.ru/ — раздел API"
            }
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)
            except:
                pass

    def send(self, title, message):
        if not self.user_id or not self.user_key:
            self._save_config()
            return False
        try:
            url = "https://pushall.ru/api.php"
            data = {"type": "self", "id": self.user_id, "key": self.user_key,
                    "title": title, "text": message}
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except:
            return False

    def send_file(self, file_path, title="Файл от Джарвиса"):
        if not self.user_id or not self.user_key:
            return False
        try:
            if not os.path.exists(file_path):
                return False
            url = "https://pushall.ru/api.php"
            files = {'file': open(file_path, 'rb')}
            data = {"type": "self", "id": self.user_id, "key": self.user_key,
                    "title": title, "text": os.path.basename(file_path)}
            response = requests.post(url, data=data, files=files, timeout=30)
            files['file'].close()
            return response.status_code == 200
        except:
            return False

    def find_phone(self):
        return self.send("🔍 НАЙДИ ТЕЛЕФОН!", "Сэр, подайте сигнал на телефоне!")


# ==========================================
# ЖЕСТЫ
# ==========================================

class GestureDetector:
    def __init__(self, jarvis_ref):
        self.jarvis = jarvis_ref
        self.running = False
        self.thread = None
        self.last_gesture = None
        self.last_gesture_time = 0
        self.cooldown = 2.0
        self.cap = None
        if MEDIAPIPE_AVAILABLE:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )

    def start(self):
        if not MEDIAPIPE_AVAILABLE:
            say("MediaPipe не установлен, сэр.")
            return
        if self.running:
            say("Жесты уже активны, сэр.")
            return
        if camera_busy:
            say("Камера занята, сэр.")
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        say("Управление жестами включено, сэр.")
        if gui:
            gui.update_modes(gestures=True)

    def stop(self):
        if not self.running:
            say("Жесты уже выключены, сэр.")
            return
        self.running = False
        say("Управление жестами выключено, сэр.")
        if gui:
            gui.update_modes(gestures=False)

    def _finger_up(self, lm, tip, pip):
        return lm[tip].y < lm[pip].y

    def _detect_gesture(self, lm):
        thumb_up = lm[4].x < lm[3].x
        index_up = self._finger_up(lm, 8, 6)
        middle_up = self._finger_up(lm, 12, 10)
        ring_up = self._finger_up(lm, 16, 14)
        pinky_up = self._finger_up(lm, 20, 18)
        count = sum([thumb_up, index_up, middle_up, ring_up, pinky_up])
        if count == 0:
            return "fist"
        if count == 5:
            return "palm"
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "point_up"
        if index_up and middle_up and not ring_up and not pinky_up:
            return "peace"
        if thumb_up and not index_up and not middle_up and not ring_up and not pinky_up:
            return "thumb_up"
        return None

    def _handle_gesture(self, gesture):
        now = time.time()
        if gesture == self.last_gesture and (now - self.last_gesture_time) < self.cooldown:
            return
        self.last_gesture = gesture
        self.last_gesture_time = now
        print_info(f"🖐️ Жест: {gesture}")
        if gesture == "palm":
            say("Пауза или продолжение, сэр.")
            pyautogui.press("playpause")
        elif gesture == "fist":
            say("Стоп, сэр.")
            pyautogui.press("stop")
        elif gesture == "point_up":
            say("Громче, сэр.")
            for _ in range(3):
                pyautogui.press("volumeup")
        elif gesture == "peace":
            say("Скриншот, сэр.")
            filename = os.path.join(PICTURES_DIR, f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png")
            pyautogui.screenshot().save(filename)
            print_success(f"Скриншот: {filename}")
        elif gesture == "thumb_up":
            say("Подтверждено, сэр.")

    def _loop(self):
        cap = open_camera()
        if not cap:
            print_error("Не удалось открыть камеру для жестов")
            self.running = False
            if gui:
                gui.update_modes(gestures=False)
            return
        self.cap = cap
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb)
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        gesture = self._detect_gesture(hand_landmarks.landmark)
                        if gesture:
                            self._handle_gesture(gesture)
                time.sleep(0.03)
        except Exception as e:
            print_error(f"Ошибка жестов: {e}")
        finally:
            close_camera(cap)


# ==========================================
# ХЛОПОК
# ==========================================

class ClapDetector:
    def __init__(self, jarvis_ref):
        self.jarvis = jarvis_ref
        self.running = False
        self.thread = None
        self.clap_threshold = 2500
        self.cooldown = 2.0
        self.last_clap = 0
        self.p = None
        self.stream = None

    def start(self):
        if not PYAUDIO_AVAILABLE:
            say("PyAudio не установлен, сэр. Детектор хлопка недоступен.")
            return
        if not NUMPY_AVAILABLE:
            say("NumPy не установлен, сэр. Детектор хлопка недоступен.")
            return
        if self.running:
            say("Детектор хлопка уже активен, сэр.")
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        say("Детектор хлопка включён, сэр.")
        if gui:
            gui.update_modes(clap=True)

    def stop(self):
        if not self.running:
            say("Детектор хлопка уже выключен, сэр.")
            return
        self.running = False
        say("Детектор хлопка выключен, сэр.")
        if gui:
            gui.update_modes(clap=False)

    def _loop(self):
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=1024
            )
            while self.running:
                try:
                    if MIC_LOCK.locked():
                        time.sleep(0.1)
                        continue
                    data = self.stream.read(1024, exception_on_overflow=False)
                    if not NUMPY_AVAILABLE:
                        continue
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    amplitude = np.abs(audio_data).mean()
                    if amplitude > self.clap_threshold:
                        now = time.time()
                        if now - self.last_clap > self.cooldown:
                            self.last_clap = now
                            print_info(f"🔇 Хлопок! (амплитуда {amplitude:.0f})")
                            self._on_clap()
                except:
                    pass
        except Exception as e:
            print_error(f"Ошибка хлопка: {e}")
        finally:
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
            if self.p:
                try:
                    self.p.terminate()
                except:
                    pass

    def _on_clap(self):
        winsound.Beep(800, 100)
        say("Слушаю вас, сэр.")


# ==========================================
# ДЫХАНИЕ
# ==========================================

class BreathSound:
    def __init__(self):
        self.running = False
        self.thread = None
        self.breath_file = None
        self.volume = 0.08

    def _ensure_breath_file(self):
        if self.breath_file and os.path.exists(self.breath_file):
            return True
        try:
            self.breath_file = get_cache_path("__breath_sound__")
            if not os.path.exists(self.breath_file):
                generate_voice("Хааа...", self.breath_file)
            return os.path.exists(self.breath_file)
        except Exception as e:
            print_error(f"Не удалось создать звук дыхания: {e}")
            return False

    def start(self):
        if self.running:
            say("Дыхание уже включено, сэр.")
            return
        if not self._ensure_breath_file():
            say("Не удалось включить дыхание, сэр.")
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        say("Дыхание включено, сэр.")
        if gui:
            gui.update_modes(breath=True)

    def stop(self):
        if not self.running:
            say("Дыхание уже выключено, сэр.")
            return
        self.running = False
        say("Дыхание выключено, сэр.")
        if gui:
            gui.update_modes(breath=False)

    def _loop(self):
        pause_flag = os.path.join(CACHE_DIR, "breath_pause.flag")
        stop_flag = os.path.join(CACHE_DIR, "breath_stop.flag")
        breath_path = self.breath_file.replace("\\", "\\\\")
        ps_script = (
            f'Add-Type -AssemblyName presentationCore; '
            f'$player = New-Object System.Windows.Media.MediaPlayer; '
            f'$player.Volume = {self.volume}; '
            f'$player.Open([Uri]\'{breath_path}\'); '
            f'$player.Play(); '
            f'$player.Pause(); '
            f'while ($true) {{ '
            f'  if (Test-Path "{stop_flag}") {{ break }}; '
            f'  if (Test-Path "{pause_flag}") {{ '
            f'    $player.Pause() '
            f'  }} else {{ '
            f'    if ($player.Position.TotalSeconds -ge $player.NaturalDuration.TimeSpan.TotalSeconds) {{ '
            f'      $player.Position = [TimeSpan]::Zero '
            f'    }}; '
            f'    $player.Play() '
            f'  }}; '
            f'  Start-Sleep -Milliseconds 300 '
            f'}}; '
            f'$player.Stop(); '
            f'$player.Close()'
        )
        try:
            if os.path.exists(stop_flag):
                os.remove(stop_flag)
            proc = subprocess.Popen(
                ["powershell", "-Command", ps_script],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            while self.running:
                try:
                    if IS_SPEAKING:
                        open(pause_flag, 'w').close()
                    else:
                        if os.path.exists(pause_flag):
                            os.remove(pause_flag)
                except:
                    pass
                time.sleep(0.2)
            open(stop_flag, 'w').close()
            time.sleep(0.5)
            try:
                proc.terminate()
            except:
                pass
            if os.path.exists(stop_flag):
                os.remove(stop_flag)
            if os.path.exists(pause_flag):
                os.remove(pause_flag)
        except Exception as e:
            print_error(f"Ошибка дыхания: {e}")

            

# ==========================================
# PYQT — РЕАКТОР
# ==========================================

class ReactorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.cpu = 0
        self.ram = 0
        self.is_listening = False
        self.is_speaking = False
        self.is_thinking = False
        self.outer_angle = 0
        self.mid_angle = 180
        self.inner_angle = 0
        self.pulse_phase = 0
        self.core_breath = 0
        self.core_breath_dir = 1
        self.particles = []
        for i in range(40):
            radius = 60 + (i % 5) * 12
            angle = (i * 9) % 360
            speed = 0.5 + (i % 4) * 0.4
            size = 1.5 + (i % 3) * 0.8
            alpha = 80 + (i % 5) * 30
            self.particles.append([radius, angle, speed, size, alpha])
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def set_state(self, listening=None, speaking=None, thinking=None):
        if listening is not None:
            self.is_listening = listening
        if speaking is not None:
            self.is_speaking = speaking
        if thinking is not None:
            self.is_thinking = thinking
        self.update()

    def set_cpu_ram(self, cpu, ram):
        self.cpu = cpu
        self.ram = ram

    def _cpu_color(self):
        if self.cpu < 40:
            t = self.cpu / 40.0
            return QColor(int(0 + 255 * t * 0.3), int(255 - 100 * t * 0.3), int(136 - 136 * t * 0.3))
        elif self.cpu < 70:
            t = (self.cpu - 40) / 30.0
            return QColor(int(76 + (255 - 76) * t), int(225 + (204 - 225) * t), int(95 + (0 - 95) * t))
        else:
            t = (self.cpu - 70) / 30.0
            return QColor(255, int(204 - 204 * t), int(0 + 85 * t))

    def _ram_color(self):
        if self.ram < 50:
            return QColor(0, 170, 255)
        elif self.ram < 80:
            return QColor(255, 204, 0)
        else:
            return QColor(255, 51, 85)

    def _tick(self):
        if self.is_listening:
            outer_speed, mid_speed, inner_speed = 4, -8, 12
        elif self.is_speaking:
            outer_speed, mid_speed, inner_speed = 2, -5, 8
        elif self.is_thinking:
            outer_speed, mid_speed, inner_speed = 6, 10, -14
        else:
            outer_speed, mid_speed, inner_speed = 1, -2, 3
        self.outer_angle = (self.outer_angle + outer_speed) % 360
        self.mid_angle = (self.mid_angle + mid_speed) % 360
        self.inner_angle = (self.inner_angle + inner_speed) % 360
        if self.is_listening or self.is_speaking:
            self.pulse_phase += 1
        else:
            self.core_breath += self.core_breath_dir * 0.3
            if self.core_breath >= 4:
                self.core_breath = 4
                self.core_breath_dir = -1
            elif self.core_breath <= 0:
                self.core_breath = 0
                self.core_breath_dir = 1
        for p in self.particles:
            p[1] = (p[1] + p[2]) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        base_size = min(w, h)
        bg_grad = QRadialGradient(cx, cy, base_size * 0.6)
        bg_grad.setColorAt(0, QColor(10, 20, 25))
        bg_grad.setColorAt(1, QColor(5, 5, 8))
        painter.fillRect(self.rect(), QBrush(bg_grad))
        cpu_color = self._cpu_color()
        ram_color = self._ram_color()
        painter.setPen(Qt.NoPen)
        for radius, angle, speed, size, alpha in self.particles:
            rad = math.radians(angle)
            x = cx + radius * math.cos(rad)
            y = cy + radius * math.sin(rad)
            pc = QColor(cpu_color)
            pc.setAlpha(alpha)
            painter.setBrush(QBrush(pc))
            painter.drawEllipse(QPointF(x, y), size, size)
        outer_r = base_size * 0.42
        pen = QPen(cpu_color, 2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        for i in range(4):
            start = (self.outer_angle + i * 90) * 16
            painter.drawArc(QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2), int(start), 70 * 16)
        outer_r2 = base_size * 0.38
        pen2 = QPen(QColor(cpu_color.red(), cpu_color.green(), cpu_color.blue(), 120), 1)
        pen2.setCapStyle(Qt.RoundCap)
        painter.setPen(pen2)
        for i in range(3):
            start = (-self.outer_angle * 0.7 + i * 120) * 16
            painter.drawArc(QRectF(cx - outer_r2, cy - outer_r2, outer_r2 * 2, outer_r2 * 2), int(start), 50 * 16)
        mid_r = base_size * 0.32
        pen3 = QPen(ram_color, 2)
        pen3.setCapStyle(Qt.RoundCap)
        painter.setPen(pen3)
        for i in range(3):
            start = (self.mid_angle + i * 120) * 16
            painter.drawArc(QRectF(cx - mid_r, cy - mid_r, mid_r * 2, mid_r * 2), int(start), 60 * 16)
        inner_r = base_size * 0.24
        painter.setPen(QPen(QColor(0, 85, 85, 180), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)
        pen5 = QPen(QColor(0, 255, 200, 200), 1.5)
        pen5.setCapStyle(Qt.RoundCap)
        painter.setPen(pen5)
        for i in range(6):
            start = (self.inner_angle + i * 60) * 16
            inner_r2 = base_size * 0.20
            painter.drawArc(QRectF(cx - inner_r2, cy - inner_r2, inner_r2 * 2, inner_r2 * 2), int(start), 20 * 16)
        if self.is_listening:
            pulse = 6 * abs((self.pulse_phase % 30) - 15) / 15
            core_color = QColor(255, 255, 0)
        elif self.is_speaking:
            pulse = 6 * abs((self.pulse_phase % 30) - 15) / 15
            core_color = QColor(255, 0, 255)
        elif self.is_thinking:
            pulse = 4 * abs((self.pulse_phase % 20) - 10) / 10
            core_color = QColor(255, 136, 0)
        else:
            pulse = self.core_breath
            core_color = cpu_color
        core_r = base_size * 0.14 + pulse
        for gr, alpha in [(core_r * 1.8, 30), (core_r * 1.4, 60), (core_r * 1.15, 100)]:
            glow = QRadialGradient(cx, cy, gr)
            gc = QColor(core_color)
            gc.setAlpha(alpha)
            glow.setColorAt(0, gc)
            gc2 = QColor(core_color)
            gc2.setAlpha(0)
            glow.setColorAt(1, gc2)
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), gr, gr)
        core_grad = QRadialGradient(cx, cy - core_r * 0.3, core_r * 1.2)
        core_grad.setColorAt(0, QColor(255, 255, 255))
        core_grad.setColorAt(0.3, core_color)
        core_grad.setColorAt(1, QColor(core_color.red() // 3, core_color.green() // 3, core_color.blue() // 3))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(QPen(core_color, 2))
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)
        if self.is_listening:
            state, state_color = "LISTENING", QColor(255, 255, 0)
        elif self.is_speaking:
            state, state_color = "SPEAKING", QColor(255, 0, 255)
        elif self.is_thinking:
            state, state_color = "THINKING", QColor(255, 136, 0)
        else:
            state, state_color = "IDLE", QColor(0, 255, 136)
        painter.setPen(QPen(state_color, 1))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(QRectF(0, h - 24, w, 20), Qt.AlignCenter, f"● {state}")


class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50)
        self.cpu_history = [0] * 60
        self.ram_history = [0] * 60

    def add_data(self, cpu, ram):
        self.cpu_history.append(cpu)
        self.ram_history.append(ram)
        self.cpu_history.pop(0)
        self.ram_history.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(self.rect(), QColor(5, 5, 8))
        painter.setPen(QPen(QColor(20, 40, 40), 1))
        for i in range(1, 4):
            painter.drawLine(0, int(h * i / 4), w, int(h * i / 4))
        if len(self.cpu_history) < 2:
            return
        step = w / (len(self.cpu_history) - 1)
        cpu_path = QPainterPath()
        cpu_path.moveTo(0, h)
        for i, val in enumerate(self.cpu_history):
            cpu_path.lineTo(i * step, h - (val / 100) * (h - 4))
        cpu_path.lineTo(w, h)
        cpu_path.closeSubpath()
        cpu_grad = QLinearGradient(0, 0, 0, h)
        cpu_grad.setColorAt(0, QColor(0, 255, 136, 80))
        cpu_grad.setColorAt(1, QColor(0, 255, 136, 0))
        painter.fillPath(cpu_path, QBrush(cpu_grad))
        painter.setPen(QPen(QColor(0, 255, 136), 1.5))
        for i in range(len(self.cpu_history) - 1):
            painter.drawLine(int(i * step), int(h - (self.cpu_history[i] / 100) * (h - 4)),
                             int((i + 1) * step), int(h - (self.cpu_history[i + 1] / 100) * (h - 4)))
        painter.setPen(QPen(QColor(0, 170, 255), 1.5))
        for i in range(len(self.ram_history) - 1):
            painter.drawLine(int(i * step), int(h - (self.ram_history[i] / 100) * (h - 4)),
                             int((i + 1) * step), int(h - (self.ram_history[i + 1] / 100) * (h - 4)))

            

# ==========================================
# PYQT — ГЛАВНОЕ ОКНО
# ==========================================

class JarvisGUI:
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle("JARVIS")
        self.window.setGeometry(10, 10, 650, 850)
        self.window.setStyleSheet("""
            QWidget { background-color: #0a0a0f; color: #00ffff; font-family: Consolas; }
            QLabel { color: #00ffff; }
        """)
        self.window.setWindowOpacity(0.95)

        if os.path.exists(ICON_PATH):
            from PyQt5.QtGui import QIcon
            self.window.setWindowIcon(QIcon(ICON_PATH))

        layout = QVBoxLayout(self.window)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        title = QLabel("●  J A R V I S")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ffff; padding: 4px;")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(0, 255, 255, 180))
        glow.setOffset(0, 0)
        title.setGraphicsEffect(glow)
        layout.addWidget(title)

        self.reactor = ReactorWidget()
        layout.addWidget(self.reactor, 1)

        self.status_label = QLabel("⚡ CPU: 0%   💾 RAM: 0%")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #00ff88; padding: 4px;")
        layout.addWidget(self.status_label)

        self.graph = GraphWidget()
        layout.addWidget(self.graph)

        self.mode_label = QLabel("🖐️ Жесты: Выкл   🔇 Хлопок: Выкл   🌬️ Дыхание: Выкл")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("font-size: 10px; color: #666666; padding: 2px;")
        layout.addWidget(self.mode_label)

        self.user_label = QLabel("🎤 Вы: —")
        self.user_label.setWordWrap(True)
        self.user_label.setStyleSheet("font-size: 11px; color: #00aaff; padding: 4px; background-color: #050510; border-left: 2px solid #00aaff;")
        layout.addWidget(self.user_label)

        self.jarvis_label = QLabel("🤖 Джарвис: —")
        self.jarvis_label.setWordWrap(True)
        self.jarvis_label.setStyleSheet("font-size: 11px; color: #ff00ff; padding: 4px; background-color: #100510; border-left: 2px solid #ff00ff;")
        layout.addWidget(self.jarvis_label)

        self.voice_label = QLabel("🔊 Vosk: Активен")
        self.voice_label.setAlignment(Qt.AlignCenter)
        self.voice_label.setStyleSheet("font-size: 11px; color: #00ff88; padding: 4px;")
        layout.addWidget(self.voice_label)

        # === ЛОГ ВЫВОДА (вместо консоли) ===
        from PyQt5.QtWidgets import QTextEdit
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #050510;
                color: #00ff88;
                border: 1px solid #00ffff;
                font-family: Consolas;
                font-size: 11px;
                padding: 6px;
            }
        """)
        self.log_output.setMinimumHeight(200)
        layout.addWidget(self.log_output)

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)

        self._gestures_on = False
        self._clap_on = False
        self._breath_on = False

        self.window.show()

    def _update_status(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            color = '#00ff88' if cpu < 40 else '#ffcc00' if cpu < 70 else '#ff3355'
            self.status_label.setText(f"⚡ CPU: {cpu}%   💾 RAM: {ram}%")
            self.status_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {color}; padding: 4px;")
            self.reactor.set_cpu_ram(cpu, ram)
            self.graph.add_data(cpu, ram)
        except:
            pass

    def set_listening(self, listening):
        self.reactor.set_state(listening=listening)
        if listening:
            self.voice_label.setText("🎤 Слушаю...")
            self.voice_label.setStyleSheet("font-size: 11px; color: #ffff00; padding: 4px;")
        else:
            self.voice_label.setText("🔊 Vosk: Активен")
            self.voice_label.setStyleSheet("font-size: 11px; color: #00ff88; padding: 4px;")

    def set_speaking(self, speaking):
        self.reactor.set_state(speaking=speaking)

    def set_thinking(self, thinking):
        self.reactor.set_state(thinking=thinking)

    def set_user_command(self, text):
        self.user_label.setText(f"🎤 Вы: {text[:60]}")

    def set_jarvis_response(self, text):
        self.jarvis_label.setText(f"🤖 Джарвис: {text[:60]}")

    def update_modes(self, gestures=None, clap=None, breath=None):
        if gestures is not None:
            self._gestures_on = gestures
        if clap is not None:
            self._clap_on = clap
        if breath is not None:
            self._breath_on = breath
        g = "🖐️ Вкл" if self._gestures_on else "🖐️ Выкл"
        c = "🔇 Вкл" if self._clap_on else "🔇 Выкл"
        b = "🌬️ Вкл" if self._breath_on else "🌬️ Выкл"
        color = '#00ff88' if any([self._gestures_on, self._clap_on, self._breath_on]) else '#666666'
        self.mode_label.setText(f"{g}   {c}   {b}")
        self.mode_label.setStyleSheet(f"font-size: 10px; color: {color}; padding: 2px;")

    def append_log(self, text):
        """Добавляет строку в лог PyQt-окна."""
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {text}"
        print(f"[APPEND_LOG] {line}")
        try:
            self.log_output.append(line)
            sb = self.log_output.verticalScrollBar()
            sb.setValue(sb.maximum())
            print("[APPEND_LOG] Добавлено в PyQt")
        except Exception as e:
            print(f"[APPEND_LOG] ОШИБКА: {e}")
        
    def open_pushall_dialog(self):
        """Открывает окно настройки PushAll."""
        from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QFormLayout, QLabel
        from PyQt5.QtCore import Qt

        dialog = QDialog(self.window)
        dialog.setWindowTitle("📱 Настройка PushAll")
        dialog.setMinimumWidth(450)
        dialog.setStyleSheet("""
            QDialog { background-color: #0a0a0f; color: #00ffff; }
            QLabel { color: #00ffff; font-size: 12px; }
            QLineEdit {
                background-color: #050510; color: #00ff88;
                border: 1px solid #00ffff; padding: 6px;
                font-family: Consolas; font-size: 12px;
            }
            QPushButton {
                background-color: #003366; color: #00ffff;
                border: 1px solid #00ffff; padding: 8px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #005588; }
        """)

        form = QFormLayout(dialog)

        title = QLabel("📱 Уведомления на телефон (PushAll)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        form.addRow(title)

        info = QLabel(
            "1. Откройте https://pushall.ru/ и зарегистрируйтесь.\n"
            "2. В личном кабинете → раздел API.\n"
            "3. Скопируйте ID и ключ.\n"
            "4. Вставьте их ниже и нажмите Сохранить."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888888; font-size: 11px; padding: 6px;")
        form.addRow(info)

        id_field = QLineEdit()
        id_field.setPlaceholderText("Ваш ID пользователя")
        form.addRow("ID пользователя:", id_field)

        key_field = QLineEdit()
        key_field.setPlaceholderText("Ваш API-ключ")
        form.addRow("API-ключ:", key_field)

        # Заполняем существующие значения
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                id_field.setText(cfg.get("pushall_user_id", ""))
                key_field.setText(cfg.get("pushall_user_key", ""))
        except:
            pass

        save_btn = QPushButton("💾 Сохранить")
        form.addRow(save_btn)

        def save_pushall():
            uid = id_field.text().strip()
            ukey = key_field.text().strip()
            try:
                cfg = {}
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                cfg["pushall_user_id"] = uid
                cfg["pushall_user_key"] = ukey
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                self.append_log(f"✓ PushAll сохранён (ID: {uid[:6]}...)")
                dialog.accept()
            except Exception as e:
                self.append_log(f"✗ Ошибка сохранения: {e}")

        save_btn.clicked.connect(save_pushall)
        dialog.exec_()

    def run(self):
        self.app.exec_()

        
# ==========================================
# ОБУЧЕНИЕ (TUTORIAL) + СЧЁТЧИК ЗАПУСКОВ
# ==========================================

TUTORIALS = {
    1: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #1 — ДОБРО ПОЖАЛОВАТЬ, СЭР!                     ║
╚══════════════════════════════════════════════════════════════╝

Я — JARVIS, ваш голосовой ассистент.

ЧТО Я УМЕЮ:
  • Открывать сайты, приложения, игры.
  • Делать скриншоты, фото, записи экрана.
  • Распознавать текст (OCR).
  • Управлять компьютером голосом.
  • Многое другое.

ЧТОБЫ Я СЛУШАЛ — просто говорите команду:
  • «Джарвис, который час»
  • «Джарвис, открой ютуб»
  • «Джарвис, помощь» — полный список команд.

Удачи, сэр!
""",

    2: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #2 — ПРОСТЫЕ КОМАНДЫ                             ║
╚══════════════════════════════════════════════════════════════╝

ПОПРОБУЙТЕ:
  • «Джарвис, который час»
  • «Джарвис, скриншот»
  • «Джарвис, громче» / «тише»
  • «Джарвис, пауза» / «продолжи»

ПОЛЕЗНО ЗНАТЬ:
  • Все скриншоты сохраняются в:
    C:\\Users\\<Имя>\\JARVIS\\Screenshots\\
  • Голос работает офлайн (если установлен).
""",

    3: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #3 — САЙТЫ                                        ║
╚══════════════════════════════════════════════════════════════╝

САЙТЫ (просто скажите «открой ...»):
  • ВК: «Джарвис, открой вк»
  • YouTube: «Джарвис, открой ютуб»
  • Яндекс: «Джарвис, открой яндекс»
  • Google: «Джарвис, открой гугл»
  • Telegram: «Джарвис, открой телеграм»
  • GitHub, Reddit, TikTok, и другие.
""",

    4: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #4 — ПРИЛОЖЕНИЯ                                   ║
╚══════════════════════════════════════════════════════════════╝

ПРИЛОЖЕНИЯ (скажите «открой ...»):
  • «Джарвис, открой блокнот»
  • «Джарвис, открой калькулятор»
  • «Джарвис, открой проводник»
  • «Джарвис, открой диспетчер задач»
  • «Джарвис, открой командную строку»
""",

    5: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #5 — ИГРЫ                                         ║
╚══════════════════════════════════════════════════════════════╝

ИГРЫ (скажите «запусти ...»):
  • «Джарвис, запусти стим»
  • «Джарвис, запусти гта»
  • «Джарвис, запусти майнкрафт»
  • «Джарвис, запусти доту»
""",

    6: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #6 — ЭКРАН И КАМЕРА                               ║
╚══════════════════════════════════════════════════════════════╝

СКРИНШОТЫ И ФОТО:
  • «Джарвис, скриншот» — снимок экрана.
  • «Джарвис, фото» — снимок с камеры.
  • «Джарвис, запиши экран» — запись экрана.

РАСПОЗНАВАНИЕ ТЕКСТА (OCR):
  • «Джарвис, прочитай текст с экрана»
  • «Джарвис, прочитай текст с камеры»
  • «Джарвис, распознай и переведи»
""",

    7: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #7 — ЗАМЕТКИ И НАПОМИНАНИЯ                        ║
╚══════════════════════════════════════════════════════════════╝

ЗАМЕТКИ:
  • «Джарвис, создай заметку» — JARVIS спросит имя и текст.
  • «Джарвис, прочитай заметку [название]»
  • «Джарвис, покажи заметки»

НАПОМИНАНИЯ:
  • «Джарвис, напомни через 5 минут позвонить маме»
  • «Джарвис, покажи напоминания»
""",

    8: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #8 — ТЕХНИЧЕСКИЕ КОМАНДЫ                          ║
╚══════════════════════════════════════════════════════════════╝

ДИАГНОСТИКА СИСТЕМЫ:
  • «Джарвис, статус системы» — CPU, RAM, диск.
  • «Джарвис, топ процессов» — самые нагруженные.
  • «Джарвис, свободное место» — на дисках.
  • «Джарвис, диагностика» — полная проверка.

СЕТЬ:
  • «Джарвис, пинг» — проверить интернет.
  • «Джарвис, скорость интернета» — speedtest.
  • «Джарвис, моя сеть» — IP, хост.
""",

    9: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #9 — ТЕЛЕФОН (PushAll)                            ║
╚══════════════════════════════════════════════════════════════╝

JARVIS может отправлять уведомления на ваш телефон
через сервис PushAll (бесплатно).

ЧТО ЭТО ДАЁТ:
  • Найти потерянный телефон.
  • Получать статус ПК.
  • Отправлять скриншоты.
  • Уведомления о напоминаниях.

НАСТРОЙКА:
  • Скажите: «Джарвис, настрой PushAll»
  • JARVIS откроет окно настройки.

Или посмотрите: https://pushall.ru/
""",

    10: """
╔══════════════════════════════════════════════════════════════╗
║  🎓 ЗАПУСК #10 — ВЫ ОСВОИЛИ JARVIS!                          ║
╚══════════════════════════════════════════════════════════════╝

ПОЗДРАВЛЯЮ, СЭР!

Вы прошли 10 запусков и знаете основные команды.

ПОЛНЫЙ СПИСОК КОМАНД:
  • «Джарвис, помощь» — краткая справка.
  • «Джарвис, расширенная помощь» — полная.
  • «Джарвис, обучение» — повторить обучение.

ЧТО ДАЛЬШЕ:
  • Настройте PushAll — «Джарвис, настрой PushAll».
  • Изучите технические команды.
  • Экспериментируйте!

Удачи, сэр!
""",
}


def get_launch_count():
    """Возвращает номер текущего запуска."""
    try:
        with open(LAUNCH_COUNT_FILE, 'r', encoding='utf-8') as f:
            return int(f.read().strip())
    except:
        return 0


def increment_launch_count():
    """Увеличивает счётчик запусков и возвращает новое значение."""
    count = get_launch_count() + 1
    try:
        with open(LAUNCH_COUNT_FILE, 'w', encoding='utf-8') as f:
            f.write(str(count))
    except:
        pass
    return count


def show_tutorial(count):
    """Показывает обучающее сообщение для конкретного запуска."""
    if count in TUTORIALS:
        text = TUTORIALS[count]
        print(text)
        try:
            if gui and hasattr(gui, 'append_log'):
                gui.append_log(f"🎓 Подсказка #{count}")
                for line in text.split('\n'):
                    if line.strip():
                        gui.append_log(line)
        except:
            pass


def show_tutorial_manual():
    """Показывает все обучение по команде 'обучение'."""
    print("\n" + "=" * 70)
    print("  🎓 ПОЛНОЕ ОБУЧЕНИЕ JARVIS")
    print("=" * 70)
    try:
        if gui and hasattr(gui, 'append_log'):
            gui.append_log("🎓 Полное обучение JARVIS")
            for i in sorted(TUTORIALS.keys()):
                text = TUTORIALS[i]
                print(text)
                for line in text.split('\n'):
                    if line.strip():
                        gui.append_log(line)
        else:
            for i in sorted(TUTORIALS.keys()):
                print(TUTORIALS[i])
    except:
        pass
    print("\n" + "=" * 70)
    print("  КОНЕЦ ОБУЧЕНИЯ")
    print("=" * 70)
    say("Обучение завершено, сэр. Скажите помощь для списка команд.")




# ==========================================
# JARVIS — ОСНОВНОЙ КЛАСС
# ==========================================

class Jarvis:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.phone = PhoneControl()
        self.translator = GoogleTranslator(source='auto', target='ru')
        self.notes = self.load_json(NOTES_FILE)
        self.passwords = self.load_json(PASSWORDS_FILE)
        self.apps = self.load_json(APPS_FILE)
        self.reminders = []
        self.voice_mouse_active = False
        self.voice_mouse_thread = None
        self.gestures = GestureDetector(self)
        self.clap = ClapDetector(self)
        self.breath_sound = BreathSound()
        self.command_history = []
        self.last_response = ""

        if not os.path.exists(CONFIG_FILE):
            self.phone._save_config()
            print_info(f"Создан конфиг: {CONFIG_FILE}")

        default_apps = {
            "блокнот": "notepad.exe",
            "калькулятор": "calc.exe",
            "проводник": "explorer.exe",
            "диспетчер задач": "taskmgr.exe",
            "командная строка": "cmd.exe",
            "панель управления": "control.exe",
        }
        steam = self.find_steam()
        if steam:
            default_apps["стим"] = steam
            default_apps["steam"] = steam
        for name, path in default_apps.items():
            if name not in self.apps:
                self.apps[name] = path

        self.night_mode_on = False

        self.popular_sites = {
            "вк": "vk.com", "vk": "vk.com", "вконтакте": "vk.com",
            "ютуб": "youtube.com", "youtube": "youtube.com",
            "яндекс": "ya.ru", "гугл": "google.com", "google": "google.com",
            "телеграм": "web.telegram.org", "telegram": "web.telegram.org",
            "github": "github.com", "реддит": "reddit.com", "reddit": "reddit.com",
            "аниме": "animego.org", "анимего": "animego.org",
            "дискорд": "discord.com", "discord": "discord.com",
            "вотсап": "web.whatsapp.com", "whatsapp": "web.whatsapp.com",
            "инстаграм": "instagram.com", "instagram": "instagram.com",
            "тикток": "tiktok.com", "tiktok": "tiktok.com",
            "нетфликс": "netflix.com", "netflix": "netflix.com",
            "твич": "twitch.tv", "twitch": "twitch.tv",
            "озон": "ozon.ru", "ozon": "ozon.ru",
            "вайлдберриз": "wildberries.ru", "wildberries": "wildberries.ru",
            "алиэкспресс": "aliexpress.ru", "aliexpress": "aliexpress.ru",
            "почта": "mail.ru", "mail": "mail.ru",
            "карты": "yandex.ru/maps", "maps": "yandex.ru/maps",
            "погода": "yandex.ru/pogoda", "weather": "yandex.ru/pogoda",
            "новости": "news.yandex.ru", "news": "news.yandex.ru",
            "переводчик": "translate.google.com", "translate": "translate.google.com",
        }

        self.wake_words = ["джарвис", "jarvis", "эй джарвис", "слушай джарвис"]

        self.games = {}
        steam_path = self.find_steam()
        if steam_path:
            self.games["стим"] = steam_path
            self.games["steam"] = steam_path
        self.games["гта"] = r"C:\Users\User\Desktop\GTA - San Andreas.lnk"
        self.games["gta"] = r"C:\Users\User\Desktop\GTA - San Andreas.lnk"
        self.games["майнкрафт"] = r"C:\Program Files (x86)\Minecraft\MinecraftLauncher.exe"
        self.games["minecraft"] = r"C:\Program Files (x86)\Minecraft\MinecraftLauncher.exe"
        self.games["дота"] = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\bin\win64\dota2.exe"
        self.games["dota"] = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\bin\win64\dota2.exe"

        self.game_variants = {
            "стим": ["стим", "сти", "ским", "steam", "стимь", "стин", "стимо", "стиму", "стима", "стиме", "стимчик", "стимка", "стимку", "стэм"],
            "гта": ["гта", "гэта", "гташка", "gta", "сан андреас", "гту", "гта 5", "гташку", "гташки", "гта сан", "гта са", "гта v"],
            "майнкрафт": ["майн", "майнкрафт", "minecraft", "майк", "маенкрафт", "майне", "майна", "майну", "маен", "майнекрафт"],
            "дота": ["дота", "dota", "доту", "доточка", "дота2", "доте", "доты", "дота 2", "дотка", "dota 2"],
        }

        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model = "qwen2.5:1.5b"
        self.ollama_available = self.check_ollama()

        if not self.ollama_available:
            print_warning("Ollama не найдена. Пытаюсь запустить...")
            try:
                ollama_paths = [
                    os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe"),
                    r"C:\Program Files\Ollama\ollama.exe",
                    r"C:\Program Files (x86)\Ollama\ollama.exe",
                ]
                ollama_path = None
                for path in ollama_paths:
                    if os.path.exists(path):
                        ollama_path = path
                        break
                if ollama_path:
                    print_info(f"Найдена Ollama: {ollama_path}")
                    subprocess.Popen([ollama_path, "serve"],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print_info("Жду загрузки Ollama (10 секунд)...")
                    time.sleep(10)
                    self.ollama_available = self.check_ollama()
                    if self.ollama_available:
                        print_success("Ollama успешно запущена!")
                    else:
                        print_warning("Ollama не отвечает. ИИ недоступен.")
                else:
                    print_warning("Ollama не найдена.")
                    print_info("Скачайте: https://ollama.com/download")
                    print_info("После установки: ollama pull qwen2.5:1.5b")
            except Exception as e:
                print_error(f"Ошибка запуска Ollama: {e}")


                # preload_phrases()  # Отключено — используем gTTS на лету
        say("Добро пожаловать, сэр. Я Джарвис.")
        if self.ollama_available:
            say("Искусственный интеллект активен.")


        # Счётчик запусков и обучение
        launch_count = increment_launch_count()
        if launch_count <= 10:
            print_info(f"Запуск #{launch_count}")
            show_tutorial(launch_count)
        else:
            print_info(f"Запуск #{launch_count}")
    # ---------- JSON ----------
    def load_json(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_json(self, filename, data):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def find_steam(self):
        for path in ["C:\\Program Files (x86)\\Steam\\Steam.exe",
                     "C:\\Program Files\\Steam\\Steam.exe"]:
            if os.path.exists(path):
                return path
        return None

    def check_ollama(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False

    # ---------- VOSK / GOOGLE ----------
    def listen_vosk(self, timeout=7):
        if not VOSK_AVAILABLE:
            return None
        try:
            with MIC_LOCK:
                p = pyaudio.PyAudio()
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                               input=True, frames_per_buffer=8000)
                stream.start_stream()
                rec = KaldiRecognizer(vosk_model, 16000)
                rec.SetWords(False)
                start_time = time.time()
                while time.time() - start_time < timeout:
                    data = stream.read(4000, exception_on_overflow=False)
                    if len(data) == 0:
                        continue
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "").strip()
                        if text:
                            stream.stop_stream(); stream.close(); p.terminate()
                            return text.lower()
                final = json.loads(rec.FinalResult())
                text = final.get("text", "").strip()
                stream.stop_stream(); stream.close(); p.terminate()
                if text:
                    return text.lower()
                return None
        except Exception as e:
            print_error(f"Vosk ошибка: {e}")
            return None

    def listen_google(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            if text:
                return text.lower()
            return None
        except:
            return None

    def listen(self):
        if gui:
            gui.set_listening(True)
        if VOSK_AVAILABLE:
            result = self.listen_vosk()
            if result:
                if gui:
                    gui.set_listening(False)
                return result
        result = self.listen_google()
        if gui:
            gui.set_listening(False)
        return result

    # ---------- WAKE WORD ----------
    def is_wake_word(self, command):
        if not command:
            return False
        for wake in self.wake_words:
            if wake in command:
                return True
        return False

    def remove_wake_word(self, command):
        for wake in self.wake_words:
            command = command.replace(wake, "")
        return command.strip()

    # ---------- ФИЛЬТР МУСОРА ----------
    def is_garbage(self, command):
        if not command:
            return True
        command = command.strip().lower()
        if len(command) < 3:
            return True
        garbage_words = {
            "эээ", "ааа", "ммм", "ну", "это", "как его", "ээ", "аа",
            "мм", "хм", "ага", "угу", "да", "нет", "ой", "ах", "ох",
            "блин", "черт", "ё", "е", "ёп", "ёпта", "вау", "упс",
        }
        words = command.split()
        if words and all(w in garbage_words for w in words):
            return True
        trigger_words = [
            "джарвис", "jarvis", "открой", "запусти", "включи", "выключи",
            "найди", "поставь", "скажи", "покажи", "сделай", "переведи",
            "напомни", "закрой", "громче", "тише", "пауза", "продолжи",
            "скриншот", "фото", "время", "погода", "курс", "статус",
            "помощь", "что ты умеешь", "список", "тихий", "голос",
            "жесты", "хлопок", "дыхание", "запиши", "прочитай",
            "распознай", "перезагрузи", "выключи", "заблокируй",
            "спящий", "брось", "сгенерируй", "шутка", "факт",
            "напоминание", "заметка", "заметки", "телефон", "отправь",
            "новая вкладка", "закрой вкладку", "обнови", "назад",
            "вперёд", "следующая вкладка", "предыдущая вкладка",
            "сверни", "браузер", "мышь", "экран", "камера",
            "ночной", "дневной", "яркость", "запись", "диск",
            "процессы", "топ", "место", "свободно",
            "диагностика", "пинг", "скорость", "температура", "батарея",
            "перегрев", "память", "кэш", "обнови", "сеть", "днс",
            "интернет", "файл", "дубликаты", "архив", "зашифруй",
            "расшифруй", "скрой", "история", "повтор", "отмени",
        ]
        if not any(w in command for w in trigger_words):
            return True
        return False

    # ---------- БЫСТРАЯ ОБРАБОТКА ----------
    def try_fast_command(self, command):
        command = command.strip().lower()

        exit_phrases = ["выход", "пока", "заверши", "до свидания",
                        "выход из системы", "заверши работу",
                        "выключись", "отключись"]
        if command in exit_phrases:
            say("До свидания, сэр.")
            return False

        actions = {
            "time": self.do_time, "screenshot": self.do_screenshot,
            "volume_up": self.do_volume_up, "volume_down": self.do_volume_down,
            "play_pause": self.do_play_pause, "system_status": self.do_system_status,
            "disk_space": self.do_disk_space, "top_processes": self.do_top_processes,
            "show_notes": self.do_show_notes, "show_reminders": self.do_show_reminders,
            "currency": self.do_currency, "weather": self.do_weather,
            "joke": self.do_joke, "fact": self.do_fact,
            "password_generate": self.do_password_generate, "dice": self.do_dice,
            "lock": self.do_lock, "sleep": self.do_sleep,
            "shutdown": self.do_shutdown, "restart": self.do_restart,
            "help": self.do_help, "help_full": self.do_help_full,
            "quiet_hour_on": self.do_quiet_hour_on, "quiet_hour_off": self.do_quiet_hour_off,
            "diagnostics": self.do_diagnostics, "ping": self.do_ping,
            "speedtest": self.do_speedtest, "temp": self.do_temp,
            "battery": self.do_battery, "overheat": self.do_overheat,
            "memory_leak": self.do_memory_leak, "cache_clear": self.do_cache_clear,
            "update_check": self.do_update_check, "my_network": self.do_my_network,
            "who_is_online": self.do_who_is_online, "dns_change": self.do_dns_change,
            "internet_off": self.do_internet_off, "internet_on": self.do_internet_on,
            "find_file": self.do_find_file, "big_files": self.do_big_files,
            "duplicates": self.do_duplicates, "old_files": self.do_old_files,
            "sort_downloads": self.do_sort_downloads, "make_archive": self.do_make_archive,
            "unpack_archive": self.do_unpack_archive, "encrypt_file": self.do_encrypt_file,
            "decrypt_file": self.do_decrypt_file, "hide_folder": self.do_hide_folder,
            "history": self.do_history, "repeat_last": self.do_repeat_last,
            "undo_last": self.do_undo_last, "forgot": self.do_forgot,
        }

        for action, variants in SIMPLE_COMMANDS.items():
            if any(v in command for v in variants):
                if action in actions:
                    print_info(f"⚡ Быстрая команда: {action}")
                    actions[action]()
                    return True

        for canonical, variants in self.game_variants.items():
            if any(v in command for v in variants):
                print_info(f"⚡ Быстрая игра: {canonical}")
                self.do_launch_game({"game_name": canonical})
                return True

        for canonical, variants in SITE_VARIANTS.items():
            if any(v in command for v in variants):
                print_info(f"⚡ Быстрый сайт: {canonical}")
                self.do_open_website({"url": canonical})
                return True

        for canonical, variants in APP_VARIANTS.items():
            if any(v in command for v in variants):
                print_info(f"⚡ Быстрое приложение: {canonical}")
                self.do_open_app({"app_name": canonical})
                return True

        if any(w in command for w in ["включи жесты", "жесты включи"]):
            self.do_gestures_on(); return True
        if any(w in command for w in ["выключи жесты", "жесты выключи"]):
            self.do_gestures_off(); return True
        if any(w in command for w in ["включи хлопок", "хлопок включи"]):
            self.do_clap_on(); return True
        if any(w in command for w in ["выключи хлопок", "хлопок выключи"]):
            self.do_clap_off(); return True
        if any(w in command for w in ["включи дыхание", "дыхание включи"]):
            self.do_breath_on(); return True
        if any(w in command for w in ["выключи дыхание", "дыхание выключи"]):
            self.do_breath_off(); return True
        if any(w in command for w in ["прочитай текст с экрана", "распознай текст"]):
            self.do_ocr_screen(); return True
        if any(w in command for w in ["прочитай текст с камеры", "распознай с камеры"]):
            self.do_ocr_camera(); return True
        if any(w in command for w in ["распознай и переведи", "переведи с экрана"]):
            self.do_ocr_translate(); return True

        if any(w in command for w in ["настрой pushall", "настроить pushall", "pushall настройка"]):
            self.do_setup_pushall(); return True
        if any(w in command for w in ["обучение", "покажи обучение", "туториал"]):
            show_tutorial_manual(); return True
        if any(w in command for w in ["открой папку jarvis", "папка jarvis", "открой jarvis папку"]):
            self.do_open_jarvis_folder(); return True

        return None

    # ---------- OLLAMA ----------
    def ask_ollama(self, prompt):
        if not self.ollama_available:
            return None
        try:
            system_prompt = "Ты — Джарвис. Верни ТОЛЬКО JSON с полями action и params.\nКоманда: "
            payload = {"model": self.ollama_model, "prompt": system_prompt + prompt,
                       "stream": False, "temperature": 0.1, "max_tokens": 150}
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                raw = result.get('response', '')
                json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
                return {"action": "chat", "params": {"answer": raw}}
            return None
        except:
            return None

        

    # ---------- ДЕЙСТВИЯ: ПРОСТЫЕ ----------

    def do_time(self, params=None):
        now = datetime.now()
        say(f"{now.hour} часов {now.minute} минут, сэр.")

    def do_open_website(self, params):
        url = params.get('url', '')
        if not url:
            say("Какой сайт открыть, сэр?")
            return
        for key, site in self.popular_sites.items():
            if key in url or url in key:
                url = site
                break
        if not url.startswith('http'):
            url = 'https://' + url
        webbrowser.open(url)
        say(f"Открываю {url}, сэр.")

    def do_open_app(self, params):
        name = params.get('app_name', '')
        for app, path in self.apps.items():
            if name in app or app in name:
                try:
                    subprocess.Popen(path)
                    say(f"Открываю {app}, сэр.")
                    return
                except:
                    pass
        say("Приложение не найдено, сэр.")

    def do_search(self, params):
        query = params.get('query', '')
        if query:
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            say(f"Ищу {query}, сэр.")

    def do_timer(self, params):
        seconds = params.get('seconds', 60)
        say(f"Таймер на {seconds} секунд, сэр.")
        def callback():
            say("Время вышло, сэр!")
            for _ in range(3):
                winsound.Beep(1000, 500)
                time.sleep(0.5)
        timer = threading.Timer(seconds, callback)
        timer.daemon = True
        timer.start()

    def do_weather(self, params=None):
        city = (params or {}).get('city', 'Москва')
        say(f"Погода в {city}, сэр.")
        try:
            response = requests.get(f"https://wttr.in/{city}?format=%t+%c+%w+%h", timeout=5)
            if response.status_code == 200:
                print_success(response.text.strip())
        except:
            say("Не удалось получить погоду, сэр.")

    def do_currency(self, params=None):
        try:
            data = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=10).json()
            usd = data['Valute']['USD']['Value']
            eur = data['Valute']['EUR']['Value']
            say(f"Доллар {usd:.2f}, Евро {eur:.2f} рублей, сэр.")
        except:
            say("Ошибка курса, сэр.")

    def do_translate(self, params):
        text = params.get('text', '')
        if text:
            try:
                result = self.translator.translate(text)
                say(f"Перевод: {result}, сэр.")
            except:
                say("Ошибка перевода, сэр.")

    def do_screenshot(self, params=None):
        filename = os.path.join(PICTURES_DIR, f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.screenshot().save(filename)
        print_success(f"Скриншот: {filename}")
        say("Скриншот сохранён, сэр.")

    def do_volume_up(self, params=None):
        for _ in range(5):
            pyautogui.press("volumeup")
        say("Громкость увеличена, сэр.")

    def do_volume_down(self, params=None):
        for _ in range(5):
            pyautogui.press("volumedown")
        say("Громкость уменьшена, сэр.")

    def do_play_pause(self, params=None):
        pyautogui.press("playpause")
        say("Готово, сэр.")

    def confirm(self, action):
        say(f"Вы хотите {action}, сэр? Скажите да.")
        answer = self.listen()
        return answer and "да" in answer

    def do_shutdown(self, params=None):
        if self.confirm("выключить компьютер"):
            say("Выключаю систему, сэр. До свидания.")
            os.system("shutdown /s /t 10")

    def do_restart(self, params=None):
        if self.confirm("перезагрузить компьютер"):
            say("Перезагружаю, сэр.")
            os.system("shutdown /r /t 10")

    def do_sleep(self, params=None):
        say("Приятного отдыха, сэр.")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    def do_lock(self, params=None):
        ctypes.windll.user32.LockWorkStation()
        say("Компьютер заблокирован, сэр.")

    def do_system_status(self, params=None):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        say(f"CPU {cpu} процентов, RAM {ram.percent} процентов, Диск {disk.percent} процентов, сэр.")
        print_status_bar(self.ollama_available)

    def do_joke(self, params=None):
        jokes = [
            "Почему программисты путают Хэллоуин и Рождество? Потому что 31 октября равно 25 декабря.",
            "Что говорит один бит другому? Прижмись, у меня единица!",
            "Программист — это машина для превращения кофе в код.",
        ]
        say(random.choice(jokes))

    def do_fact(self, params=None):
        facts = [
            "Первый компьютерный вирус появился в 1971 году.",
            "CAPTCHA — это тест Тьюринга.",
            "Первая компьютерная мышь была деревянной.",
        ]
        say(f"Интересный факт, сэр: {random.choice(facts)}")

    def do_password_generate(self, params=None):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(16))
        say(f"Пароль: {password}, сэр.")
        pyperclip.copy(password)

    def do_dice(self, params=None):
        sides = (params or {}).get('sides', 6)
        result = random.randint(1, sides)
        say(f"Выпало {result} на {sides}-гранном кубике, сэр.")

    def do_close_app(self, params):
        name = params.get('program_name', '')
        if not name:
            say("Какую программу закрыть, сэр?")
            return
        found = False
        for proc in psutil.process_iter(['name']):
            try:
                if name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    found = True
            except:
                pass
        say("Программа закрыта, сэр." if found else f"Не найдено '{name}', сэр.")

    def do_voice_mouse(self, params=None):
        if self.voice_mouse_active:
            say("Управление мышью уже активно, сэр.")
            return
        self.voice_mouse_active = True
        say("Управление мышью, сэр. Скажите выйти.")

        def mouse_loop():
            step = 50
            while self.voice_mouse_active:
                cmd = self.listen()
                if not cmd:
                    continue
                if "вверх" in cmd: pyautogui.moveRel(0, -step)
                elif "вниз" in cmd: pyautogui.moveRel(0, step)
                elif "влево" in cmd: pyautogui.moveRel(-step, 0)
                elif "вправо" in cmd: pyautogui.moveRel(step, 0)
                elif "клик" in cmd: pyautogui.click()
                elif "выйти" in cmd or "стоп" in cmd:
                    say("Выхожу, сэр.")
                    self.voice_mouse_active = False
                    break

        self.voice_mouse_thread = threading.Thread(target=mouse_loop, daemon=True)
        self.voice_mouse_thread.start()

    def do_screen_record(self, params):
        duration = (params or {}).get('duration', 30)
        if not SCREEN_RECORD_AVAILABLE:
            say("Библиотеки не установлены, сэр.")
            return
        say(f"Запись экрана на {duration} секунд, сэр.")
        try:
            screen = pyautogui.size()
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            filename = os.path.join(RECORDINGS_DIR, f"record_{time.strftime('%Y%m%d_%H%M%S')}.avi")
            out = cv2.VideoWriter(filename, fourcc, 15.0, (screen.width, screen.height))
            start = time.time()
            while time.time() - start < duration:
                img = ImageGrab.grab(bbox=(0, 0, screen.width, screen.height))
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
                out.write(frame)
                time.sleep(0.066)
            out.release()
            say("Запись сохранена, сэр.")
        except Exception as e:
            print_error(f"Ошибка записи: {e}")
            say("Ошибка записи, сэр.")

    def do_photo(self, params=None):
        if not CV2_AVAILABLE:
            say("Камера не доступна, сэр.")
            return
        say("Делаю снимок, сэр.")
        cap = open_camera()
        if not cap:
            say("Камера занята, сэр.")
            return
        try:
            time.sleep(0.5)
            ret, frame = cap.read()
            if ret:
                filename = os.path.join(PHOTOS_DIR, f"photo_{time.strftime('%Y%m%d_%H%M%S')}.png")
                cv2.imwrite(filename, frame)
                say("Фото сохранено, сэр.")
                os.system(f'start "" "{filename}"')
        except Exception as e:
            print_error(f"Ошибка фото: {e}")
            say("Ошибка фото, сэр.")
        finally:
            close_camera(cap)

    def do_night_mode(self, params=None):
        try:
            subprocess.run(["powershell", "-Command",
                "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,20)"],
                capture_output=True)
            say("Ночной режим включён, сэр.")
        except:
            say("Ошибка, сэр.")

    def do_day_mode(self, params=None):
        try:
            subprocess.run(["powershell", "-Command",
                "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)"],
                capture_output=True)
            say("Дневной режим включён, сэр.")
        except:
            say("Ошибка, сэр.")

    def do_create_note(self, params):
        title = params.get('title', '')
        text = params.get('text', '')
        if not title:
            say("Название заметки, сэр?")
            title = self.listen()
            if not title: return
        if not text:
            say("Текст заметки, сэр?")
            text = self.listen()
            if not text: return
        self.notes[title] = {"text": text, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self.save_json(NOTES_FILE, self.notes)
        say("Заметка сохранена, сэр.")

    def do_read_note(self, params):
        title = params.get('title', '')
        if not title:
            say("Какую заметку прочитать, сэр?")
            title = self.listen()
        if title:
            for name, data in self.notes.items():
                if title in name:
                    say(f"{name}: {data['text'][:200]}, сэр.")
                    return
            say("Заметка не найдена, сэр.")

    def do_show_notes(self, params=None):
        if not self.notes:
            say("Нет заметок, сэр.")
            return
        print_info("СПИСОК ЗАМЕТОК:")
        for i, (name, data) in enumerate(self.notes.items(), 1):
            print(f"    {i}. {name} - {data['text'][:50]}...")
        say("Список заметок на экране, сэр.")

    def do_phone_notify(self, params):
        text = params.get('text', '')
        if text and self.phone.send("📱 Джарвис", text):
            say("Уведомление отправлено, сэр.")
        else:
            say("Не удалось отправить, сэр.")

    def do_phone_find(self, params=None):
        if self.phone.find_phone():
            say("Сигнал отправлен на телефон, сэр.")
        else:
            say("Не удалось отправить сигнал, сэр.")
            
    def do_setup_pushall(self, params=None):
        """Открывает окно настройки PushAll."""
        say("Открываю окно настройки PushAll, сэр.")
        if gui:
            gui.open_pushall_dialog()
            print_info("Окно настройки PushAll открыто.")
        else:
            print_warning("GUI недоступен, настраиваю через консоль.")
            try:
                uid = input("Введите ваш ID пользователя: ").strip()
                ukey = input("Введите ваш API-ключ: ").strip()
                cfg = {}
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                cfg["pushall_user_id"] = uid
                cfg["pushall_user_key"] = ukey
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                self.phone._load_config()
                say("PushAll настроен, сэр.")
            except Exception as e:
                print_error(f"Ошибка: {e}")
                say("Не удалось настроить, сэр.")

    def do_open_jarvis_folder(self, params=None):
        """Открывает папку JARVIS."""
        say("Открываю папку JARVIS, сэр.")
        try:
            os.startfile(JARVIS_HOME)
        except Exception as e:
            print_error(f"Ошибка: {e}")
            say("Не удалось открыть, сэр.")

    def do_phone_screenshot(self, params=None):
        say("Делаю скриншот и отправляю, сэр.")
        filename = os.path.join(PICTURES_DIR, f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.screenshot().save(filename)
        if self.phone.send_file(filename, "📸 Скриншот"):
            say("Скриншот отправлен, сэр.")
        else:
            say("Не удалось отправить, сэр.")

    def do_phone_status(self, params=None):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        msg = f"⚡ CPU: {cpu}%\n💾 RAM: {ram.percent}%\n💽 Диск: {disk.percent}%"
        say("Статус отправлен, сэр." if self.phone.send("📊 Статус ПК", msg) else "Не удалось отправить, сэр.")

    def do_phone_time(self, params=None):
        now = datetime.now()
        msg = f"{now.strftime('%H:%M:%S')}\n{now.strftime('%d.%m.%Y')}"
        say("Время отправлено, сэр." if self.phone.send("⏰ Время", msg) else "Не удалось отправить, сэр.")

    def do_phone_weather(self, params):
        city = (params or {}).get('city', 'Москва')
        try:
            response = requests.get(f"https://wttr.in/{city}?format=%t+%c+%w+%h", timeout=5)
            if response.status_code == 200:
                if self.phone.send(f"🌤️ Погода: {city}", response.text.strip()):
                    say("Погода отправлена, сэр.")
                else:
                    say("Не удалось отправить, сэр.")
        except:
            say("Ошибка погоды, сэр.")

    def do_phone_currency(self, params=None):
        try:
            data = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=10).json()
            usd = data['Valute']['USD']['Value']
            eur = data['Valute']['EUR']['Value']
            msg = f"💵 USD: {usd:.2f}\n💶 EUR: {eur:.2f}"
            say("Курс отправлен, сэр." if self.phone.send("💱 Курс", msg) else "Не удалось отправить, сэр.")
        except:
            say("Ошибка курса, сэр.")

    def do_quiet_hour_on(self, params=None):
        global VOICE_ENABLED
        say("Тихий час включён, сэр. Я буду молчать.")
        VOICE_ENABLED = False

    def do_quiet_hour_off(self, params=None):
        global VOICE_ENABLED
        VOICE_ENABLED = True
        say("Тихий час выключен, сэр. Я снова говорю.")

    def do_new_tab(self, params=None):
        pyautogui.hotkey('ctrl', 't'); say("Открываю новую вкладку, сэр.")

    def do_close_tab(self, params=None):
        pyautogui.hotkey('ctrl', 'w'); say("Закрываю вкладку, сэр.")

    def do_refresh_page(self, params=None):
        pyautogui.hotkey('f5'); say("Обновляю страницу, сэр.")

    def do_back_page(self, params=None):
        pyautogui.hotkey('alt', 'left'); say("Иду назад, сэр.")

    def do_forward_page(self, params=None):
        pyautogui.hotkey('alt', 'right'); say("Иду вперёд, сэр.")

    def do_next_tab(self, params=None):
        pyautogui.hotkey('ctrl', 'tab'); say("Переключаю вкладку, сэр.")

    def do_prev_tab(self, params=None):
        pyautogui.hotkey('ctrl', 'shift', 'tab'); say("Переключаю вкладку, сэр.")

    def do_minimize_browser(self, params=None):
        pyautogui.hotkey('win', 'down'); say("Сворачиваю браузер, сэр.")

    def do_close_browser(self, params=None):
        browsers = ["chrome", "msedge", "firefox", "opera", "browser", "yandex"]
        found = False
        for proc in psutil.process_iter(['name']):
            try:
                for b in browsers:
                    if b in proc.info['name'].lower():
                        proc.terminate()
                        found = True
                        break
            except:
                pass
        say("Браузер закрыт, сэр." if found else "Браузер не найден, сэр.")

    def do_reminder(self, params):
        minutes = params.get('minutes', 10)
        text = params.get('text', 'Напоминание!')
        reminder_data = {"text": text, "time": datetime.now() + timedelta(minutes=minutes), "minutes": minutes}
        self.reminders.append(reminder_data)

        def reminder_callback():
            say(f"Напоминаю, сэр! {text}")
            for _ in range(3):
                winsound.Beep(1500, 500)
                time.sleep(0.3)
            try:
                self.reminders.remove(reminder_data)
            except:
                pass

        timer = threading.Timer(minutes * 60, reminder_callback)
        timer.daemon = True
        timer.start()
        say(f"Напоминание установлено, сэр. Через {minutes} минут.")

    def do_show_reminders(self, params=None):
        if not self.reminders:
            say("Напоминаний нет, сэр.")
            return
        print_info(f"АКТИВНЫЕ НАПОМИНАНИЯ ({len(self.reminders)}):")
        for i, r in enumerate(self.reminders, 1):
            remaining = (r['time'] - datetime.now()).total_seconds() / 60
            if remaining > 0:
                print(f"    {i}. {r['text']} — через {remaining:.1f} мин")
        say(f"Активных напоминаний: {len(self.reminders)}, сэр.")

        

    # ---------- ДЕЙСТВИЯ: ИГРЫ, ТЕХНИЧЕСКИЕ, OCR ----------

    def do_launch_game(self, params):
        game_name = params.get('game_name', '').lower()
        if not game_name:
            say("Какую игру запустить, сэр?")
            return
        canonical_name = game_name
        for canonical, variants in self.game_variants.items():
            for variant in variants:
                if variant in game_name or game_name in variant:
                    canonical_name = canonical
                    break
        for game_key, game_path in self.games.items():
            if game_key in canonical_name or canonical_name in game_key:
                if os.path.exists(game_path):
                    os.startfile(game_path)
                    say(f"Запускаю {game_key}, сэр. Приятной игры.")
                    return
                else:
                    say(f"Не найдена игра {game_key}, сэр.")
                    return
        say(f"Игра '{game_name}' не найдена, сэр.")

    def do_disk_space(self, params=None):
        print_info("СВОБОДНОЕ МЕСТО:")
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                print(f"    {partition.device} {usage.free / (1024**3):.1f} ГБ из {usage.total / (1024**3):.1f} ГБ")
            except:
                pass
        say("Свободное место показано, сэр.")

    def do_top_processes(self, params=None):
        print_info("ТОП-10 ПРОЦЕССОВ:")
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        for i, p in enumerate(processes[:10], 1):
            print(f"    {i}. {p['name']} - CPU: {p['cpu_percent']:.1f}%")
        say("Топ процессов показан, сэр.")

    def do_diagnostics(self, params=None):
        say("Запускаю диагностику, сэр.")
        print_info("═" * 60)
        print_info("ПОЛНАЯ ДИАГНОСТИКА СИСТЕМЫ")
        print_info("═" * 60)
        cpu = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        print(f"  CPU: {cpu}%  |  Ядра: {cpu_cores}  |  Потоки: {cpu_threads}")
        if cpu_freq:
            print(f"       Частота: {cpu_freq.current:.0f} МГц (макс {cpu_freq.max:.0f})")
        ram = psutil.virtual_memory()
        print(f"  RAM: {ram.percent}%  |  Всего: {ram.total / (1024**3):.2f} ГБ  |  Свободно: {ram.available / (1024**3):.2f} ГБ")
        print(f"  ДИСКИ:")
        for part in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(part.mountpoint)
                print(f"    {part.device}  {u.percent}%  ({u.free / (1024**3):.1f} / {u.total / (1024**3):.1f} ГБ)")
            except:
                pass
        try:
            net = psutil.net_io_counters()
            print(f"  СЕТЬ: Отправлено: {net.bytes_sent / (1024**2):.1f} МБ  |  Получено: {net.bytes_recv / (1024**2):.1f} МБ")
        except:
            pass
        try:
            bat = psutil.sensors_battery()
            if bat:
                plug = "подключён" if bat.power_plugged else "не подключён"
                print(f"  БАТАРЕЯ: {bat.percent}%  |  Питание: {plug}")
        except:
            pass
        try:
            requests.get("https://www.google.com", timeout=3)
            print(f"  ИНТЕРНЕТ: доступен")
        except:
            print(f"  ИНТЕРНЕТ: недоступен")
        print_info("═" * 60)
        say("Диагностика завершена, сэр.")

    def do_ping(self, params=None):
        say("Пингую Google, сэр.")
        try:
            result = subprocess.run(["ping", "-n", "4", "8.8.8.8"],
                                    capture_output=True, text=True, timeout=15,
                                    encoding='cp866' if os.name == 'nt' else 'utf-8')
            print_info("РЕЗУЛЬТАТ ПИНГА:")
            print(result.stdout)
            say("Пинг успешен, сэр." if result.returncode == 0 else "Пинг не удался, сэр.")
        except Exception as e:
            print_error(f"Ошибка пинга: {e}")
            say("Ошибка пинга, сэр.")

    def do_speedtest(self, params=None):
        say("Запускаю тест скорости, сэр. Это займёт около 30 секунд.")
        try:
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000
            ping = st.results.ping
            print_info("═" * 50)
            print(f"  ⬇️  Загрузка:  {download:.2f} Мбит/с")
            print(f"  ⬆️  Отдача:    {upload:.2f} Мбит/с")
            print(f"  📡 Пинг:      {ping:.1f} мс")
            print_info("═" * 50)
            say(f"Загрузка {download:.1f}, отдача {upload:.1f} мегабит в секунду, сэр.")
        except ImportError:
            say("Библиотека speedtest не установлена, сэр.")
        except Exception as e:
            print_error(f"Ошибка speedtest: {e}")
            say("Ошибка теста скорости, сэр.")

    def do_temp(self, params=None):
        say("Проверяю температуру, сэр.")
        found = False
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for e in entries:
                        print(f"  {name} / {e.label or '—'}: {e.current}°C")
                        found = True
        except:
            pass
        say("Температура показана, сэр." if found else "Датчики температуры недоступны, сэр.")

    def do_battery(self, params=None):
        try:
            bat = psutil.sensors_battery()
            if not bat:
                say("Батарея не обнаружена, сэр.")
                return
            plug = "подключён к сети" if bat.power_plugged else "работает от батареи"
            secs = bat.secsleft
            if secs == psutil.POWER_TIME_UNLIMITED:
                time_left = "неограниченно"
            elif secs < 0:
                time_left = "неизвестно"
            else:
                time_left = f"{secs // 3600}ч {(secs % 3600) // 60}мин"
            print_info(f"🔋 Заряд: {bat.percent}%  |  {plug}  |  Осталось: {time_left}")
            say(f"Заряд {bat.percent} процентов, сэр. {plug}.")
        except:
            say("Ошибка батареи, сэр.")

    def do_overheat(self, params=None):
        say("Проверяю перегрев, сэр.")
        cpu = psutil.cpu_percent(interval=1)
        alert = False
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for e in entries:
                        if e.current and e.current > 80:
                            print_warning(f"⚠️ {name}: {e.current}°C — ПЕРЕГРЕВ!")
                            alert = True
        except:
            pass
        if cpu > 90:
            print_warning(f"⚠️ CPU загружен на {cpu}%")
            alert = True
        say("Внимание, сэр! Обнаружен перегрев." if alert else "Перегрева нет, сэр. Всё в норме.")

    def do_memory_leak(self, params=None):
        print_info("ТОП-10 ПРОЦЕССОВ ПО ПАМЯТИ:")
        procs = []
        for p in psutil.process_iter(['name', 'memory_percent', 'memory_info']):
            try:
                procs.append(p.info)
            except:
                pass
        procs.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
        for i, p in enumerate(procs[:10], 1):
            mb = (p['memory_info'].rss / (1024**2)) if p['memory_info'] else 0
            print(f"    {i}. {p['name']} — {p['memory_percent']:.1f}% ({mb:.0f} МБ)")
        say("Топ процессов по памяти показан, сэр.")

    def do_cache_clear(self, params=None):
        say("Очищаю кэш, сэр.")
        try:
            count = 0
            size = 0
            for f in os.listdir(CACHE_DIR):
                path = os.path.join(CACHE_DIR, f)
                if os.path.isfile(path):
                    size += os.path.getsize(path)
                    os.remove(path)
                    count += 1
            print_success(f"Удалено {count} файлов, освобождено {size / (1024**2):.1f} МБ")
            say(f"Кэш очищен, сэр. Удалено {count} файлов.")
        except Exception as e:
            print_error(f"Ошибка очистки: {e}")
            say("Ошибка очистки кэша, сэр.")

    def do_update_check(self, params=None):
        say("Проверяю обновления пакетов, сэр.")
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list", "--outdated"],
                                    capture_output=True, text=True, timeout=60)
            if result.stdout.strip():
                print_info("ДОСТУПНЫ ОБНОВЛЕНИЯ:")
                print(result.stdout)
                say("Обновления найдены, сэр.")
            else:
                say("Все пакеты обновлены, сэр.")
        except Exception as e:
            print_error(f"Ошибка: {e}")
            say("Ошибка проверки обновлений, сэр.")

    def do_my_network(self, params=None):
        say("Показываю сетевую информацию, сэр.")
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            hostname, local_ip = "—", "—"
        print_info("СЕТЕВАЯ ИНФОРМАЦИЯ:")
        print(f"  Хост: {hostname}")
        print(f"  Локальный IP: {local_ip}")
        try:
            r = requests.get("https://api.ipify.org?format=json", timeout=5)
            print(f"  Внешний IP: {r.json().get('ip', '—')}")
        except:
            print(f"  Внешний IP: не удалось определить")
        say("Сетевая информация на экране, сэр.")

    def do_who_is_online(self, params=None):
        say("Сканирую локальную сеть, сэр.")
        try:
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
            print_info("УСТРОЙСТВА В ЛОКАЛЬНОЙ СЕТИ:")
            print(result.stdout)
            say("Список устройств на экране, сэр.")
        except Exception as e:
            print_error(f"Ошибка сканирования: {e}")
            say("Ошибка сканирования сети, сэр.")

    def do_dns_change(self, params=None):
        say("Смена DNS требует прав администратора, сэр.")
        print_info("DNS Google: 8.8.8.8 / 8.8.4.4")
        print_info("DNS Cloudflare: 1.1.1.1 / 1.0.0.1")
        say("Инструкция на экране, сэр.")

    def do_internet_off(self, params=None):
        say("Отключаю сеть, сэр.")
        try:
            subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "admin=disable"],
                           capture_output=True, timeout=10)
            say("Интернет отключён, сэр.")
        except:
            say("Не удалось отключить интернет, сэр.")

    def do_internet_on(self, params=None):
        say("Включаю сеть, сэр.")
        try:
            subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "admin=enable"],
                           capture_output=True, timeout=10)
            say("Интернет включён, сэр.")
        except:
            say("Не удалось включить интернет, сэр.")

    def do_find_file(self, params=None):
        name = (params or {}).get('text', '')
        if not name:
            say("Какое имя файла искать, сэр?")
            return
        say(f"Ищу файл {name}, сэр.")
        found = []
        for root, dirs, files in os.walk("C:\\Users"):
            for f in files:
                if name.lower() in f.lower():
                    found.append(os.path.join(root, f))
                    if len(found) >= 20:
                        break
            if len(found) >= 20:
                break
        if found:
            print_info(f"НАЙДЕНО {len(found)} ФАЙЛОВ:")
            for f in found[:20]:
                print(f"    {f}")
            say(f"Найдено {len(found)} файлов, сэр.")
        else:
            say("Файл не найден, сэр.")

    def do_big_files(self, params=None):
        say("Ищу самые большие файлы, сэр.")
        big = []
        for root, dirs, files in os.walk("C:\\Users"):
            for f in files:
                try:
                    p = os.path.join(root, f)
                    big.append((os.path.getsize(p), p))
                except:
                    pass
        big.sort(reverse=True)
        print_info("ТОП-10 БОЛЬШИХ ФАЙЛОВ:")
        for size, path in big[:10]:
            print(f"    {size / (1024**2):8.1f} МБ — {path}")
        say("Топ больших файлов на экране, сэр.")

    def do_duplicates(self, params=None):
        say("Ищу дубликаты в Загрузках, сэр.")
        hashes = {}
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads):
            say("Папка Загрузки не найдена, сэр.")
            return
        for root, dirs, files in os.walk(downloads):
            for f in files:
                p = os.path.join(root, f)
                try:
                    h = hashlib.md5(open(p, 'rb').read()).hexdigest()
                    hashes.setdefault(h, []).append(p)
                except:
                    pass
        dups = {h: paths for h, paths in hashes.items() if len(paths) > 1}
        if dups:
            print_info("НАЙДЕНЫ ДУБЛИКАТЫ:")
            for h, paths in list(dups.items())[:10]:
                print(f"    {paths[0]}  <->  {paths[1]}")
            say(f"Найдено {len(dups)} групп дубликатов, сэр.")
        else:
            say("Дубликатов не найдено, сэр.")

    def do_old_files(self, params=None):
        say("Ищу старые файлы, сэр.")
        cutoff = time.time() - 365 * 24 * 3600
        old = []
        for root, dirs, files in os.walk("C:\\Users"):
            for f in files:
                p = os.path.join(root, f)
                try:
                    if os.path.getmtime(p) < cutoff:
                        old.append(p)
                except:
                    pass
        print_info(f"Найдено {len(old)} старых файлов (первые 20):")
        for p in old[:20]:
            print(f"    {p}")
        say(f"Найдено {len(old)} старых файлов, сэр.")

    def do_sort_downloads(self, params=None):
        say("Сортирую Загрузки, сэр.")
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads):
            say("Папка Загрузки не найдена, сэр.")
            return
        folders = {
            "Изображения": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            "Документы": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
            "Видео": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
            "Музыка": [".mp3", ".wav", ".flac", ".aac"],
            "Архивы": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Программы": [".exe", ".msi", ".apk", ".dmg"],
        }
        moved = 0
        for f in os.listdir(downloads):
            p = os.path.join(downloads, f)
            if not os.path.isfile(p):
                continue
            ext = os.path.splitext(f)[1].lower()
            for folder, exts in folders.items():
                if ext in exts:
                    dest_dir = os.path.join(downloads, folder)
                    os.makedirs(dest_dir, exist_ok=True)
                    try:
                        os.rename(p, os.path.join(dest_dir, f))
                        moved += 1
                    except:
                        pass
                    break
        say(f"Отсортировано {moved} файлов, сэр.")

    def do_make_archive(self, params=None):
        say("Создаю архив, сэр.")
        folder = (params or {}).get('text', '')
        if not folder or not os.path.exists(folder):
            say("Папка не найдена, сэр.")
            return
        zip_name = os.path.join(APP_DATA, f"archive_{time.strftime('%Y%m%d_%H%M%S')}.zip")
        try:
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                for root, dirs, files in os.walk(folder):
                    for f in files:
                        p = os.path.join(root, f)
                        z.write(p, os.path.relpath(p, os.path.dirname(folder)))
            say(f"Архив {zip_name} создан, сэр.")
        except:
            say("Ошибка создания архива, сэр.")

    def do_unpack_archive(self, params=None):
        say("Распаковываю архив, сэр.")
        archives = [f for f in os.listdir(APP_DATA) if f.endswith(('.zip', '.rar', '.7z'))]
        if not archives:
            say("Архивов не найдено, сэр.")
            return
        last = max([os.path.join(APP_DATA, a) for a in archives], key=os.path.getmtime)
        if last.endswith('.zip'):
            try:
                with zipfile.ZipFile(last, 'r') as z:
                    z.extractall(os.path.join(APP_DATA, f"extracted_{time.strftime('%Y%m%d_%H%M%S')}"))
                say(f"Архив {last} распакован, сэр.")
            except:
                say("Ошибка распаковки, сэр.")
        else:
            say("Поддерживается только ZIP, сэр.")

    def do_encrypt_file(self, params=None):
        say("Шифрую файл, сэр.")
        path = (params or {}).get('text', '')
        if not path or not os.path.exists(path):
            say("Файл не найден, сэр.")
            return
        try:
            key = "JARVIS_SECRET_KEY_2024"
            data = open(path, 'rb').read()
            encrypted = bytes(b ^ ord(key[i % len(key)]) for i, b in enumerate(data))
            open(path + ".enc", 'wb').write(encrypted)
            say("Файл зашифрован, сэр.")
        except:
            say("Ошибка шифрования, сэр.")

    def do_decrypt_file(self, params=None):
        say("Расшифровываю файл, сэр.")
        path = (params or {}).get('text', '')
        if not path or not os.path.exists(path):
            say("Файл не найден, сэр.")
            return
        try:
            key = "JARVIS_SECRET_KEY_2024"
            data = open(path, 'rb').read()
            decrypted = bytes(b ^ ord(key[i % len(key)]) for i, b in enumerate(data))
            open(path.replace(".enc", ""), 'wb').write(decrypted)
            say("Файл расшифрован, сэр.")
        except:
            say("Ошибка расшифровки, сэр.")

    def do_hide_folder(self, params=None):
        say("Скрываю папку, сэр.")
        path = (params or {}).get('text', '')
        if not path or not os.path.exists(path):
            say("Папка не найдена, сэр.")
            return
        try:
            subprocess.run(["attrib", "+h", "+s", path], capture_output=True)
            say("Папка скрыта, сэр.")
        except:
            say("Ошибка, сэр.")

    def do_history(self, params=None):
        if not self.command_history:
            say("История пуста, сэр.")
            return
        print_info("ПОСЛЕДНИЕ 20 КОМАНД:")
        for i, cmd in enumerate(self.command_history[-20:], 1):
            print(f"    {i}. {cmd}")
        say("История на экране, сэр.")

    def do_repeat_last(self, params=None):
        say(self.last_response if self.last_response else "Нечего повторять, сэр.")

    def do_undo_last(self, params=None):
        say("Последнее действие отменено, сэр.")

    def do_forgot(self, params=None):
        if self.command_history:
            say(f"Вы недавно говорили: {self.command_history[-1]}, сэр.")
        else:
            say("Не переживайте, сэр. Это было неважно.")

    def do_ocr_screen(self, params=None):
        if not OCR_AVAILABLE:
            say("Tesseract не установлен, сэр.")
            return
        say("Распознаю текст с экрана, сэр.")
        try:
            screenshot = pyautogui.screenshot()
            text = pytesseract.image_to_string(screenshot, lang='rus+eng')
            if not text.strip():
                say("Текст на экране не найден, сэр.")
                return
            pyperclip.copy(text)
            lines = len([l for l in text.split('\n') if l.strip()])
            say(f"Текст скопирован в буфер, сэр. Распознано {lines} строк.")
        except:
            say("Ошибка распознавания, сэр.")

    def do_ocr_file(self, params):
        if not OCR_AVAILABLE:
            say("Tesseract не установлен, сэр.")
            return
        path = params.get('text', '')
        if not path:
            say("Какой файл распознать, сэр?")
            path = input("Введите путь к картинке: ").strip()
        if not os.path.exists(path):
            say("Файл не найден, сэр.")
            return
        say("Распознаю текст из файла, сэр.")
        try:
            img = Image.open(path)
            text = pytesseract.image_to_string(img, lang='rus+eng')
            if not text.strip():
                say("Текст на картинке не найден, сэр.")
                return
            pyperclip.copy(text)
            lines = len([l for l in text.split('\n') if l.strip()])
            say(f"Текст скопирован в буфер, сэр. Распознано {lines} строк.")
        except:
            say("Ошибка распознавания, сэр.")

    def do_ocr_camera(self, params=None):
        if not OCR_AVAILABLE:
            say("Tesseract не установлен, сэр.")
            return
        if not CV2_AVAILABLE:
            say("OpenCV не установлен, сэр.")
            return
        say("Наведите камеру на текст, сэр.")
        cap = open_camera()
        if not cap:
            say("Камера занята, сэр.")
            return
        try:
            time.sleep(2)
            ret, frame = cap.read()
            if not ret:
                say("Не удалось получить кадр, сэр.")
                return
            filename = os.path.join(OCR_DIR, f"ocr_camera_{time.strftime('%Y%m%d_%H%M%S')}.png")
            cv2.imwrite(filename, frame)
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            text = pytesseract.image_to_string(img, lang='rus+eng')
            if not text.strip():
                say("Текст на камере не найден, сэр.")
                return
            pyperclip.copy(text)
            lines = len([l for l in text.split('\n') if l.strip()])
            say(f"Распознано {lines} строк. Текст в буфере, сэр.")
        except Exception as e:
            print_error(f"Ошибка OCR камеры: {e}")
            say("Ошибка распознавания, сэр.")
        finally:
            close_camera(cap)

    def do_ocr_translate(self, params=None):
        if not OCR_AVAILABLE:
            say("Tesseract не установлен, сэр.")
            return
        say("Распознаю текст с экрана и перевожу, сэр.")
        try:
            screenshot = pyautogui.screenshot()
            text = pytesseract.image_to_string(screenshot, lang='rus+eng')
            if not text.strip():
                say("Текст на экране не найден, сэр.")
                return
            try:
                translated = GoogleTranslator(source='auto', target='en').translate(text)
            except:
                translated = text
            pyperclip.copy(translated)
            lines = len([l for l in text.split('\n') if l.strip()])
            say(f"Распознано {lines} строк, переведено. В буфере, сэр.")
        except:
            say("Ошибка распознавания, сэр.")

            

    def do_gestures_on(self, params=None):
        self.gestures.start()

    def do_gestures_off(self, params=None):
        self.gestures.stop()

    def do_clap_on(self, params=None):
        self.clap.start()

    def do_clap_off(self, params=None):
        self.clap.stop()

    def do_breath_on(self, params=None):
        self.breath_sound.start()

    def do_breath_off(self, params=None):
        self.breath_sound.stop()

    def do_show_desktop(self, params=None):
        pyautogui.hotkey('win', 'd')
        say("Сворачиваю окна, сэр.")

    def do_dictation(self, params=None):
        say("Слушаю вас, сэр.")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                dictated = self.recognizer.recognize_google(audio, language="ru-RU")
                time.sleep(0.5)
                pyperclip.copy(dictated)
                pyautogui.hotkey('ctrl', 'v')
                say("Текст вставлен, сэр.")
        except:
            say("Не удалось распознать, сэр.")

    def do_help_full(self, params=None):
        categories = {
            "ГОЛОС И ЖЕСТЫ": [
                "Джарвис, [команда]", "включи/выключи жесты",
                "включи/выключи хлопок", "включи/выключи дыхание",
                "тихий час / включи голос",
            ],
            "СИСТЕМА И САЙТЫ": [
                "который час", "открой вк / ютуб / яндекс / гугл",
                "открой блокнот / калькулятор / проводник",
                "найди [запрос]", "статус системы", "свободное место",
                "топ процессов", "закрой [программа]",
            ],
            "ИГРЫ": ["запусти стим / гта / майнкрафт / дота"],
            "МЕДИА": ["громче / тише", "пауза / продолжи",
                      "шутка / факт", "брось кубик", "сгенерируй пароль"],
            "ЭКРАН И КАМЕРА": ["скриншот", "фото", "запиши экран",
                               "прочитай текст с экрана", "прочитай текст с камеры",
                               "распознай и переведи"],
            "ФАЙЛЫ И ЗАМЕТКИ": ["создай заметку", "прочитай заметку [название]",
                                "покажи заметки", "напомни через X минут [текст]",
                                "покажи напоминания"],
            "ТЕЛЕФОН (PushAll)": ["напомни на телефоне [текст]", "найди телефон",
                                  "отправь скриншот на телефон", "статус на телефон",
                                  "время на телефон", "погода на телефон", "курс на телефон"],
            "ТЕХНИЧЕСКИЕ": ["диагностика", "пинг", "скорость интернета",
                            "температура", "батарея", "перегрев",
                            "утечка памяти", "сбрось кэш", "обнови себя",
                            "моя сеть", "кто в сети", "смени днс",
                            "отключи/включи интернет", "найди файл [имя]",
                            "большие файлы", "дубликаты", "старые файлы",
                            "сортируй загрузки", "в архив / из архива",
                            "зашифруй / расшифруй", "скрытая папка",
                            "история", "повтор", "отмени последнее", "я забыл что хотел"],
            "ПИТАНИЕ": ["выключи компьютер", "перезагрузи компьютер",
                        "спящий режим", "заблокируй компьютер"],
        }
        try:
            if gui and hasattr(gui, 'append_log'):
                gui.append_log("📖 РАСШИРЕННАЯ ПОМОЩЬ JARVIS")
                for title, commands in categories.items():
                    gui.append_log(f"{title}: " + ", ".join(commands))
                gui.append_log("Полный список — в консоли.")
        except Exception as e:
            print(f"[do_help_full] append_log ошибка: {e}")

    def do_help(self, params=None):
        print("=" * 90)
        print("  J A R V I S  —  П О Л Н Ы Й  С П И С О К  К О М А Н Д")
        print("=" * 90)
        print("\nКАК ОБРАЩАТЬСЯ:")
        print("  • Просто говорите команду: «открой ютуб»")
        print("  • Или с обращением: «Джарвис, включи музыку»")
        print("  • Быстрые команды срабатывают мгновенно")
        print("  • Сложные фразы обрабатывает Ollama")
        sections = [
            ("ВРЕМЯ", ["который час", "сколько времени"]),
            ("ИГРЫ", ["стим", "гта", "майнкрафт", "дота"]),
            ("МЕДИА", ["громче", "тише", "пауза", "продолжи",
                       "шутка", "факт", "брось кубик", "сгенерируй пароль"]),
            ("ЭКРАН И КАМЕРА", ["скриншот", "фото", "запиши экран",
                                "прочитай текст с экрана", "распознай и переведи"]),
            ("ЗАМЕТКИ", ["создай заметку", "прочитай заметку", "покажи заметки"]),
            ("ТЕЛЕФОН", ["напомни на телефоне", "найди телефон",
                         "отправь скриншот на телефон", "статус на телефон"]),
            ("БРАУЗЕР", ["новая вкладка", "закрой вкладку", "закрой браузер"]),
            ("СИСТЕМА", ["статус системы", "свободное место", "топ процессов"]),
            ("ТЕХНИЧЕСКИЕ", ["диагностика", "пинг", "скорость интернета",
                             "температура", "батарея", "сбрось кэш",
                             "моя сеть", "найди файл", "большие файлы",
                             "дубликаты", "история", "повтор"]),
            ("ПИТАНИЕ", ["выключи компьютер", "перезагрузи компьютер",
                         "спящий режим", "заблокируй компьютер"]),
            ("ЖЕСТЫ", ["включи жесты", "выключи жесты",
                       "включи хлопок", "выключи хлопок",
                       "включи дыхание", "выключи дыхание"]),
            ("ПОМОЩЬ", ["помощь", "расширенная помощь", "выход"]),
        ]
        for title, commands in sections:
            print(f"\n{'─' * 90}")
            print(f"{title}")
            print(f"{'─' * 90}")
            for cmd in commands:
                print(f"  • {cmd}")
        print("  Всего команд: более 250.")
        print("=" * 90)
        try:
            if gui and hasattr(gui, 'append_log'):
                gui.append_log("📖 ПОЛНАЯ СПРАВКА JARVIS")
                for title, commands in sections:
                    gui.append_log(f"{title}: " + ", ".join(commands))
                gui.append_log("Полный список — в консоли.")
        except Exception as e:
            print(f"[do_help] append_log ошибка: {e}")

    def do_chat(self, params):
        answer = params.get('answer', '')
        say(answer if answer else "Я не понял, сэр.")

    def do_ignore(self, params=None):
        print("  🤖 (игнорирую — не мне)")
        return True

    # ---------- ОБРАБОТКА КОМАНД ----------
    def process(self, command):
        if not command:
            return True
        if gui:
            gui.set_thinking(True)
        try:
            self.command_history.append(command)
            if len(self.command_history) > 100:
                self.command_history.pop(0)

            result = self.try_fast_command(command)
            if result is False:
                return False
            if result is True:
                return True

            if self.is_garbage(command):
                print("  🤖 (мусор, игнорирую)")
                return True

            has_wake_word = self.is_wake_word(command)
            if self.ollama_available:
                print_thinking()
                clean_command = self.remove_wake_word(command) if has_wake_word else command
                if not clean_command.strip():
                    say("Слушаю вас, сэр.")
                    return True
                result = self.ask_ollama(clean_command)
                if result:
                    action = result.get('action', 'chat')
                    params = result.get('params', {})
                    actions = {
                        'time': self.do_time, 'open_website': self.do_open_website,
                        'open_app': self.do_open_app, 'search': self.do_search,
                        'timer': self.do_timer, 'weather': self.do_weather,
                        'currency': self.do_currency, 'translate': self.do_translate,
                        'screenshot': self.do_screenshot, 'volume_up': self.do_volume_up,
                        'volume_down': self.do_volume_down, 'play_pause': self.do_play_pause,
                        'shutdown': self.do_shutdown, 'restart': self.do_restart,
                        'sleep': self.do_sleep, 'lock': self.do_lock,
                        'system_status': self.do_system_status, 'joke': self.do_joke,
                        'fact': self.do_fact, 'password_generate': self.do_password_generate,
                        'dice': self.do_dice, 'close_app': self.do_close_app,
                        'voice_mouse': self.do_voice_mouse, 'screen_record': self.do_screen_record,
                        'photo': self.do_photo, 'night_mode': self.do_night_mode,
                        'day_mode': self.do_day_mode, 'create_note': self.do_create_note,
                        'read_note': self.do_read_note, 'show_notes': self.do_show_notes,
                        'phone_notify': self.do_phone_notify, 'phone_find': self.do_phone_find,
                        'phone_screenshot': self.do_phone_screenshot, 'phone_status': self.do_phone_status,
                        'phone_time': self.do_phone_time, 'phone_weather': self.do_phone_weather,
                        'phone_currency': self.do_phone_currency, 'quiet_hour_on': self.do_quiet_hour_on,
                        'quiet_hour_off': self.do_quiet_hour_off, 'new_tab': self.do_new_tab,
                        'close_tab': self.do_close_tab, 'refresh_page': self.do_refresh_page,
                        'back_page': self.do_back_page, 'forward_page': self.do_forward_page,
                        'next_tab': self.do_next_tab, 'prev_tab': self.do_prev_tab,
                        'minimize_browser': self.do_minimize_browser, 'close_browser': self.do_close_browser,
                        'reminder': self.do_reminder, 'show_reminders': self.do_show_reminders,
                        'launch_game': self.do_launch_game, 'disk_space': self.do_disk_space,
                        'top_processes': self.do_top_processes, 'ocr_screen': self.do_ocr_screen,
                        'ocr_file': self.do_ocr_file, 'show_desktop': self.do_show_desktop,
                        'dictation': self.do_dictation, 'help': self.do_help,
                        'chat': self.do_chat, 'ignore': self.do_ignore,
                        'gestures_on': self.do_gestures_on, 'gestures_off': self.do_gestures_off,
                        'clap_on': self.do_clap_on, 'clap_off': self.do_clap_off,
                        'breath_on': self.do_breath_on, 'breath_off': self.do_breath_off,
                        'ocr_camera': self.do_ocr_camera, 'ocr_translate': self.do_ocr_translate,
                        'help_full': self.do_help_full, 'diagnostics': self.do_diagnostics,
                        'ping': self.do_ping, 'speedtest': self.do_speedtest,
                        'temp': self.do_temp, 'battery': self.do_battery,
                        'overheat': self.do_overheat, 'memory_leak': self.do_memory_leak,
                        'cache_clear': self.do_cache_clear, 'update_check': self.do_update_check,
                        'my_network': self.do_my_network, 'who_is_online': self.do_who_is_online,
                        'dns_change': self.do_dns_change, 'internet_off': self.do_internet_off,
                        'internet_on': self.do_internet_on, 'find_file': self.do_find_file,
                        'big_files': self.do_big_files, 'duplicates': self.do_duplicates,
                        'old_files': self.do_old_files, 'sort_downloads': self.do_sort_downloads,
                        'make_archive': self.do_make_archive, 'unpack_archive': self.do_unpack_archive,
                        'encrypt_file': self.do_encrypt_file, 'decrypt_file': self.do_decrypt_file,
                        'hide_folder': self.do_hide_folder, 'history': self.do_history,
                        'repeat_last': self.do_repeat_last, 'undo_last': self.do_undo_last,
                        'forgot': self.do_forgot,
                    }
                    if action in actions:
                        try:
                            actions[action](params)
                        except Exception as e:
                            print_error(f"Ошибка в {action}: {e}")
                            say("Ошибка выполнения, сэр.")
                        return True
                    else:
                        say("Я не понял, сэр.")
                        return True
                else:
                    say("Ошибка ИИ, сэр.")
                    return True
            if has_wake_word:
                say("Я не понял, сэр. Скажите помощь.")
            else:
                print("  🤖 (игнорирую — не мне)")
            return True
        finally:
            if gui:
                gui.set_thinking(False)

    # ---------- ГЛАВНЫЙ ЦИКЛ ----------
    def run(self):
        print_waiting()
        while True:
            try:
                print("  🎤 Слушаю...", end="", flush=True)
                command = self.listen()
                print("\r" + " " * 50 + "\r", end="")
                if command:
                    print_user(command)
                    if gui:
                        gui.set_user_command(command)
                    start_time = time.time()
                    if not self.process(command):
                        break
                    elapsed = time.time() - start_time
                    print(f"  ⏱️  Выполнено за {elapsed:.2f} сек")
                    print_status_bar(self.ollama_available)
                    print_waiting()
            except KeyboardInterrupt:
                say("Завершаю работу, сэр.")
                break
            except Exception as e:
                print_error(f"Ошибка в цикле: {e}")
                time.sleep(1)
                continue


# ==========================================
# ЗАПУСК
# ==========================================

def run_assistant():
    time.sleep(1)
    try:
        assistant = Jarvis()
        assistant.run()
    except Exception as e:
        print_error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


def main():
    global gui
    try:
        gui = JarvisGUI()
        assistant_thread = threading.Thread(target=run_assistant, daemon=True)
        assistant_thread.start()
        gui.run()
    except Exception as e:
        print_error(f"Критическая ошибка GUI: {e}")
        import traceback
        traceback.print_exc()
        try:
            input("Нажмите Enter для выхода...")
        except:
            pass


if __name__ == "__main__":
    main()

    

