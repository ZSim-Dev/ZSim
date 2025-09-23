# -*- coding: utf-8 -*-
"""物理队伍配置"""

from .team_configs import TeamConfigBase, TeamRegistry
from zsim.models.session.session_run import CommonCfg, CharConfig, EnemyConfig


class PhysicalTeamVivianConfig(TeamConfigBase):
    """薇薇安物理队配置"""

    def __init__(self):
        super().__init__(
            team_name="薇薇安物理队",
            description="薇薇安-柳-耀嘉音物理属性队伍"
        )

    def create_config(self) -> CommonCfg:
        """创建薇薇安物理队配置"""
        return CommonCfg(
            session_id="test-team-vivian-physical",
            char_config=[
                CharConfig(
                    name="薇薇安",
                    weapon="青溟笼舍",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="自由蓝调",
                    equip_set2_a="灵魂摇滚",
                ),
                CharConfig(
                    name="柳",
                    weapon="时流贤者",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="自由蓝调",
                    equip_set2_a="灵魂摇滚",
                ),
                CharConfig(
                    name="耀嘉音",
                    weapon="飞鸟星梦",
                    weapon_level=1,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="自由蓝调",
                    equip_set2_a="灵魂摇滚",
                ),
            ],
            enemy_config=EnemyConfig(index_id=11412, adjustment_id=22412, difficulty=8.74),
            apl_path="./zsim/data/APLData/薇薇安-柳-耀嘉音.toml",
        )

    def get_expected_characters(self) -> list:
        """获取预期的角色列表"""
        return ["薇薇安", "柳", "耀嘉音"]


class PhysicalTeamConfigs:
    """物理队伍配置集合"""

    @staticmethod
    def register_all():
        """注册所有物理队伍配置"""
        TeamRegistry.register(PhysicalTeamVivianConfig())

    @staticmethod
    def get_vivian_team() -> PhysicalTeamVivianConfig:
        """获取薇薇安物理队配置"""
        return PhysicalTeamVivianConfig()

    @staticmethod
    def get_all_configs() -> list:
        """获取所有物理队伍配置"""
        return [
            PhysicalTeamConfigs.get_vivian_team()
        ]


# 自动注册
PhysicalTeamConfigs.register_all()