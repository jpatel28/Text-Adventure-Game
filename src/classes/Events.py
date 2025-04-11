from __future__ import annotations
from dataclasses import dataclass
from typing import List, TYPE_CHECKING
from src.classes.Areas import Area
if TYPE_CHECKING:
    from src.classes.World import World
from src.classes.Items import Item
from typing import Any
from src.singletons.GamePrint import gamePrint

@dataclass
class Information:
    type: str
    data: Any

class Condition(Information):
    def check_condition(self, world: World):
        match self.type:
            case 'inventory_has':
                return world.player.inventory.has(self.data)
            case 'area':
                return world.player.current_area.id == self.data

class Affect(Information):
    def apply_affect(self, world: World):
        match self.type:
            case 'end_game':
                world.running = False
            case 'dialog':
                gamePrint.abs_print(self.data)
            case 'add_item_to_inventory':
                world.player.inventory.add(self.data.id, self.data)
            case 'take_item':
                if world.player.current_area.items.has(self.data.id):
                    world.player.inventory.add(self.data.id, self.data)
                    world.player.current_area.items.remove(self.data.id)
            case 'add_item_to_current_area':
                world.player.current_area.items.add(self.data.id, self.data)
            case 'force_meet_condition_in_current_area':
                exit = world.player.current_area.exits.has(self.data)
                if exit:
                    target_exit = world.player.current_area.exits.get(self.data)
                    target_exit.transitionRequirement.force_fulfill()
                    gamePrint.abs_print(target_exit.transitionRequirement.fulfilled_description)

@dataclass
class Event:
    id: str
    trigger_data: Any
    additional_conditions: List[Condition]
    affects: List[Affect]
    once: bool
    has_run: bool = False

    def should_run(self):
        if not self.has_run:
            self.has_run = True
            return True
        return not self.once

    def check_conditions(self, target: Any, world: World):
        if not self.should_run():
            return False
        if target.__class__ != self.trigger_data.__class__:
            return False
        if target.id != self.trigger_data.id:
            return False
        for condition in self.additional_conditions:
            if not condition.check_condition(world):
                return False
        return True

    def apply_affects(self, world: World):
        for affect in self.affects:
            affect.apply_affect(world)

@dataclass
class TakeEvent(Event):
    trigger_data: Item

@dataclass
class EnterEvent(Event):
    trigger_data: Area

@dataclass
class ExamineEvent(Event):
    trigger_data: Item

@dataclass
class UseEvent(Event):
    trigger_data: Item

@dataclass
class ThrowEvent(Event):
    trigger_data: Item