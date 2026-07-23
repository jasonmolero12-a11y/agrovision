"""Compatibilidade local para Django 5.0 em Python 3.14."""

from django.template.context import BaseContext


def _base_context_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.__dict__.update(self.__dict__)
    duplicate.dicts = self.dicts[:]
    return duplicate


def aplicar_patch_contexto():
    BaseContext.__copy__ = _base_context_copy


aplicar_patch_contexto()
