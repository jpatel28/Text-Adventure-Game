import os
from typing import List, Any
from dataclasses import dataclass
from src.classes.DataStores import DataStore, NamableDataStore
from src.classes.Areas import Area, Group, Exit
from src.classes.Items import Item
from src.classes.Characters import Character, NPC, Player, Enemy
from src.classes.Events import Event
from src.singletons.Locale import locale as loc
from src.singletons.GamePrint import gamePrint
import random

@dataclass
class World:
    def __init__(self):
        self.data_areas = NamableDataStore[Area]()
        self.data_groups = NamableDataStore[Group]()
        self.data_items = NamableDataStore[Item]()
        self.data_exits = DataStore[Exit]()
        self.data_inputs = DataStore[str]()
        self.data_characters: List[Character] = []
        self.data_triggers = DataStore[List[Event]]()
        self.player: Player # Reference to player in data_characters
        self.running = True

    def append_character(self, character: Character):
        if isinstance(character, Player):
            self.player = character
            self.data_characters.append(self.player)
            self.player.current_area.characters.append(self.player)
        else:
            self.data_characters.append(character)
            character.current_area.characters.append(character)

    def update_brightness(self, should_print: bool = True):
        if not self.player.current_area.require_light:
            gamePrint.brightness = 100
        elif self.player.lantern_count == 0:
            gamePrint.brightness = 50
            if should_print:
                gamePrint.abs_print(loc.t("inputResponses.tooDark"))
        else:
            gamePrint.brightness = 100
    
    def handle_input(self, action: str):

        if action == "":
            gamePrint.abs_print(loc.t("inputResponses.standingStill"), end=" ")
            return None

        parts = action.strip().lower().split(" ")

        cmd = None
        target = None
        cmd_group = None

        for i in range(len(parts)):
            parsed_word = " ".join(parts[:i+1])
            if self.data_inputs.has(parsed_word):
                cmd = parsed_word
                target = " ".join(parts[i+1:])
                cmd_group = self.data_inputs.get(parsed_word)

        if cmd is None or target is None or cmd_group is None:
            gamePrint.abs_print(loc.t("inputResponses.commandUnknown"), end=" ")
            return None
        
        self.match_input_command(cmd_group, cmd, target)
    
    def match_input_command(self, cmd_group: str, cmd: str, target: str):

        if cmd_group == "exit":
            self.running = False
            return None
        
        if cmd_group == "pass":
            gamePrint.abs_print(loc.t("inputResponses.standingStill"), end=" ")
            return None
        
        if cmd_group == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            return None
        
        if cmd_group == "dict":
            gamePrint.abs_print("Available commands:")
            for cmd in self.data_inputs.get_all().keys():
                gamePrint.abs_print(f"- {cmd}")
            return None
        
        if cmd_group == "loc":
            gamePrint.print(self.player.current_area.printable_enter_description, end=" ")
            return None
        
        if cmd_group == "inventory":
            inventory_items = self.player.inventory.values()
            if not inventory_items:
                gamePrint.abs_print(loc.t("inputResponses.nothingInInventory"), end=" ")
                return None
            
            gamePrint.abs_print(loc.t("inputResponses.playerItemList", items=loc.conjunction_list([item.name for item in inventory_items])), end=" ")
            return None
        
        if cmd_group == "hide":
            if self.player.current_area.is_hidable:
                self.player.is_hiding = True
                gamePrint.abs_print(loc.t("inputResponses.quicklyHide"), end=" ")
            else:
                gamePrint.abs_print(loc.t("inputResponses.cannotHide"), end=" ")
            return None
        
        if cmd_group == "throw":
            if self.player.inventory.has_by_name(target):
                item = self.player.inventory.get_by_name(target)
                if item is not None:
                    self.player.inventory.remove_by_name(target)
                    self.player.current_area.items.add(item.id, item)
                    gamePrint.abs_print(loc.t("inputResponses.throwItem", item=target), end=" ")
                    self.check_event_trigger('throw', item)
                else:
                    gamePrint.abs_print(loc.t("inputResponses.inventoryFail", item=target), end=" ")
            return None
        
        if cmd_group == "go":
            currArea = self.player.current_area
            if currArea.exits.has(target) and (currArea.exits.get(target).transitionRequirement.is_met or not currArea.exits.get(target).transitionRequirement.is_hidden_when_unfulfilled):
                curr_exit = currArea.exits.get(target)
                can_passthrough = curr_exit.passthrough(currArea)
                if can_passthrough:
                    self.player.current_area = can_passthrough
                    self.update_brightness()
                    gamePrint.print(can_passthrough.printable_enter_description, end=" ")
                    self.check_event_trigger('go', can_passthrough)
                else:
                    gamePrint.abs_print(curr_exit.transitionRequirement.unfufilled_description, end=" ")
            else:
                gamePrint.abs_print(loc.t("inputResponses.cannotGo", dir=target), end=" ")
            return None
        
        if cmd_group == "examine":
            if self.player.current_area.items.has_by_name(target):
                item = self.player.current_area.items.get_by_name(target)
                if item is not None:
                    gamePrint.abs_print(item.description, end=" ")
                    self.check_event_trigger('examine', item)
            elif self.player.inventory.has_by_name(target):
                item = self.player.inventory.get_by_name(target)
                if item is not None:
                    gamePrint.abs_print(item.description, end=" ")
                    self.check_event_trigger('examine', item)
            else:
                gamePrint.abs_print(loc.t("inputResponses.cannotExamine"), end=" ")
            return None
        
        if cmd_group == "talk":
            if not any(isinstance(char, NPC) for char in self.player.current_area.characters):
                gamePrint.abs_print(loc.t("inputResponses.noOneToTalkTo"), end=" ")
                return None
            for char in self.player.current_area.characters:
                if char.name.lower() == target.lower():
                    if isinstance(char, NPC):
                        gamePrint.abs_print(char.dialog)
                    else:
                        gamePrint.abs_print(loc.t("inputResponses.dontWantToTalk", name=char.name), end=" ")
            return None
        
        if cmd_group == "take":
            if self.player.current_area.items.has_by_name(target):
                item = self.player.current_area.items.get_by_name(target)
                if item is not None and item.isInventoryItem:
                    self.player.inventory.add(item.id, item)
                    self.player.current_area.items.remove_by_name(target)
                    gamePrint.abs_print(loc.t("inputResponses.takeSuccess", item=target), end=" ")
                    self.check_event_trigger('take', item)
                else:
                    gamePrint.abs_print(loc.t("inputResponses.takeNotAllowed", item=target), end=" ")
                    
            else:
                gamePrint.abs_print(loc.t("inputResponses.takeDoesNotExist", item=target), end=" ")
            return None
        
        if cmd_group == "use":
            if self.player.inventory.has_by_name(target):
                item = self.player.inventory.get_by_name(target)
                if item is not None:
                    if item.is_light_item:
                        self.player.lantern_count = item.light_count
                        gamePrint.abs_print(loc.t("inputResponses.useSuccess", item=target), end=" ")
                    else:
                        is_used = self.player.current_area.use_item(item)
                        is_used = True if self.check_event_trigger('use', item) else is_used
                        if not is_used: gamePrint.abs_print(loc.t("inputResponses.useFail"), end=" ")
            else:
                gamePrint.abs_print(loc.t("inputResponses.inventoryFail", item=target), end=" ")
            return None
        
        gamePrint.abs_print(loc.t("inputResponses.commandNotExist", cmd_group=cmd_group), end=" ")

    def check_event_trigger(self, trigger: str, target: Any) -> bool:
        is_used = False
        if self.data_triggers.has(trigger):
            for event in self.data_triggers.get(trigger):
                if event.check_conditions(target, self):
                    is_used = True
                    event.apply_affects(self)
        return is_used

    def handle_pre_input(self):
        # If there are enemies in adjacent rooms to the player, print a message
        has_enemies_adjacent = False
        enemies_directions: List[str] = []
        for exit in self.player.current_area.exits.values():
            dest = exit.find_dest(self.player.current_area)
            for char in dest.characters:
                if isinstance(char, Enemy):
                    has_enemies_adjacent = True
                    enemies_directions.append(dest.name)
                    break
            if has_enemies_adjacent: break
        if has_enemies_adjacent:
            gamePrint.abs_print(loc.t("inputResponses.enemiesAdjacent", directions=loc.conjunction_list(enemies_directions)), end=" ")

        if self.player.is_hiding:
            gamePrint.abs_print(loc.t("inputResponses.safeToLeaveHiding"), end=" ")
        self.player.is_hiding = False

        gamePrint.abs_print("")

    def handle_after_input(self):
        # If player health is 0, end the game
        if self.player.health == 0:
            self.running = False
            gamePrint.abs_print(loc.t("inputResponses.playerHealthZero"), end=" ")
            return None
        
        self.player.deplete_lantern()
        self.update_brightness(False)

        self_defense_words = loc.t("mechanics.selfDefenseWords")

        # Check for enemies in room
        enemies_in_room = [char for char in self.player.current_area.characters if isinstance(char, Enemy)]
        if enemies_in_room:
            for enemy in enemies_in_room:
                if self.player.is_hiding:
                    gamePrint.abs_print(loc.t("inputResponses.hidingSafe"), end=" ")
                else:
                    if self.player.inventory.has_by_name('knife'):
                        def prompt_defense_words():
                            words = random.sample(self_defense_words, 3)
                            formatted_words = loc.conjunction_list(words)
                            gamePrint.abs_print(f"{loc.t("inputResponses.attackedCanDefend")} \r\n{formatted_words}", end="\r\n> ")
            
                            def input_with_timeout(timeout):
                                import sys, select
                                ready, _, _ = select.select([sys.stdin], [], [], timeout)
                                if ready:
                                    return sys.stdin.readline()
                                else:
                                    raise TimeoutError

                            user_input = ""
                            try:
                                user_input = input_with_timeout(10).strip().lower()
                            except TimeoutError:
                                gamePrint.abs_print(" ")
                                gamePrint.abs_print(loc.t("inputResponses.attackedDefenseTooSlow"), end=" ")
                                return False

                            if all(word in user_input for word in words) or user_input == formatted_words:
                                gamePrint.abs_print(" ")
                                return True
                            else:
                                gamePrint.abs_print(loc.t("inputResponses.attackedDefenseMistake"), end=" ")
                                return False

                        if not prompt_defense_words():
                            self.player.take_damage(enemy)
                            gamePrint.abs_print(loc.t("inputResponses.attackedDefenseFailure"), end=" ")
                        else:
                            gamePrint.abs_print(loc.t("inputResponses.attackedDefenseSuccess"), end=" ")
                    else:
                        self.player.take_damage(enemy)
                        gamePrint.abs_print(loc.t("inputResponses.attackedRegular"), end=" ")
                while True:
                    new_area = self.data_areas.get_random([npc.current_area.id for npc in self.data_characters if isinstance(npc, NPC)])
                    if new_area and new_area != self.player.current_area: 
                        enemy.current_area = new_area
                        break
        else:
            # Move enemies to adjacent rooms
            for enemy in self.data_characters:
                if isinstance(enemy, Enemy):
                    adjacent_exit = enemy.current_area.exits.get_random([npc.current_area.id for npc in self.data_characters if isinstance(npc, NPC)])
                    if adjacent_exit:
                        new_area = adjacent_exit.find_dest(enemy.current_area)
                        enemy.current_area = new_area

        gamePrint.abs_print("")
