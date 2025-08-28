import gc
import time
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from zsim.define import (
    APL_MODE,
    APL_PATH,
    ENEMY_ADJUST_ID,
    ENEMY_DIFFICULTY,
    ENEMY_INDEX_ID,
)
from zsim.sim_progress.Buff import (
    BuffLoadLoop,
    buff_add,
)
from zsim.sim_progress.Character.skill_class import Skill
from zsim.sim_progress.data_struct import ActionStack, Decibelmanager, ListenerManger
from zsim.sim_progress.Enemy import Enemy
from zsim.sim_progress.Load import DamageEventJudge, SkillEventSplit
from zsim.sim_progress.Preload import PreloadClass
from zsim.sim_progress.RandomNumberGenerator import RNG
from zsim.sim_progress.Report import start_report_threads, stop_report_threads
from zsim.sim_progress.ScheduledEvent import ScheduledEvent as ScE
from zsim.sim_progress.Update.Update_Buff import update_time_related_effect
from zsim.simulator.dataclasses import (
    CharacterData,
    GlobalStats,
    InitData,
    LoadData,
    ScheduleData,
)

from zsim.simulator.dataclasses import SimCfg

if TYPE_CHECKING:
    from zsim.models.session.session_run import CommonCfg


class Confirmation(BaseModel):
    session_id: str
    status: str
    timestamp: int
    sim_cfg: "SimCfg | None" = None


Confirmation.model_rebuild()


class Simulator:
    """模拟器类。

    ## 模拟器的初始状态，包括但不限于：

    ### 常规变量

    - 模拟器时间刻度（tick）每秒为60ticks
    - 暴击种子（crit_seed）为RNG模块使用，未来接入随机功能时用于复现测试
    - 初始化数据（init_data）包含数据库读到的大部分数据
    - 角色数据（char_data）包含角色的实例

    ### 参与tick逻辑的内部对象

    - 加载数据（load_data）
    - 调度数据（schedule_data）
    - 全局统计数据（global_stats）
    - 技能列表（skills）
    - 预加载类（preload）
    - 游戏状态（game_state）包含前面的大多数数据
    - 喧响管理器（decibel_manager）
    - 监听器管理器（listener_manager）

    ### 其他实例

    - 随机数生成器实例（rng_instance）
    - 并行模式标志（in_parallel_mode）
    - 模拟配置，用于控制并行模式下，模拟器作为子进程的参数（sim_cfg）
    """

    tick: int
    crit_seed: int
    init_data: InitData
    enemy: Enemy
    char_data: CharacterData
    load_data: LoadData
    schedule_data: ScheduleData
    global_stats: GlobalStats
    skills: list[Skill]
    preload: PreloadClass
    game_state: dict[str, Any]
    decibel_manager: Decibelmanager
    listener_manager: ListenerManger
    rng_instance: RNG
    in_parallel_mode: bool
    sim_cfg: "SimCfg | None"

    def cli_init_simulator(self, sim_cfg: "SimCfg | None"):
        """CLI和WebUI的旧方法，重置模拟器实例为初始状态。"""
        self.__detect_parallel_mode(sim_cfg)
        self.init_data = InitData(common_cfg=None, sim_cfg=sim_cfg)
        self.enemy = Enemy(
            index_id=ENEMY_INDEX_ID,
            adjustment_id=ENEMY_ADJUST_ID,
            difficulty=ENEMY_DIFFICULTY,
            sim_instance=self,
        )
        self.__init_data_struct(sim_cfg)
        start_report_threads(sim_cfg)  # 启动线程以处理日志和结果写入

    def api_init_simulator(self, common_cfg: "CommonCfg", sim_cfg: "SimCfg | None"):
        """api初始化模拟器实例的接口。"""
        self.__detect_parallel_mode(sim_cfg)
        self.init_data = InitData(common_cfg=common_cfg, sim_cfg=sim_cfg)
        self.enemy = Enemy(
            index_id=common_cfg.enemy_config.index_id,
            adjustment_id=int(common_cfg.enemy_config.adjustment_id),
            difficulty=common_cfg.enemy_config.difficulty,
            sim_instance=self,
        )
        self.__init_data_struct(sim_cfg, api_apl_path=common_cfg.apl_path)
        start_report_threads(
            sim_cfg, session_id=common_cfg.session_id
        )  # 启动线程以处理日志和结果写入

    def api_run_simulator(
        self, common_cfg: "CommonCfg", sim_cfg: "SimCfg | None", stop_tick: int | None = None
    ) -> Confirmation:
        """api运行模拟器实例的接口。

        Args:
            common_cfg: 通用配置对象，包含角色和敌人配置
            sim_cfg: 模拟配置对象，包含模拟的详细参数
            stop_tick: 停止模拟的帧数，默认为10800帧（3分钟）

        Returns:
            包含运行确认信息的字典
        """
        if stop_tick is None:
            stop_tick = 10800
        self.api_init_simulator(common_cfg, sim_cfg)
        self.main_loop(stop_tick=stop_tick, sim_cfg=sim_cfg, use_api=True)

        # 返回确认信息
        confirmation = Confirmation(
            session_id=common_cfg.session_id,
            status="completed",
            timestamp=int(time.time()),
            sim_cfg=sim_cfg,
        )

        return confirmation

    def __detect_parallel_mode(self, sim_cfg):
        if sim_cfg is not None:
            self.in_parallel_mode = True
            self.sim_cfg = sim_cfg
        else:
            self.in_parallel_mode = False
            self.sim_cfg = None

    def __init_data_struct(self, sim_cfg, *, api_apl_path: str | None = None):
        self.tick = 0
        self.crit_seed = 0
        self.char_data = CharacterData(self.init_data, sim_cfg, sim_instance=self)
        self.load_data = LoadData(
            name_box=self.init_data.name_box,
            Judge_list_set=self.init_data.Judge_list_set,
            weapon_dict=self.init_data.weapon_dict,
            cinema_dict=self.init_data.cinema_dict,
            action_stack=ActionStack(),
            char_obj_dict=self.char_data.char_obj_dict,
            sim_instance=self,
        )
        self.schedule_data = ScheduleData(
            enemy=self.enemy,
            char_obj_list=self.char_data.char_obj_list,
            sim_instance=self,
        )
        if self.schedule_data.enemy.sim_instance is None:
            self.schedule_data.enemy.sim_instance = self
        self.global_stats = GlobalStats(name_box=self.init_data.name_box, sim_instance=self)
        skills = [char.skill_object for char in self.char_data.char_obj_list]
        self.preload = PreloadClass(
            skills,
            load_data=self.load_data,
            apl_path=APL_PATH if api_apl_path is None else api_apl_path,
            sim_instance=self,
        )
        self.game_state: dict[str, Any] = {
            "tick": self.tick,
            "init_data": self.init_data,
            "char_data": self.char_data,
            "load_data": self.load_data,
            "schedule_data": self.schedule_data,
            "global_stats": self.global_stats,
            "preload": self.preload,
        }
        self.decibel_manager = Decibelmanager(self)
        self.listener_manager = ListenerManger(self)
        self.rng_instance = RNG(sim_instance=self)
        # 监听器的初始化需要整个Simulator实例，因此在这里进行初始化
        self.load_data.buff_0_manager.initialize_buff_listener()

    def main_loop(
        self, stop_tick: int = 10800, *, sim_cfg: "SimCfg | None" = None, use_api: bool = False
    ):
        """
        CLI和WebUI使用此方法直接从文件读取数据，运行模拟器。
        传入的值仅为stop_tick和并行模拟配置。
        """
        if not use_api:
            self.cli_init_simulator(sim_cfg)
        while True:
            # Tick Update
            # report_to_log(f"[Update] Tick step to {tick}")
            update_time_related_effect(
                self.global_stats.DYNAMIC_BUFF_DICT,
                self.tick,
                self.load_data.exist_buff_dict,
                self.schedule_data.enemy,
            )

            # Preload
            self.preload.do_preload(
                self.tick,
                self.schedule_data.enemy,
                self.init_data.name_box,
                self.char_data,
            )
            preload_list = self.preload.preload_data.preload_action

            if stop_tick is None:
                if not APL_MODE and self.preload.preload_data.skills_queue.head is None:
                    # Old Sequence mode left, not compatible with APL mode now
                    stop_tick = self.tick + 120
            elif self.tick >= stop_tick:
                break

            # Load
            if preload_list:
                SkillEventSplit(
                    preload_list,
                    self.load_data.load_mission_dict,
                    self.load_data.name_dict,
                    self.tick,
                    self.load_data.action_stack,
                )
            DamageEventJudge(
                self.tick,
                self.load_data.load_mission_dict,
                self.schedule_data.enemy,
                self.schedule_data.event_list,
                self.char_data.char_obj_list,
            )
            BuffLoadLoop(
                self.tick,
                self.load_data.load_mission_dict,
                self.load_data.exist_buff_dict,
                self.init_data.name_box,
                self.load_data.LOADING_BUFF_DICT,
                self.load_data.all_name_order_box,
                sim_instance=self,
            )
            buff_add(
                self.tick,
                self.load_data.LOADING_BUFF_DICT,
                self.global_stats.DYNAMIC_BUFF_DICT,
                self.schedule_data.enemy,
            )

            # Load.DamageEventJudge(tick, load_data.load_mission_dict, schedule_data.enemy, schedule_data.event_list, char_data.char_obj_list)
            # ScheduledEvent
            sce = ScE(
                self.global_stats.DYNAMIC_BUFF_DICT,
                self.schedule_data,
                self.tick,
                self.load_data.exist_buff_dict,
                self.load_data.action_stack,
                sim_instance=self,
            )
            sce.event_start()
            # self.tick += 1
            # if sce.data.processed_times > 0:
            # print(f"\r{self.tick}", end="")
            if self.schedule_data.processed_state_this_tick and self.tick != 0:
                minutes = self.tick // 3600
                rest_seconds = self.tick % 3600 / 60
                if rest_seconds == 60:
                    rest_seconds = 0
                    minutes += 1
                print()
                print(
                    f"▲ ▲ ▲第{self.tick}帧({minutes:.0f}分 {rest_seconds:02.0f}秒)发生的事件如上▲ ▲ ▲\n ",
                    end="",
                )
                print("---------------------------------------------")
            self.tick += 1
            self.schedule_data.reset_processed_event()
            if self.tick % 500 == 0 and self.tick != 0:
                gc.collect()
        stop_report_threads()

    def __deepcopy__(self, memo):
        return self
