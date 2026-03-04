

from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup)
from typing import Callable, List

class User:

    def __init__(self, id: str, approved_users: List[dict] = []):
        self.id = id
        self._commands = []
        self.storage = []
        self.role = self._get_role(id, approved_users)

    @staticmethod
    def _get_role(id: str, approved_users: List[dict]) -> str:
        if not approved_users:
            return ''
        for user in approved_users:
            if str(id) == user['user_id']:
                return user['role']
        return ''

    def is_stack_empty(self):
        return len(self._commands) == 0

    def get_cmd_stack(self):
        if len(self._commands) > 0:
            return self._commands[-1]
        return []

    def set_cmd_stack(self, cmd_stack):
        if isinstance(cmd_stack, dict):
            self._commands.append(cmd_stack)

    cmd_stack = property(get_cmd_stack, set_cmd_stack)

    def clear_stack(self):
        self._commands.clear()

    def cmd_stack_pop(self):
        if len(self._commands) > 0:
            return self._commands.pop()
        return
    
class Button:
    NAME_LENTH = 50
    def __init__(self, domain: str, name: str, service: str = '',
                 parent_id: int|None = None, handler: Callable|None = None) -> None:
        self.id: int|None = None
        self.parent_id = parent_id
        self.handler = handler
        self.domain = domain
        self.service = service
        self.name = name
    
    def make_inline_markup(self) -> InlineKeyboardButton:
        name = self.name if len(self.name) <= self.NAME_LENTH else self.name[:self.NAME_LENTH]
        return InlineKeyboardButton(text=name, callback_data=self.id)
    
    def make_action(self):
        if self.handler is None:
            print(f'Для кнопки "{self.name}" ({self.id}) не назначено действие.')
            return
        attrs = {'service': self.service, 'domain': self.domain, 'id': self.id}
        return self.handler(**attrs)
    
    def __str__(self) -> str:
        return f'<Button obj: {self.name}>'
    

class ButtonStorage:
    def __init__(self, buttons: List[Button] = []) -> None:
        self._storage = {}
        self._relationships = {}
        self.__free_id = 0
        if buttons:
            self.add_many(buttons)
    
    def reset(self) -> None:
        self._storage = {}
        self._relationships = {}
        self.__free_id = 0

    def __generate_id(self) -> int:
        id = self.__free_id
        self.__free_id += 1
        return id
    
    def add_button(self, button: Button) -> None:
        id = self.__generate_id()
        button.id = id
        self._storage.update({id: button})
        parent_id = button.parent_id
        if parent_id is not None :
            child = self._relationships.setdefault(parent_id, [id,])
            if id not in child:
                child.append(id)

    def add_many(self, buttons: List[Button]) -> None:
        for button in buttons:
            self.add_button(button)

    def get_button(self, id: int) -> Button|None:
        return self._storage.get(id)

    def get_child(self, parent_id) -> List[Button]:
        child_ids = self._relationships.get(parent_id)
        if not child_ids:
            return []
        child = []
        for id in child_ids:
            child.append(self._storage[id])
        return child
    

if __name__ == '__main__':
    storage = ButtonStorage()
    dev_btn = Button(domain='switch', name='Switch-1')
    storage.add_button(dev_btn)

    on_btn = Button(domain='switch', name='on', service='on', parent_id=dev_btn.id)
    off_btn = Button(domain='switch', name='off', service='off', parent_id=dev_btn.id)
    storage.add_many([on_btn, off_btn])

    child = storage.get_child(dev_btn.id)
    for btn in child:
        print(btn)
        btn.make_action()
