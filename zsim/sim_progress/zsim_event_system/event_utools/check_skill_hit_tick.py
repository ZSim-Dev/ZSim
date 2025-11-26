from ....define import SkillSubEventTypes


def check_skill_hit_tick(
    tick: int,
    default_split: bool = True,
    time_line: dict[SkillSubEventTypes, list[int | float]] | None = None,
) -> bool:
    if time_line is None:
        print("【ZSim调试报错】尝试检查技能命中时刻,但time_line为空,无法进行命中检查,默认返回False")
        return False
    hit_list: list[int | float] = time_line.get(SkillSubEventTypes.HIT, [])
    if not hit_list:
        return False
    # 对于按照默认分割的命中时间点,hit_tick往往是float，而当前tick是int，需要进行范围判断
    if default_split:
        for ticks in hit_list:
            if tick - 1 <= ticks < tick + 1:
                return True
        else:
            return False
    else:
        # 对于非默认分割的命中时间点，hit_tick往往是int，直接进行等值判断即可
        for ticks in hit_list:
            if tick == ticks:
                return True
        else:
            return False
