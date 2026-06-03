import time
import os
import random


def process_chunk(data_chunk):
    return sum(data_chunk)


def heavy_computation(x):
    result = sum(i * i for i in range(x * 100_000))
    return (x, result, os.getpid())


def intense_math(x):
    return sum(i * i for i in range(50_000))


def process_image_chunk(args):
    chunk_id, size = args
    result = sum(i % 256 * i % 256 for i in range(size))
    return {"chunk_id": chunk_id, "checksum": result % 1_000_000, "worker_pid": os.getpid()}


def convert_grayscale(image_id):
    return sum(i * i for i in range(100_000))


def worker_task(x):
    return x ** 2
