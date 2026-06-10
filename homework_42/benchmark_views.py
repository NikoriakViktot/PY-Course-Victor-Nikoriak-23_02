"""Sequential HTTP benchmark for homework_42 Django views.

Run the Django server first, for example:
    python manage.py runserver 127.0.0.1:8000

Then run this script from the homework_42 directory:
    python benchmark_views.py --base-url http://127.0.0.1:8000 --username admin --password <password>
"""

from __future__ import annotations

import argparse
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

import requests


@dataclass(frozen=True)
class EndpointResult:
    name: str
    path: str
    count: int
    average_seconds: float
    min_seconds: float
    max_seconds: float
    total_seconds: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure sequential response times for notes app views."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument(
        "--label",
        default="benchmark",
        help="Label shown in the optional markdown report, e.g. sync or async.",
    )
    parser.add_argument(
        "--report-path",
        help="Optional path to write a markdown report with the measured results.",
    )
    return parser.parse_args()


def extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    if not match:
        raise RuntimeError("Could not find CSRF token on the login page.")
    return match.group(1)


def login(
    session: requests.Session, base_url: str, username: str, password: str
) -> None:
    login_url = f"{base_url}/login/"
    response = session.get(login_url)
    response.raise_for_status()
    csrf_token = extract_csrf_token(response.text)

    response = session.post(
        login_url,
        data={
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": csrf_token,
        },
        headers={"Referer": login_url},
        allow_redirects=True,
    )
    response.raise_for_status()
    if "/login/" in response.url:
        raise RuntimeError("Login failed; check --username and --password.")


def discover_endpoints(
    session: requests.Session, base_url: str
) -> list[tuple[str, str]]:
    endpoints = [
        ("notes_list", "/"),
        ("note_create", "/create/"),
        ("categories_list", "/categories/"),
        ("category_create", "/categories/create/"),
        ("api_notes", "/api/notes/"),
    ]

    categories_response = session.get(f"{base_url}/categories/")
    categories_response.raise_for_status()
    category_match = re.search(
        r'href="(/categories/\d+/edit)"', categories_response.text
    )
    if category_match:
        endpoints.append(("category_update", category_match.group(1)))

    response = session.get(f"{base_url}/api/notes/")
    response.raise_for_status()
    notes = response.json().get("notes", [])
    if notes:
        endpoints.append(("api_note_detail", f"/api/notes/{notes[0]['id']}/"))
        endpoints.append(("note_detail", f"/{notes[0]['id']}/"))

    return endpoints


def measure_endpoint(
    session: requests.Session, base_url: str, name: str, path: str, repeats: int
) -> EndpointResult:
    durations = []
    for _ in range(repeats):
        started_at = time.perf_counter()
        response = session.get(f"{base_url}{path}")
        duration = time.perf_counter() - started_at
        response.raise_for_status()
        durations.append(duration)

    return EndpointResult(
        name=name,
        path=path,
        count=repeats,
        average_seconds=statistics.mean(durations),
        min_seconds=min(durations),
        max_seconds=max(durations),
        total_seconds=sum(durations),
    )


def print_results(results: list[EndpointResult]) -> None:
    print("view,path,count,avg_seconds,min_seconds,max_seconds,total_seconds")
    for result in results:
        print(
            f"{result.name},{result.path},{result.count},"
            f"{result.average_seconds:.4f},{result.min_seconds:.4f},"
            f"{result.max_seconds:.4f},{result.total_seconds:.4f}"
        )
    print(f"TOTAL_SECONDS,{sum(result.total_seconds for result in results):.4f}")


def build_markdown_report(
    label: str, base_url: str, results: list[EndpointResult]
) -> str:
    total_seconds = sum(result.total_seconds for result in results)
    lines = [
        f"# Benchmark report: {label}",
        "",
        "## Command",
        "",
        f"Base URL: `{base_url}`",
        "",
        "## Results",
        "",
        "| View | Endpoint | Requests | Avg, s | Min, s | Max, s | Total, s |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            f"| `{result.name}` | `{result.path}` | {result.count} | "
            f"{result.average_seconds:.4f} | {result.min_seconds:.4f} | "
            f"{result.max_seconds:.4f} | {result.total_seconds:.4f} |"
        )
    lines.extend(
        [
            f"| **Total** | — | **{sum(result.count for result in results)}** | — | — | — | **{total_seconds:.4f}** |",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown_report(
    path: str, label: str, base_url: str, results: list[EndpointResult]
) -> None:
    report_path = Path(path)
    report_path.write_text(
        build_markdown_report(label, base_url, results), encoding="utf-8"
    )
    print(f"Report saved to {report_path}")


def main() -> None:
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    with requests.Session() as session:
        login(session, base_url, args.username, args.password)
        endpoints = discover_endpoints(session, base_url)
        results = [
            measure_endpoint(session, base_url, name, path, args.repeats)
            for name, path in endpoints
        ]

    print_results(results)
    if args.report_path:
        write_markdown_report(args.report_path, args.label, base_url, results)


if __name__ == "__main__":
    main()