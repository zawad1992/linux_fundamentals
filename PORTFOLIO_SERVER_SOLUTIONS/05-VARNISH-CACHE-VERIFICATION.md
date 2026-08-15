# Verifying Varnish Caching for Dynamic Portfolio Pages

## Problem

The portfolio response contained apparently conflicting cache headers.

Backend-related headers included:

``` text
Cache-Control: public, max-age=604800, s-maxage=604800
```

while the final response also contained:

``` text
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Expires: -1
```

Therefore, response headers alone were insufficient to determine whether
Varnish was actually caching the page.

## Solution: Trace Varnish Directly

Generate a unique URL and trace only that URL:

``` bash
TOKEN="TRACE_$(date +%s%N)"
URL="https://zawadulkawum.com/portfolio-details.php?project_id=${TOKEN}"

rm -f /tmp/portfolio-varnish.log

timeout 15 varnishlog -g request -q "ReqURL ~ \"${TOKEN}\"" > /tmp/portfolio-varnish.log 2>&1 &
VPID=$!

sleep 2

curl -sS -o /dev/null "$URL"
sleep 2
curl -sS -o /dev/null "$URL"

wait $VPID 2>/dev/null || true

grep -E 'ReqMethod|ReqURL|Hit|Miss|Backend|BerespStatus|TTL|Fetch|RespStatus' /tmp/portfolio-varnish.log
```

## Expected Behavior

Request 1:

``` text
Request
→ Varnish MISS
→ Backend 127.0.0.1:8080
→ 200
→ Store
```

Request 2:

``` text
Request
→ Varnish HIT
→ 200
```

The investigation confirmed this exact pattern.

The cache TTL was:

``` text
604800 seconds
```

which equals seven days.

## Counter Check

``` bash
varnishstat -1 | grep -E 'MAIN.cache_(hit|miss|hitpass|hitmiss)'
```

A HIT should increase:

``` text
MAIN.cache_hit
```

A backend fetch should increase:

``` text
MAIN.cache_miss
```

## Why It Matters

Without caching:

``` text
Visitor
→ Nginx
→ PHP-FPM
→ MySQL
```

With a cache HIT:

``` text
Visitor
→ Varnish
→ Cached HTML
```

For a portfolio page that changes infrequently, the second path is
substantially cheaper.

## Lesson

When cache headers are contradictory, inspect the cache layer directly.
`varnishlog` provides the evidence needed to distinguish MISS, backend
fetch, cache storage, and HIT behavior.
