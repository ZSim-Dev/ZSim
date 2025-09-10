from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zsim.sim_progress import Buff
from zsim.sim_progress.Character import Character
from zsim.sim_progress.data_struct import (
    ActionStack,
    PolarizedAssaultEvent,
    QuickAssistEvent,
    SchedulePreload,
    SPUpdateData,
)
from zsim.sim_progress.Load.loading_mission import LoadingMission
from zsim.sim_progress.Preload import SkillNode
from zsim.sim_progress.Update import update_anomaly

if TYPE_CHECKING:
    from zsim.simulator.dataclasses import ScheduleData
    from zsim.simulator.simulator_class import Simulator


class ScConditionData:
    """
    用于记录在本tick可能的判断 buff 数据，以方便后续计算伤害
    """

    def __init__(self):
        self.buff_list: list = []
        self.when_crit: bool = False


class ScheduledEvent:
    """
    计划事件方法类

    主逻辑链 self.event_start()：
    1、读取计划事件列表，将其中所有的buff示例排到列表最靠前的位置。self.sort_events()
    2、遍历事件列表，从开始到结束，将每一个事件派发到分支逻辑链内进行处理
    """

    def __init__(
        self,
        dynamic_buff: dict,
        data,
        tick: int,
        exist_buff_dict: dict,
        action_stack: ActionStack,
        *,
        loading_buff: dict | None = None,
        sim_instance: Simulator,
    ):
        self.data: "ScheduleData" = data
        self.data.dynamic_buff = dynamic_buff
        self.data.processed_times = 0
        # self.judge_required_info_dict = data.judge_required_info_dict
        self.action_stack = action_stack

        if loading_buff is None:
            loading_buff = {}
        elif not isinstance(loading_buff, dict):
            raise ValueError(f"loading_buff参数必须为字典，但你输入了{loading_buff}")

        if not isinstance(tick, int):
            raise ValueError(f"tick参数必须为整数，但你输入了{tick}")

        # 更新Data
        self.tick = tick
        self.data.loading_buff = loading_buff
        self.exist_buff_dict = exist_buff_dict
        self.enemy = self.data.enemy

        self.execute_tick_key_map = {
            SkillNode: "preload_tick",
            QuickAssistEvent: "execute_tick",
            SchedulePreload: "execute_tick",
            PolarizedAssaultEvent: "execute_tick",
        }
        self.sim_instance: Simulator = sim_instance
        # 确保事件处理器已注册
        self._ensure_handlers_registered()

    def _ensure_handlers_registered(self) -> None:
        """确保所有事件处理器已注册"""
        try:
            from .concrete_handlers import register_all_handlers
            from .event_handlers import event_handler_factory

            if not event_handler_factory.list_handlers():
                register_all_handlers()
                print(
                    f"DEBUG: 事件处理器注册完成，可用的处理器: {event_handler_factory.list_handlers()}"
                )
            else:
                print(
                    f"DEBUG: 事件处理器已经注册，可用的处理器: {event_handler_factory.list_handlers()}"
                )
        except ImportError as e:
            raise RuntimeError(f"事件处理器导入失败: {e}") from e

    def _create_event_context(self) -> dict[str, Any]:
        """
        创建事件处理上下文

        Returns:
            dict[str, Any]: 包含事件处理所需数据的上下文字典
        """
        return {
            "data": self.data,
            "tick": self.tick,
            "enemy": self.enemy,
            "dynamic_buff": self.data.dynamic_buff,
            "exist_buff_dict": self.exist_buff_dict,
            "action_stack": self.action_stack,
            "sim_instance": self.sim_instance,
        }

    def event_start(self):
        """Schedule主逻辑"""
        # 更新角色面板
        for char in self.data.char_obj_list:
            char: Character
            sp_update_data = SPUpdateData(char_obj=char, dynamic_buff=self.data.dynamic_buff)
            char.update_sp_and_decibel(sp_update_data)
            if hasattr(char, "refresh_myself"):
                char.refresh_myself()
        self.process_event()

    def process_event(self):
        """
        处理当前所有事件

        使用事件处理器模式来处理各种类型的事件，替代原有的大型if-elif链。
        提高代码的可读性和可维护性。
        """
        if not self.data.event_list:
            return

        # 先处理优先级高的buff
        self.solve_buff()

        # 筛选出可处理的事件，并按照优先级排序
        processable_events = self.select_processable_event()

        # 使用事件处理器处理事件
        for event in processable_events:
            try:
                self._process_single_event(event)
                # 事件处理完毕，从列表中移除
                self.data.event_list.remove(event)
                self.data.processed_times += 1
            except Exception as e:
                raise RuntimeError(f"处理事件 {type(event)} 时发生错误: {e}") from e

        # 如果计算过程中又有新的事件生成，则继续循环
        if self.data.event_list and not self.check_all_event():
            self.process_event()

    def _process_single_event(self, event: Any) -> None:
        """
        处理单个事件

        Args:
            event: 待处理的事件对象

        Raises:
            NotImplementedError: 当事件类型不被支持时
            RuntimeError: 当事件处理器无法找到时
        """
        try:
            # 特殊处理Buff事件
            from zsim.sim_progress import Buff

            if isinstance(event, Buff.Buff):
                raise NotImplementedError(f"{type(event)}，目前不应存在于 event_list")

            # 事件处理上下文
            context = self._create_event_context()

            try:
                from .event_handlers import event_handler_factory
            except ImportError as e:
                raise RuntimeError(f"事件处理器工厂导入失败: {e}") from e

            # 获取事件处理器
            handler = event_handler_factory.get_handler(event)
            if handler is None:
                print(f"DEBUG: 可用的事件处理器: {event_handler_factory.list_handlers()}")
                print(f"DEBUG: 事件类型: {type(event)}")
                raise RuntimeError(f"无法找到适合处理事件类型 {type(event)} 的处理器")

            # 处理事件
            handler.handle(event, context)
        except Exception as e:
            # 增强错误信息
            error_msg = f"处理事件 {type(event).__name__} 时发生错误: {e}"
            # 记录原始异常信息
            import logging

            logging.error(error_msg, exc_info=True)
            # 重新抛出异常，保持原始类型
            if isinstance(e, (RuntimeError, NotImplementedError)):
                raise
            else:
                raise RuntimeError(error_msg) from e

    def check_all_event(self):
        """检查所有残留事件是否到期，只要有一个残留事件已经到期，直接返回False，激活递归。"""
        for event in self.data.event_list:
            # 获取事件类型对应的tick属性名
            execute_tick = self.get_execute_tick(event)
            if execute_tick is None:
                return False
            if execute_tick > self.tick:  # 严格大于当前tick才视为未到期
                continue
            else:
                return False
        return True

    def get_execute_tick(self, event) -> int | None:
        """获取事件的执行tick，获取不到则返回None"""
        tick_attr = self.execute_tick_key_map.get(type(event), None)
        if tick_attr is None:
            """获取不到属性时，说明该event并不具备计划事件的需求，所以这种事件是必须在当前tick被清空的，直接返回None"""
            return None
        execute_tick = getattr(event, tick_attr, None)
        if execute_tick is None:
            raise AttributeError(f"{type(event)} 没有属性 {tick_attr}")
        return execute_tick

    def update_anomaly_bar_after_skill_event(self, event):
        """在Schedule阶段，处理完一个SkillEvent后，都要进行一次异常条更新。"""
        """
        将异常值更新移动到Schedule阶段的主要原因：原有的Buff更新、异常/紊乱结算的顺序不合理；
        原有顺序：
        Preload -> Load -> update_anomaly() -> Buff(第一轮) ->  Schedule -> Buff(第二轮)
        现有顺序：
        Preload -> Load -> Buff(第一轮) ->  Schedule -> update_anomaly() -> Buff(第二轮)
        
        由于update_anomaly()函数是根据现有积蓄值来判断是否触发属性异常的，
        所以在运行过程中，只有先把积蓄值打满的下一次update_anomaly()才会触发属性异常，
        无论是哪种结构，enemy的receive_hit()函数都会在Schedule阶段执行，
        故任何早于Schedule阶段的update_anomaly都只能更新到上个tick的属性异常，
        所以，原有结构中，第Ntick打满的异常条，会在第N+1 tick被激活，
        
        一般情况下，这种迟滞1tick的激活行为不会对模拟的结果造成影响，
        (长难句警告！！)--但若是某个Buff事件的激活 依赖于发生在 技能last_hit标签处的属性异常更新--
        那么在老的结构下，事件的更新顺序为
            --(第N Tick)-- 
                -> update_anomaly(此时的异常条还没打满[来自于上个tick]所以第Ntick的运行无结果)
                -> Buff事件触发器检测（异常条更新状态没有改变，所以触发器不触发） 
                -> Schedule，异常条满，
            --(第N+1 Tick)--
                -> update_anomaly(异常条满，更新异常)
                -> Buff事件触发器检测（已经错过了触发窗口，所以触发器不触发）
            
        而在新的结构下，事件更新顺序为：
            --(第N Tick)-- 
                -> Schedule，异常条满，
                -> update_anomaly(异常条满，更新异常)
                -> Buff事件触发器检测（将该Buff改为Schedule处理类型）
        
        上述结构的改变就能够彻底规避来自于结构的触发误差——来自柳极性紊乱触发器的启发
        """
        if isinstance(event, SkillNode):
            _node = event
        elif isinstance(event, LoadingMission):
            _node = event.mission_node
        else:
            raise TypeError("无法解析的事件类型")
        """接下来要通过技能的异常更新特性，判断当前Tick的技能是否能够更新异常
        由于调用函数的位置是ScheduleEvent，所以一定是Hit事件发生时，
        所以，直接调用loading_mission.hitted_count数量就可以获得当前正在被结算的Hit次数。"""
        should_update = False
        if not _node.skill.anomaly_update_rule:
            if _node.loading_mission is None:
                _loading_mission = LoadingMission(_node)
                _loading_mission.mission_start(timenow=self.sim_instance.tick)
                _node.loading_mission = _loading_mission
            last_hit = _node.loading_mission.get_last_hit()
            if last_hit is not None and self.tick - 1 < last_hit <= self.tick:
                should_update = True
        else:
            if _node.skill.anomaly_update_rule == -1:
                should_update = True
            else:
                if (
                    _node.loading_mission is not None
                    and _node.skill.anomaly_update_rule is not None
                    and (
                        isinstance(_node.skill.anomaly_update_rule, list)
                        and _node.loading_mission.hitted_count in _node.skill.anomaly_update_rule
                        or isinstance(_node.skill.anomaly_update_rule, int)
                        and _node.loading_mission.hitted_count == _node.skill.anomaly_update_rule
                    )
                ):
                    should_update = True
        if should_update:
            update_anomaly(
                _node.element_type,
                self.enemy,
                self.tick,
                self.data.event_list,
                self.data.char_obj_list,
                skill_node=_node,
                dynamic_buff_dict=self.data.dynamic_buff,
                sim_instance=self.sim_instance,
            )

    def solve_buff(self) -> None:
        """提前处理Buff实例"""
        # Buff.buff_add(
        #     self.tick, self.data.loading_buff, self.data.dynamic_buff, self.data.enemy
        # )
        buff_events = []
        other_events = []
        for event in self.data.event_list[:]:
            if isinstance(event, Buff.Buff):
                buff_events.append(event)
            else:
                other_events.append(event)
        self.data.event_list = buff_events + other_events

    def select_processable_event(self):
        """筛选当前可执行的事件，并且按照优先级排序，获取不到优先级的默认为0，"""
        _output_event_list = []
        for _event in self.data.event_list:
            execute_tick = self.get_execute_tick(_event)
            if execute_tick is None or execute_tick <= self.tick:
                """说明事件不存在execute_tick或已到期，需要被立刻执行。"""
                schedule_priority = getattr(_event, "schedule_priority", 0)
                # 使用bisect模块进行高效插入
                import bisect

                priorities = [getattr(e, "schedule_priority", 0) for e in _output_event_list]
                insert_pos = bisect.bisect_right(priorities, schedule_priority)
                _output_event_list.insert(insert_pos, _event)
        return _output_event_list


if __name__ == "__main__":
    pass
