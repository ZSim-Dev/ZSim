"""
具体事件处理器实现

该模块定义了各种类型事件的具体处理器类。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zsim.models.event_enums import ListenerBroadcastSignal as LBS
from zsim.sim_progress import Report
from zsim.sim_progress.anomaly_bar import AnomalyBar as AnB
from zsim.sim_progress.anomaly_bar.CopyAnomalyForOutput import (
    DirgeOfDestinyAnomaly as Abloom,
)
from zsim.sim_progress.anomaly_bar.CopyAnomalyForOutput import (
    Disorder,
    NewAnomaly,
    PolarityDisorder,
)
from zsim.sim_progress.Buff import ScheduleBuffSettle
from zsim.sim_progress.Character import Character
from zsim.sim_progress.data_struct import (
    ActionStack,
    PolarizedAssaultEvent,
    QuickAssistEvent,
    SchedulePreload,
    ScheduleRefreshData,
    SingleHit,
    StunForcedTerminationEvent,
)
from zsim.sim_progress.Load.LoadDamageEvent import (
    ProcessFreezLikeDots,
    ProcessHitUpdateDots,
)
from zsim.sim_progress.Load.loading_mission import LoadingMission
from zsim.sim_progress.Preload import SkillNode
from zsim.sim_progress.Update import update_anomaly

from ..CalAnomaly import CalAbloom, CalAnomaly, CalDisorder, CalPolarityDisorder
from ..Calculator import Calculator
from .base import BaseEventHandler
from .context import EventContext

if TYPE_CHECKING:
    from zsim.sim_progress.Enemy import Enemy
    from zsim.simulator.dataclasses import ScheduleData
    from zsim.simulator.simulator_class import Simulator


class SkillEventHandler(BaseEventHandler):
    """技能事件处理器"""

    def __init__(self):
        super().__init__("skill")

    def can_handle(self, event: Any) -> bool:
        return isinstance(event, SkillNode | LoadingMission)

    def handle(self, event: SkillNode | LoadingMission, context: EventContext) -> None:
        """处理技能事件"""
        # 验证输入
        self._validate_event(event, (SkillNode, LoadingMission))
        self._validate_context(context)

        data = self._get_context_data(context)
        tick = self._get_context_tick(context)
        enemy = self._get_context_enemy(context)
        dynamic_buff = self._get_context_dynamic_buff(context)
        exist_buff_dict = self._get_context_exist_buff_dict(context)
        action_stack = self._get_context_action_stack(context)
        sim_instance = self._get_context_sim_instance(context)

        # 检查是否到达执行时间
        execute_tick = self._get_execute_tick(event, context)
        if execute_tick is None or execute_tick > tick:
            return

        self._process_skill_event(
            event=event,
            data=data,
            tick=tick,
            enemy=enemy,
            dynamic_buff=dynamic_buff,
            exist_buff_dict=exist_buff_dict,
            action_stack=action_stack,
            sim_instance=sim_instance,
        )

    def _get_execute_tick(
        self, event: SkillNode | LoadingMission, context: EventContext
    ) -> int | None:
        """获取事件的执行tick"""
        if isinstance(event, SkillNode):
            return event.preload_tick
        elif isinstance(event, LoadingMission):
            return event.mission_node.preload_tick
        return None

    def _process_skill_event(
        self,
        event: SkillNode | LoadingMission,
        data: ScheduleData,
        tick: int,
        enemy: Enemy,
        dynamic_buff: dict,
        exist_buff_dict: dict,
        action_stack: ActionStack,
        sim_instance: Simulator,
    ) -> None:
        """处理技能事件的具体逻辑"""

        # 获取技能节点和命中次数
        skill_node, hit_count = self._extract_skill_info(event)

        # 查找角色对象
        char_obj = self._find_character(skill_node.skill.char_name, data.char_obj_list)

        # 计算伤害
        self._calculate_damage(skill_node, char_obj, enemy, dynamic_buff, hit_count, event, tick)

        # 更新异常条
        self._update_anomaly_bar_after_skill_event(
            skill_node, enemy, tick, data, dynamic_buff, sim_instance
        )

        # 处理buff结算
        self._settle_buffs(
            tick, exist_buff_dict, enemy, dynamic_buff, action_stack, skill_node, sim_instance
        )

        # 处理伤害更新
        self._update_damage_effects(tick, enemy, data, event)
        self._broadcast_skill_event_to_char(event=event, sim_instance=sim_instance)

    def _broadcast_skill_event_to_char(self, event: SkillNode | LoadingMission, sim_instance: Simulator):
        """广播技能事件到角色"""
        event_to_broadcast = event if isinstance(event, SkillNode) else event.mission_node
        for char_obj in sim_instance.char_data.char_obj_list:
            if hasattr(char_obj, "update_special_resource"):
                char_obj.update_special_resource(event_to_broadcast)

    def _extract_skill_info(self, event: SkillNode | LoadingMission) -> tuple[SkillNode, int]:
        """提取技能节点和命中次数信息

        Args:
            event: 技能事件对象

        Returns:
            tuple[SkillNode, int]: (技能节点, 命中次数)
        """
        if isinstance(event, LoadingMission):
            return event.mission_node, event.hitted_count
        else:
            return event, 0

    def _find_character(self, char_name: str, char_obj_list: list[Character]) -> Character:
        """查找角色对象"""
        for character in char_obj_list:
            if character.NAME == char_name:
                return character
        raise ValueError(f"角色 {char_name} 未找到")

    def _calculate_damage(
        self,
        skill_node: SkillNode,
        char_obj: Character,
        enemy: Enemy,
        dynamic_buff: dict,
        hit_count: int,
        event: SkillNode | LoadingMission,
        tick: int,
    ) -> None:
        """计算伤害"""
        calculator = Calculator(
            skill_node=skill_node,
            character_obj=char_obj,
            enemy_obj=enemy,
            dynamic_buff=dynamic_buff,
        )

        snapshot = calculator.cal_snapshot()
        stun = calculator.cal_stun()
        damage_expect = calculator.cal_dmg_expect()
        damage_crit = calculator.cal_dmg_crit()

        # 获取实际的active_generation值
        if isinstance(event, SkillNode):
            proactive = event.active_generation
        else:
            proactive = event.mission_node.active_generation

        hit_result = SingleHit(
            skill_tag=skill_node.skill_tag,
            snapshot=snapshot,
            stun=stun,
            dmg_expect=damage_expect,
            dmg_crit=damage_crit,
            hitted_count=hit_count,
            proactive=proactive,
        )

        hit_result.skill_node = skill_node

        if skill_node.skill.follow_by:
            hit_result.proactive = False

        if skill_node.hit_times == hit_count and skill_node.skill.heavy_attack:
            hit_result.heavy_hit = True

        enemy.hit_received(hit_result, tick)  # 使用实际的tick值

        Report.report_dmg_result(
            tick=tick,  # 使用实际的tick值
            element_type=skill_node.element_type,
            skill_tag=skill_node.skill_tag,
            dmg_expect=round(damage_expect, 2),
            dmg_crit=round(damage_crit, 2),
            stun=round(stun, 2),
            buildup=round(snapshot[1], 2),
            **enemy.dynamic.get_status(),
            UUID=skill_node.UUID if skill_node.UUID is not None else "",
            crit_rate=calculator.regular_multipliers.crit_rate,
            crit_dmg=calculator.regular_multipliers.crit_dmg,
        )

    def _update_anomaly_bar_after_skill_event(
        self,
        skill_node: SkillNode,
        enemy: Enemy,
        tick: int,
        data: ScheduleData,
        dynamic_buff: dict,
        sim_instance: Simulator,
    ) -> None:
        """
        在技能事件后更新异常条

        Args:
            skill_node: 技能节点
            enemy: 敌人对象
            tick: 当前时间刻
            data: 调度数据
            dynamic_buff: 动态buff
            sim_instance: 模拟器实例
        """
        # 复制原始 __init__.py 中的 update_anomaly_bar_after_skill_event 逻辑
        _node = skill_node

        # 判断当前Tick的技能是否能够更新异常
        should_update = False
        if not _node.skill.anomaly_update_rule:
            if _node.loading_mission is None:
                _loading_mission = LoadingMission(_node)
                _loading_mission.mission_start(timenow=sim_instance.tick)
                _node.loading_mission = _loading_mission
            last_hit = _node.loading_mission.get_last_hit()
            if last_hit is not None and tick - 1 < last_hit <= tick:
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
                enemy,
                tick,
                data.event_list,
                data.char_obj_list,
                skill_node=_node,
                dynamic_buff_dict=dynamic_buff,
                sim_instance=sim_instance,
            )

    def _settle_buffs(
        self,
        tick: int,
        exist_buff_dict: dict,
        enemy: Enemy,
        dynamic_buff: dict,
        action_stack: ActionStack,
        skill_node: SkillNode,
        sim_instance: Simulator,
    ) -> None:
        """处理buff结算

        Args:
            tick: 当前tick
            exist_buff_dict: 已存在的buff字典
            enemy: 敌人对象
            dynamic_buff: 动态buff字典
            action_stack: 动作栈
            skill_node: 技能节点
            sim_instance: 模拟器实例
        """
        ScheduleBuffSettle(
            tick,
            exist_buff_dict,
            enemy,
            dynamic_buff,
            action_stack,
            skill_node=skill_node,
            sim_instance=sim_instance,
        )

    def _update_damage_effects(
        self,
        tick: int,
        enemy: Enemy,
        data: ScheduleData,
        event: SkillNode | LoadingMission,
    ) -> None:
        """处理伤害更新效果

        Args:
            tick: 当前tick
            enemy: 敌人对象
            data: 调度数据
            event: 技能事件对象
        """
        ProcessHitUpdateDots(tick, enemy.dynamic.dynamic_dot_list, data.event_list)
        ProcessFreezLikeDots(timetick=tick, enemy=enemy, event_list=data.event_list, event=event)


class AnomalyEventHandler(BaseEventHandler):
    """异常事件处理器"""

    def __init__(self):
        super().__init__("anomaly")

    def can_handle(self, event: Any) -> bool:
        return type(event) is AnB or type(event) is NewAnomaly

    def handle(self, event: AnB | NewAnomaly, context: EventContext) -> None:
        """处理异常事件（包括 NewAnomaly）"""
        # 验证输入
        self._validate_event(event, AnB)
        self._validate_context(context)

        enemy = self._get_context_enemy(context)
        dynamic_buff = self._get_context_dynamic_buff(context)
        exist_buff_dict = self._get_context_exist_buff_dict(context)
        action_stack = self._get_context_action_stack(context)
        sim_instance = self._get_context_sim_instance(context)
        tick = self._get_context_tick(context)

        # 计算异常伤害
        calculator = CalAnomaly(
            anomaly_obj=event,
            enemy_obj=enemy,
            dynamic_buff=dynamic_buff,
            sim_instance=sim_instance,
        )

        damage_anomaly = calculator.cal_anomaly_dmg()

        Report.report_dmg_result(
            tick=tick,
            skill_tag=event.rename_tag if event.rename else None,
            element_type=event.element_type,
            dmg_expect=round(damage_anomaly, 2),
            is_anomaly=True,
            dmg_crit=round(damage_anomaly, 2),
            stun=0,
            buildup=0,
            **enemy.dynamic.get_status(),
            UUID=event.UUID if event.UUID is not None else "",
        )

        # 处理buff结算
        ScheduleBuffSettle(
            tick,
            exist_buff_dict,
            enemy,
            dynamic_buff,
            action_stack,
            anomaly_bar=event,
            sim_instance=sim_instance,
        )


class DisorderEventHandler(BaseEventHandler):
    """紊乱事件处理器"""

    def __init__(self):
        super().__init__("disorder")

    def can_handle(self, event: Any) -> bool:
        return type(event) is Disorder

    def handle(self, event: Disorder, context: EventContext) -> None:
        """处理紊乱事件"""
        enemy = self._get_context_enemy(context)
        dynamic_buff = self._get_context_dynamic_buff(context)
        sim_instance = self._get_context_sim_instance(context)
        tick = self._get_context_tick(context)

        # 广播紊乱事件
        sim_instance.listener_manager.broadcast_event(event=event, signal=LBS.DISORDER_SETTLED)

        # 计算紊乱伤害
        calculator = CalDisorder(
            disorder_obj=event,
            enemy_obj=enemy,
            dynamic_buff=dynamic_buff,
            sim_instance=sim_instance,
        )

        damage_disorder = calculator.cal_anomaly_dmg()
        stun = calculator.cal_disorder_stun()

        # 更新敌人眩晕值
        enemy.update_stun(stun)

        Report.report_dmg_result(
            tick=tick,
            element_type=event.element_type,
            dmg_expect=round(damage_disorder, 2),
            dmg_crit=round(damage_disorder, 2),
            is_anomaly=True,
            is_disorder=True,
            stun=round(stun, 2),
            buildup=0,
            **enemy.dynamic.get_status(),
            UUID=event.UUID if event.UUID is not None else "",
        )


class PolarityDisorderEventHandler(BaseEventHandler):
    """极性紊乱事件处理器"""

    def __init__(self):
        super().__init__("polarity_disorder")

    def can_handle(self, event: Any) -> bool:
        # 使用 type() 而不是 isinstance() 来避免子类误匹配
        return type(event) is PolarityDisorder

    def handle(self, event: PolarityDisorder, context: EventContext) -> None:
        """处理极性紊乱事件"""
        enemy = self._get_context_enemy(context)
        dynamic_buff = self._get_context_dynamic_buff(context)
        sim_instance = self._get_context_sim_instance(context)
        tick = self._get_context_tick(context)

        # 广播极性紊乱事件
        sim_instance.listener_manager.broadcast_event(event=event, signal=LBS.DISORDER_SETTLED)

        # 计算极性紊乱伤害
        calculator = CalPolarityDisorder(
            disorder_obj=event,
            enemy_obj=enemy,
            dynamic_buff=dynamic_buff,
            sim_instance=sim_instance,
        )

        damage_disorder = calculator.cal_anomaly_dmg()

        Report.report_dmg_result(
            tick=tick,
            element_type=event.element_type,
            skill_tag="极性紊乱",
            dmg_expect=round(damage_disorder, 2),
            dmg_crit=round(damage_disorder, 2),
            is_anomaly=True,
            is_disorder=True,
            stun=0,
            buildup=0,
            **enemy.dynamic.get_status(),
            UUID=event.UUID if event.UUID is not None else "",
        )


class AbloomEventHandler(BaseEventHandler):
    """薇薇安异放事件处理器"""

    def __init__(self):
        super().__init__("abloom")

    def can_handle(self, event: Any) -> bool:
        return type(event) is Abloom

    def handle(self, event: Abloom, context: EventContext) -> None:
        """处理薇薇安异放事件"""
        enemy = self._get_context_enemy(context)
        dynamic_buff = self._get_context_dynamic_buff(context)
        sim_instance = self._get_context_sim_instance(context)
        tick = self._get_context_tick(context)

        # 计算异放伤害
        calculator = CalAbloom(
            abloom_obj=event,
            enemy_obj=enemy,
            dynamic_buff=dynamic_buff,
            sim_instance=sim_instance,
        )

        damage_anomaly = calculator.cal_anomaly_dmg()

        Report.report_dmg_result(
            tick=tick,
            element_type=event.element_type,
            skill_tag="异放",
            dmg_expect=round(damage_anomaly, 2),
            is_anomaly=True,
            dmg_crit=round(damage_anomaly, 2),
            stun=0,
            buildup=0,
            **enemy.dynamic.get_status(),
            UUID=event.UUID if event.UUID is not None else "",
        )


class RefreshEventHandler(BaseEventHandler):
    """数据刷新事件处理器"""

    def __init__(self):
        super().__init__("refresh")

    def can_handle(self, event: Any) -> bool:
        return isinstance(event, ScheduleRefreshData)

    def handle(self, event: ScheduleRefreshData, context: EventContext) -> None:
        """处理数据刷新事件"""
        try:
            data = self._get_context_data(context)

            # 创建角色映射
            char_mapping = {character.NAME: character for character in data.char_obj_list}

            # 更新能量
            for target in event.sp_target:
                if target != "":
                    if target not in char_mapping:
                        raise KeyError(f"目标角色 {target} 未找到")
                    char_mapping[target].update_sp(event.sp_value)

            # 更新喧响
            for target in event.decibel_target:
                if target != "":
                    if target not in char_mapping:
                        raise KeyError(f"目标角色 {target} 未找到")
                    char_mapping[target].update_decibel(event.decibel_value)

        except Exception as e:
            self._handle_error(e, "数据刷新事件处理", event)


class QuickAssistEventHandler(BaseEventHandler):
    """快速支援事件处理器"""

    def __init__(self):
        super().__init__("quick_assist")

    def can_handle(self, event: Any) -> bool:
        return isinstance(event, QuickAssistEvent)

    def handle(self, event: QuickAssistEvent, context: EventContext) -> None:
        """处理快速支援事件"""
        data = self._get_context_data(context)
        tick = self._get_context_tick(context)

        # 检查是否到达执行时间
        if tick < event.execute_tick:
            # 时间未到，将事件重新加入列表
            data.event_list.append(event)
            return

        # 执行事件
        event.execute_update(tick)


class PreloadEventHandler(BaseEventHandler):
    """预加载事件处理器"""

    def __init__(self):
        super().__init__("preload")

    def can_handle(self, event: Any) -> bool:
        return isinstance(event, SchedulePreload)

    def handle(self, event: SchedulePreload, context: EventContext) -> None:
        """处理预加载事件"""
        data = self._get_context_data(context)
        tick = self._get_context_tick(context)

        # 检查是否到达执行时间
        if tick < event.execute_tick:
            # 时间未到，将事件重新加入列表
            data.event_list.append(event)
            return

        # 执行事件
        event.execute_myself()


class StunForcedTerminationEventHandler(BaseEventHandler):
    """眩晕强制终止事件处理器"""

    def __init__(self):
        super().__init__("stun_forced_termination")

    def can_handle(self, event: Any) -> bool:
        return type(event) is StunForcedTerminationEvent

    def handle(self, event: StunForcedTerminationEvent, context: EventContext) -> None:
        """处理眩晕强制终止事件"""
        data = self._get_context_data(context)
        tick = self._get_context_tick(context)

        # 检查是否到达执行时间
        if tick < event.execute_tick:
            # 时间未到，将事件重新加入列表
            data.event_list.append(event)
            return

        # 执行事件
        event.execute_myself()


class PolarizedAssaultEventHandler(BaseEventHandler):
    """极性强击事件处理器"""

    def __init__(self):
        super().__init__("polarized_assault")

    def can_handle(self, event: Any) -> bool:
        return type(event) is PolarizedAssaultEvent

    def handle(self, event: PolarizedAssaultEvent, context: EventContext) -> None:
        """处理极性强击事件"""
        data = self._get_context_data(context)
        tick = self._get_context_tick(context)

        # 检查是否到达执行时间
        if tick < event.execute_tick:
            # 时间未到，将事件重新加入列表
            data.event_list.append(event)
            return

        # 执行事件
        event.execute()


def register_all_handlers() -> None:
    """注册所有事件处理器"""
    from . import event_handler_factory

    handlers = [
        SkillEventHandler(),
        AnomalyEventHandler(),
        DisorderEventHandler(),
        PolarityDisorderEventHandler(),
        AbloomEventHandler(),
        RefreshEventHandler(),
        QuickAssistEventHandler(),
        PreloadEventHandler(),
        StunForcedTerminationEventHandler(),
        PolarizedAssaultEventHandler(),
    ]

    for handler in handlers:
        event_handler_factory.register_handler(handler)
