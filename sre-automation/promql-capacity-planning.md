# Capacity Planning PromQL Queries

These queries support Assignment 6 capacity planning by connecting system load to concrete Prometheus metrics.

## CPU Usage Per Container

```promql
rate(container_cpu_usage_seconds_total[1m])
```

Shows CPU seconds consumed per second for each container. Use this to identify CPU-bound services and decide when to increase CPU limits or scale replicas.

## Memory Usage Per Container

```promql
container_memory_usage_bytes
```

Shows current memory usage per container. Use this to identify memory-heavy services and plan memory reservations or larger instances.

## Request Rate / RPS

```promql
sum(rate(http_requests_total[1m]))
```

Shows total application requests per second across the microservices. Use this to compare traffic growth against CPU, memory, and latency trends.

## Error Rate

```promql
sum(rate(http_requests_total{status=~"5.."}[1m]))
```

Shows server-side errors per second. Use this to detect overload, dependency failures, or application regressions during increased demand.

## Service Availability

```promql
up
```

Shows whether Prometheus can scrape each target. Use this for uptime tracking and to detect service or monitoring target failures.

## Container Restart Frequency

```promql
changes(container_start_time_seconds[10m])
```

Shows whether containers restarted in the last 10 minutes. Use this to detect crash loops, unstable deployments, or resource exhaustion.
