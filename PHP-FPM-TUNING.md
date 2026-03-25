# PHP-FPM Tuning Guide (RAM-Based VPS Optimization)

This guide explains how to tune **PHP-FPM** for best performance
depending on available **server RAM**.

File to edit:

    /etc/php/8.3/fpm/pool.d/www.conf

Key settings:

    pm
    pm.max_children
    pm.start_servers
    pm.min_spare_servers
    pm.max_spare_servers
    pm.max_requests

------------------------------------------------------------------------

# How to Calculate `pm.max_children`

Approximate memory usage per PHP process:

    Average PHP Process ≈ 30–50 MB

Formula:

    pm.max_children = (Available RAM for PHP) / (Average PHP process size)

Example:

    2GB RAM → 1500MB usable
    1500 / 40MB ≈ 37 children

------------------------------------------------------------------------

# Recommended Configurations

## 1 GB RAM VPS

    pm = dynamic
    pm.max_children = 10
    pm.start_servers = 3
    pm.min_spare_servers = 2
    pm.max_spare_servers = 5
    pm.max_requests = 500

------------------------------------------------------------------------

## 2 GB RAM VPS

    pm = dynamic
    pm.max_children = 25
    pm.start_servers = 5
    pm.min_spare_servers = 3
    pm.max_spare_servers = 10
    pm.max_requests = 1000

------------------------------------------------------------------------

## 4 GB RAM VPS

    pm = dynamic
    pm.max_children = 50
    pm.start_servers = 8
    pm.min_spare_servers = 5
    pm.max_spare_servers = 20
    pm.max_requests = 1500

------------------------------------------------------------------------

## 8 GB RAM VPS

    pm = dynamic
    pm.max_children = 100
    pm.start_servers = 10
    pm.min_spare_servers = 10
    pm.max_spare_servers = 30
    pm.max_requests = 2000

------------------------------------------------------------------------

# Important Settings

## pm = dynamic

Best general choice.

Other modes:

  Mode       Description
  ---------- ---------------------------------
  static     Fixed number of processes
  dynamic    Automatically adjusts processes
  ondemand   Spawns only when needed

------------------------------------------------------------------------

## pm.max_requests

Restarts PHP workers after serving requests to prevent **memory leaks**.

Typical values:

    500 – 2000

------------------------------------------------------------------------

# Restart PHP-FPM

After changes:

    sudo systemctl restart php8.3-fpm

------------------------------------------------------------------------

# Monitoring PHP-FPM

Check usage:

    ps --no-headers -o "rss,cmd" -C php-fpm8.3 | awk '{ sum+=$1 } END { print sum/NR/1024 " MB avg" }'

------------------------------------------------------------------------

# Performance Tips

Use with:

-   Nginx
-   OPcache enabled
-   Redis caching
-   PHP 8.2+

OPcache example:

    opcache.memory_consumption=256
    opcache.max_accelerated_files=20000
    opcache.validate_timestamps=0

------------------------------------------------------------------------

# Summary

  RAM   Recommended max_children
  ----- --------------------------
  1GB   10
  2GB   25
  4GB   50
  8GB   100
