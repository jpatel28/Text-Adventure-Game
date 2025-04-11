from dataclasses import dataclass, field
import random
from typing import Callable, Dict, Generic, List, TypeVar


T = TypeVar('T')

@dataclass
class DataStore(Generic[T]):
    data: Dict[str, T] = field(default_factory=dict)

    def add(self, key: str, value: T):
        self.data[key] = value

    def get(self, key: str) -> T:
        return self.data[key]
    
    def get_safe(self, key: str) -> T | None:
        return self.data.get(key, None)
    
    def has_get(self, key: str, func: Callable[[T], None]):
        if self.has(key):
            func(self.get(key))

    def has(self, key: str) -> bool:
        return key in self.data

    def get_all(self) -> Dict[str, T]:
        return self.data
    
    def remove(self, key: str):
        del self.data[key]

    def values(self) -> list[T]:
        return list(self.data.values())
    
    def keys(self) -> list[str]:
        return list(self.data.keys())
    
    def items(self) -> list[tuple[str, T]]:
        return list(self.data.items())

    def get_random(self, do_not_include: List[str] = []) -> T | None:
        if len(self.data) == 0:
            return None
        random_key_list = [key for key in self.data.keys() if key not in do_not_include]
        random_key = random.choice(random_key_list)
        return self.data[random_key]
    
@dataclass
class NamableDataStore(DataStore[T]):
    name_to_id: Dict[str, str] = field(default_factory=dict)

    def add(self, key: str, value: T):
        super().add(key, value)
        name = getattr(value, 'name', None)
        if name: self.name_to_id[name.lower()] = key

    def get_by_name(self, name: str) -> T | None:
        id = self.name_to_id.get(name.lower())
        if id: return self.get(id)
        return None

    def has_by_name(self, name: str) -> bool:
        return name.lower() in self.name_to_id

    def has_get_by_name(self, name: str, func: Callable[[T], None]):
        item = self.get_by_name(name.lower())
        if item is not None:
            func(item)

    def remove(self, key: str):
        name = getattr(self.get(key), 'name', None)
        super().remove(key)
        if name: self.name_to_id.pop(name.lower(), None)

    def remove_by_name(self, name: str):
        id = self.name_to_id.get(name.lower(), None)
        if id is not None: self.remove(id)