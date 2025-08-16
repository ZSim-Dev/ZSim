from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...Character.character import Character
    from ...Enemy import Enemy
    from ..buff_class import Buff


class BuffRecordBaseClass:
    def __init__(self):
        self.char: "Character | None" = None
        self.sub_exist_buff_dict: dict[str, "Buff"] | None = None
        self.dynamic_buff_list: dict[str, list] | None = None
        self.enemy: "Enemy | None" = None
        self.trans_ratio: float = 1.6  # 转化比率
