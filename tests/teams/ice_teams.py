# -*- coding: utf-8 -*-
"""冰属性队伍配置"""

from zsim.models.session.session_run import CharConfig, CommonCfg, EnemyConfig

from .team_configs import TeamConfigBase, TeamRegistry


class IceTeamExampleConfig(TeamConfigBase):
    """示例冰属性队配置"""

    def __init__(self):
        super().__init__(
            team_name="示例冰属性队",
            description="角色1-角色2-角色3冰属性队伍"
        )

    def create_config(self) -> CommonCfg:
        """创建示例冰属性队配置"""
        return CommonCfg(
            session_id="test-team-ice-example",
            char_config=[
                CharConfig(
                    name="角色1",
                    weapon="武器1",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="套装4",
                    equip_set2_a="套装2",
                ),
                CharConfig(
                    name="角色2",
                    weapon="武器2",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="套装4",
                    equip_set2_a="套装2",
                ),
                CharConfig(
                    name="角色3",
                    weapon="武器3",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="套装4",
                    equip_set2_a="套装2",
                ),
            ],
            enemy_config=EnemyConfig(index_id=11412, adjustment_id=22412, difficulty=8.74),
            apl_path="./zsim/data/APLData/冰属性队伍.toml",
        )

    def get_expected_characters(self) -> list:
        """获取预期的角色列表"""
        return ["角色1", "角色2", "角色3"]


class IceTeamConfigs:
    """冰属性队伍配置集合"""

    @staticmethod
    def register_all():
        """注册所有冰属性队伍配置"""
        TeamRegistry.register(IceTeamExampleConfig())

    @staticmethod
    def get_example_team() -> IceTeamExampleConfig:
        """获取示例冰属性队配置"""
        return IceTeamExampleConfig()

    @staticmethod
    def get_all_configs() -> list:
        """获取所有冰属性队伍配置"""
        return [
            IceTeamConfigs.get_example_team()
        ]


# # 自动注册
# IceTeamConfigs.register_all()
