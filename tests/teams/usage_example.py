# -*- coding: utf-8 -*-
"""团队配置使用示例"""

from .physical_teams import PhysicalTeamConfigs
from .team_configs import TeamRegistry


def example_usage():
    """团队配置使用示例"""

    # 1. 获取所有团队配置
    all_teams = TeamRegistry.get_all_teams()
    print(f"总共注册了 {len(all_teams)} 个队伍")

    # 2. 按属性查找队伍
    physical_teams = TeamRegistry.get_teams_by_attribute("物理")
    fire_teams = TeamRegistry.get_teams_by_attribute("火")
    electric_teams = TeamRegistry.get_teams_by_attribute("雷")

    print(f"物理队伍: {[team.team_name for team in physical_teams]}")
    print(f"火属性队伍: {[team.team_name for team in fire_teams]}")
    print(f"雷属性队伍: {[team.team_name for team in electric_teams]}")

    # 3. 直接获取特定队伍
    vivian_team = PhysicalTeamConfigs.get_vivian_team()
    print(f"薇薇安队伍信息: {vivian_team.get_team_info()}")

    # 4. 创建新队伍配置示例
    class ExampleNewTeamConfig:
        """示例：如何创建新的队伍配置"""

        def create_new_team_config(self):
            """创建新队伍配置的示例"""
            from zsim.models.session.session_run import CommonCfg

            from .team_configs import TeamConfigBase

            class NewIceTeamConfig(TeamConfigBase):
                def __init__(self):
                    super().__init__(team_name="冰属性新队伍", description="冰属性队伍示例")

                def create_config(self) -> CommonCfg:
                    # 这里实现具体的配置逻辑
                    pass

                def get_expected_characters(self) -> list:
                    return ["冰角色1", "冰角色2", "冰角色3"]

            # 注册新队伍
            TeamRegistry.register(NewIceTeamConfig())

    # 5. 批量获取所有配置用于测试
    all_team_configs = TeamRegistry.get_all_team_configs()
    print(f"获取到 {len(all_team_configs)} 个队伍配置用于测试")

    for team_name, config in all_team_configs:
        print(f"队伍: {team_name}, 角色: {[char.name for char in config.char_config]}")


if __name__ == "__main__":
    example_usage()
