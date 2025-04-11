from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from src.classes.Characters import Character, Player
from src.classes.Items import Item
from src.classes.DataStores import NamableDataStore
from src.types.ConfigTypes import ConfigArea
from src.singletons.GamePrint import gamePrint
from src.singletons.Locale import locale as loc

@dataclass
class TransitionRequirement:
    conditions: Dict[str, bool] = field(default_factory=dict) # str is item id
    unfufilled_description: str = ""
    fulfilled_description: str = ""
    is_hidden_when_unfulfilled: bool = False
    
    @property
    def is_met(self) -> bool:
        return all(self.conditions.values())
    
    def check(self, item: Item) -> bool:
        if item.id in self.conditions:
            self.conditions[item.id] = True
            return True
        return False
    
    def force_fulfill(self):
        for key in self.conditions.keys():
            self.conditions[key] = True

    def add_condition(self, item_id: str):
        self.conditions[item_id] = False

@dataclass
class Exit:
    direction: str
    area: Area
    areas: Tuple[Area, Area]
    transitionRequirement: TransitionRequirement = field(default_factory=TransitionRequirement)

    def find_dest(self, current_area: Area) -> Area:
        return self.areas[0] if current_area == self.areas[1] else self.areas[1]
    
    def passthrough(self, current_area: Area) -> Area | None:
        if self.transitionRequirement.is_met:
            return self.find_dest(current_area)
        return None

@dataclass
class Area:
    id: str
    name: str
    enter_description: str
    config: ConfigArea
    require_light: bool
    is_hidable: bool
    exits: NamableDataStore[Exit] = field(default_factory=NamableDataStore[Exit])
    items: NamableDataStore[Item] = field(default_factory=NamableDataStore[Item])
    characters: List[Character] = field(default_factory=list[Character])
    groups: List[Group] = field(default_factory=list)

    @property
    def printable_enter_description(self) -> str:
        printable = self.enter_description + " "
        items = loc.conjunction_list([f"{item.name}" for item in self.items.values() if not item.is_hidden])
        if items:
            printable += loc.t("inputResponses.areaListItems", items=items)
        exits = loc.conjunction_list([loc.t("inputResponses.dirToDest", dir=dir, dest=target.find_dest(self).name) for dir, target in self.exits.items() if target.transitionRequirement.is_met or not target.transitionRequirement.is_hidden_when_unfulfilled])
        characters = loc.conjunction_list([f"{char.name}" for char in self.characters if not isinstance(char, Player)])
        if characters:
            printable += loc.t("inputResponses.areaListItems", items=characters)
        if exits:
            printable += loc.t("inputResponses.areaListExits", exits=exits)
        if self.is_hidable:
            printable += " " + loc.t("inputResponses.areaHidable")
        return printable
    
    def use_item(self, item: Item) -> bool:
        is_used = False
        for exit in self.exits.values():
            valid_item = exit.transitionRequirement.check(item)
            if valid_item: 
                is_used = True
                gamePrint.abs_print(exit.transitionRequirement.fulfilled_description)
        return is_used

@dataclass
class Group:
    id: str
    name: str
    enter_description: str
    exit_description: str
    areas: NamableDataStore[Area] = field(default_factory=NamableDataStore[Area])