# Nginx Access Log Growth and Disk Consumption

## Problem

After MySQL logs were investigated, another major disk consumer was
found under:

``` text
/home/zawadulkawum/logs/nginx
```

The Nginx log directory had grown to approximately 2.5 GB, with
historical access logs reaching hundreds of megabytes.

## Investigation

``` bash
du -sh /home/zawadulkawum/logs/nginx
du -ah /home/zawadulkawum/logs/nginx | sort -h | tail -30
find /home/zawadulkawum/logs/nginx -type f -printf '%s %p\n' | sort -nr | head -30
wc -l /home/zawadulkawum/logs/nginx/access.log
```

## Cleanup

Remove only reviewed obsolete logs. For example, after confirming
retention requirements:

``` bash
find /home/zawadulkawum/logs/nginx -type f -name '*.log' -mtime +30 -delete
```

The immediate cleanup reduced the Nginx log directory from approximately
2.5 GB to approximately 33 MB.

## Long-Term Solution

Use log rotation rather than allowing access logs to grow indefinitely.

Check existing configuration:

``` bash
ls -l /etc/logrotate.d/
grep -Rni nginx /etc/logrotate.d/ /etc/logrotate.conf
```

A typical policy may include:

``` text
daily
rotate 14
compress
delaycompress
missingok
notifempty
```

The exact retention should match operational and compliance
requirements.

## Important Discovery

Large access logs are usually a symptom of request volume. After
cleanup, the investigation continued by analyzing which endpoints and
clients were generating the traffic.

## Lesson

The correct sequence is:

``` text
Large logs
→ Identify request volume
→ Identify high-volume endpoints
→ Identify request sources
→ Control abnormal traffic
→ Configure log rotation
```
