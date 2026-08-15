# MySQL Log Growth Caused by Repeated MY-013360 Warnings

## Problem

The server disk became almost full. Filesystem investigation showed that
MySQL logs were one of the major consumers of disk space.

MySQL was repeatedly writing warning `MY-013360`, related to the
deprecated `mysql_native_password` authentication mechanism. The warning
was being generated tens of thousands of times, causing the MySQL error
log to grow substantially.

## Investigation

Check large log directories:

``` bash
sudo du -xhd1 /var/log 2>/dev/null | sort -h
sudo find /var/log -type f -size +100M -printf '%s %p\n' 2>/dev/null | sort -nr | head -30
```

Search for the warning:

``` bash
grep -R "MY-013360" /var/log/mysql /var/log 2>/dev/null | head
grep -R "MY-013360" /var/log/mysql /var/log 2>/dev/null | wc -l
```

The investigation found approximately 44,254 occurrences.

## Solution

Suppress the specific repetitive warning rather than disabling MySQL
logging:

``` sql
SET GLOBAL log_error_suppression_list = 'MY-013360';
SET PERSIST log_error_suppression_list = 'MY-013360';
```

`SET GLOBAL` changes the current runtime configuration. `SET PERSIST`
keeps the setting across restarts.

## Verification

``` bash
before=$(grep -c "MY-013360" /var/log/mysql/error.log)
sleep 60
after=$(grep -c "MY-013360" /var/log/mysql/error.log)

echo "Before: $before"
echo "After:  $after"
echo "New warnings: $((after-before))"
```

The expected result is:

``` text
New warnings: 0
```

## Lesson

Do not solve a disk-space problem by blindly deleting logs or disabling
logging. Identify which log is growing, determine why it is growing, fix
the source of the noise, and then establish sensible log retention.
