from zsim.sim_progress.Buff import Buff
from zsim.sim_progress.Dot import BaseDot
from zsim.sim_progress.Enemy import Enemy
from zsim.sim_progress.Report import report_buff_to_queue, report_to_log


def update_time_related_effect(DYNAMIC_BUFF_DICT: dict, timetick, exist_buff_dict: dict, enemy: Enemy):
    """
    更新一些和时间相关的效果，异常条、Buff、Dot
    """
    update_anomaly_bar(timetick, enemy)
    update_buff(DYNAMIC_BUFF_DICT, enemy, exist_buff_dict, timetick)
    update_dot(enemy, timetick)
    return DYNAMIC_BUFF_DICT


def update_buff(DYNAMIC_BUFF_DICT, enemy, exist_buff_dict, timetick):
    """
    该函数用于更新当前正处于活跃状态的Buff，
    并且根据时间或是其他规则判断这些Buff是否应该结束。
    结束的Buff会被移除。
    注意，该函数的运行位置会导致所有Buff于Ntick末尾消失的Buff在N+1tick的开头处理，
    当然这大部分情况下不会影响正确性。
    """
    for charname, sub_dynamic_buff_list in DYNAMIC_BUFF_DICT.items():
        remove_buff_list = []
        for _ in sub_dynamic_buff_list:
            CheckBuff(_, charname)
            # 首先根据Buff的结束行为是否复杂进行分流
            if not _.ft.simple_exit_logic:
                # 结束行为复杂的Buff，其结束逻辑由xexit()控制
                shoud_exit = _.logic.xexit()
                if not shoud_exit:
                    # 如果buff的xexit()函数认为buff不应该结束，则再记录一次层数。
                    report_buff_to_queue(charname, timetick, _.ft.index, _.dy.count, True, level=4)
                else:
                    # 若buff的xexit()函数认为buff应该结束，则移除buff
                    remove_buff_list.append(_)
            else:
                # 处理完了结束行为较为复杂的Buff，现在来处理结束行为简单的Buff

                # 对于alltime的buff，自然是每个tick都存在，所以每个tick都记录。
                if _.ft.alltime:
                    report_buff_to_queue(charname, timetick, _.ft.index, _.dy.count, True, level=4)
                    continue

                # 对于层数独立结算的buff，需要特殊判断；
                if _.ft.individual_settled:
                    if len(_.dy.built_in_buff_box) <= 0:
                        # 层数为0时候结束
                        remove_buff_list.append(_)
                        continue
                    else:
                        process_individual_buff(_, timetick)
                        # 先更新层数，再report。
                        report_buff_to_queue(
                            charname, timetick, _.ft.index, _.dy.count, True, level=4
                        )

                # 接下来处理的是层数不独立结算的buff
                else:
                    # 层数不独立的buff，时间到点了就要结束。
                    if timetick > _.dy.endticks:
                        remove_buff_list.append(_)
                        continue

                    # 没结束的buffreport一下层数。
                    else:
                        report_buff_to_queue(
                            charname, timetick, _.ft.index, _.dy.count, True, level=4
                        )

        else:
            # 统一执行KickOut函数，移除buff
            sub_exist_buff_dict = exist_buff_dict[charname]
            for removed_buff in remove_buff_list:
                KickOutBuff(
                    DYNAMIC_BUFF_DICT,
                    removed_buff,
                    charname,
                    enemy,
                    sub_exist_buff_dict,
                    timetick,
                )


def process_individual_buff(_, timetick):
    """
    针对层数独立结算的buff的tuple的独立结算。去除过期的tuple
    """
    end_tuples_list = []
    for tuples in _.dy.built_in_buff_box:
        if tuples[1] < timetick:
            end_tuples_list.append(tuples)
    else:
        for _end_tuples in end_tuples_list:
            _.dy.built_in_buff_box.remove(_end_tuples)
    _.dy.count = len(_.dy.built_in_buff_box)


def KickOutBuff(
    DYNAMIC_BUFF_DICT: dict,
    buff: Buff,
    charname: str,
    enemy,
    sub_exist_buff_dict: dict,
    timetick: int,
):
    buff.end(timetick, sub_exist_buff_dict)
    DYNAMIC_BUFF_DICT[charname].remove(buff)
    report_to_log(f"[Buff END]:{timetick}:{charname} 的 {buff.ft.index} 结束，已从动态列表移除", level=4)
    if buff.ft.is_debuff:
        enemy.dynamic.dynamic_debuff_list.remove(buff)


def CheckBuff(_, charname):
    """
    检查buff的参数情况。
    """
    if not isinstance(_, Buff):
        raise TypeError(f"{_}不是Buff类！")
    if _.ft.is_debuff and charname != "enemy":
        raise ValueError(f"{_.ft.index}是debuff但是却进入了{charname}的buff池！")
    if (not _.ft.is_debuff) and charname == "enemy":
        raise ValueError(f"{_.ft.index}是buff但是却在enemy的debuff池中！")


def update_dot(enemy: Enemy, timetick):
    for _ in enemy.dynamic.dynamic_dot_list[:]:
        if not isinstance(_, BaseDot.Dot):
            raise TypeError(f"Enemy的dot列表中的{_}不是Dot类！")
        if not _.ft.complex_exit_logic:
            if timetick >= _.dy.end_ticks:
                _.end(timetick)
                enemy.dynamic.dynamic_dot_list.remove(_)
                report_to_log(f"[Dot END]:{timetick}:{_.ft.index}结束，已从动态列表移除", level=4)
        else:
            exit_result = _.exit_judge(enemy=enemy)
            # 不是所有的dot的退出函数都有返回，这里必须处理退出函数不返回内容的情况
            if exit_result is None:
                raise ValueError("复杂退出逻辑Dot的退出函数必须返回有效布尔值")
            if exit_result:
                _.end(timetick)
                enemy.dynamic.dynamic_dot_list.remove(_)
                report_to_log(f"[Dot END]:{timetick}:{_.ft.index}结束，已从动态列表移除", level=4)


def update_anomaly_bar(time_now: int, enemy: Enemy):
    for element_type, bar in enemy.anomaly_bars_dict.items():
        result = bar.check_myself(time_now)
        if result:
            setattr(
                enemy.dynamic,
                enemy.trans_anomaly_effect_to_str[element_type],
                bar.active,
            )
            enemy.dynamic.active_anomaly_bar_dict[element_type] = None
