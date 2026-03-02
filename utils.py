import requests

from typing import Dict, List

HOST = 'http://192.168.1.89:8123'


def get_services(ha_token: str) -> List[dict]:
    url = HOST + '/api/services'
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
                'services': services}})
    if not services_tree:
        return {'empty': {'info': 'no_services'}}
    return services_tree
