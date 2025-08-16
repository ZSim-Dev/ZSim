from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...Character.character import Character
    from ...Character.Alice import Alice
    from ...Character.Yixuan import Yixuan
    from ...Enemy import Enemy
    from ..buff_class import Buff
    from ...data_struct.ActionStack import ActionStack
    from ...Preload.PreloadDataClass import PreloadData


class BuffRecordBaseClass:
    def __init__(self):
        self.char: "Character | None | Alice | Yixuan" = None
        self.sub_exist_buff_dict: dict[str, "Buff"] | None = None
        self.dynamic_buff_list: dict[str, list] | None = None
        self.enemy: "Enemy | None" = None
        self.equipper: "str | None" = None
        self.action_stack: "ActionStack | None" = None
        self.event_list: list | None = None
        self.preload_data: "PreloadData | None" = None
        self.char_obj_list: "list[Character] | None" = None
        self.na_skill_level: "int | None" = None
        self.trans_ratio: float = 0
