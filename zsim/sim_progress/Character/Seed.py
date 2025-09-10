from typing import TYPE_CHECKING
from .character import Character
from .utils.filters import _skill_node_filter
from define import SEED_REPORT

if TYPE_CHECKING:
    from zsim.sim_progress.Preload import SkillNode
    from zsim.simulator.simulator_class import Simulator


class Seed(Character):
    def __init__(self, **kwargs):
        """
        Seed的特殊机制
        """
        super().__init__(**kwargs)
        self._steel_charge: float = 0.0  # 钢能值
        self.max_steel_charge: int = 150  # 最大钢能值
        self.sna_steel_charge_cost: int = 60 if self.cinema < 1 else 50   # 落华·崩坠一式、二式消耗的钢能值
        self.sp_to_steel_ratio: float = 0.5  # 技能能耗转换为钢能值的比例
        self.Q_steel_charge_get: int = 60   # Q技能获得的钢能值
        self.vanguard: Character | None = None      # 正兵
        self.sna_quick_release: bool = False        # sna的快速释放状态
        self.onslaught: bool = False    # 强袭状态
        self.direct_strike: bool = False    # 明攻状态


    @property
    def besiege(self) -> bool:
        """围杀状态，当强袭状态和明攻状态同时为True时，为True"""
        return self.onslaught and self.direct_strike

    def special_resources(self, *args, **kwargs) -> None:
        """模拟Seed的特殊资源机制"""
        # 输入类型检查
        skill_nodes: list[SkillNode] = _skill_node_filter(*args, **kwargs)
        # 对输入的skill_node进行遍历
        for node in skill_nodes:
            # 更新钢能值
            self.update_steel_charge_from_sp_cost(skill_node=node)
            
            # 更新特殊状态
            self.update_special_state(node)
            
            if node.char_name == self.NAME:
                # SNA技能消耗钢能值
                if node.skill_tag in ["1461_SNA_2", "1461_SNA_3"]:
                    self.update_steel_charge(value=self.sna_steel_charge_cost * -1, update_origin=node.skill_tag)
                
                # Q技能获得钢能值
                elif node.skill_tag == "1461_Q":
                    self.update_steel_charge(value=self.Q_steel_charge_get, update_origin=node.skill_tag)
                    if SEED_REPORT:
                        self.sim_instance.schedule_data.change_process_state()
                        print(f"【席德事件】席德释放了 {node.skill_tag} 获得了{self.Q_steel_charge_get}点钢能值")
                
                # SNA_1处理
                elif node.skill_tag == "1461_SNA_1":
                    if self.sna_quick_release:
                        self.sna_quick_release = False

    @property
    def steel_charge(self) -> float:
        return self._steel_charge

    @steel_charge.setter
    def steel_charge(self, value: int | float) -> None:
        # 检查钢能值足够的上升沿（支持1画和0画的不同门槛）
        threshold = self.sna_steel_charge_cost * 2
        if self._steel_charge < threshold <= self._steel_charge + value:
            # 在检测到钢能值足够的上升沿时，打开sna的快速释放标记。
            self.sna_quick_release = True
            if SEED_REPORT:
                self.sim_instance.schedule_data.change_process_state()
                print(f"【席德事件】钢能值达到门槛({threshold}点)，开启SNA快速释放")
        
        value = min(value, self.max_steel_charge)
        self._steel_charge = value

    def update_steel_charge(self, value: int | float, update_origin: str) -> None:
        """更新钢能值"""
        if value < 0:
            assert abs(value) < self.steel_charge, f"{update_origin}企图消耗{abs(value):.2f}点钢能值，目前钢能值为{self.steel_charge:.2f}点，钢能值不足！"
        self.steel_charge += value

    @property
    def steel_charge_enough(self) -> bool:
        """判断钢能值是否足够"""
        return self.steel_charge >= self.sna_steel_charge_cost

    def update_special_resource(self, skill_node: SkillNode):
        """
        从命中中更新钢能值，该函数的调用时机为命中后，
        所以不在Character的special_resource内进行更新，而是在Schedule阶段调用。
        """
        if skill_node.char_name != self.NAME:
            return
        if skill_node.labels is None:
            return
        if "steel_charge" in skill_node.labels:
            total_value = skill_node.labels["steel_charge"]
            value = total_value/skill_node.skill.hit_times
            self.update_steel_charge(value=value, update_origin=skill_node.skill_tag)

    def update_steel_charge_from_sp_cost(self, skill_node: SkillNode):
        """
        因技能能耗而更新钢能值，但注意，只有正兵和席德本身的能耗才能转化为钢能值
        """
        # 筛选出正兵和席德本身的技能
        if self.vanguard is not None:
            if skill_node.char_name not in [self.NAME, self.vanguard.NAME]:
                return
        else:
            if skill_node.char_name not in [self.NAME]:
                return
        sp_consume = skill_node.skill.sp_consume
        if sp_consume == 0:
            return
        value = sp_consume * self.sp_to_steel_ratio
        self.update_steel_charge(value=value, update_origin=f"{skill_node.skill_tag}能耗转化")
        if SEED_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print(f"【席德事件】{skill_node.skill_tag}消耗了{sp_consume:.2f}点能量，转化为{value:.2f}点钢能值")

    def update_special_state(self, skill_node: SkillNode):
        """更新席德的特殊状态"""
        pass

    def POST_INIT_DATA(self, sim_instance: "Simulator"):
        """在初始化阶段，席德需要通过基础攻击力来确认“正兵”人选，只有强攻类型的角色才能成为正兵"""
        atk_box = []
        vanguard = None
        for char_obj in sim_instance.char_data.char_obj_list:
            if not char_obj.specialty == "强攻":
                continue
            char_atk_outside = char_obj.statement.ATK
            atk_box.append(char_atk_outside)
            if char_atk_outside == max(atk_box):
                vanguard = char_obj
        else:
            self.vanguard = vanguard
            if SEED_REPORT:
                self.sim_instance.schedule_data.change_process_state()
                print(f"【席德事件】本次模拟中，席德找到的正兵为：{self.vanguard.NAME}！")
        if self.vanguard is None:
            if SEED_REPORT:
                self.sim_instance.schedule_data.change_process_state()
                print("【席德事件】注意！席德并未在当前队伍里找到正兵！")

    def get_resources(self, *args, **kwargs) -> tuple[str | None, int | float | None]:
        return "钢能值", self.steel_charge

    def get_special_stats(self, *args, **kwargs) -> dict[str | None, object | None]:
        return {
            "钢能值足够": self.steel_charge_enough,
            "sna快速释放": self.sna_quick_release,
            "强袭状态": self.onslaught,
            "明攻状态": self.direct_strike,
            "围杀状态": self.besiege,
            "正兵": self.vanguard.NAME if self.vanguard else None,
        }
