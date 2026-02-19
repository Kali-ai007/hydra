"""
PLUGIN AUTO-DISCOVERY
Scans plugins/ folder and registers any class that inherits from PluginBase.
Drop a new .py file in plugins/ and it's automatically available.
"""

import importlib
import pkgutil
from pathlib import Path
from plugins.base import PluginBase

_registry: dict[str, type[PluginBase]] = {}


def discover_plugins():
    plugins_dir = Path(__file__).parent
    for module_info in pkgutil.iter_modules([str(plugins_dir)]):
        if module_info.name in ("base", "__init__"):
            continue
        module = importlib.import_module(f"plugins.{module_info.name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type)
                    and issubclass(attr, PluginBase)
                    and attr is not PluginBase
                    and attr.name):
                _registry[attr.name] = attr


def get_plugin(name: str) -> PluginBase:
    if not _registry:
        discover_plugins()
    if name not in _registry:
        available = ", ".join(_registry.keys())
        raise ValueError(f"Unknown plugin: '{name}'. Available: {available}")
    return _registry[name]()


def list_plugins() -> dict[str, type[PluginBase]]:
    if not _registry:
        discover_plugins()
    return _registry.copy()
