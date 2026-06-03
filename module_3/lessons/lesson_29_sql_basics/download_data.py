import requests
import argparse
from pathlib import Path
import time

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)

MONTHS = 12
YEAR = 2019
MAX_RETRIES = 3


def download(url, path):
    if path.exists():
        print(f"⏭ SKIP (exists): {path.name}")
        return True

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"⬇ ({attempt}/{MAX_RETRIES}) {url}")

            with requests.get(url, stream=True, timeout=60) as r:
                if r.status_code != 200:
                    print(f"❌ HTTP {r.status_code}")
                    return False

                total = int(r.headers.get("content-length", 0))
                downloaded = 0

                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total:
                                percent = downloaded / total * 100
                                print(
                                    f"\r📦 {path.name} {percent:5.1f}%",
                                    end=""
                                )

            print(f"\n✅ DONE: {path.name}")
            return True

        except Exception as e:
            print(f"\n⚠️ ERROR: {e}")
            time.sleep(2)

    print(f"❌ FAILED: {path.name}")
    return False


def main(year, months):
    for month in range(1, months + 1):
        fname = f"yellow_tripdata_{year}-{month:02d}.parquet"
        url = f"{BASE_URL}/{fname}"

        year_dir = OUT_DIR / f"year={year}"
        month_dir = year_dir / f"month={month:02d}"
        month_dir.mkdir(parents=True, exist_ok=True)

        path = month_dir / fname

        success = download(url, path)

        if not success:
            print(f"⚠️ SKIPPED: {fname}")


if __name__ == "__main__":
    import argparse
    import sys

    if len(sys.argv) == 1:
        print("⚠️ No args → using defaults (2019, 12)")

    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--months", type=int, default=12)

    args = parser.parse_args()

    print(f"🚀 RUN: year={args.year}, months={args.months}")

    main(year=args.year, months=args.months)