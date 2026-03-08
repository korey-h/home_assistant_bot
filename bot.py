import logging
import json
import os
import threading
import time

import connect_conf as concf, utils

from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from telebot import TeleBot
from typing import List

from models import ButtonStorage, User

if os.path.exists('.env'):
    load_dotenv('.env')
else:
    print('файл .env с ключами доступа к боту и т.п. не найден.')

LET_VIEW_EXS = False

bot = TeleBot(concf.tg_token) 

logger = logging.getLogger(__name__)
handler = RotatingFileHandler(
    'exceptions.log', maxBytes=50000000, backupCount=3)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

err_info = ''
users = {}
approved_users = []
active_devices = []
storage = ButtonStorage()

def load_configs():
    global active_devices
    global approved_users

    with open('users.txt', encoding='utf-8') as f:
        raw_user_list = f.read()
    try:
        approved_users = json.loads(raw_user_list)
    except Exception as e:
        print(f'Файл со списком доверенных пользователей заполнен с ошибками. \n', e)

    with open('active_devices.txt', encoding='utf-8') as f:
        raw_devices = f.read()
    try:
        active_devices = json.loads(raw_devices)
    except Exception as e:
        print(f'Файл со списком устройств заполнен с ошибками. \n', e)


@bot.message_handler(commands=['start'])
def welcome(message):
    load_configs() # TODO добавить отправку ошибок
    user = get_user(message)
    user.set_role(approved_users)
    if not has_access(user):
        return
    ha_services = utils.get_services()
    if not ha_services:
        bot.send_message(
            user.id,
            text = 'Сервер Home Assistance не доступен.')
        return
    active_services = utils.make_services_tree(ha_services, active_devices)
    storage.reset()
    if active_services:
        utils.fill_storage(active_services, storage)
        send_multymessage(user.id,
            [{'text': 'Доступные устройства:','reply_markup': utils.make_devices_kbd(storage)}]
        )


@bot.message_handler(content_types=['text'])
def command_router(message):
    user = get_user(message)
    if not has_access(user):
        return
    data = message.text
    try_exec_stack(message, user, data)


@bot.callback_query_handler(func=lambda call: True, )
def inline_keys_exec(call):
    user = get_user(call.message)
    try:
        id = int(call.data)
    except Exception:
        return
    button = storage.get_button(id)
    res = {}
    if button:
        res = button.make_action()
    if res:
        get_ext_action(user.id, **res)



def get_user(message) -> User:
    user_id = message.chat.id
    return users.setdefault(user_id, User(user_id))


def try_exec_stack(message, user: User, data, **kwargs):
    command = user.get_cmd_stack()
    if command and callable(command['cmd']): # type: ignore
        call_from = 'stack'
        if kwargs and kwargs.get('from'):
            call_from = kwargs.get('from')
        context = {
            'message': message,
            'user': user,
            'data': data,
            'from': call_from}
        command['cmd'](**context) # type: ignore
    else:
        bot.send_message(user.id, text='?')


def has_access(user: User):
    if user.role != 'manager':
        bot.send_message(user.id, text='В доступе к серверу Home Assistant отказано.')
        return False
    return True


def send_multymessage(user_id, pre_mess: List[dict]):
    for mess_data in pre_mess:
        bot.send_message(user_id, **mess_data)


def get_ext_action(user_id, ext_act_name:str, data: dict) -> None:
    ext_actions = {'send_multymessage': send_multymessage}
    action = ext_actions.get(ext_act_name)
    if action:
        action(user_id, **data)


##################################################################
def err_informer(chat_id):
    global err_info
    prev_err = err_info
    while True:
        if err_info == '' or err_info == prev_err:
            time.sleep(60)
            print('!', end=' ')
            continue
        prev_err = err_info
        try:
            bot.send_message(
                chat_id,
                f'Было выброшено исключение: {err_info}')
        except Exception:
            pass


if __name__ == '__main__':
    develop_id = os.getenv('DEVELOP_ID')
    t1 = threading.Thread(target=err_informer, args=[develop_id])
    t1.start()

    while True:
        try:
            bot.polling(non_stop=True)
        except Exception as error:
            if LET_VIEW_EXS:
                break
            err_info = error.__repr__()
            logger.exception(error)
            time.sleep(3)