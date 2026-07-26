from dataclasses import dataclass, field
from typing import List

@dataclass
class PluginMetadata:
    plugin_id: str
    name: str
    version: str
    author: str
    category: str
    description: str
    entry_class: str
    dependencies: List[str] = field(default_factory=list)
    min_ecodep_version: str = "1.0.0"
