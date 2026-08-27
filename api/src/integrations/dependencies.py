"""Importaciones de compatibilidad para dependencias de integraciones.

Las dependencias de base de datos tienen una única implementación canónica en
``src.dependencies.database``.
"""

from src.dependencies.database import DatabaseDep, SessionDep

__all__ = ["DatabaseDep", "SessionDep"]
