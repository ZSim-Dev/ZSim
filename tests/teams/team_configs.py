# -*- coding: utf-8 -*-
"""团队配置基础类和注册器"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from zsim.models.session.session_run import CommonCfg


class TeamConfigBase(ABC):
    """团队配置基类"""

    def __init__(self, team_name: str, description: str = ""):
        self.team_name = team_name
        self.description = description

    @abstractmethod
    def create_config(self) -> CommonCfg:
        """创建团队配置，子类必须实现此方法"""
        pass

    @abstractmethod
    def get_expected_characters(self) -> List[str]:
        """获取预期的角色列表，子类必须实现此方法"""
        pass

    def get_team_info(self) -> Dict[str, Any]:
        """获取团队信息"""
        return {
            "team_name": self.team_name,
            "description": self.description,
            "characters": self.get_expected_characters()
        }


class TeamRegistry:
    """团队配置注册器"""

    _instance = None
    _teams: Dict[str, TeamConfigBase] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, team_config: TeamConfigBase):
        """注册团队配置"""
        cls._teams[team_config.team_name] = team_config

    @classmethod
    def get_team(cls, team_name: str) -> TeamConfigBase:
        """获取团队配置"""
        return cls._teams.get(team_name)

    @classmethod
    def get_all_teams(cls) -> List[TeamConfigBase]:
        """获取所有团队配置"""
        return list(cls._teams.values())

    @classmethod
    def get_all_team_configs(cls) -> List[Tuple[str, CommonCfg]]:
        """获取所有团队的配置元组列表"""
        configs = []
        for team in cls.get_all_teams():
            try:
                config = team.create_config()
                configs.append((team.team_name, config))
            except Exception as e:
                print(f"创建团队 '{team.team_name}' 配置失败: {e}")
        return configs

    @classmethod
    def get_teams_by_attribute(cls, attribute: str) -> List[TeamConfigBase]:
        """根据属性获取团队配置"""
        return [team for team in cls.get_all_teams()
                if attribute.lower() in team.team_name.lower()]

    @classmethod
    def list_team_names(cls) -> List[str]:
        """获取所有团队名称"""
        return list(cls._teams.keys())


def auto_register_teams():
    """自动注册所有团队配置"""
    # 导入所有团队配置模块以触发注册

    # 返回注册器实例
    return TeamRegistry()
