from typing import Sequence

from .tree import LeafConfiguration


class ZSimEventConfigRepository(LeafConfiguration):
    """状态树系统的事件配置仓库, 用于存储各个节点的事件配置, 是整个树系统的基础模块"""

    def __init__(self, snapshot: dict[str, Sequence[LeafConfiguration]] | None = None):
        self._snaoshot: dict[str, list[LeafConfiguration]] = {
            node_id: list(configurations) for node_id, configurations in (snapshot or {}).items()
        }

    def register(self, node_id: str, configuration: LeafConfiguration) -> LeafConfiguration:
        """
        注册一个节点的事件配置
        :param node_id: 节点ID
        :param configuration: 节点的事件配置
        :return: 注册的事件配置
        """
        self._snaoshot.setdefault(node_id, []).append(configuration)
        return configuration

    def load_leaf_config(self, node_id: str) -> Sequence[LeafConfiguration]:
        """加载一个节点的事件配置"""
        return tuple(self._snaoshot.get(node_id, ()))
