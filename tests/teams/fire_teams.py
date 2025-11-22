# -*- coding: utf-8 -*-
"""火属性队伍配置"""

from zsim.models.session.session_run import CharConfig, CommonCfg, EnemyConfig

from .team_configs import TeamConfigBase, TeamRegistry


class FireTeamLighterConfig(TeamConfigBase):
    """莱特火属性队配置"""

    def __init__(self):
        super().__init__(team_name="莱特火属性队", description="莱特-扳机-雨果火属性队伍")

    def create_config(self) -> CommonCfg:
        """创建莱特火属性队配置"""
        return CommonCfg(
            session_id="test-team-lighter-fire",
            char_config=[
                CharConfig(
                    name="莱特",
                    weapon="焰心桂冠",
                    weapon_level=5,
                    cinema=0,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="震星迪斯科",
                    equip_set2_a="炎狱重金属",
                ),
                CharConfig(
                    name="扳机",
                    weapon="索魂影眸",
                    weapon_level=5,
                    cinema=0,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="如影相随",
                    equip_set2_a="啄木鸟电音",
                ),
                CharConfig(
                    name="雨果",
                    weapon="千面日陨",
                    weapon_level=5,
                    cinema=0,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="啄木鸟电音",
                    equip_set2_a="激素朋克",
                ),
            ],
            enemy_config=EnemyConfig(index_id=11412, adjustment_id=22412, difficulty=8.74),
            apl_path="./zsim/data/APLData/莱特-扳机-雨果.toml",
        )

    def get_expected_characters(self) -> list:
        """获取预期的角色列表"""
        return ["莱特", "扳机", "雨果"]


class FireTeamConfigs:
    """火属性队伍配置集合"""

    @staticmethod
    def register_all():
        """注册所有火属性队伍配置"""
        TeamRegistry.register(FireTeamLighterConfig())

    @staticmethod
    def get_lighter_team() -> FireTeamLighterConfig:
        """获取莱特火属性队配置"""
        return FireTeamLighterConfig()

    @staticmethod
    def get_all_configs() -> list:
        """获取所有火属性队伍配置"""
        return [FireTeamConfigs.get_lighter_team()]


# 自动注册
FireTeamConfigs.register_all()
