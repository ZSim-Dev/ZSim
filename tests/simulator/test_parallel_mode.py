# -*- coding: utf-8 -*-
"""并行模式测试"""

import pytest
from pydantic import ValidationError
from zsim.api_src.services.sim_controller.sim_controller import SimController
from zsim.models.session.session_create import Session
from zsim.models.session.session_run import (
    ExecAttrCurveCfg,
    ExecWeaponCfg,
    ParallelCfg,
    SessionRun,
)


class TestParallelMode:
    """并行模式测试"""

    def test_parallel_args_generation_attr_curve(self):
        """Test async generation of attribute curve parallel arguments."""
        from ..test_simulator import TestSimulator
        test_sim = TestSimulator()

        controller = SimController()
        session = Session()
        session_run_config = test_sim.create_session_run_config("parallel")

        # Generate parallel arguments
        args_iterator = controller.generate_parallel_args(session, session_run_config)
        args_list = list(args_iterator)

        # Verify generated arguments
        assert len(args_list) == 12  # 2 attributes × 6 values each
        for arg in args_list:
            assert isinstance(arg, ExecAttrCurveCfg)
            assert arg.stop_tick == 1000
            assert arg.mode == "parallel"
            assert arg.func == "attr_curve"

    def test_parallel_args_generation_weapon(self):
        """Test async generation of weapon parallel arguments."""
        from ..test_simulator import TestSimulator
        test_sim = TestSimulator()

        controller = SimController()
        session = Session()

        # Create weapon parallel configuration
        session_run_config = SessionRun(
            stop_tick=1000,
            mode="parallel",
            common_config=test_sim.create_test_common_config(),
            parallel_config=ParallelCfg(
                enable=True,
                adjust_char=2,
                func="weapon",
                func_config=ParallelCfg.WeaponConfig(
                    weapon_list=[
                        ParallelCfg.WeaponConfig.SingleWeapon(name="青溟笼舍", level=5),
                        ParallelCfg.WeaponConfig.SingleWeapon(name="时流贤者", level=5),
                        ParallelCfg.WeaponConfig.SingleWeapon(name="飞鸟星梦", level=1),
                    ]
                ),
            ),
        )

        # Generate parallel arguments
        args_iterator = controller.generate_parallel_args(session, session_run_config)
        args_list = list(args_iterator)

        # Verify generated arguments
        assert len(args_list) == 3
        for arg in args_list:
            assert isinstance(arg, ExecWeaponCfg)
            assert arg.stop_tick == 1000
            assert arg.mode == "parallel"
            assert arg.func == "weapon"

    def test_parallel_args_generation_edge_cases(self):
        """Test parallel argument generation edge cases."""
        from ..test_simulator import TestSimulator
        test_sim = TestSimulator()

        controller = SimController()
        session = Session()

        # Test unknown attribute names
        session_run_config = SessionRun(
            stop_tick=1000,
            mode="parallel",
            common_config=test_sim.create_test_common_config(),
            parallel_config=ParallelCfg(
                enable=True,
                adjust_char=2,
                func="attr_curve",
                func_config=ParallelCfg.AttrCurveConfig(
                    sc_range=(0, 7),
                    sc_list=["unknown_stat"],  # Unknown attribute
                    remove_equip_list=[],
                ),
            ),
        )

        # Generate parallel arguments, should skip unknown attributes
        args_iterator = controller.generate_parallel_args(session, session_run_config)
        args_list = list(args_iterator)
        assert len(args_list) == 0  # Unknown attributes should be skipped

    def test_parallel_args_generation_invalid_mode(self):
        """Test parallel argument generation with invalid mode."""
        from ..test_simulator import TestSimulator
        test_sim = TestSimulator()

        controller = SimController()
        session = Session()
        session_run_config = test_sim.create_session_run_config("normal")  # Normal mode

        # Generate parallel arguments, should return empty
        args_iterator = controller.generate_parallel_args(session, session_run_config)
        args_list = list(args_iterator)
        assert len(args_list) == 0

    def test_parallel_args_generation_missing_config(self):
        """Test parallel argument generation with missing configuration."""
        from ..test_simulator import TestSimulator
        test_sim = TestSimulator()

        with pytest.raises(ValidationError) as excinfo:
            SessionRun(
                stop_tick=1000,
                mode="parallel",
                common_config=test_sim.create_test_common_config(),
                # Missing parallel_config
            )
        assert "并行模式下，parallel_config 不能为空" in str(excinfo.value)