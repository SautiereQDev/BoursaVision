"""
Package principal du domaine métier.

Ce package regroupe les entités, agrégats, value objects et services
liés au domaine financier de l'application.
"""

from . import entities, events, value_objects

__all__ = [
    "entities",
    "events",
    "value_objects",
]
