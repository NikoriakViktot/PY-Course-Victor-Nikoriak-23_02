from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROBOTS_URLS = [
    "https://www.wikipedia.org/robots.txt",
    "https://twitter.com/robots.txt",
    "https://www.reddit.com/robots.txt",
]


def get_domain_name(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc.replace("www.", "").replace(".", "_")


def download_robots_txt(url, output_folder):
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    with urlopen(request, timeout=10) as response:
        content = response.read().decode("utf-8", errors="ignore")

    file_name = f"{get_domain_name(url)}_robots.txt"
    file_path = output_folder / file_name
    file_path.write_text(content, encoding="utf-8")

    return file_path


def main():
    output_folder = Path(__file__).parent / "downloaded_robots"
    output_folder.mkdir(exist_ok=True)

    for url in ROBOTS_URLS:
        try:
            saved_file = download_robots_txt(url, output_folder)
            print(f"Saved: {saved_file}")
        except HTTPError as error:
            print(f"HTTP error while downloading {url}: {error}")
        except URLError as error:
            print(f"URL error while downloading {url}: {error}")
        except TimeoutError:
            print(f"Timeout while downloading {url}")


if __name__ == "__main__":
    main()
