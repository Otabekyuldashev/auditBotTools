import os
import time
import psutil
import telebot
import threading
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib
matplotlib.use("Agg")  # Используем бэкенд без GUI

# Настройки бота
TOKEN = "8135569163:AAH26rkIRhLOlkvqJ3gGycvC0RA7M8g1mIM"
bot = telebot.TeleBot(TOKEN)

# Пути для логов и изображений
LOG_DIR = "log"
IMG_DIR = os.path.join(LOG_DIR, "img_log")
os.makedirs(IMG_DIR, exist_ok=True)

# Флаг для мониторинга
monitoring_active = False

def get_processes():
    """Получает список активных процессов с доп. информацией."""
    process_list = []
    for proc in psutil.process_iter(attrs=["pid", "name", "create_time", "cpu_percent", "memory_info"]):
        try:
            pid = proc.info["pid"]
            name = proc.info["name"]
            create_time = datetime.fromtimestamp(proc.info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
            uptime = int((datetime.now() - datetime.fromtimestamp(proc.info["create_time"])).total_seconds())
            cpu_usage = proc.info["cpu_percent"]
            memory_usage = round(proc.info["memory_info"].rss / (1024 * 1024), 2)  # В мегабайтах
            
            process_info = f"PID: {pid}\n" \
                           f"Название: {name}\n" \
                           f"Запущен: {create_time}\n" \
                           f"Время работы: {uptime} сек\n" \
                           f"CPU: {cpu_usage}%\n" \
                           f"Память: {memory_usage} MB\n" \
                           f"{'-' * 30}"
            
            process_list.append(process_info)
        
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return "\n".join(process_list)

def monitor_system(chat_id):
    """Функция мониторинга нагрузки системы."""
    global monitoring_active
    monitoring_active = True
    while monitoring_active:
        cpu_usage = psutil.cpu_percent(interval=1)
        mem_usage = psutil.virtual_memory().percent

        plt.figure()
        plt.bar(['CPU', 'RAM'], [cpu_usage, mem_usage], color=['blue', 'green'])
        plt.ylim(0, 100)
        plt.ylabel('% Загрузки')
        plt.title('Мониторинг системы')

        img_path = os.path.join(IMG_DIR, "monitoring.png")
        plt.savefig(img_path)
        plt.close()

        with open(img_path, "rb") as img:
            bot.send_photo(chat_id, img)

        time.sleep(120)  # Каждые 2 минуты

@bot.message_handler(commands=['htop'])
def send_processes(message):
    processes = get_processes()
    with open("log/processes.txt", "w", encoding="utf-8") as file:
        file.write(processes)
    with open("log/processes.txt", "rb") as file:
        bot.send_document(message.chat.id, file)

@bot.message_handler(commands=['exit_htop'])
def exit_thtop(message):
    bot.send_message(message.chat.id, "Команда htop завершена.")

@bot.message_handler(commands=['monitoring'])
def start_monitoring(message):
    bot.send_message(message.chat.id, "Мониторинг запущен. Скриншоты каждые 2 минуты.")
    threading.Thread(target=monitor_system, args=(message.chat.id,), daemon=True).start()

@bot.message_handler(commands=['exit_monitoring'])
def stop_monitoring(message):
    global monitoring_active
    monitoring_active = False
    bot.send_message(message.chat.id, "Мониторинг остановлен.")

# Запуск бота
print("Бот запущен...")
bot.polling(none_stop=True)
