from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from zsim.sim_progress.data_struct import (
        ActionStack,
    )
    from zsim.sim_progress.Enemy import Enemy
    from zsim.simulator.dataclasses import ScheduleData
    from zsim.simulator.simulator_class import Simulator


class EventHandlerABC(ABC):
    """事件处理器抽象基类"""

    @abstractmethod
    def can_handle(self, event: Any) -> bool:
        """
        判断是否可以处理指定类型的事件

        Args:
            event: 待处理的事件对象

        Returns:
            bool: 如果可以处理该类型事件则返回True，否则返回False
        """
        pass

    @abstractmethod
    def handle(self, event: Any, context: dict[str, Any]) -> None:
        """
        处理事件

        Args:
            event: 待处理的事件对象
            context: 事件处理上下文，包含所需的数据和环境信息

        Raises:
            NotImplementedError: 如果子类未实现此方法
        """
        pass

    @property
    @abstractmethod
    def event_type(self) -> str:
        """
        返回处理器支持的事件类型名称

        Returns:
            str: 事件类型名称
        """
        pass


class BaseEventHandler(EventHandlerABC):
    """基础事件处理器，提供通用功能"""

    def __init__(self, event_type: str):
        self._event_type = event_type

    @property
    def event_type(self) -> str:
        return self._event_type

    def _get_context_data(self, context: dict[str, Any]) -> ScheduleData:
        """从上下文中获取ScheduleData"""
        return context["data"]

    def _get_context_tick(self, context: dict[str, Any]) -> int:
        """从上下文中获取当前tick"""
        return context["tick"]

    def _get_context_enemy(self, context: dict[str, Any]) -> Enemy:
        """从上下文中获取敌人对象"""
        return context["enemy"]

    def _get_context_dynamic_buff(self, context: dict[str, Any]) -> dict:
        """从上下文中获取动态buff"""
        return context["dynamic_buff"]

    def _get_context_exist_buff_dict(self, context: dict[str, Any]) -> dict:
        """从上下文中获取已存在buff字典"""
        return context["exist_buff_dict"]

    def _get_context_action_stack(self, context: dict[str, Any]) -> ActionStack:
        """从上下文中获取动作栈"""
        return context["action_stack"]

    def _get_context_sim_instance(self, context: dict[str, Any]) -> Simulator:
        """从上下文中获取模拟器实例"""
        return context["sim_instance"]

    def _validate_event(
        self, event: Any, expected_type: type | tuple[type, ...] | None = None
    ) -> None:
        """
        验证事件参数

        Args:
            event: 待验证的事件对象
            expected_type: 期望的事件类型，如果为None则只验证非None

        Raises:
            TypeError: 当事件类型不符合期望时
            ValueError: 当事件为None时
        """
        if event is None:
            raise ValueError("事件对象不能为None")

        if expected_type is not None and not isinstance(event, expected_type):
            if isinstance(expected_type, tuple):
                expected_names = [t.__name__ for t in expected_type]
                raise TypeError(
                    f"期望事件类型为 {expected_names} 之一，实际得到 {type(event).__name__}"
                )
            else:
                raise TypeError(
                    f"期望事件类型为 {expected_type.__name__}，实际得到 {type(event).__name__}"
                )

    def _validate_context(self, context: dict[str, Any]) -> None:
        """
        验证上下文数据

        Args:
            context: 待验证的上下文字典

        Raises:
            ValueError: 当上下文缺少必需的键时
        """
        if not isinstance(context, dict):
            raise TypeError("上下文必须是字典类型")

        required_keys = {
            "data",
            "tick",
            "enemy",
            "dynamic_buff",
            "exist_buff_dict",
            "action_stack",
            "sim_instance",
        }

        missing_keys = required_keys - context.keys()
        if missing_keys:
            raise ValueError(f"上下文缺少必需的键: {sorted(missing_keys)}")

    def _handle_error(self, error: Exception, operation: str, event: Any = None) -> None:
        """
        统一错误处理方法

        Args:
            error: 发生的异常
            operation: 操作描述
            event: 相关事件对象（可选）

        Raises:
            RuntimeError: 包装后的异常信息
        """
        error_msg = f"在 {operation} 时发生错误: {error}"
        if event is not None:
            error_msg = f"在 {operation} 事件 {type(event)} 时发生错误: {error}"

        raise RuntimeError(error_msg) from error
