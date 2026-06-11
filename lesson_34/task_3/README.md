# Task 3

This script uses several threads to make requests to Pushshift API.

Example:

```text
Enter subreddit name: python
Enter comments limit: 30
Enter number of threads: 3
```

The result is saved to `comments.json` in chronological order.

If Pushshift API is unavailable, the script prints a request error instead of crashing.
