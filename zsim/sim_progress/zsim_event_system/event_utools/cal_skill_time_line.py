from typing import Dict, List, Optional, Union

from ....define import SkillSubEventTypes


def cal_skill_time_line(
    preload_tick: int,
    hit_times: int,
    ticks: int,
    hit_list: Optional[List[Union[int, float]]],
) -> Dict[SkillSubEventTypes, List[Union[int, float]]]:
    """计算技能的时间线"""
    time_line: Dict[SkillSubEventTypes, List[Union[int, float]]] = {}
    if hit_list is None:
        step_length = (ticks - 1) / (hit_times + 1)
        hits = [preload_tick + i * step_length for i in range(hit_times + 1)]
    else:
        hits = [preload_tick + i for i in hit_list]
    start_tick = preload_tick
    end_tick = preload_tick + ticks
    time_line[SkillSubEventTypes.START] = [start_tick]
    time_line[SkillSubEventTypes.HIT] = hits
    time_line[SkillSubEventTypes.END] = [end_tick]
    return time_line
