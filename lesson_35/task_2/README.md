Task 2

This script downloads comments from Pushshift API and saves them to comments.json in chronological order.

It uses:
1. concurrent.futures.ThreadPoolExecutor
2. multiprocessing.Pool

Run:
python lesson_35/task_2/reddit_comments_concurrent.py

Example input:
Enter subreddit name: python
Enter comments limit: 40
Enter workers count: 4
Enter how many last days to search: 30

Note: If Pushshift API is unavailable, the script prints the request error instead of crashing.
