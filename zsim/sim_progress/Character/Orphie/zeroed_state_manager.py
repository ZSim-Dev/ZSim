from zsim.define import ORPHIE_REPORT
from zsim.sim_progress.Preload import SkillNode

from ..character import Character


class ZeroedState:
    """单个角色的准星聚焦状态"""

    def __init__(self, manager: "ZeroedStateManager", owner: Character):
        self.manager = manager
        self.orphie = self.manager.orphie  # 奥菲斯
        self.owner: Character = owner  # 拥有该状态的角色
        self.extend_max_duration: int = (
            self.manager.extend_max_duration
        )  # 最大可延长的持续时间，单位tick
        self.initial_duration: int = self.manager.initial_duration  # 初始持续时间，单位tick
        self.extend_tick: int = self.manager.extend_tick  # 每次延长的时间
        self.start_symbol: str = self.manager.start_symbol  # 触发准星聚焦状态的技能标签
        self._last_active_tick: int = 0  # 上一次激活的时间点，单位tick
        self._end_tick: int = 0  # 准星聚焦状态结束的时间点，单位tick
        self._tick_has_extended: int = 0  # 已经延长的时间，单位tick

    @property
    def last_active_tick(self) -> int:
        """上一次激活的时间点"""
        return self._last_active_tick

    @last_active_tick.setter
    def last_active_tick(self, tick: int) -> None:
        """更新上一次激活的时间点，同时更新结束时间点。"""
        assert tick >= self._last_active_tick, "last_active_tick 只能递增"
        self._last_active_tick = tick
        self._tick_has_extended = 0  # 清空已延长的时间
        self._end_tick = tick + self.initial_duration

    @property
    def is_active(self) -> bool:
        """当前是否处于准星聚焦状态"""
        sim_instance = self.orphie.sim_instance
        assert sim_instance is not None
        tick = sim_instance.tick
        return tick <= self._end_tick

    def extend_duration(self) -> None:
        """延长准星聚焦状态的持续时间"""
        assert self.is_active, (
            "当准星聚焦状态不活跃时，不应该调用 extend_duration 方法，请检查前置的 is_active 属性或update_myself 方法"
        )

        if self._tick_has_extended >= self.extend_max_duration:
            # 当本轮延长的时间已经达到上限时，无法继续延长
            return
        self._end_tick += self.extend_tick
        self._tick_has_extended += self.extend_tick

    def zeroed_active(self) -> None:
        """触发准星聚焦状态"""
        sim_instance = self.orphie.sim_instance
        assert sim_instance is not None
        tick = sim_instance.tick
        self.last_active_tick = tick

    def update_myself(self, skill_node: SkillNode) -> None:
        """更新自身状态，但不包括激活逻辑"""
        if not self.is_active:
            # 当自身不处于活跃状态时，直接返回即可
            return
        if skill_node.char_name != self.owner.NAME:
            # 只有当技能节点属于该角色时，才会触发延长效果
            return
        if not skill_node.is_after_shock_attack:
            # 过滤掉所有不是追加攻击的技能节点
            return
        self.extend_duration()
        if ORPHIE_REPORT:
            sim_instance = self.orphie.sim_instance
            assert sim_instance is not None
            sim_instance.schedule_data.change_process_state()
            print(
                f"【奥菲斯事件】检测到来自{self.owner.NAME}的追加攻击：{skill_node.skill.skill_text}，将准星聚焦状态延长至{self._end_tick}tick，当前已延长时间为{self._tick_has_extended}tick"
            )


class ZeroedStateManager:
    """奥菲斯的准星聚焦状态管理器"""

    def __init__(self, char: Character):
        from zsim.sim_progress.Character.Orphie import Orphie

        assert isinstance(char, Orphie)
        self.orphie = char
        self.extend_max_duration: int = 1200  # 最大可延长的持续时间，单位tick
        self.extend_tick: int = 240  # 每次延长的时间，单位tick
        self.initial_duration: int = (
            720 if self.orphie.cinema < 4 else 960
        )  # 初始持续时间，单位tick，在4画以上时变为16秒（960tick）
        self.zeroed_state_map: dict[int, ZeroedState] = {}  # key为角色id，value为ZeroedState实例
        self.start_symbol: str = "1301_E_EX_C"  # 触发准星聚焦状态的技能标签

    def update_whole_group(self, skill_node: SkillNode) -> None:
        """更新全队的准星聚焦状态"""
        if self.zeroed_state_map == {}:
            # 如果还没有初始化全队的准星聚焦状态，则进行初始化
            self.initialize_zeroed_states()
        if skill_node.skill_tag == self.start_symbol:
            for zeroed_state in self.zeroed_state_map.values():
                zeroed_state.zeroed_active()
            return
        for zeroed_state in self.zeroed_state_map.values():
            zeroed_state.update_myself(skill_node=skill_node)

    def initialize_zeroed_states(self):
        """初始化全队的准星聚焦状态"""
        sim_instance = self.orphie.sim_instance
        assert sim_instance is not None
        char_obj_list = sim_instance.char_data.char_obj_list
        for char in char_obj_list:
            self.zeroed_state_map[char.CID] = ZeroedState(manager=self, owner=char)
        else:
            if ORPHIE_REPORT:
                sim_instance.schedule_data.change_process_state()
                print(
                    f"【奥菲斯事件】初始化全队准星聚焦状态，已完成初始化的成员：{', '.join([char.NAME for char in char_obj_list])}"
                )
