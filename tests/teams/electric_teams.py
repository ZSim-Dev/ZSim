# -*- coding: utf-8 -*-
"""雷属性队伍配置"""

from zsim.models.session.session_run import CharConfig, CommonCfg, EnemyConfig

from .team_configs import TeamConfigBase, TeamRegistry


class ElectricTeamQingyiConfig(TeamConfigBase):
    """青衣雷属性队配置"""

    def __init__(self):
        super().__init__(team_name="青衣雷属性队", description="青衣-丽娜-雅雷属性队伍")

    def create_config(self) -> CommonCfg:
        """创建青衣雷属性队配置"""
        return CommonCfg(
            session_id="test-team-qingyi-electric",
            char_config=[
                CharConfig(
                    name="青衣",
                    weapon="玉壶青冰",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="震星迪斯科",
                    equip_set2_a="啄木鸟电音",
                ),
                CharConfig(
                    name="丽娜",
                    weapon="啜泣摇篮",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="静听嘉音",
                    equip_set2_a="摇摆爵士",
                ),
                CharConfig(
                    name="雅",
                    weapon="霰落星殿",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="折枝剑歌",
                    equip_set2_a="啄木鸟电音",
                ),
            ],
            enemy_config=EnemyConfig(index_id=11412, adjustment_id=22412, difficulty=8.74),
            apl_path="./zsim/data/APLData/青衣-丽娜-雅.toml",
        )

    def get_expected_characters(self) -> list:
        """获取预期的角色列表"""
        return ["青衣", "丽娜", "雅"]


class ElectricTeamSeedZeroAnbiConfig(TeamConfigBase):
    """席德大安比队伍"""

    def __init__(self):
        super().__init__(team_name="席德大安比队", description="席德-大安比-扳机队伍")

    # TODO：扳机的影画目前只支持到1画，不能给高！

    def create_config(self) -> CommonCfg:
        return CommonCfg(
            session_id="test-team-seed-zeroanbi-electric",
            char_config=[
                CharConfig(
                    name="席德",
                    weapon="机巧心种",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="拂晓生花",
                    equip_set2_a="啄木鸟电音",
                ),
                CharConfig(
                    name="零号·安比",
                    weapon="牺牲洁纯",
                    weapon_level=5,
                    cinema=6,
                    scATK_percent=30,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="如影相随",
                    equip_set2_a="拂晓生花",
                ),
                CharConfig(
                    name="扳机",
                    weapon="索魂影眸",
                    weapon_level=5,
                    cinema=1,
                    scATK_percent=47,
                    scCRIT=30,
                    scCRIT_DMG=50,
                    equip_style="4+2",
                    equip_set4="如影相随",
                    equip_set2_a="折枝剑歌",
                ),
            ],
            enemy_config=EnemyConfig(index_id=11412, adjustment_id=22412, difficulty=8.74),
            apl_path="./zsim/data/APLData/席德-大安比-扳机.toml",
        )

    def get_expected_characters(self) -> list:
        """获取预期的角色列表"""
        return ["席德", "零号·安比", "扳机"]


class ElectricTeamConfigs:
    """雷属性队伍配置集合"""

    @staticmethod
    def register_all():
        """注册所有雷属性队伍配置"""
        TeamRegistry.register(ElectricTeamQingyiConfig())
        TeamRegistry.register(ElectricTeamSeedZeroAnbiConfig())

    @staticmethod
    def get_qingyi_team() -> ElectricTeamQingyiConfig:
        """获取青衣雷属性队配置"""
        return ElectricTeamQingyiConfig()

    @staticmethod
    def get_seed_zeroanbi_team() -> ElectricTeamSeedZeroAnbiConfig:
        """获取席德大安比队伍配置"""
        return ElectricTeamSeedZeroAnbiConfig()

    @staticmethod
    def get_all_configs() -> list:
        """获取所有雷属性队伍配置"""
        return [ElectricTeamConfigs.get_qingyi_team(), ElectricTeamConfigs.get_seed_zeroanbi_team()]


# 自动注册
ElectricTeamConfigs.register_all()
