from __future__ import annotations
from dataclasses import dataclass
import random
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.classes.Areas import Area
from src.classes.DataStores import NamableDataStore
from src.classes.Items import Item
from src.singletons.GamePrint import gamePrint
from src.singletons.Locale import locale as loc

class Character:
    __current_area: Area
    name: str
    
    @property
    def current_area(self):
        return self.__current_area

    @current_area.setter
    def current_area(self, value: Area):
        self.__current_area.characters.remove(self)
        self.__current_area = value
        self.__current_area.characters.append(self)

    def __init__(self, name: str, current_area: Area):
        self.__current_area = current_area
        self.name = name

    def move_adjacent(self, direction: str | None):
        if direction is None:
            # Move to a random adjacent room
            exit = random.choice(self.current_area.exits.values())
            self.current_area = exit.find_dest(self.current_area)
        else:
            if self.current_area.exits.has(direction):
                exit = self.current_area.exits.get(direction)
                self.current_area = exit.find_dest(self.current_area)
            else:
                gamePrint.abs_print(loc.t("inputResponses.cannotGo", dir=direction))

class Player(Character):
    max_health = 100
    __health = max_health

    def __init__(self, name: str, current_area: Area, hiding_safety: int):
        super().__init__(name, current_area)
        self.inventory = NamableDataStore[Item]()
        self.lantern_count = 0
        self.is_hiding = False
        self.hiding_safety = hiding_safety

    @property
    def health(self):
        return self.__health

    @health.setter
    def health(self, value):
        self.__health = value if value > 0 else 0
        if self.__health == 0:
            gamePrint.abs_print(loc.t("inputResponses.playerDied"))
        else:
            gamePrint.abs_print(loc.t("inputResponses.healthStatus", health=self.__health), end=" ")

    def take_damage(self, enemy: Enemy):
        
        final_dmg = 0
        if not self.current_area.require_light:
            final_dmg = enemy.damage_with_light
        elif self.lantern_count > 0:
            final_dmg = enemy.damage_with_light
        else:
            final_dmg = enemy.damage

        if self.is_hiding and self.current_area.is_hidable:
            if random.random() > self.hiding_safety / 100:
                final_dmg = 0
                gamePrint.abs_print(loc.t("inputResponses.enemyAttackPlayerHidden"))
            else:
                gamePrint.abs_print(loc.t("inputResponses.enemyAttackPlayerFound"))
        else:
            gamePrint.abs_print(loc.t("inputResponses.attackedRegular"))
        self.health -= final_dmg
        self.is_hiding = False

    def deplete_lantern(self):
        if self.lantern_count == 1:
            gamePrint.abs_print(loc.t("inputResponses.lightDepelted"))
            self.lantern_count = 0
        elif self.lantern_count > 1:
            self.lantern_count -= 1

@dataclass
class NPC(Character):
    def __init__(self, name: str, dialog: str, current_area: Area):
        super().__init__(name, current_area)
        self.dialog = dialog

@dataclass
class Enemy(Character):
    damage: int
    damage_with_light: int

    def __init__(self, name: str, current_area: Area, damage: int, damage_with_light: int):
        super().__init__(name, current_area)
        self.damage = damage
        self.damage_with_light = damage_with_light