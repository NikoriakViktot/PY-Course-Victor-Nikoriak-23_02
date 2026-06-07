"""
domain/policies.py — Queue routing operations.

Each function operates on a plain list[dict] — JSON-serializable,
Dash-Store-compatible. The policy argument selects the data-structure behavior.

Educational mapping:
  FIFO     → collections.deque.popleft()  — O(1), serves oldest first
  LIFO     → list.pop()                   — O(1), serves newest first
  RANDOM   → list[random index].pop()     — O(1), random selection
  PRIORITY → sorted by distance ascending — O(n) insert, O(1) pop
"""
from __future__ import annotations

import bisect
import random as _rand
from typing import Optional


# ---------------------------------------------------------------------------
# Enqueue
# ---------------------------------------------------------------------------

def enqueue(queue: list, trip: dict, policy: str) -> None:
    """
    Insert trip into queue according to policy.

    FIFO / LIFO / RANDOM: simple append to the right.
    PRIORITY: insert in sorted position (distance ascending = short trips first).
    """
    if policy == "PRIORITY":
        # Binary search insertion maintains sorted order — O(n) due to list shift,
        # but list is bounded (max ~300 items) so constant is tiny.
        distances = [t["distance"] for t in queue]
        pos = bisect.bisect_left(distances, trip["distance"])
        queue.insert(pos, trip)
    else:
        queue.append(trip)  # FIFO / LIFO / RANDOM all append right


# ---------------------------------------------------------------------------
# Dequeue
# ---------------------------------------------------------------------------

def dequeue(queue: list, policy: str) -> Optional[dict]:
    """
    Remove and return the trip to process next, based on policy.

    Returns None if queue is empty.

    FIFO     → pop from index 0 (oldest item)
    LIFO     → pop from index -1 (newest item)
    RANDOM   → swap random item to end, then pop
    PRIORITY → pop from index 0 (lowest distance, pre-sorted by enqueue)
    """
    if not queue:
        return None

    if policy == "FIFO":
        return queue.pop(0)         # oldest at index 0

    if policy == "LIFO":
        return queue.pop()          # newest at end

    if policy == "RANDOM":
        idx = _rand.randrange(len(queue))
        queue[idx], queue[-1] = queue[-1], queue[idx]
        return queue.pop()

    if policy == "PRIORITY":
        return queue.pop(0)         # smallest distance at index 0 (sorted by enqueue)

    return queue.pop(0)             # fallback: FIFO


# ---------------------------------------------------------------------------
# Display order helpers
# ---------------------------------------------------------------------------

def queue_display_order(queue: list, policy: str) -> list[dict]:
    """
    Return queue items in the visual order that makes the policy obvious.

    FIFO:     oldest at top → newest at bottom (index 0 served first)
    LIFO:     newest at top → oldest at bottom (index -1 served first)
    RANDOM:   no meaningful order — return as-is
    PRIORITY: lowest distance at top (index 0 served first, already sorted)
    """
    if policy == "FIFO":
        return list(queue)          # [oldest, ..., newest]
    if policy == "LIFO":
        return list(reversed(queue))  # [newest, ..., oldest]
    if policy == "PRIORITY":
        return list(queue)          # already sorted ascending by distance
    return list(queue)              # RANDOM: no order guarantee
