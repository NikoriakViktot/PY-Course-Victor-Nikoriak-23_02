import time
import os
import random

TILE_PROCESS_TIME = 0.25


def mp_process_tile(tile_data):
    tile_id, region, raster_data = tile_data
    time.sleep(TILE_PROCESS_TIME)
    flood_px = sum(1 for v in raster_data if v % 7 < 2)
    return {
        "tile_id": tile_id,
        "region": region,
        "flood_pixels": flood_px,
        "worker_pid": os.getpid()
    }


def worker_heavy_ipc(args):
    tile_id, huge_data = args
    time.sleep(0.05)
    return sum(huge_data[:10])


def worker_minimal_ipc(tile_id):
    time.sleep(0.05)
    return 45


def stage2_analyze(tile_info):
    time.sleep(TILE_PROCESS_TIME)
    flood_pct = abs(hash(tile_info["tile_id"])) % 30
    return {
        "tile_id": tile_info["tile_id"],
        "flood_pct": flood_pct,
        "worker_pid": os.getpid()
    }


def cpu_task(x):
    return sum(i * i for i in range(30_000))


def quick_task(tile_id):
    time.sleep(0.01)
    return f"done_{tile_id}"


def sar_analyze(tile_id):
    time.sleep(0.1)
    return {"tile": tile_id, "flood": abs(hash(tile_id)) % 30}
