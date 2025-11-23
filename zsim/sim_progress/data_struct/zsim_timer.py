from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator


class ZSimTimer:
    def __init__(self, sim_instance: "Simulator"):
        self.sim_instance: "Simulator" = sim_instance

    @property
    def tick(self) -> int:
        return self.sim_instance.tick

    def update_tick(self) -> None:
        self.sim_instance.tick += 1
