import requests
import time

import connect_conf as concf

from typing import Dict, List

from models import Button, ButtonStorage
from telebot.types import InlineKeyboardMarkup


def make_api_request(endpoint: str, req_type: str, **params) -> dict|None:
    url = concf.HOST + '/api' + endpoint
    headers = {
        'Authorization': f'Bearer {concf.ha_token}',
        'Content-Type': 'application/json'}
    method = None
    if req_type == 'get':
        method = requests.get
    elif req_type == 'post':
        method = requests.post
    
    if method is None:
        return
    
    try:
        response = method(url=url, headers=headers, **params)
    except Exception as e:
        print(f'Адрес {url} не существует либо сервер не доступен. \n', e)
        return
    status = response.status_code
    if  status == 200:
        return response.json()
    print(f'{status}: {url}')


def get_services() -> List[dict]:
    endpoint = '/services'
    res = make_api_request(endpoint=endpoint, req_type='get')
    res = res if res is not None else []
    return res # type: ignore


def make_services_tree(ha_services: List[Dict[str, dict|str]],
                       active_devices: List[Dict[str, str]]
                       ) -> Dict[str, Dict[str, str|Dict[int, str]]]:
    services_tree = {}
    if not (active_devices or ha_services):
        return {'empty': {'info': 'no_input_data'}}
    for device in active_devices:
        entity_id = device.get('entity_id', '')
        domain = entity_id.split('.')[0]
        name = device.get('name','')
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


def dev_btn_handler(id: int,
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


def serv_btn_handler(id: int, store_class: ButtonStorage) -> dict:
    button = store_class.get_button(id)
    if not button:
        mess = {'text':'кнопка не найдена'}
        print(f'dev_serv_handler: {mess}')
        return {'ext_act_name': 'send_multymessage',
                'data': {'pre_mess': [mess]}}
    entity_id = button.entity_id
    service = button.service
    domain = button.domain
    endpoint = f'/services/{domain}/{service}'
    json={'entity_id': entity_id}
    res = make_api_request(endpoint=endpoint,req_type='post', json=json)
    time.sleep(1)
    state = check_state(entity_id)
    if state:
        text = f'Состояние: "{state}"'
    else:
        text = 'Результат действия не известен.'
    return {'ext_act_name': 'send_multymessage',
            'data': {'pre_mess': [{'text': text}]}}


def check_state(entity_id: str) -> str:
    endpoint = '/states' + f'/{str(entity_id)}'
    res = make_api_request(endpoint=endpoint, req_type='get')
    if res:
        return res['state']
    return ''