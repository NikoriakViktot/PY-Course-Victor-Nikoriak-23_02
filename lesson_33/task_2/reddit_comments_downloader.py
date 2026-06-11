import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://api.pushshift.io/reddit/comment/search/"


def download_comments(subreddit, limit):
    params = {
        "subreddit": subreddit,
        "size": limit,
        "sort_type": "created_utc",
        "sort": "asc",
    }
    url = f"{API_URL}?{urlencode(params)}"

    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    with urlopen(request, timeout=20) as response:
        response_data = response.read().decode("utf-8", errors="ignore")

    data = json.loads(response_data)
    comments = data.get("data", [])

    return sorted(comments, key=lambda comment: comment.get("created_utc", 0))


def save_comments(comments, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(comments, file, indent=4, ensure_ascii=False)


def main():
    subreddit = input("Enter subreddit name: ").strip()
    limit = int(input("Enter comments limit: ").strip())

    output_file = Path(__file__).parent / "comments.json"

    try:
        comments = download_comments(subreddit, limit)
        save_comments(comments, output_file)
        print(f"Saved {len(comments)} comments to {output_file}")
    except ValueError:
        print("Comments limit must be a number")
    except HTTPError as error:
        print(f"HTTP error: {error}")
    except URLError as error:
        print(f"URL error: {error}")
    except TimeoutError:
        print("Request timeout")
    except json.JSONDecodeError:
        print("Could not decode API response")


if __name__ == "__main__":
    main()
