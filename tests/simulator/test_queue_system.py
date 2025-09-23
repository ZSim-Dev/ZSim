# -*- coding: utf-8 -*-
"""队列系统测试"""

from datetime import datetime

import pytest

from zsim.api_src.services.sim_controller.sim_controller import SimController
from zsim.models.session.session_create import Session


class TestQueueSystem:
    """队列系统测试"""

    @pytest.mark.asyncio
    async def test_async_queue_multiple_teams(self):
        """使用队列系统测试多个不同队伍的异步模拟，替代单队伍测试。

        注意：此测试可能存在环境共享问题，建议使用 test_isolated_teams.py
        中的隔离测试方法进行多队伍测试。
        """
        from zsim.api_src.services.database.session_db import get_session_db

        from ..teams import auto_register_teams
        from ..test_simulator import TestSimulator

        test_sim = TestSimulator()
        controller = SimController()
        db = await get_session_db()

        # 使用团队配置注册器获取配置
        team_registry = auto_register_teams()
        team_configs = team_registry.get_all_team_configs()
        completed_sessions = []

        try:
            # 为每个队伍创建会话并放入队列
            for i, (team_name, common_cfg) in enumerate(team_configs):
                session_run_config = test_sim.create_session_run_config("normal")
                session_run_config.stop_tick = 3000

                session = Session(
                    session_id=f"queue-test-team-{i}-{team_name.replace(' ', '-')}",
                    create_time=datetime.now(),
                    status="pending",
                    session_run=session_run_config,
                    session_result=None,
                )

                completed_sessions.append(session.session_id)
                await db.add_session(session)

                # 将队伍配置放入队列
                await controller.put_into_queue(session.session_id, common_cfg, None)

                print(f"队伍 '{team_name}' 已添加到队列")

            # 执行所有队伍的模拟（注意：这里可能存在环境共享问题）
            print(f"开始执行 {len(team_configs)} 个队伍的模拟...")
            print("警告：此测试可能存在环境共享问题，建议使用隔离测试方法")

            # 由于 execute_simulation_test 方法的限制，我们需要分批处理队伍
            # 该方法每次只处理 max_tasks 数量的任务，所以需要多次调用
            executed_sessions = []
            batch_size = 2  # 每批处理2个队伍以避免环境共享问题

            for i in range(0, len(team_configs), batch_size):
                batch_executed = await controller.execute_simulation_test(max_tasks=batch_size)
                executed_sessions.extend(batch_executed)

            # 验证结果
            assert len(executed_sessions) == len(team_configs), (
                f"期望执行 {len(team_configs)} 个队伍，实际执行了 {len(executed_sessions)} 个"
            )
            assert set(executed_sessions) == set(completed_sessions), "执行的会话ID与预期不匹配"

            # 验证所有会话状态
            for session_id in completed_sessions:
                updated_session = await db.get_session(session_id)
                assert updated_session is not None, f"会话 {session_id} 未找到"
                assert updated_session.status == "completed", (
                    f"会话 {session_id} 状态不是 completed"
                )

            print(f"所有 {len(team_configs)} 个队伍模拟均已完成")

        finally:
            # 清理数据库
            for session_id in completed_sessions:
                await db.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_async_queue_parallel_mode_execution(self):
        """使用队列系统测试并行模式执行。"""
        from zsim.api_src.services.database.session_db import get_session_db
        from zsim.models.session.session_run import ParallelCfg

        from ..test_simulator import TestSimulator

        test_sim = TestSimulator()
        common_cfg = test_sim.create_test_common_config()
        controller = SimController()

        # 创建简化的并行配置以减少任务数量
        session_run_config = test_sim.create_session_run_config("parallel")
        session_run_config.stop_tick = 100  # 减少执行时间
        session_run_config.parallel_config = ParallelCfg(
            enable=True,
            adjust_char=2,
            func="attr_curve",
            func_config=ParallelCfg.AttrCurveConfig(
                sc_range=(0, 1),  # 只测试2个值
                sc_list=["攻击力%"],  # 单个属性
                remove_equip_list=[],
            ),
        )

        session = Session(
            session_id="queue-test-parallel-session",
            create_time=datetime.now(),
            status="pending",
            session_run=session_run_config,
            session_result=None,
        )

        # 设置数据库
        db = await get_session_db()
        await db.add_session(session)

        parallel_session_ids = []  # 初始化在try块外面

        try:
            # 生成并行参数并放入队列
            args_iterator = controller.generate_parallel_args(session, session_run_config)
            args_list = list(args_iterator)

            # 为每个并行任务创建单独的会话并放入队列
            for i, sim_cfg in enumerate(args_list):
                parallel_session_id = f"queue-test-parallel-session-{i}"
                parallel_session = Session(
                    session_id=parallel_session_id,
                    create_time=datetime.now(),
                    status="pending",
                    session_run=session_run_config,
                    session_result=None,
                )
                parallel_session_ids.append(parallel_session_id)
                await db.add_session(parallel_session)
                await controller.put_into_queue(parallel_session_id, common_cfg, sim_cfg)

            # 执行并行任务
            completed_sessions = await controller.execute_simulation_test_parallel(
                session.session_id, parallel_count=len(args_list)
            )

            # 验证结果 - 应该有2个并行任务完成
            assert len(completed_sessions) == 2
            assert set(completed_sessions) == set(parallel_session_ids)

            # 验证所有并行会话状态
            for parallel_session_id in parallel_session_ids:
                updated_session = await db.get_session(parallel_session_id)
                assert updated_session is not None
                assert updated_session.status == "completed"

        finally:
            # 清理数据库
            await db.delete_session(session.session_id)
            for parallel_session_id in parallel_session_ids:
                await db.delete_session(parallel_session_id)

    @pytest.mark.asyncio
    async def test_async_queue_empty_handling(self):
        """测试队列为空时的处理。"""
        controller = SimController()

        # 执行空队列
        completed_sessions = await controller.execute_simulation_test(max_tasks=1)

        # 应该返回空列表
        assert len(completed_sessions) == 0

    @pytest.mark.asyncio
    async def test_async_queue_error_handling(self):
        """测试队列系统的错误处理。"""
        from ..test_simulator import TestSimulator

        test_sim = TestSimulator()
        controller = SimController()

        # 创建一个无效的会话（不存在于数据库中）
        common_cfg = test_sim.create_test_common_config()
        await controller.put_into_queue("non-existent-session", common_cfg, None)

        # 执行应该能处理错误而不崩溃
        completed_sessions = await controller.execute_simulation_test(max_tasks=1)

        # 应该返回空列表（因为会话不存在）
        assert len(completed_sessions) == 0
