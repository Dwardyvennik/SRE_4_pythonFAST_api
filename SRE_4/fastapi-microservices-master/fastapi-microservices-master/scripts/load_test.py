#!/usr/bin/env python3
import argparse
import concurrent.futures
import time
import urllib.error
import urllib.request


DEFAULT_URLS = [
    "http://localhost:8080/auth/health",
    "http://localhost:8080/users/health",
    "http://localhost:8080/products/health",
    "http://localhost:8080/orders/health",
    "http://localhost:8080/chat/health",
]


def request_once(url: str, timeout: float) -> tuple[bool, float, str]:
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            response.read()
            elapsed = time.perf_counter() - start
            return 200 <= response.status < 500, elapsed, str(response.status)
    except (urllib.error.URLError, TimeoutError) as exc:
        elapsed = time.perf_counter() - start
        return False, elapsed, exc.__class__.__name__


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple health endpoint load test for Assignment 6.")
    parser.add_argument("--requests", type=int, default=100, help="Total requests to send.")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent workers.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Request timeout in seconds.")
    args = parser.parse_args()

    if args.requests < 1:
        parser.error("--requests must be at least 1")
    if args.concurrency < 1:
        parser.error("--concurrency must be at least 1")

    urls = [DEFAULT_URLS[i % len(DEFAULT_URLS)] for i in range(args.requests)]
    started_at = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(executor.map(lambda url: request_once(url, args.timeout), urls))

    total_time = time.perf_counter() - started_at
    successes = sum(1 for ok, _, _ in results if ok)
    failures = len(results) - successes
    durations = [duration for _, duration, _ in results]
    avg_ms = (sum(durations) / len(durations)) * 1000
    max_ms = max(durations) * 1000
    rps = len(results) / total_time if total_time > 0 else 0

    print("Assignment 6 Load Test Results")
    print("============================================================")
    print(f"Total requests:      {len(results)}")
    print(f"Successful requests: {successes}")
    print(f"Failed requests:     {failures}")
    print(f"Concurrency:         {args.concurrency}")
    print(f"Total time:          {total_time:.2f}s")
    print(f"Requests/sec:        {rps:.2f}")
    print(f"Average latency:     {avg_ms:.2f} ms")
    print(f"Max latency:         {max_ms:.2f} ms")
    print("============================================================")

    if failures:
        print("Failed response summary:")
        summary: dict[str, int] = {}
        for ok, _, status in results:
            if not ok:
                summary[status] = summary.get(status, 0) + 1
        for status, count in sorted(summary.items()):
            print(f"  {status}: {count}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
