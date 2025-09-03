# 此文件记录了所有的和事件广播以及后置初始化有关的枚举类

from enum import Enum


class SpecialStateUpdateSignal(Enum):
    """特殊状态管理器的更新信号类"""

    """在Preload之后，广播点位位于Preload末尾，ConfirmEngine中与外部数据交互时。"""
    BEFORE_PRELOAD = "BeforePreload"
    """在角色接收技能的点位广播"""
    CHARACTER = "Character"
    """广播点位位于Enemy接受到攻击时候"""
    RECEIVE_HIT = "ReceiveHit"


SSUS = SpecialStateUpdateSignal


class PostInitObjectType(Enum):
    """记录了所有需要后置初始化的数据的大类型，以及它们在各自的管理器中传入工厂函数所对应的参数"""

    SweetScare = ("SweetScare", [SSUS.RECEIVE_HIT, SSUS.BEFORE_PRELOAD, SSUS.CHARACTER])


class ListenerBroadcastSignal(Enum):
    """监听器广播函数所涉及到的更新信号"""

    SWITCHING_IN = "switching_in_event"  # 角色切入前场
    ENTER_BATTLE = "enter_battle_event"  # 角色进入战斗
    ANOMALY = "anomaly_event"  # 属性异常事件
    STUN = "stun_event"  # 失衡事件
    PARRY = "parry_event"  # 招架事件
    BLOCK = "block_event"  # 格挡事件（其他具备格挡功能的技能响应进攻事件）
    DISORDER_SPAWN = "disorder_event_spawn"     # 紊乱事件产生
    DISORDER_SETTLED = "disorder_event_settled"       # 紊乱事件结算
    ASSAULT_STATE_ON = "assistant_state_on"     # 畏缩状态上升沿或者刷新——等价于“队伍中任意角色对敌人施加物理异常状态”
    ASSAULT_SPAWN = "assault_spawn"     # 强击触发
    POLARIZED_ASSAULT_SPAWN = "polarized_assault"     # 极性强击触发
