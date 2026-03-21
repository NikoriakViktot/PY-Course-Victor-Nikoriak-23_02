"""
models.py — Shared game state definition
=========================================

This file defines the starting state of the game.
All modules receive this dictionary and return a modified version of it.

State fields:
  - health  (int): Player's health points. Game ends if it drops too low.
  - energy  (int): Player's energy level. GAME OVER if it reaches 0 or below.
  - food    (int): Amount of food collected. Affects health changes.

DO NOT modify this file. It is shared by all teams.
"""


def get_initial_state() -> dict:
    """Return the starting state for Day 1."""
    return {
        "health": 55,
        "energy": 30,
        "food": 0,
    }
