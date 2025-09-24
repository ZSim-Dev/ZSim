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

    def ready_check(self) -> bool:
        """检查是否准备好生成追加攻击"""
        if self.last_update_tick == 0:
            return True
        else:
            assert self.char.sim_instance is not None
            tick = self.char.sim_instance.tick
            return tick - self.last_update_tick >= self.cd

    def try_spawn_after_shock_attack(self, skill_node: SkillNode) -> None:
        """尝试生成追加攻击"""
        if not self.ready_check():
            return
        assert self.char.sim_instance is not None
        tick = self.char.sim_instance.tick
        from zsim.sim_progress.data_struct.SchedulePreload import schedule_preload_event_factory

        preload_tick_list = [tick]
        skill_tag_list = []
        for skill_tag, check_func in self.after_shock_attack_map.items():
            if check_func():
                skill_tag_list.append(skill_tag)
                break
        else:
            if not skill_tag_list:
                return
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
