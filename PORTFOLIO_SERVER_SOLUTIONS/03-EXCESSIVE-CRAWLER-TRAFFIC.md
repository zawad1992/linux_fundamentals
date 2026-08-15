# Investigating Excessive Crawler Traffic

## Problem

The Nginx access log showed unusually high traffic to:

``` text
/portfolio-details.php
```

Known crawler user agents included:

-   ClaudeBot
-   GPTBot
-   Applebot
-   meta-externalagent
-   SERankingBacklinksBot

## Measure Traffic

``` bash
grep '\[15/Aug/2026:' /home/zawadulkawum/logs/nginx/access.log | grep 'GET /portfolio-details.php' | wc -l
```

Known crawler traffic:

``` bash
grep '\[15/Aug/2026:' /home/zawadulkawum/logs/nginx/access.log | grep 'GET /portfolio-details.php' | grep -Ei 'GPTBot|ClaudeBot|Applebot|meta-externalagent|SERankingBacklinksBot' | wc -l
```

Breakdown:

``` bash
grep '\[15/Aug/2026:' /home/zawadulkawum/logs/nginx/access.log | grep 'GET /portfolio-details.php' | grep -Ei 'GPTBot|ClaudeBot|Applebot|meta-externalagent|SERankingBacklinksBot' | grep -Eo 'ClaudeBot|GPTBot|Applebot|meta-externalagent|SERankingBacklinksBot' | sort | uniq -c | sort -nr
```

The measured period contained approximately:

``` text
Total portfolio requests: 143,071
Known crawler requests:   141,941
```

Approximate crawler counts:

``` text
ClaudeBot                 112,115
GPTBot                     23,889
SERankingBacklinksBot       2,734
meta-externalagent          2,718
Applebot                      540
```

## Inspect Source IPs

``` bash
grep 'ClaudeBot' /home/zawadulkawum/logs/nginx/access.log | grep 'portfolio-details.php' | awk '{print $1}' | sort | uniq -c | sort -nr | head -20
```

Repeat for other crawler user agents.

Do not blindly trust a User-Agent string for security decisions. If
blocking or whitelisting matters, use the crawler's published
identity-verification method.

## Lesson

Before blocking bots, determine:

1.  Which endpoints they request.
2.  How frequently they request them.
3.  Whether URLs are unique.
4.  Whether requests reach PHP/MySQL.
5.  Whether they are legitimate crawlers.
6.  Whether throttling is sufficient.

For a personal portfolio, gentle rate limiting can be preferable to an
immediate blanket block.
