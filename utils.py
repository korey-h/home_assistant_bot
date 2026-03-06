import json
import requests

import connect_conf as concf

from typing import Dict, List

from models import Button, ButtonStorage
from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup)


def get_services(ha_token: str) -> List[dict]:
    url = concf.HOST + '/api/services'
    headers = {
        'Authorization': f'Bearer {ha_token}',
        'Content-Type': 'application/json'}
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        print(f'Адрес {url} не существует либо сервер не доступен. \n', e)
        return []
    if response.status_code != 200:
        return []
    return response.json()


def make_services_tree(ha_services: List[Dict[str, dict|str]],
                       active_devices: List[Dict[str, str]]
                       ) -> Dict[str, Dict[str, str|Dict[int, str]]]:
    services_tree = {}
    if not (active_devices or ha_services):
        return {'empty': {'info': 'no_input_data'}}
    for device in active_devices:
        entity_id = device.get('entity_id')
        domain = device.get('domain')
        name = device.get('domain','')
        if not (entity_id or domain):
            continue
        domain_services = []
        for group in ha_services:
            orig_domain = group.get('domain', '')
            if not orig_domain:
                continue
            if orig_domain == domain:
                orig_services: Dict[str, dict] = group.get('services', {}) # type: ignore
                if not orig_services:
                    continue
                domain_services = list(orig_services.keys())
                break
        if not domain_services:
            continue
        domain_services.sort()
        services = {num: serv for num, serv in enumerate(domain_services)}
        services_tree.update({
            entity_id: {
                'entity_name': name,
                'domain': domain,
                'services': services}})
    if not services_tree:
        return {'empty': {'info': 'no_services'}}
    return services_tree


def fill_storage(active_services: dict, storage: ButtonStorage) -> None:
    for device, features in active_services.items():
        name = features['entity_name'] if features['entity_name'] else device
        domain = features['domain']
        dev_btn = Button(entity_id=device, name=name, domain=domain,
                         handler=dev_btn_handler)
        storage.add_button(dev_btn)
        for service in features['services'].values():
            serv_btn = Button(entity_id=device, name=service, domain=domain,
                              parent_id=dev_btn.id, service=service,
                              handler=serv_btn_handler)
            storage.add_button(serv_btn)


def make_devices_kbd(storage: ButtonStorage):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = storage.get_devices_btn()
    if not buttons:
        return
    for button in buttons:
        keyboard.add(button.make_inline_markup())
    return keyboard


def dev_btn_handler(service: str, domain: str, id: int,
                    store_class: ButtonStorage) -> Dict[str, dict|str]:
    buttons = store_class.get_child(id)
    if not buttons:
        return {}
    keyboard = InlineKeyboardMarkup(row_width=3)
    markuped = []
    for button in buttons:
        markuped.append(button.make_inline_markup())
    keyboard.add(*markuped)
    pre_mess = [
        {'text': 'Доступные действия:', 'reply_markup': keyboard}
    ]
    return {'ext_act_name': 'send_multymessage',
            'data': {'pre_mess': pre_mess}}


def serv_btn_handler(service: str, domain: str, id: int,
                    store_class: ButtonStorage) -> None:
    button = store_class.get_button(id)
    if not button:
        print('dev_serv_handler: кнопка не найдена')
        return
    entity_id = button.entity_id
    service = button.service
    domain = button.domain
    url = concf.HOST + '/api/services' + f'/{domain}/{service}'
    headers = {
        'Authorization': f'Bearer {concf.ha_token}',
        'Content-Type': 'application/json'}
    
    json={'entity_id': entity_id}
    
    try:
        response = requests.post(url, headers=headers, json=json)
    except Exception as e:
        print(f'{url} не существует либо сервер не доступен. \n', e)
        return
    if response.status_code != 200:
        return
    print(response.json())