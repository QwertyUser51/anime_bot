import sqlite3
from telebot import TeleBot, types
from telebot.apihelper import ApiException
from db import *
from config import *
from admin import *

user_states = {}
bot = TeleBot(token)
init_db()

def check_user_subscription(user_id, channel_id):
    try:
        chat_member = bot.get_chat_member(channel_id, user_id)
        return chat_member.status in ['member', 'administrator', 'creator', 'restricted']
    except:
        return False

def check_all_subscriptions(user_id):
    channels = get_channels()
    if not channels:
        return True  
    
    for channel in channels:
        if not check_user_subscription(user_id, channel['id']):
            return False
    return True

def create_subscription_keyboard():
    channels = get_channels()
    markup = types.InlineKeyboardMarkup()
    
    for channel in channels:
        channel_button = types.InlineKeyboardButton(
            text="📢ПОДПИСАТЬСЯ",
            url=channel['link']
        )
        markup.add(channel_button)
    
    check_button = types.InlineKeyboardButton(
        text="✅ Проверить подписку", 
        callback_data="check_subscription"
    )
    markup.add(check_button)
    
    return markup

def create_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    search_button = types.KeyboardButton("🔍 Найти аниме по коду")
    markup.add(search_button)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_states[user_id] = {'waiting_for_code': False}
    if check_all_subscriptions(user_id):
        show_main_menu(message.chat.id)
    else:
        show_subscription_request(message.chat.id)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.send_message(message.chat.id, "❌ Доступ запрещен")
        return
    
    user_states[user_id] = {'admin_mode': True}
    bot.send_message(
        message.chat.id, 
        "👑 Панель администратора", 
        reply_markup=create_admin_keyboard()
    )

def show_subscription_request(chat_id):
    channels = get_channels()
    
    if not channels:
        bot.send_message(chat_id, "❌ Ошибка: каналы для подписки не найдены в базе данных.")
        return
    
    message_text = (
        "📢 <b>Для использования бота необходимо подписаться на следующие каналы:</b>\n\n"
        "Нажмите на кнопки ниже чтобы перейти к каналам и подписаться:\n\n"
        "После подписки нажмите кнопку <b>'✅ Проверить подписку'</b>"
    )
    
    keyboard = create_subscription_keyboard()
    bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode='HTML')

def show_main_menu(chat_id):
    markup = create_main_keyboard()
    bot.send_message(
        chat_id, 
        "✅ <b>Отлично! Вы подписаны на все необходимые каналы.</b>\n\n"
        "Теперь вы можете использовать функции бота.\n"
        "Нажмите кнопку ниже для поиска аниме по коду.", 
        reply_markup=markup,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def handle_check_subscription(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if check_all_subscriptions(user_id):
        bot.answer_callback_query(call.id, "✅ Подписка подтверждена!")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✅ <b>Подписка подтверждена!</b>\n\nТеперь вы можете использовать бота.",
            parse_mode='HTML'
        )
        show_main_menu(chat_id)
    else:
        bot.answer_callback_query(call.id, "❌ Вы не подписаны на все каналы!")
        update_subscription_status(chat_id, message_id, user_id)

def update_subscription_status(chat_id, message_id, user_id):
    message_text = "\n<b>Подпишитесь на все каналы и нажмите '✅ Проверить подписку'</b>"
    keyboard = create_subscription_keyboard()
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=message_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda message: message.text == "🔍 Найти аниме по коду")
def handle_search_request(message):
    user_id = message.from_user.id
    
    if not check_all_subscriptions(user_id):
        show_subscription_request(message.chat.id)
        return
    user_states[user_id] = {'waiting_for_code': True}
    bot.send_message(
        message.chat.id, 
        "🔢 Введите код аниме для поиска:",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Обработчики админских кнопок
@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def handle_stats(message):
    if is_admin(message.from_user.id):
        show_stats(bot, message)

@bot.message_handler(func=lambda message: message.text == "➕ Добавить аниме")
def handle_add_anime(message):
    if is_admin(message.from_user.id):
        add_anime_start(bot, message, user_states)

@bot.message_handler(func=lambda message: message.text == "📢 Добавить канал")
def handle_add_channel(message):
    if is_admin(message.from_user.id):
        add_channel_start(bot, message, user_states)

@bot.message_handler(func=lambda message: message.text == "🎬 Список аниме")
def handle_anime_list(message):
    if is_admin(message.from_user.id):
        show_anime_list(bot, message)

@bot.message_handler(func=lambda message: message.text == "👥 Список каналов")
def handle_channels_list(message):
    if is_admin(message.from_user.id):
        show_channels_list(bot, message)

@bot.message_handler(func=lambda message: message.text == "➖ Удалить аниме")
def handle_delete_anime(message):
    if is_admin(message.from_user.id):
        delete_anime_start(bot, message, user_states)

@bot.message_handler(func=lambda message: message.text == "🗑️ Удалить канал")
def handle_delete_channel(message):
    if is_admin(message.from_user.id):
        delete_channel_start(bot, message, user_states)

@bot.message_handler(func=lambda message: message.text == "🔙 Главное меню")
def handle_back_to_main(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        user_states[user_id] = {'admin_mode': False}
    
    if check_all_subscriptions(user_id):
        show_main_menu(message.chat.id)
    else:
        show_subscription_request(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "❌ Отмена")
def handle_cancel(message):
    if is_admin(message.from_user.id):
        cancel_operation(bot, message, user_states)

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    user_id = message.from_user.id
    
    if is_admin(user_id) and handle_admin_operations(bot, message, user_states):
        return

    if user_id not in user_states or not user_states[user_id].get('waiting_for_code', False):
        if check_all_subscriptions(user_id):
            show_main_menu(message.chat.id)
        else:
            show_subscription_request(message.chat.id)
        return
    
    code = message.text.strip()
    if not code.isdigit():
        bot.send_message(message.chat.id, "❌ Код должен состоять только из цифр. Попробуйте еще раз:")
        return
    
    anime_name = get_movie(code)
    
    if anime_name:
        response = f"🎌 <b>Найденное аниме:</b>\n\n🔢 Код: {code}\n📺 Название: {anime_name}"
    else:
        response = f"❌ Аниме с кодом {code} не найдено в базе данных."
    
    user_states[user_id]['waiting_for_code'] = False
    
    if check_all_subscriptions(user_id):
        bot.send_message(message.chat.id, response, reply_markup=create_main_keyboard(), parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, response, parse_mode='HTML')
        show_subscription_request(message.chat.id)

if __name__ == "__main__":
    bot.polling(none_stop=True)