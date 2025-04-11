from __future__ import annotations
import py_hot_reload
import os
import json
import sys
from typing import Dict, Any
from src.types.ConfigTypes import GameConfig, ConfigTransitionRequirement
from src.classes.Areas import Area, Exit
from src.classes.Characters import Enemy, NPC, Player
from src.classes.Items import Item
from src.classes.Areas import Group, Area, TransitionRequirement, Exit
from src.classes.World import World
from src.classes.Events import Event, ThrowEvent, EnterEvent, TakeEvent, ExamineEvent, UseEvent, Affect, Condition
from src.singletons.Locale import locale as loc
from src.singletons.GamePrint import gamePrint

class Game:
    player: Player
    world: World

    def load_data(self):
        game_config: GameConfig | None = None
        with open('./game.config.json', 'r') as f:
            game_config = json.load(f)

        if game_config is None:
            gamePrint.abs_print("Could not load game configuration.")
            sys.exit(1)
            return None

        self.world = World()
        
        # Load items
        for item in game_config['items']:
            item_obj = Item(
                id=item['id'],
                name=loc.t(item['t_name']), 
                description=loc.t(item['t_description']),
                isInventoryItem=item['isInventoryItem'],
                is_light_item=item['isLightItem'],
            )
            if 'lightCount' in item:
                item_obj.light_count = item['lightCount']
            if 'isHidden' in item:
                item_obj.is_hidden = item['isHidden']
            self.world.data_items.add(item['id'], item_obj)

        # Load Groups
        for group in game_config['groups']:
            self.world.data_groups.add(group['id'], Group(
                id=group['id'],
                name=loc.t(group['t_name']),
                enter_description=loc.t(group['t_enterDescription']),
                exit_description=loc.t(group['t_exitDescription']),
            ))

        # Load areas
        for area in game_config['areas']:
            self.world.data_areas.add(area['id'], Area(
                id=area['id'],
                name=loc.t(area['t_name']),
                enter_description=loc.t(area['t_enterDescription']),
                config=area,
                require_light=area['requireLight'],
                is_hidable=area['isHidable']
            ))
            for group_id in area['r_groups']:
                self.world.data_groups.has_get(group_id, lambda group: group.areas.add(area['id'], self.world.data_areas.get(area['id'])))
                self.world.data_areas.get(area['id']).groups.append(self.world.data_groups.get(group_id))

        # Load exits and items for areas
        exit_registration_tracker: Dict[str, Exit] = {}
        temp_transition_requirements: Dict[str, ConfigTransitionRequirement] = {}
        for transition in game_config['transitionRequirements']:
            temp_transition_requirements[transition['id']] = transition

        for config_area in game_config['areas']:
            curr_area = self.world.data_areas.get(config_area['id'])
            if curr_area:
                if ('exits' in config_area):
                    for exit in config_area['exits']:
                        their_id = exit['r_pointer']
                        me_them_id = f"{curr_area.id}_to_{their_id}"
                        if me_them_id not in exit_registration_tracker:
                            # them_me
                            transition = TransitionRequirement()
                            if 'requirement' in exit:
                                req_id = exit['requirement']['r_transitionRequirement']
                                req_det = temp_transition_requirements.get(req_id)
                                if req_det:
                                    transition.unfufilled_description = loc.t(req_det['t_unfulfilled_description'])
                                    transition.fulfilled_description = loc.t(req_det['t_fulfilled_description'])
                                    req_items = req_det['fulfillCondition']['r_items']
                                    for item in req_items:
                                        transition.add_condition(item)
                                    if 'isHiddenWhenUnfulfilled' in req_det:
                                        transition.is_hidden_when_unfulfilled = req_det['isHiddenWhenUnfulfilled']
                            
                            our_exit = Exit(
                                direction=exit['c_direction'],
                                area=self.world.data_areas.get(their_id),
                                areas=(curr_area, self.world.data_areas.get(their_id)),
                                transitionRequirement=transition
                            )

                            them_me_id = f"{their_id}_to_{curr_area.id}"
                            exit_registration_tracker[them_me_id] = our_exit
                            curr_area.exits.add(exit['c_direction'], our_exit)
                        else:
                            # me_them
                            their_exit = exit_registration_tracker[me_them_id]
                            their_area = their_exit.find_dest(curr_area)
                            if their_area.config:
                                if 'requirement' in their_area.config:
                                    req_id = their_area.config['requirement']['r_transitionRequirement']
                                    req_det = temp_transition_requirements.get(req_id)
                                    if req_det:
                                        req_items = req_det['fulfillCondition']['r_items']
                                        for item in req_items:
                                            their_exit.transitionRequirement.add_condition(item)
                            curr_area.exits.add(exit['c_direction'], their_exit)
                            exit_registration_tracker.pop(me_them_id, None)
                            
                if ('items' in config_area):
                    for item in config_area['items']:
                        self.world.data_items.has_get(item, lambda item: curr_area.items.add(item.id, item))

        # Load Commands
        for cmd_group in loc.t('commands'):
            for cmd in loc.t(f"commands.{cmd_group}"):
                self.world.data_inputs.add(cmd, cmd_group)
        
        del exit_registration_tracker
        del temp_transition_requirements

        # Load Player
        starting_area = self.world.data_areas.get_safe(game_config['general']['player']['startingState']['r_area'])
        if starting_area is None:
            gamePrint.abs_print("Could not find starting area.")
            sys.exit(1)
            return None
        self.player = Player(
            name="Evelyn",
            current_area=starting_area,
            hiding_safety=game_config['general']['player']['hidingSafety']
        )
        self.world.append_character(self.player)

        # Load NPCs
        for npc in game_config['npcs']:
            npc_area = self.world.data_areas.get_safe(npc['r_area'])
            if npc_area:
                self.world.append_character(NPC(
                    name=loc.t(npc['t_name']),
                    dialog=loc.t(npc['t_dialog']),
                    current_area=npc_area
                ))

        # Load Enemies
        for enemy in game_config['enemies']:
            roaming_group = self.world.data_groups.get_safe(enemy['r_roaming_group'])
            if roaming_group:
                random_area = roaming_group.areas.get_random([npc.current_area.id for npc in self.world.data_characters if isinstance(npc, NPC)])
                if random_area:
                    self.world.append_character(Enemy(
                        name=enemy['id'],
                        current_area=random_area,
                        damage=enemy['damage'],
                        damage_with_light=enemy['damageWithLight']
                    ))

        # Load Events
        for event in game_config['events']:
            trigger_type = event['trigger']['type']
            command_group: str | None = None
            to_add: Event | None = None

            if trigger_type == 'enter':
                command_group = 'go'
                to_add = EnterEvent(
                    id=event['id'],
                    trigger_data=self.world.data_areas.get(event['trigger']['data']),
                    additional_conditions=[],
                    affects=[],
                    once=event['once']
                )
            elif trigger_type == 'take':
                command_group = 'take'
                to_add = TakeEvent(
                    id=event['id'],
                    trigger_data=self.world.data_items.get(event['trigger']['data']),
                    additional_conditions=[],
                    affects=[],
                    once=event['once']
                )
            elif trigger_type == 'examine':
                command_group = 'examine'
                to_add = ExamineEvent(
                    id=event['id'],
                    trigger_data=self.world.data_items.get(event['trigger']['data']),
                    additional_conditions=[],
                    affects=[],
                    once=event['once']
                )
            elif trigger_type == 'use':
                command_group = 'use'
                to_add = UseEvent(
                    id=event['id'],
                    trigger_data=self.world.data_items.get(event['trigger']['data']),
                    additional_conditions=[],
                    affects=[],
                    once=event['once']
                )
            elif trigger_type == 'throw':
                command_group = 'throw'
                to_add = ThrowEvent(
                    id=event['id'],
                    trigger_data=self.world.data_items.get(event['trigger']['data']),
                    additional_conditions=[],
                    affects=[],
                    once=event['once']
                )

            if command_group is None or to_add is None:
                continue
                
            if 'additional_conditions' in event:
                for condition in event['additional_conditions']:
                    to_add.additional_conditions.append(Condition(
                        type=condition['type'],
                        data=condition['data']
                    ))

            if 'affects' in event:
                for affect in event['affects']:
                    parsed_data: Any = None
                    if affect['type'] == 'dialog':
                        parsed_data = loc.t(affect['data'])
                    elif affect['type'] == 'add_item_to_inventory':
                        parsed_data = self.world.data_items.get(affect['data'])
                    elif affect['type'] == 'take_item':
                        parsed_data = self.world.data_items.get(affect['data'])
                    elif affect['type'] == 'add_item_to_current_area':
                        parsed_data = self.world.data_items.get(affect['data'])
                    else:
                        parsed_data = affect['data']

                    to_add.affects.append(Affect(
                        type=affect['type'],
                        data=parsed_data
                    ))

            if self.world.data_triggers.has(command_group):
                self.world.data_triggers.get(command_group).append(to_add)
                continue

            self.world.data_triggers.add(command_group, [to_add])

    def ask_language(self):
        supported_langs = loc.data_locale.keys()
        gamePrint.abs_print(f"What language would you like to play in? ({', '.join(supported_langs) })")
        lang = input()
        loc.set_locale(lang)
        os.system('cls' if os.name == 'nt' else 'clear')

    def run(self):
        gamePrint.abs_print(loc.t("general.opening"), end="\r\n\r\n")
        gamePrint.print(self.player.current_area.printable_enter_description)
        self.world.handle_after_input()
        while self.world.running:
            self.world.handle_pre_input()
            gamePrint.abs_print(f"\r\n{loc.t("inputResponses.waitingInput")}\r\n> ", end="")
            action = input()
            gamePrint.abs_print("")
            self.world.handle_input(action)
            self.world.handle_after_input()
        gamePrint.abs_print(loc.t("inputResponses.thankYou"))
        exit(0)

    def mode(self):
        # Development mode
        if "dev" in sys.argv:
            gamePrint.abs_print("Running in development mode.")
            self.player.current_area = self.world.data_areas.get("church")
            self.player.inventory.add("knife", self.world.data_items.get("knife"))
            self.player.inventory.add("libraryKey", self.world.data_items.get("libraryKey"))
            self.player.inventory.add("mansionKey", self.world.data_items.get("mansionKey"))
            self.player.inventory.add("cleansingGadget", self.world.data_items.get("cleansingGadget"))

def main():
    game = Game()
    game.ask_language()
    game.load_data()
    game.mode()
    game.run()

if __name__ == "__main__":
    if "clear" in sys.argv:
        os.system('cls' if os.name == 'nt' else 'clear')
    if "dev" in sys.argv:
        py_hot_reload.run_with_reloader(main)
    else:
        main()