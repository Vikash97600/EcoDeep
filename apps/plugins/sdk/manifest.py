from dataclasses import dataclass, field


@dataclass
class PluginMetadata:
    plugin_id: str
    name: str
    version: str
    author: str
    category: str
    description: str
    entry_class: str
    dependencies: list[str] = field(default_factory=list)
    min_ecodep_version: str = "1.0.0"
