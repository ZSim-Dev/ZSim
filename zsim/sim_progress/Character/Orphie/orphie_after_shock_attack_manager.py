from zsim.define import ORPHIE_REPORT
from zsim.sim_progress.Character.character import Character
from zsim.sim_progress.Preload import SkillNode


class OrphieAfterShockAttackManager:
    def __init__(self, character: Character) -> None:
        """这是奥菲斯的追加攻击管理器"""
        self.char = character
        from zsim.sim_progress.Character.Orphie import Orphie

        assert isinstance(self.char, Orphie), (
            f"OrphieAfterShockManager 只能用于 Orphie 角色，当前角色类型：{type(self.char).__name__}"
        )
        self.cd = 300  # 追加攻击内置CD
        self.last_update_tick = 0  # 上一次更新时间
        self.after_shock_attack_map: dict = {
            "1301_E_EX_A": lambda: self.char.sp >= 60,
            "1301_E_B": lambda: True,
        }
        self._last_lock_tick: int = 0  # 锁定状态的上一次更新时间
        self._last_lock_origin: SkillNode | None = None  # 上一次造成锁定的技能节点
        self.leagal_lock_skill_tags: list[str] = [
            "1301_QTE",
            "1301_Q_1",
            "1301_Q_2",
            "1301_E_EX_C",
            "1301_E_EX_D",
        ]  # 会造成锁定状态的技能标签

    @property
    def last_lock_origin(self) -> SkillNode | None:
        """上一次造成锁定的技能节点"""
        return self._last_lock_origin

    @last_lock_origin.setter
    def last_lock_origin(self, skill_node: SkillNode | None) -> None:
        """更新技能锁定状态"""
        if skill_node is not None:
            assert skill_node.skill_tag in self.leagal_lock_skill_tags
        self._last_lock_origin = skill_node
        sim_instance = self.char.sim_instance
        assert sim_instance is not None
        self._last_lock_tick = sim_instance.tick
        if ORPHIE_REPORT and skill_node is not None:
            sim_instance.schedule_data.change_process_state()
            print(
                f"【奥菲斯事件】检测到奥菲斯释放了技能：{skill_node.skill.skill_text}，进入锁定状态，在{self._last_lock_tick + skill_node.skill.ticks}tick之前，无法触发追加攻击"
            )

    @property
    def is_locked(self) -> bool:
        """当前是否处于锁定状态"""
        # 当角色处于前台时，默认处于锁定状态，无法触发追加攻击
        if self.char.dynamic.on_field:
            return True
        if self._last_lock_origin is None:
            return False
        assert self.char.sim_instance is not None
        tick = self.char.sim_instance.tick
        return tick - self._last_lock_tick > self._last_lock_origin.skill.ticks

    def update_myself(self, skill_node: SkillNode) -> None:
        """更新自身状态"""
        # 先更新锁定状态，再尝试触发追加攻击
        self.update_state(skill_node=skill_node)
        if not self.is_locked:
            self.try_spawn_after_shock_attack(skill_node=skill_node)

    def after_shock_attack_ready_check(self) -> bool:
        """检查是否准备好生成追加攻击"""
        if self.last_update_tick == 0:
            return True
        else:
            assert self.char.sim_instance is not None
            tick = self.char.sim_instance.tick
            return tick - self.last_update_tick >= self.cd

    def try_spawn_after_shock_attack(self, skill_node: SkillNode) -> None:
        """尝试生成追加攻击"""
        if not self.after_shock_attack_ready_check():
            return
        assert self.char.sim_instance is not None
        tick = self.char.sim_instance.tick
        from zsim.sim_progress.data_struct.SchedulePreload import schedule_preload_event_factory

        preload_tick_list = [tick]
        skill_tag_list = []
        for skill_tag, check_func in self.after_shock_attack_map.items():
            # 按照顺序，应先检查 E_EX_A，再检查 E_B，即满足能量条件是，优先触发 E_EX_A。
            if check_func():
                skill_tag_list.append(skill_tag)
                break
        else:
            # 若没有任何一个技能满足触发条件，则不生成任何追加攻击
            if not skill_tag_list:
                return
        assert len(skill_tag_list) == 1
        preload_data = self.char.sim_instance.preload.preload_data
        schedule_preload_event_factory(
            preload_tick_list=preload_tick_list,
            skill_tag_list=skill_tag_list,
            preload_data=preload_data,
            sim_instance=self.char.sim_instance,
        )
        self.last_update_tick = tick
        if ORPHIE_REPORT:
            self.char.sim_instance.schedule_data.change_process_state()
            print(f"【奥菲斯事件】触发了一次追加攻击：{skill_tag_list}")

    def update_state(self, skill_node: SkillNode) -> None:
        """更新状态"""
        if skill_node.skill_tag in self.leagal_lock_skill_tags:
            # 更新锁定状态
            self.last_lock_origin = skill_node
