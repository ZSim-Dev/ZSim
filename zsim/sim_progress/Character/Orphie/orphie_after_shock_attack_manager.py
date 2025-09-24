from zsim.sim_progress.Character.character import Character
from zsim.sim_progress.Preload import SkillNode


class OrphieAfterShockAttackManager:
    def __init__(self, character: Character) -> None:
        """这是奥菲斯的追加攻击管理器"""
        self.char = character
        from zsim.sim_progress.Character.Orphie import Orphie
        assert isinstance(self.char, Orphie), f"OrphieAfterShockManager 只能用于 Orphie 角色，当前角色类型：{type(self.char).__name__}"
        self.cd = 300       # 追加攻击内置CD
        self.last_update_tick = 0       # 上一次更新时间
        self.after_shock_attack_map: {}

    def ready_check(self) -> bool:
        """检查是否准备好生成追加攻击"""
        if self.last_update_tick == 0:
            return True
        else:
            tick = self.char.sim_instance.tick
            return tick - self.last_update_tick >= self.cd

    def try_spawn_after_shock_attack(self, skill_node: SkillNode) -> None:
        """尝试生成追加攻击"""
        if not self.ready_check():
            return
        from zsim.sim_progress.data_struct.SchedulePreload import schedule_preload_event_factory
        tick = self.char.sim_instance.tick

        schedule_preload_event_factory()
        self.last_update_tick = tick
        pass
