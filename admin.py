import sqlite3
from telebot import types
from config import admin_id, db_name
from db import new_movie, new_channel, get_channels, delete_anime, delete_channel

# Глобальный словарь для состояний админов (если нужно будет расширить на нескольких админов)
admin_states = {}

def is_admin(user_id):
    return str(user_id) == admin_id

def create_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "📊 Статистика",
        "➕ Добавить аниме", 
        "➖ Удалить аниме",
        "📢 Добавить канал",
        "🗑️ Удалить канал",
        "👥 Список каналов",
        "🎬 Список аниме",
        "🔙 Главное меню"
    ]
    markup.add(*buttons)
    return markup

def get_bot_stats():
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        
        # Статистика аниме
        cur.execute("SELECT COUNT(*) FROM movies")
        anime_count = cur.fetchone()[0]
        
        # Статистика каналов
        cur.execute("SELECT COUNT(*) FROM channels")
        channels_count = cur.fetchone()[0]
        
        con.close()
        
        return anime_count, channels_count
        
    except Exception as e:
        return None, str(e)

def show_stats(bot, message):
    anime_count, channels_count = get_bot_stats()
    
    if isinstance(channels_count, str):  # Если вернулась ошибка
        bot.send_message(message.chat.id, f"❌ Ошибка: {channels_count}")
        return
    
    stats_text = f"""📊 Статистика бота:

🎬 Аниме в базе: {anime_count}
📢 Каналов для подписки: {channels_count}
"""
    bot.send_message(message.chat.id, stats_text)

def add_anime_start(bot, message, user_states):
    user_id = message.from_user.id
    user_states[user_id] = {'adding_anime': True, 'step': 'waiting_name'}
    bot.send_message(
        message.chat.id, 
        "Введите название аниме:",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Отмена")
    )

def add_channel_start(bot, message, user_states):
    user_id = message.from_user.id
    user_states[user_id] = {'adding_channel': True, 'step': 'waiting_link'}
    bot.send_message(
        message.chat.id, 
        "Отправьте ссылку на канал:",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Отмена")
    )

def show_anime_list(bot, message):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("SELECT name, code FROM movies LIMIT 50")
        anime_list = cur.fetchall()
        con.close()
        
        if not anime_list:
            bot.send_message(message.chat.id, "📭 База аниме пуста")
            return
        
        text = "🎬 Список аниме (первые 50):\n\n"
        for anime in anime_list:
            text += f"🔹 {anime[0]} - Код: {anime[1]}\n"
        
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                bot.send_message(message.chat.id, part)
        else:
            bot.send_message(message.chat.id, text)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

def show_channels_list(bot, message):
    try:
        channels = get_channels()
        
        if not channels:
            bot.send_message(message.chat.id, "📭 Нет каналов для подписки")
            return
        
        text = "📢 Список каналов:\n\n"
        for channel in channels:
            text += f"🔹 ID: {channel['id']}\nСсылка: {channel['link']}\n\n"
        
        bot.send_message(message.chat.id, text)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

def delete_anime_start(bot, message, user_states):
    user_id = message.from_user.id
    user_states[user_id] = {'deleting_anime': True}
    bot.send_message(
        message.chat.id, 
        "Введите код аниме для удаления:",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Отмена")
    )

def delete_channel_start(bot, message, user_states):
    user_id = message.from_user.id
    user_states[user_id] = {'deleting_channel': True}
    bot.send_message(
        message.chat.id, 
        "Введите ID канала для удаления:",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Отмена")
    )

def cancel_operation(bot, message, user_states):
    user_id = message.from_user.id
    user_states[user_id] = {'admin_mode': True}
    bot.send_message(
        message.chat.id, 
        "Операция отменена", 
        reply_markup=create_admin_keyboard()
    )

def handle_admin_operations(bot, message, user_states):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return False
    
    state = user_states[user_id]
    
    # Добавление аниме
    if state.get('adding_anime'):
        if state.get('step') == 'waiting_name':
            state['anime_name'] = message.text
            state['step'] = 'waiting_code'
            bot.send_message(message.chat.id, "Теперь введите код аниме:")
            return True
        elif state.get('step') == 'waiting_code':
            try:
                code = int(message.text)
                if new_movie(state['anime_name'], code):
                    bot.send_message(
                        message.chat.id, 
                        f"✅ Аниме '{state['anime_name']}' с кодом {code} добавлено!",
                        reply_markup=create_admin_keyboard()
                    )
                else:
                    bot.send_message(message.chat.id, "❌ Ошибка добавления аниме")
                
                user_states[user_id] = {'admin_mode': True}
                return True
            except ValueError:
                bot.send_message(message.chat.id, "❌ Код должен быть числом!")
                return True
    
    # Добавление канала
    elif state.get('adding_channel'):
        if state.get('step') == 'waiting_link':
            state['channel_link'] = message.text
            state['step'] = 'waiting_id'
            bot.send_message(message.chat.id, "Теперь введите ID канала (число):")
            return True
        elif state.get('step') == 'waiting_id':
            try:
                channel_id = int(message.text)
                if new_channel(state['channel_link'], channel_id):
                    bot.send_message(
                        message.chat.id, 
                        f"✅ Канал с ID {channel_id} добавлен!",
                        reply_markup=create_admin_keyboard()
                    )
                else:
                    bot.send_message(message.chat.id, "❌ Ошибка добавления канала")
                
                user_states[user_id] = {'admin_mode': True}
                return True
            except ValueError:
                bot.send_message(message.chat.id, "❌ ID должен быть числом!")
                return True
    
    # Удаление аниме
    elif state.get('deleting_anime'):
        try:
            code = int(message.text)
            if delete_anime(code):
                bot.send_message(
                    message.chat.id, 
                    f"✅ Аниме с кодом {code} удалено!",
                    reply_markup=create_admin_keyboard()
                )
            else:
                bot.send_message(message.chat.id, "❌ Аниме с таким кодом не найдено")
            
            user_states[user_id] = {'admin_mode': True}
            return True
        except ValueError:
            bot.send_message(message.chat.id, "❌ Код должен быть числом!")
            return True
    
    # Удаление канала
    elif state.get('deleting_channel'):
        try:
            channel_id = int(message.text)
            if delete_channel(channel_id):
                bot.send_message(
                    message.chat.id, 
                    f"✅ Канал с ID {channel_id} удален!",
                    reply_markup=create_admin_keyboard()
                )
            else:
                bot.send_message(message.chat.id, "❌ Канал с таким ID не найден")
            
            user_states[user_id] = {'admin_mode': True}
            return True
        except ValueError:
            bot.send_message(message.chat.id, "❌ ID должен быть числом!")
            return True
    
    return False