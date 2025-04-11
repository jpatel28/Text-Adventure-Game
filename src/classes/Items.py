from dataclasses import dataclass, field

@dataclass
class Item:
    id: str
    name: str
    description: str
    isInventoryItem: bool = True
    is_light_item: bool = False
    light_count: int = 0
    is_hidden: bool = False

@dataclass
class Inventory:
    items: list[Item] = field(default_factory=list)
 
    def add_item(self, item: Item):
        self.items.append(item)