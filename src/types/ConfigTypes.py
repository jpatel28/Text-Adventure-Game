from typing import Dict, List, TypedDict

class ConfigRequirement(TypedDict):
    r_transitionRequirement: str
    stateKey: str

class ConfigExit(TypedDict):
    c_direction: str
    r_pointer: str
    requirement: ConfigRequirement

class ConfigArea(TypedDict):
    id: str
    r_groups: List[str]
    t_name: str
    t_enterDescription: str
    requireLight: bool
    exits: List[ConfigExit]
    items: List[str]
    isHidable: bool

class ConfigPlayerStartingState(TypedDict):
    r_area: str
    startingSanity: int

class ConfigPlayer(TypedDict):
    startingState: ConfigPlayerStartingState
    hidingSafety: int

class ConfigGeneralEnemy(TypedDict):
    t_encounterDialog: str
    damage: int

class ConfigGeneral(TypedDict):
    player: ConfigPlayer
    enemy: ConfigGeneralEnemy

class ConfigEventInfo(TypedDict):
    type: str
    data: str

class ConfigEvent(TypedDict):
    id: str
    trigger: ConfigEventInfo
    additional_conditions: List[ConfigEventInfo]
    affects: List[ConfigEventInfo]
    once: bool

class ConfigGroup(TypedDict):
    id: str
    t_name: str
    t_enterDescription: str
    t_exitDescription: str

class ConfigTransitionRequirement(TypedDict):
    id: str
    interactions: List[Dict[str, str]]
    fulfillCondition: Dict[str, List[str]]
    t_unfulfilled_description: str
    t_fulfilled_description: str
    isHiddenWhenUnfulfilled: bool

class ConfigItemInteraction(TypedDict):
    r_command: str
    t_response: str

class ConfigItem(TypedDict):
    id: str
    t_name: str
    t_description: str
    interactions: List[ConfigItemInteraction]
    isInventoryItem: bool
    isLightItem: bool
    lightCount: int
    isHidden: bool

class ConfigNPCDialogue(TypedDict):
    t_line: str
    t_trigger: str

class ConfigNPC(TypedDict):
    id: str
    t_name: str
    t_dialog: str
    r_area: str

class ConfigEnemy(TypedDict):
    id: str
    damage: int
    damageWithLight: int
    r_roaming_group: str

class ConfigCommand(TypedDict):
    id: str
    t_vocabularyList: str

class GameConfig(TypedDict):
    general: ConfigGeneral
    areas: List[ConfigArea]
    events: List[ConfigEvent]
    groups: List[ConfigGroup]
    transitionRequirements: List[ConfigTransitionRequirement]
    items: List[ConfigItem]
    npcs: List[ConfigNPC]
    enemies: List[ConfigEnemy]
    commands: List[ConfigCommand]