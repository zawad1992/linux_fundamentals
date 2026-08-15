# Portfolio Server Investigation — Complete Chronological Story

## 1. The problem started with the server disk almost full

The first symptom was straightforward: **the server's disk space was almost completely consumed**.

At that point, there was no assumption that the cause was the portfolio application, crawlers, Varnish, or Nginx traffic. The first task was simply to determine **what was consuming the disk**.

The investigation therefore started at the filesystem level, looking for unusually large files and directories.

That led to the first major discovery.

---

## 2. MySQL was consuming a large amount of disk through its logs

The investigation found that **MySQL logs had grown significantly**.

The important part was not simply that MySQL had a large log file. The log was growing because MySQL was repeatedly writing the same warning.

The relevant warning was:

```text
MY-013360
```

The warning was related to MySQL's native password authentication mechanism being deprecated.

The important observation was that this warning was being generated **thousands of times**, rather than being a one-time startup warning.

The warning count reached:

```text
44,254
```

This explained why the MySQL log had become a significant disk consumer.

### Fix

Instead of disabling MySQL logging completely, the specific warning was suppressed:

```sql
SET GLOBAL log_error_suppression_list = 'MY-013360';
SET PERSIST log_error_suppression_list = 'MY-013360';
```

The result was verified afterward.

The warning stopped being generated:

```text
New MY-013360 warnings: 0
```

So the first major issue was resolved:

```text
MySQL warning flood
        ↓
Huge MySQL log
        ↓
Disk consumption
        ↓
Suppress MY-013360
        ↓
Warning generation stopped
```

---

# 3. After MySQL was investigated, Nginx logs became the next major disk consumer

The disk investigation did not stop after fixing MySQL.

The filesystem was checked again to identify the other large consumers.

Another major source was discovered under:

```text
/home/zawadulkawum/logs/nginx
```

The Nginx log directory had grown to approximately:

```text
2.5 GB
```

The individual access-log files were extremely large, with several historical daily logs reaching hundreds of megabytes.

Examples included files around:

```text
382 MB
382 MB
382 MB
374 MB
371 MB
304 MB
275 MB
```

This changed the direction of the investigation.

The question became:

> **Why is this server receiving so many HTTP requests that the access logs are growing this quickly?**

The old Nginx logs were cleaned up.

The Nginx log directory went from approximately:

```text
2.5 GB
```

to:

```text
33 MB
```

The server's used disk space also dropped from approximately:

```text
15 GB
```

to:

```text
12 GB
```

At this point, the immediate disk-space problem was under control.

But the investigation had uncovered a second problem:

> **The server was receiving a very large amount of web traffic.**

---

# 4. The large Nginx access logs were investigated

The Nginx access log was analyzed to determine what was generating the traffic.

A particular endpoint stood out:

```text
/portfolio-details.php
```

The investigation then separated normal visitors from known crawlers.

The major crawlers found in the logs included:

```text
ClaudeBot
GPTBot
Applebot
meta-externalagent
SERankingBacklinksBot
```

The traffic was much larger than expected for a personal portfolio.

For the measured period, the investigation found:

```text
Total portfolio requests:
143,071
```

Crawler requests accounted for:

```text
141,941
```

The crawler breakdown was approximately:

```text
ClaudeBot                 112,115
GPTBot                     23,889
SERankingBacklinksBot       2,734
meta-externalagent          2,718
Applebot                      540
```

This explained the enormous Nginx access logs.

The problem was no longer simply:

> "My logs are large."

It became:

> **"Why are crawlers requesting my portfolio detail endpoint at this scale?"**

---

# 5. The crawler URLs looked abnormal

The next investigation focused on the URLs being requested.

The portfolio endpoint used URLs similar to:

```text
/portfolio-details.php?project_id=...
```

but the `project_id` values were long encrypted strings.

The logs showed an enormous number of different values.

The analysis found approximately:

```text
144,713 unique encrypted project_id values
```

That was suspicious because the actual portfolio database contained only a relatively small number of projects.

The next question was therefore:

> **Are these really 144,713 different projects, or are many different encrypted URLs representing the same project?**

---

# 6. The encryption implementation revealed why the URLs were changing

The portfolio application was using this encryption approach:

```php
$cipher = 'AES-128-CBC';
```

and, importantly, generated a random IV for every encryption operation:

```php
$iv = openssl_random_pseudo_bytes(16);
```

The encrypted value was then generated from:

```text
IV + encrypted data
```

and encoded into a URL-safe string.

That means the same database ID could produce different ciphertext every time.

Conceptually:

```text
Project ID 45
     │
     ├── random IV → encrypted URL A
     ├── random IV → encrypted URL B
     ├── random IV → encrypted URL C
     ├── random IV → encrypted URL D
     └── ...
```

So the application did not have a stable URL for a project.

This was especially problematic for crawlers.

A crawler encountering different encrypted URLs could treat them as different resources even though they ultimately represented the same project.

---

# 7. The encrypted URLs were decrypted to verify the hypothesis

Instead of assuming that the URLs represented duplicate projects, the actual encrypted IDs from the crawler logs were decrypted using the application's encryption implementation.

The result confirmed the problem.

The analysis found:

```text
Unique encrypted IDs: 144,713
```

but only:

```text
Unique actual project IDs: 50
```

All 50 decrypted IDs were valid projects in the database.

So the actual relationship was:

```text
144,713 encrypted URL values
            ↓
         50 projects
```

This was the critical finding.

The crawler traffic was not discovering 144,713 different portfolio projects.

It was requesting the same small set of projects through a huge number of different encrypted URLs.

---

# 8. The application was inspected to find where those URLs were generated

The source code was then traced.

The portfolio URLs were being generated from places such as:

```text
index.php
layouts/sidebar_portfolio.php
```

The application was calling:

```php
$crypt->encrypt($project['id'])
```

and:

```php
$crypt->encrypt($grouped_project['id'])
```

The investigation also found the corresponding decryption logic in:

```text
layouts/db_portfolio_query.php
```

The request parameters were decrypted before being used to query the database.

This confirmed that the instability was coming directly from the application's URL-generation mechanism.

---

# 9. The portfolio URL strategy was changed

The solution was to stop generating a new random ciphertext for the same project.

The requirement was:

* Do not expose the raw database ID directly.
* Keep the existing application concept/functionality.
* Give every project a stable identifier.
* Make the same project always produce the same URL.
* Allow Varnish and crawlers to recognize the resource consistently.

The portfolio URLs were therefore changed to use a **stable obscured project identifier** instead of the previous randomized AES ciphertext.

The desired model became:

```text
Project 45
    ↓
Stable project identifier
    ↓
Same URL every time
    ↓
Same Varnish cache key
```

instead of:

```text
Project 45
    ↓
Random IV
    ↓
New encrypted value
    ↓
New URL
```

This was an important architectural change because it addressed the root cause of the enormous number of logically duplicate URLs.

---

# 10. Varnish caching was then investigated

After changing the URL structure, the next question was:

> **Is Varnish actually caching these portfolio pages correctly?**

The response headers initially looked confusing.

The backend produced cache-related headers such as:

```text
Cache-Control: public, max-age=604800, s-maxage=604800
```

but the final response also contained:

```text
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Expires: -1
```

Because of this conflict, looking only at `curl` response headers was not enough.

The actual Varnish transaction was traced.

---

# 11. Varnish was proven to cache the portfolio page

A unique test URL was generated and requested twice.

The first request showed a backend fetch:

```text
BackendOpen
127.0.0.1:8080
```

followed by:

```text
BerespStatus 200
```

and:

```text
TTL RFC 604800
TTL VCL 604800
```

The response was stored in Varnish.

The second request produced:

```text
Hit
```

and did not perform another backend fetch.

The transaction therefore behaved as:

```text
Request 1
   ↓
Varnish MISS
   ↓
Nginx/PHP backend
   ↓
Store response
   ↓
Varnish

Request 2
   ↓
Varnish HIT
   ↓
No backend fetch
```

The cache lifetime was:

```text
604800 seconds
```

which is:

```text
7 days
```

So Varnish was functioning correctly.

---

# 12. Database activity was also investigated

Because the portfolio page executes database queries, MySQL activity was measured.

The application performs several prepared statements when processing the page.

The database statement counters were measured before and after a single request.

The test showed the expected increase in:

```text
Prepare
Execute
Close stmt
Quit
```

This confirmed that requests reaching PHP were capable of generating database activity.

The investigation then separated:

```text
Varnish cache HIT
```

from:

```text
Varnish cache MISS → PHP → MySQL
```

This was important because the objective was not merely to make PHP faster; it was to prevent unnecessary requests from reaching PHP/MySQL in the first place.

---

# 13. A second performance issue was discovered during repeated-request testing

Repeated requests to the same stable portfolio URL produced an unexpected timing pattern.

The first request was fast:

```text
~0.027 seconds
```

but subsequent requests took approximately:

```text
~0.99 seconds
```

Repeated tests showed the same pattern:

```text
Request 1 → ~0.027s
Request 2 → ~0.990s
Request 3 → ~0.988s
Request 4 → ~0.986s
Request 5 → ~0.986s
Request 6 → ~0.990s
```

The investigation then broke the request timing into:

```text
DNS
TCP connection
TLS
TTFB
Total
```

DNS and connection establishment were very fast.

TLS was also approximately:

```text
25–30 ms
```

The approximately one-second delay was appearing in the **time to first byte**.

So the delay was not caused by DNS or TLS.

---

# 14. Direct backend testing ruled out PHP-FPM/backend slowness

The backend was also tested directly.

The direct Nginx/PHP backend response was approximately:

```text
0.003 seconds
```

PHP-FPM was confirmed to be:

```text
active
```

and listening on:

```text
127.0.0.1:19005
```

Therefore the backend itself was capable of responding extremely quickly.

The approximately one-second delay was happening before or around request processing at the public Nginx/Varnish layer.

---

# 15. The one-second delay was traced to Nginx `limit_req`

The Nginx configuration contained rate limiting.

The relevant behavior was:

```nginx
limit_req zone=limit burst=10;
```

without:

```nginx
nodelay
```

That distinction was important.

With `nodelay`, excess burst requests are processed immediately until the burst is exhausted, after which requests can receive `429`.

Without `nodelay`, Nginx **delays excess requests** according to the configured request rate.

The configured rate was approximately:

```text
1 request/second
```

Therefore the measured result made sense:

```text
First request
    ↓
Immediate

Next rapid request
    ↓
~1 second delay

Next rapid request
    ↓
~1 second delay
```

The repeated ~0.99-second delay was therefore not a Varnish failure or PHP-FPM problem.

It was the intended behavior of the Nginx rate limiter.

---

# 16. `nodelay` was tested and rejected for this use case

The earlier configuration using:

```nginx
limit_req zone=limit burst=10 nodelay;
```

was tested.

Rapid requests eventually produced:

```text
200
200
200
200
200
200
429
429
429
...
```

That behavior was considered too aggressive for the portfolio.

The objective was not to immediately reject legitimate crawlers or a user who happens to click/reload several times.

The goal was to **slow down continuous rapid requests**.

Therefore:

```nginx
limit_req zone=limit burst=10;
```

was retained without `nodelay`.

---

# 17. The final behavior was validated

The final test produced:

```text
Request 1 | HTTP=200 | ~0.027s
Request 2 | HTTP=200 | ~0.990s
Request 3 | HTTP=200 | ~0.988s
Request 4 | HTTP=200 | ~0.986s
Request 5 | HTTP=200 | ~0.986s
Request 6 | HTTP=200 | ~0.990s
```

This means the server is not immediately returning `429` to repeated requests.

Instead, rapid repeated requests are being **throttled**.

For the stated goal, that is the desired behavior.

---

# 18. Final state

The investigation started with a storage problem and gradually uncovered several independent issues.

The final chain was:

```text
SERVER DISK ALMOST FULL
        │
        ▼
Investigate filesystem
        │
        ├─────────────────────────────┐
        ▼                             ▼
MySQL log flood                 Nginx access logs
        │                             │
        ▼                             ▼
MY-013360 warnings              ~2.5 GB logs
44,254 occurrences                    │
        │                             ▼
        ▼                       Investigate traffic
Suppress specific warning             │
        │                             ▼
        ▼                       Huge crawler traffic
Warning generation stopped            │
                                      ▼
                              /portfolio-details.php
                                      │
                                      ▼
                              Random encrypted URLs
                                      │
                                      ▼
                         144,713 encrypted IDs
                                      │
                                      ▼
                               Only 50 real projects
                                      │
                                      ▼
                         Random-IV URL generation
                                      │
                                      ▼
                          Stable project identifiers
                                      │
                                      ▼
                             Investigate Varnish
                                      │
                                      ▼
                            MISS → Backend → STORE
                                      │
                                      ▼
                                   HIT works
                                      │
                                      ▼
                            Investigate ~1 sec delay
                                      │
                                      ▼
                           Nginx limit_req behavior
                                      │
                                      ▼
                            Requests are throttled
                                      │
                                      ▼
                              Final state
```

## Final problems and their status

| Problem                          | Finding                                                     | Status                                       |
| -------------------------------- | ----------------------------------------------------------- | -------------------------------------------- |
| Server disk almost full          | Large log consumption                                       | **Resolved**                                 |
| MySQL log growth                 | Repeated `MY-013360` warning                                | **Fixed**                                    |
| Nginx log growth                 | Extremely high HTTP request volume                          | **Controlled / logs cleaned**                |
| Excessive crawler traffic        | Mostly ClaudeBot/GPTBot and other crawlers                  | **Controlled with rate limiting**            |
| Random portfolio URLs            | AES-CBC random IV generated different URLs for same project | **Fixed**                                    |
| 144k encrypted IDs               | Represented only 50 actual projects                         | **Root cause identified**                    |
| Varnish caching uncertainty      | Conflicting response headers                                | **Investigated; actual cache HIT confirmed** |
| Varnish cache                    | 7-day TTL, MISS → STORE → HIT                               | **Working**                                  |
| Backend performance              | Direct backend ~milliseconds                                | **Healthy**                                  |
| ~1-second repeated-request delay | Nginx `limit_req` without `nodelay`                         | **Expected behavior**                        |
| Continuous rapid requests        | Need to slow rather than immediately block                  | **Implemented**                              |

## The final outcome

The server went from a situation where **disk space was being consumed by uncontrolled log growth**, to a system where the underlying causes were identified individually:

**MySQL logging was controlled → Nginx logs were cleaned → crawler traffic was analyzed → unstable encrypted URLs were replaced with stable identifiers → Varnish caching was verified → Nginx request throttling was tuned.**

The final architecture therefore protects the personal portfolio from continuous rapid requests while still allowing normal visitors and legitimate crawlers to access the portfolio.
