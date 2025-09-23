from typing import TYPE_CHECKING

from .buff_class import Buff

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator
    from zsim.sim_progress.Enemy import Enemy


def _buff_filter(*args, **kwargs):
    buff_name_list: list[str] = []
    for arg in args:
        if isinstance(arg, str):
            buff_name_list.append(arg)
        elif isinstance(arg, Buff):
            buff_name_list.append(arg.ft.index)
    for value in kwargs.values():
        if isinstance(value, str):
            buff_name_list.append(value)
        if isinstance(value, Buff):
            buff_name_list.append(value.ft.index)
    return buff_name_list


def buff_add_strategy(
    *added_buffs: str | Buff,
    benifit_list: list[str] | None = None,
    specified_count: int | float | None = None,
    sim_instance: "Simulator" = None,
):
    """
    这个函数是暴力添加buff用的，比如霜寒、畏缩等debuff，
    又比如核心被动强行添加buff的行为，都可以通过这个函数来实现。
    Args:
        added_buffs: str: 需要添加的Buff的index
        benifit_list: list[str]: 受益者名单
        specified_count: int | float | None: 指定层数，非必要参数
        sim_instance: Simulator: 模拟器实例
    """
    if sim_instance is None:
        raise ValueError("调用buff_add_strategy函数时，sim_instance是None")
    buff_name_list: list[str] = _buff_filter(*added_buffs)

    all_name_order_box = sim_instance.load_data.all_name_order_box
    # name_box = main_module.load_data.name_box
    # name_box_now = name_box + ['enemy']
    enemy = sim_instance.schedule_data.enemy
    exist_buff_dict = sim_instance.load_data.exist_buff_dict
    tick = sim_instance.tick
    DYNAMIC_BUFF_DICT = sim_instance.global_stats.DYNAMIC_BUFF_DICT
    """
    将Buff名称、Buff实例转化为对应的Buff并且添加到DYNAMIC_BUFF_DICT或者其他地方。
    是在Load阶段以外暴力互动DYNAMIC_BUFF_DICT的通用方式。
    """
    # 对于buff_name_list中的每个Buff都执行一次

    for buff_name in buff_name_list:
        # FIXME: 这里可能存在Bug，指定受益人（benifit_list）可能与自动查找的逻辑冲突。
        selected_characters = confirm_selected_character(exist_buff_dict, buff_name, all_name_order_box, benifit_list)
        if selected_characters is None:
            print(f"【BuffAddStrategy警告】并未找到适用于{buff_name}的受益人！本次Buff添加将被跳过！")
            continue

        # 针对每位受益人，都执行一次Buff添加
        for names in selected_characters:
            let_buff_start(DYNAMIC_BUFF_DICT, buff_name, enemy, exist_buff_dict, names, specified_count, tick)
    # __check_buff_add_result(buff_name, selected_characters, exist_buff_dict, DYNAMIC_BUFF_DICT, sim_instance)


def let_buff_start(
        DYNAMIC_BUFF_DICT: dict[str, list[Buff]],
        buff_name: str,
        enemy: "Enemy",
        exist_buff_dict: dict[str, dict[str, Buff]],
        names: str,
        specified_count: int,
        tick: int
    ):
    """
    这个函数是buff_add_strategy函数的添加Buff的核心业务函数。
    Args:
        DYNAMIC_BUFF_DICT: dict: 动态Buff字典
        buff_name: str: Buff名称
        enemy: Character: 敌人
        exist_buff_dict: dict: 存在的Buff字典
        names: str: 受益者名称
        specified_count: int | float | None: 指定层数，非必要参数
        tick: int: 当前时间
    """
    from copy import deepcopy
    # 对于不同的Buff受益人，sub_exist_buff_dict是不同的，需要重新获取
    sub_exist_buff_dict = exist_buff_dict[names]
    copyed_buff = sub_exist_buff_dict[buff_name]
    buff_new = deepcopy(copyed_buff)
    buff_new.ft.operator = copyed_buff.ft.operator
    buff_new.ft.passively_updating = copyed_buff.ft.passively_updating
    buff_new.ft.beneficiary = copyed_buff.ft.beneficiary
    # buff_new = Buff.create_new_from_existing(copyed_buff)
    if copyed_buff.ft.simple_start_logic and buff_new.ft.simple_effect_logic:
        if specified_count is not None:
            buff_new.simple_start(
                tick,
                sub_exist_buff_dict,
                specified_count=specified_count,
            )
        else:
            buff_new.simple_start(tick, sub_exist_buff_dict)

    elif not copyed_buff.ft.simple_start_logic:
        # print(buff_new.ft.index)
        buff_new.logic.xstart(benifit=names)
    elif not copyed_buff.ft.simple_effect_logic:
        # print(buff_new.ft.index)
        buff_new.logic.xeffect()
    # 更新 DYNAMIC_BUFF_DICT
    dynamic_buff_list = DYNAMIC_BUFF_DICT.get(names, [])
    buff_existing_check = next(
        (
            existing_buff
            for existing_buff in dynamic_buff_list
            if existing_buff.ft.index == buff_new.ft.index
        ),
        None,
    )
    if buff_existing_check:
        dynamic_buff_list.remove(buff_existing_check)
    # print(f'强制添加Buff函数执行，本次为 {names} 添加的Buff为：{buff_new.ft.index}，激活状态为：{buff_new.dy.active}，开始时间为：{buff_new.dy.startticks}，结束时间为：{buff_new.dy.endticks}，层数：{buff_new.dy.count}')
    dynamic_buff_list.append(buff_new)
    # 如果是敌人，更新动态 Debuff 列表
    if names == "enemy":
        enemy_dynamic_debuff_list = enemy.dynamic.dynamic_debuff_list
        debuff_existing_check = next(
            (
                existing_buff
                for existing_buff in enemy_dynamic_debuff_list
                if existing_buff.ft.index == buff_new.ft.index
            ),
            None,
        )
        if debuff_existing_check:
            enemy_dynamic_debuff_list.remove(debuff_existing_check)
        enemy_dynamic_debuff_list.append(buff_new)


def get_selected_character(adding_buff_code, all_name_order_box, copyed_buff):
    if copyed_buff.ft.add_buff_to == "0001" or copyed_buff.ft.operator == "enemy":
        selected_characters = ["enemy"]
    else:
        name_box_now = all_name_order_box[copyed_buff.ft.operator]
        selected_characters = [
            name_box_now[i] for i in range(len(name_box_now)) if adding_buff_code[i] == "1"
        ]
    return selected_characters


def confirm_selected_character(exist_buff_dict: dict[str, dict[str, Buff]], buff_name: str, all_name_order_box: dict[str, list[str]], benifit_list: list[str] = None) -> list[str] | None:
    """
    确认选中的角色是否存在。
    Args:
        exist_buff_dict: dict[str,dict[str,Buff]]: 存在Buff字典
        buff_name: str: 即将执行强行添加的Buff名称
        all_name_order_box: dict[str, list[str]]: 所有角色的名称列表
        benifit_list: list[str]: 外部制定的受益者名单
    """
    for char_name, sub_dict in exist_buff_dict.items():

        # 首先判断Buff是否在当前检查角色(char_name)的收益列表中
        if buff_name not in sub_dict:
            continue
        selected_buff = sub_dict[buff_name]
        # assert isinstance(selected_buff, Buff), "buff_add_strategy函数中，buff_name_list中的元素必须是Buff类"

        # 确定本次Buff添加的受益人
        adding_buff_code = str(int(selected_buff.ft.add_buff_to)).zfill(4)
        selected_characters = (
            get_selected_character(adding_buff_code, all_name_order_box, selected_buff)
            if benifit_list is None
            else benifit_list
        )
        return selected_characters
    else:
        return None


def __check_buff_add_result(buff_name: str, selected_characters: list[str], exist_buff_dict: dict[str, dict[str, Buff]], DYNAMIC_BUFF_DICT: dict[str, list[Buff]], sim_instance: "Simulator"):
    """
    检查Buff添加结果是否符合预期。
    Args:
        buff_name: str: 即将执行强行添加的Buff名称
        selected_characters: list[str]: 选中的角色列表
        exist_buff_dict: dict[str,dict[str,Buff]]: 存在Buff字典
        DYNAMIC_BUFF_DICT: dict[str, list[Buff]: 动态Buff字典
    """
    tick = sim_instance.tick
    for char_name in selected_characters:
        sub_list = DYNAMIC_BUFF_DICT[char_name]
        for buffs in sub_list:
            assert isinstance(buffs, Buff)
            buff_0 = exist_buff_dict[char_name][buffs.ft.index]
            if buffs.ft.index == buff_name:
                if all([buffs.dy.startticks == buff_0.dy.startticks,
                        buffs.dy.endticks == buff_0.dy.endticks,
                        buffs.dy.count == buff_0.dy.count]):
                    print(f"【BuffAddStrategy检查】{tick}tick：{char_name}成功添加了{buff_name}, 其层数为{buffs.dy.count}，{buffs.dy.startticks} - {buffs.dy.endticks}")
                    return
    print(f"【BuffAddStrategy检查】{tick}tick：{char_name}未添加{buff_name}")
