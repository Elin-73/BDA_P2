from controllers import ENTITY_TYPES
from menu_common import EntityMenu


class ConsoleMenu(EntityMenu):
    def __init__(self, operations, role="boss", advisor_id=None):
        super().__init__(operations, ENTITY_TYPES[0], role, advisor_id)
