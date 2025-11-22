# -*- coding: utf-8 -*-
"""团队配置模块"""

from .electric_teams import ElectricTeamConfigs
from .fire_teams import FireTeamConfigs
from .ice_teams import IceTeamConfigs
from .physical_teams import PhysicalTeamConfigs
from .team_configs import TeamConfigBase, TeamRegistry, auto_register_teams

__all__ = [
    "PhysicalTeamConfigs",
    "FireTeamConfigs",
    "ElectricTeamConfigs",
    "TeamConfigBase",
    "TeamRegistry",
    "auto_register_teams",
]
