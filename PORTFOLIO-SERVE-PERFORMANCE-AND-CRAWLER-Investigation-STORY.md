# Portfolio Server Performance & Crawler Investigation — The Story

## 1. The Problem Started With Storage Consumption

The initial problem was not actually the portfolio page itself.

The server was experiencing massive log growth, eventually consuming several gigabytes of storage. The investigation initially focused on the possibility that Nginx, Varnish, PHP-FPM, or crawler traffic was generating excessive logs.

The first important discovery was:

```text
/home/zawadulkawum/logs/nginx
2.5G
```

Inside it, several daily Nginx access logs were enormous:

```text
access.log-2026-08-14   382M
access.log-2026-08-13   382M
access.log-2026-08-12   382M
access.log-2026-08-10   374M
access.log-2026-08-09   371M
access.log-2026-08-08   304M
access.log-2026-08-11   275M
```

The immediate cleanup removed the old access logs and reduced the directory from approximately:

```text
2.5G
```

to:

```text
33M
```

Disk usage dropped from:

```text
15G used
```

to:

```text
12G used
```

So the immediate storage pressure was resolved.

But this exposed a bigger question:

> **Why was the server generating so much traffic and logging so many requests?**

---

# 2. The MySQL Warning Flood Was a Separate Major Problem

During the investigation, another serious source of storage consumption was discovered in MySQL.

The MySQL error log contained tens of thousands of:

```text
MY-013360
```

warnings related to the MySQL native password authentication deprecation.

The warning count was measured:

```text
44254
```

The important realization was that this wasn't a normal application error. It was a **repeated MySQL warning being generated at very high frequency**.

Instead of disabling all MySQL warnings, the specific warning was suppressed:

```sql
SET GLOBAL log_error_suppression_list = 'MY-013360';
SET PERSIST log_error_suppression_list = 'MY-013360';
```

The result was verified by measuring the warning count before and after a 30-second interval:

```text
Before: 44254
After:  44254
New MY-013360 warnings: 0
```

This was a successful fix because:

* MySQL warnings were not globally disabled.
* Only the problematic warning was suppressed.
* The setting was persisted.
* New occurrences stopped.

This became an important lesson:

> **When a log is flooding storage, identify the exact message/event responsible and suppress or fix that specific source rather than disabling logging globally.**

---

# 3. Attention Shifted to Crawler Traffic

Once the storage problem was controlled, the next concern was the enormous amount of crawler traffic hitting:

```text
/portfolio-details.php
```

The server was receiving requests from several crawlers, including:

* ClaudeBot
* GPTBot
* Applebot
* Meta external agent
* SERankingBacklinksBot

The traffic was particularly aggressive against the portfolio detail endpoint.

At one point, crawler traffic analysis showed approximately:

```text
Total portfolio requests:
143,071

Bot portfolio requests:
141,941
```

That means approximately **99.2% of the portfolio-detail requests were crawler traffic** during the measured period.

The crawler breakdown was:

```text
ClaudeBot                  112,115
GPTBot                      23,889
SERankingBacklinksBot        2,734
meta-externalagent           2,718
Applebot                       540
```

ClaudeBot alone accounted for more than 112,000 requests.

---

# 4. The Crawler Was Not Simply Repeating the Same URL

Initially, it would have been easy to assume that the crawler was repeatedly requesting one expensive URL.

The investigation showed something more interesting.

There were:

```text
141,910 unique full portfolio URLs
```

and:

```text
133,272 unique encrypted project IDs
```

At first, this looked alarming because the application was generating different encrypted IDs for the same project.

The encryption implementation used AES-128-CBC with a random IV:

```php
$iv = openssl_random_pseudo_bytes(16);
```

Therefore, encrypting the same project ID produced a different URL every time.

For example, the same underlying project could generate different encrypted values.

That meant Varnish could treat each generated URL as a different cache key.

---

# 5. The Encryption Design Became a Cache-Fragmentation Problem

The investigation then decrypted the crawler-generated IDs.

The result was very revealing:

```text
Unique encrypted IDs:       144,713
Successfully decrypted:          50
Unique actual project IDs:       50
```

All 50 decrypted IDs existed in the database.

So the crawler wasn't discovering 144,713 different projects.

It was essentially crawling the same **50 actual portfolio projects**, but the application's randomized AES encryption was producing a huge number of different URLs.

This created a classic cache-key fragmentation problem:

```text
Same project
    ↓
Random IV
    ↓
Different encrypted URL
    ↓
Different Varnish cache key
    ↓
Different cache object
```

The application was effectively making the URL unstable.

---

# 6. The Application's URL Generation Was Investigated

The source code was then traced.

The application generated portfolio URLs in:

```text
index.php
layouts/sidebar_portfolio.php
```

with calls such as:

```php
$crypt->encrypt($project['id'])
```

and:

```php
$crypt->encrypt($grouped_project['id'])
```

The detail page then decrypted:

```php
$_GET['project_id']
```

The encryption implementation used:

```php
AES-128-CBC
```

with a randomly generated IV.

That confirmed the root cause of the unstable URL generation.

---

# 7. Stable Portfolio IDs Were Introduced

The solution was to stop generating a different encrypted representation for the same project on every page render.

The portfolio URLs were changed to use a **stable project identifier** rather than randomized AES ciphertext.

The important architectural goal was:

```text
One project
    ↓
One stable URL identifier
    ↓
Same URL every time
    ↓
Same Varnish cache key
```

The actual numeric database ID was still not exposed directly.

The new representation remained an obscured/stable identifier rather than:

```text
project_id=45
```

This preserved the original requirement of not exposing the raw database ID while eliminating the randomized URL problem.

---

# 8. Varnish Was Then Investigated

After the URL changes, the next question was:

> **Is Varnish actually caching these portfolio pages?**

Initial response headers were confusing because the application/backend returned contradictory cache headers.

The response contained things such as:

```text
X-Cache-Lifetime: 604800
```

but also:

```text
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Expires: -1
```

This initially made the cache behavior look suspicious.

So instead of relying on response headers alone, a direct Varnish trace was performed.

---

# 9. The Varnish Trace Proved Caching Was Working

A unique test URL was generated.

The first request showed:

```text
BackendOpen
127.0.0.1:8080

BerespStatus 200

TTL RFC 604800
TTL VCL 604800

Storage malloc
```

That means:

```text
Client
 ↓
Varnish MISS
 ↓
Nginx/PHP backend
 ↓
Response
 ↓
Varnish stores object
```

Then the exact same URL was requested again.

The second request showed:

```text
Hit
```

and there was no second backend fetch.

Therefore:

```text
Request 1 → MISS → Backend → CACHE
Request 2 → HIT  → Varnish
```

This definitively established:

> **Varnish was functioning correctly.**

The cache lifetime was:

```text
604800 seconds
```

which is:

```text
7 days
```

---

# 10. A False Lead: Varnish Was Initially Suspected of Causing a 1-Second Delay

Another issue appeared during testing.

The first request was fast:

```text
~0.027 seconds
```

but subsequent requests were taking approximately:

```text
~0.99 seconds
```

At first, this could have looked like a Varnish or PHP problem.

A detailed timing analysis was performed.

DNS:

```text
~0.001 seconds
```

Connection:

```text
~0.001 seconds
```

TLS:

```text
~0.025–0.030 seconds
```

The important difference appeared in:

```text
TTFB
```

The pattern was:

```text
Request 1 → ~0.027s
Request 2 → ~0.990s
Request 3 → ~0.988s
Request 4 → ~0.986s
Request 5 → ~0.986s
Request 6 → ~0.990s
```

The approximately one-second delay was extremely consistent.

---

# 11. The Actual Cause of the 1-Second Delay Was Nginx Rate Limiting

The Nginx configuration contained:

```nginx
limit_req_zone $binary_remote_addr zone=limit:10m rate=1r/s;
```

and the portfolio endpoint had:

```nginx
limit_req zone=limit burst=10;
```

The crucial detail was that `nodelay` was **not** specified.

Therefore, Nginx was not immediately rejecting excess requests.

Instead, it was **delaying them** to enforce approximately one request per second.

This exactly matched the measurements.

The behavior was:

```text
Request 1
    ↓
Immediate

Request 2
    ↓
~1 second delay

Request 3
    ↓
~1 second delay

Request 4
    ↓
~1 second delay
```

This was finally confirmed with a dedicated six-request test:

```text
Request 1 → 0.027659s
Request 2 → 0.990452s
Request 3 → 0.988486s
Request 4 → 0.985888s
Request 5 → 0.986114s
Request 6 → 0.989594s
```

The pattern was conclusive.

---

# 12. The Rate Limiter Was Actually Doing Its Job

Although the one-second delay initially appeared to be a performance problem, it was actually a consequence of the deliberate protection mechanism.

The original goal was not to completely block crawlers.

The goal was:

> **Allow crawlers to crawl, but prevent aggressive clients from hammering the PHP application continuously.**

The configuration:

```nginx
limit_req zone=limit burst=10;
```

does exactly that, while avoiding the aggressive behavior of:

```nginx
limit_req zone=limit burst=10 nodelay;
```

The `nodelay` version caused a rapid sequence of requests to eventually receive:

```text
429
```

whereas the delayed version allows requests through more gently.

---

# 13. The Final Decision

The final design decision was:

### Keep rate limiting

Because a human user continuously clicking/reloading the same portfolio endpoint should also be protected from excessive request generation.

### Keep Varnish

Varnish is successfully caching the portfolio pages.

### Keep PHP-FPM

PHP-FPM was confirmed healthy and listening on:

```text
127.0.0.1:19005
```

### Keep the stable project URL

This eliminated the huge randomized URL/cache-key problem.

### Keep the crawler traffic controlled

The crawlers are allowed to crawl rather than being completely blocked.

### Accept the controlled delay

The approximately one-second delay for repeated requests from the same IP is the intended consequence of the `1r/s` rate limit.

---

# 14. Final Architecture

The system now effectively looks like this:

```text
                    Internet
                       │
                       ▼
                ┌──────────────┐
                │    Nginx     │
                │              │
                │ Rate limiting│
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │   Varnish    │
                │              │
                │ 7-day cache  │
                └──────┬───────┘
                       │
                 Cache MISS only
                       │
                       ▼
                ┌──────────────┐
                │ Nginx :8080  │
                │              │
                │ PHP-FPM      │
                └──────┬───────┘
                       │
                       ▼
                  ┌─────────┐
                  │ MySQL   │
                  └─────────┘
```

For a cached request:

```text
Client
  ↓
Nginx rate limiter
  ↓
Varnish HIT
  ↓
Response
```

PHP and MySQL are not involved.

For a cache miss:

```text
Client
  ↓
Nginx rate limiter
  ↓
Varnish MISS
  ↓
Nginx :8080
  ↓
PHP-FPM
  ↓
MySQL
  ↓
Varnish stores response
  ↓
Client
```

---

# 15. What Was Actually Fixed

The investigation ultimately uncovered **three different problems**, not one.

### Problem 1 — MySQL warning flood

**Cause:** Repeated `MY-013360` native-password deprecation warnings.

**Fix:**

```sql
SET PERSIST log_error_suppression_list = 'MY-013360';
```

**Result:** Warning generation stopped without disabling all MySQL warnings.

---

### Problem 2 — Massive crawler traffic + unstable portfolio URLs

**Cause:** Random-IV AES encryption generated a different URL for the same project.

**Result:**

```text
144,713 encrypted IDs
        ↓
50 actual projects
```

**Fix:** Stable, obscured project identifiers.

**Result:** Same project → same URL → same cache key.

---

### Problem 3 — Excessive repeated requests

**Cause:** Crawlers and potentially humans could continuously request the same endpoint.

**Fix:**

```nginx
limit_req zone=limit burst=10;
```

with:

```nginx
rate=1r/s
```

**Result:** Requests are throttled instead of allowing unlimited rapid requests.

The ~1-second delay for repeated requests is therefore **expected behavior**, not a Varnish/PHP/MySQL failure.

---

# 16. The Most Important Lessons

The investigation demonstrates several useful production-debugging principles.

### Don't assume the largest symptom has one cause

The storage problem involved multiple independent sources:

```text
Nginx access logs
+
MySQL warning flood
+
very high crawler traffic
```

They had to be investigated separately.

### Measure before changing architecture

Several components were suspected:

```text
Nginx
Varnish
PHP-FPM
MySQL
crawler traffic
URL generation
```

Each was tested independently.

### Don't trust cache headers alone

The application was sending contradictory cache headers.

The actual Varnish trace was more authoritative:

```text
MISS → Backend → Store
HIT → No Backend
```

### Randomized URLs are bad cache keys

If the same resource gets a different URL every time, a reverse proxy cannot effectively reuse the cache.

### Rate limiting and caching solve different problems

Varnish reduces backend work.

Rate limiting controls request frequency.

You need both when protecting a dynamic endpoint from aggressive clients.

### A delay can be a successful protection mechanism

The ~1-second response time was initially suspicious.

After measuring the request phases, it turned out to be exactly what the configured rate limiter was designed to produce.

---

# Final State

The original situation was roughly:

```text
Massive logs
      +
MySQL warning flood
      +
141K+ crawler requests
      +
randomized portfolio URLs
      +
cache fragmentation
      +
uncontrolled repeated requests
```

The resulting system is now:

```text
Stable portfolio URLs
        +
Varnish 7-day caching
        +
PHP-FPM functioning normally
        +
MySQL warning flood suppressed specifically
        +
Crawler traffic allowed
        +
Request-rate protection
        +
Human rapid-request protection
```

So the investigation ended not by simply "blocking the crawlers", but by making the portfolio endpoint **cache-friendly, rate-controlled, and resistant to excessive repeated requests while remaining publicly crawlable**.
