"""main.py — Survival Simulator Entry Point (Teacher Reference)."""

from models import get_initial_state
from modules import resources, weather, events, health

TOTAL_DAYS = 30


def run_day(day: int, state: dict) -> dict:
    """Run all modules for a single day. Return updated state."""
    print(f"=== Day {day} ===\n")

    state = resources.run(state)
    state = weather.run(state)
    state = events.run(state)
    state = health.run1(state)

    # Reset food each day — it doesn't carry over
    state["food"] = 0

    print()
    return state


def check_game_over(state: dict) -> bool:
    """Return True and print message if player cannot continue."""
    if state["energy"] <= 0:
        print("You are too exhausted to go on... GAME OVER")
        return True
    if state["health"] <= 0:
        print("You died from your injuries... GAME OVER")
        return True
    return False


def main():
    print("Welcome to Survival Simulator")
    print(f"You must survive {TOTAL_DAYS} days.\n")

    state = get_initial_state()

    for day in range(1, TOTAL_DAYS + 1):
        state = run_day(day, state)
        if check_game_over(state):
            exit()

    print("=== FINAL STATUS ===")
    print(f"Health: {state['health']}")
    print(f"Energy: {state['energy']}")
    print(f"Food:   {state['food']}")
    print("\nYou survived! Congratulations.")


if __name__ == "__main__":
    main()
