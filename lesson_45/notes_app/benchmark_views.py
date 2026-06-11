import json
import re
import statistics
import time
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "alice"
PASSWORD = "alice12345"
REPEATS = 3

ENDPOINTS = [
    ("notes_list", "/"),
    ("group_notes", "/?view=group"),
    ("create_note_form", "/notes/create/"),
    ("note_detail", "/notes/1/"),
]


def get_csrf_token(html):
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    if match:
        return match.group(1)
    return ""


def login(session):
    login_url = f"{BASE_URL}/login/"
    response = session.get(login_url, timeout=10)
    response.raise_for_status()

    csrf_token = get_csrf_token(response.text) or session.cookies.get("csrftoken", "")
    response = session.post(
        login_url,
        data={
            "username": USERNAME,
            "password": PASSWORD,
            "csrfmiddlewaretoken": csrf_token,
        },
        headers={"Referer": login_url},
        timeout=10,
        allow_redirects=True,
    )
    response.raise_for_status()


def measure_endpoint(session, path):
    start = time.perf_counter()
    response = session.get(f"{BASE_URL}{path}", timeout=10)
    elapsed = time.perf_counter() - start
    return elapsed, response.status_code


def main():
    session = requests.Session()
    login(session)

    results = []
    total_start = time.perf_counter()

    for name, path in ENDPOINTS:
        measurements = []
        status_codes = []

        for _ in range(REPEATS):
            elapsed, status_code = measure_endpoint(session, path)
            measurements.append(elapsed)
            status_codes.append(status_code)

        results.append(
            {
                "view": name,
                "path": path,
                "status_codes": status_codes,
                "average_seconds": round(statistics.mean(measurements), 5),
                "min_seconds": round(min(measurements), 5),
                "max_seconds": round(max(measurements), 5),
            }
        )

    total_seconds = time.perf_counter() - total_start
    output = {
        "approach": "async views",
        "repeats_per_endpoint": REPEATS,
        "total_seconds": round(total_seconds, 5),
        "results": results,
        "conclusion": (
            "For this small local Django app the async version is not always faster. "
            "The requests are measured sequentially and most work is still database/template work. "
            "Async views are more useful when the view waits for external IO or handles many concurrent connections."
        ),
    }

    for item in results:
        print(
            f"{item['view']}: avg={item['average_seconds']}s, "
            f"min={item['min_seconds']}s, max={item['max_seconds']}s, "
            f"status={item['status_codes']}"
        )

    print(f"Total: {output['total_seconds']}s")
    print(output["conclusion"])

    result_path = Path(__file__).resolve().parent / "benchmark_results.json"
    result_path.write_text(json.dumps(output, indent=4), encoding="utf-8")
    print(f"Results saved to {result_path}")


if __name__ == "__main__":
    main()
