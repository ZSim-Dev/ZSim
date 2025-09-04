from math import floor
from typing import TYPE_CHECKING
from zsim.define import ALICE_REPORT
from .character import Character
from .utils.filters import _skill_node_filter

if TYPE_CHECKING:
    from zsim.sim_progress.Preload import SkillNode
    from zsim.simulator.simulator_class import Simulator


class Alice(Character):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.blade_etiquette: float = 300.0  # 剑仪
        self.max_blade_etiquette: float = 300.0  # 最大剑仪值
        self.victory_state_update_tick: int = 0  # 六画的决胜状态的更新时间
        self.victory_state_duration: int = 1800  # 决胜状态持续时间
        self.victory_state_activation_origin: list[str] = ["1401_SNA_3", "1401_Q"]  # 决胜状态激活源
        self.victory_state_attack_counter: int = 0  # 六画的决胜状态的剩余攻击次数
        self.victory_state_max_attack_count: int = 6  # 六画的决胜状态的最大攻击次数
        self.cinema_6_additional_attack_skill_tag: str = "1401_Cinema_6"  # 6画额外攻击的技能tag
        self._na_enhancement_state: bool = False  # 强化平A可用状态
        self.decibel = 1000.0 if self.cinema < 2 else 2000.0         # 爱丽丝喧响值

    @property
    def na_enhancement_state(self) -> bool:
        """强化平A是否可用"""
        return self._na_enhancement_state

    @na_enhancement_state.setter
    def na_enhancement_state(self, value: bool) -> None:
        """强化平A状态的赋值函数"""
        if not self._na_enhancement_state and not value:
            raise ValueError(
                "【爱丽丝时间警告】企图将强化平A状态从False切换到False，这意味着Preload在强化平A不可用的情况下放行了强化A5"
            )
        self._na_enhancement_state = value

    @property
    def victory_state(self) -> bool:
        """决胜状态是否处于激活状态"""
        from zsim.simulator.simulator_class import Simulator
        assert isinstance(self.sim_instance, Simulator), "角色未正确初始化，请检查函数"
        # 攻击次数尚未耗尽，或是时间为0tick(未发生过更新)，此时的决胜状态都判定为False
        if self.victory_state_update_tick == 0 or self.victory_state_attack_counter == 0:
            return False
        else:
            # 层数没耗尽时，才检查时间条件
            return (
                self.sim_instance.tick - self.victory_state_update_tick
                < self.victory_state_duration
            )

    @property
    def blade_etquitte_bar(self) -> int:
        # 剑仪条格子数（向下取整）
        return floor(self.blade_etiquette / 100)

    def reset_myself(self):
        # 重置能量、喧响值
        self.sp: float = 40.0
        self.decibel: float = 1000.0 if self.cinema < 2 else 2000.0
        # 重置动态属性
        self.dynamic.reset()

    def special_resources(self, *args, **kwargs) -> None:
        """爱丽丝的特殊资源模块"""
        from zsim.simulator.simulator_class import Simulator
        assert isinstance(self.sim_instance, Simulator), "角色未正确初始化，请检查函数"
        # 输入类型检查
        skill_nodes: list[SkillNode] = _skill_node_filter(*args, **kwargs)
        for node in skill_nodes:
            if node.char_name == self.NAME:
                # 6画情况下，优先更新决胜状态的相关参数
                if self.cinema == 6:
                    if node.skill_tag in self.victory_state_activation_origin:
                        self.victory_state_update_tick = self.sim_instance.tick
                        self.victory_state_attack_counter = self.victory_state_max_attack_count
                        if ALICE_REPORT:
                            self.sim_instance.schedule_data.change_process_state()
                            print(
                                f"【爱丽丝事件】【6画】检测到爱丽丝释放了{node.skill.skill_text}，激活了决胜状态"
                            )
                # 更新强化A5状态
                if node.skill_tag == "1401_NA_5_PLUS":
                    self.na_enhancement_state = False
                    if ALICE_REPORT:
                        self.sim_instance.schedule_data.change_process_state()
                        print(
                            f"【爱丽丝事件】爱丽丝成功释放了一次强化A5：{node.skill.skill_text}，强化A5状态关闭"
                        )
                # 更新剑仪值
                self.update_blade_etiquette(update_obj=node)
            else:
                # 队友的skill_node判断；
                pass

    def update_blade_etiquette(self, update_obj: "SkillNode | float | int") -> None:
        # 更新剑仪值的函数
        from zsim.simulator.simulator_class import Simulator
        from zsim.sim_progress.Preload import SkillNode
        assert isinstance(self.sim_instance, Simulator), "角色未正确初始化，请检查函数"
        if update_obj is None:
            raise ValueError("【剑仪值更新警告】在调用剑仪值更新函数时，必须传入update_obj参数")
        if isinstance(update_obj, SkillNode):
            if update_obj.labels is None:
                raise ValueError(
                    f"【剑仪值更新警告】传入的{update_obj.skill_tag}没有初始化label参数，请检查数据库"
                )
            if "blade_etiquette" not in update_obj.labels:
                print(
                    f"【剑仪值更新警告】技能{update_obj.skill_tag}的label中不包含剑仪值，请检查数据库"
                )
                return
            blade_etiquette = update_obj.labels.get("blade_etiquette", 0)
        elif isinstance(update_obj, float | int):
            blade_etiquette = update_obj
        assert isinstance(blade_etiquette, float | int), "剑仪值更新函数传入的参数类型错误"
        self.blade_etiquette = min(self.max_blade_etiquette, self.blade_etiquette + blade_etiquette)
        if ALICE_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print(
                f"【爱丽丝事件】爱丽丝 {'恢复' if blade_etiquette >= 0 else '消耗'} 了 {abs(blade_etiquette):.2f} 点剑仪值，当前剑仪值为 {self.blade_etiquette:.2f}"
            )

    def POST_INIT_DATA(self, sim_insatnce: "Simulator"):
        """初始化爱丽丝的监听器组"""
        listener_manager = sim_insatnce.listener_manager
        # 组队被动激活时，初始化紊乱回剑仪值的监听器
        if self.additional_abililty_active:
            listener_manager.listener_factory(
                listener_owner=self, initiate_signal="Alice_1", sim_instance=sim_insatnce
            )

        # 初始化本体固有监听器（紊乱倍率、物理积蓄效率）
        for listener_id in ["Alice_2", "Alice_3", "Alice_4", "Alice_5"]:
            listener_manager.listener_factory(
                listener_owner=self, initiate_signal=listener_id, sim_instance=sim_insatnce
            )

        # 1画激活时，初始化1画监听器（减防Buff）
        if self.cinema >= 1:
            listener_manager.listener_factory(
                listener_owner=self, initiate_signal="Alice_Cinema_1_A", sim_instance=sim_insatnce
            )
            listener_manager.listener_factory(
                listener_owner=self, initiate_signal="Alice_Cinema_1_B", sim_instance=sim_insatnce
            )

        # 2画激活时，初始化2画监听器（紊乱伤害提升）
        if self.cinema >= 2:
            listener_manager.listener_factory(
                listener_owner=self, initiate_signal="Alice_Cinema_2_A", sim_instance=sim_insatnce
            )

    def spawn_extra_attack(self) -> None:
        """6画额外攻击的接口，向Preload添加一次额外攻击事件，同时扣除一次使用次数"""
        assert self.victory_state, "6画额外攻击接口调用时，决胜状态未激活，请检查前置判断逻辑"
        assert self.sim_instance is not None, "角色未正确初始化，请检查函数"
        from zsim.sim_progress.data_struct.SchedulePreload import schedule_preload_event_factory

        preload_tick_list = [self.sim_instance.tick]
        skill_tag_list = [self.cinema_6_additional_attack_skill_tag]
        preload_data = self.sim_instance.preload.preload_data

        schedule_preload_event_factory(
            preload_tick_list=preload_tick_list,
            skill_tag_list=skill_tag_list,
            preload_data=preload_data,
            sim_instance=self.sim_instance,
        )
        if ALICE_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print(
                f"【爱丽丝事件】【6画】队友攻击命中，爱丽丝触发额外攻击！当前剩余额外攻击次数：{self.victory_state_attack_counter}"
            )
        # 保险起见，计数器在最后更新
        self.victory_state_attack_counter -= 1

    def personal_action_replace_strategy(self, action: str):
        """爱丽丝的个人动作替换策略，其核心是：尝试把NA_5替换为它的强化版本"""
        if action == "1401_NA_5":
            if self.na_enhancement_state:
                return "1401_NA_5_PLUS"
        return action

    def get_resources(self, *args, **kwargs) -> tuple[str, int]:
        return "剑仪格", self.blade_etquitte_bar

    def get_special_stats(self, *args, **kwargs) -> dict[str | None, object | None]:
        return {"剑仪值": self.blade_etiquette, "强化A5状态": self.na_enhancement_state}
