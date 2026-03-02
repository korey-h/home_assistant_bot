from typing import List

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