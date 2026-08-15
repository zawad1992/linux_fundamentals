# Nginx Rate Limiting: Throttle Rapid Requests Without Immediate 429s

## Problem

The portfolio endpoint was receiving a very high volume of crawler
requests.

The endpoint was protected with:

``` nginx
limit_req zone=limit burst=10;
```

The design choice was whether to add `nodelay`.

## With `nodelay`

``` nginx
limit_req zone=limit burst=10 nodelay;
```

Requests inside the burst are handled immediately. Once the burst is
exhausted, excess requests can receive:

``` text
429 Too Many Requests
```

A rapid test produced a pattern like:

``` text
200
200
200
200
200
200
429
429
429
```

This is useful when rapid excess traffic should be rejected
aggressively.

## Without `nodelay`

``` nginx
limit_req zone=limit burst=10;
```

Excess requests are delayed according to the configured request rate
instead of being immediately rejected.

With a rate around one request per second, repeated requests showed
approximately:

``` text
Request 1 → 0.027s
Request 2 → 0.990s
Request 3 → 0.988s
Request 4 → 0.986s
Request 5 → 0.986s
Request 6 → 0.990s
```

Every request still returned:

``` text
HTTP 200
```

## Why This Was Selected

The server is a personal portfolio.

The objective was not:

> Block anyone who clicks or reloads repeatedly.

The objective was:

> Slow continuous rapid requests while allowing normal visitors and
> legitimate crawlers to continue.

Therefore:

``` nginx
limit_req zone=limit burst=10;
```

was preferable to:

``` nginx
limit_req zone=limit burst=10 nodelay;
```

## Validate the Behavior

``` bash
URL="https://zawadulkawum.com/portfolio-details.php?project_id=1"

for i in {1..6}; do
    curl -sS -o /dev/null     -w "Request $i | HTTP=%{http_code} | TTFB=%{time_starttransfer}s | Total=%{time_total}s\n"     "$URL"
done
```

## Rule of Thumb

Use:

``` nginx
limit_req zone=limit burst=10 nodelay;
```

when the priority is rapid rejection.

Use:

``` nginx
limit_req zone=limit burst=10;
```

when the priority is throttling.

For a personal portfolio where availability should be preserved while
continuous rapid requests are controlled, throttling is usually the more
appropriate behavior.

## Performance Investigation

The approximately one-second delay was verified to be rate limiting
rather than PHP-FPM or network latency.

Break down a request:

``` bash
curl -sS -o /dev/null -w '\nDNS=%{time_namelookup}s\nConnect=%{time_connect}s\nTLS=%{time_appconnect}s\nTTFB=%{time_starttransfer}s\nTotal=%{time_total}s\n' "https://zawadulkawum.com/portfolio-details.php?project_id=1"
```

The direct backend test was approximately 0.003 seconds, while repeated
public requests showed approximately one-second TTFB.

This matched the configured request throttling behavior.

## Lesson

Rate limiting is not only about returning `429`. It can also be used as
a traffic-shaping mechanism.

For expensive dynamic endpoints, targeted throttling can protect
PHP/MySQL without making the entire website inaccessible to normal
users.
