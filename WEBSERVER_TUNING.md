# Nginx + PHP-FPM Performance Tuning Guide (PHP 8.3)

Production tuning reference for Ubuntu servers running **Nginx + PHP-FPM (PHP 8.3)**.

This document provides optimized baseline configurations for:

* Nginx performance
* PHP-FPM process management
* PHP Opcache
* FastCGI optimization
* Monitoring and verification

These settings are suitable for **small–medium servers (2-8 CPU cores)**.

---

# Server Stack

Example environment:

| Component           | Version |
| ------------------- | ------- |
| OS                  | Ubuntu  |
| Web Server          | Nginx   |
| PHP                 | 8.3     |
| PHP Process Manager | PHP-FPM |
| Cache               | OPcache |

Check PHP version:

```bash
php -v
```

Example output:

```
PHP 8.3.6
Zend Engine v4.3.6
Zend OPcache v8.3.6
```

---

# 1. Nginx Optimization

Edit main config:

```
sudo nano /etc/nginx/nginx.conf
```

Recommended baseline configuration:

```nginx
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 4096;
    multi_accept on;
}

http {

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    keepalive_timeout 65;
    keepalive_requests 1000;

    types_hash_max_size 4096;

    server_tokens off;

    client_max_body_size 50M;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    gzip on;
    gzip_comp_level 5;
    gzip_min_length 256;

    gzip_types
        text/plain
        text/css
        text/xml
        application/json
        application/javascript
        application/xml
        application/rss+xml
        image/svg+xml;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

## Key Performance Settings

| Setting                 | Purpose                         |
| ----------------------- | ------------------------------- |
| worker_processes auto   | Uses all CPU cores              |
| worker_connections 4096 | Allows thousands of connections |
| sendfile                | Faster static file delivery     |
| tcp_nopush              | Optimizes packet transmission   |
| gzip                    | Reduces bandwidth usage         |

---

# 2. PHP-FPM Optimization

Edit pool configuration:

```
sudo nano /etc/php/8.3/fpm/pool.d/www.conf
```

Recommended configuration:

```ini
pm = dynamic

pm.max_children = 20
pm.start_servers = 4
pm.min_spare_servers = 2
pm.max_spare_servers = 6

pm.max_requests = 500
```

## Explanation

| Setting           | Meaning                                |
| ----------------- | -------------------------------------- |
| pm                | Process manager mode                   |
| max_children      | Maximum PHP workers                    |
| start_servers     | Workers started initially              |
| min_spare_servers | Minimum idle workers                   |
| max_spare_servers | Maximum idle workers                   |
| max_requests      | Restart worker to prevent memory leaks |

For **small servers**, these values provide balanced performance.

---

# 3. PHP Opcache Configuration

Edit:

```
sudo nano /etc/php/8.3/fpm/php.ini
```

Recommended settings:

```ini
opcache.enable=1
opcache.memory_consumption=128
opcache.max_accelerated_files=20000
opcache.validate_timestamps=1
opcache.revalidate_freq=2
```

## Benefits

* PHP scripts cached in memory
* Faster execution
* Reduced CPU usage

Typical improvement: **3x – 10x faster PHP execution**

---

# 4. FastCGI Optimization

Example Nginx PHP handler:

```nginx
location ~ \.php$ {

    include snippets/fastcgi-php.conf;

    fastcgi_pass unix:/run/php/php8.3-fpm.sock;

    fastcgi_buffers 16 16k;
    fastcgi_buffer_size 32k;

}
```

Benefits:

* Reduces request latency
* Improves PHP response handling

---

# 5. Restart Services

After configuration changes:

```bash
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl restart php8.3-fpm
```

---

# 6. Monitor Server Performance

Install monitoring tools:

```bash
sudo apt install htop
```

Run:

```
htop
```

Monitor:

* CPU usage
* PHP-FPM processes
* Nginx workers
* Memory usage

---

# 7. Check Active PHP-FPM Workers

```
ps aux | grep php-fpm
```

Example output:

```
www-data php-fpm: pool www
```

---

# 8. Optional Advanced Optimizations

These can further improve performance:

### Brotli Compression

```
sudo apt install nginx-extras
```

### Microcaching

Useful for high-traffic applications.

Example:

```nginx
fastcgi_cache_path /var/cache/nginx levels=1:2 keys_zone=PHP:100m inactive=60m;
```

### HTTP/2

Enable in SSL server block:

```nginx
listen 443 ssl http2;
```

---

# 9. Benchmark Server

Install ApacheBench:

```
sudo apt install apache2-utils
```

Example test:

```
ab -n 1000 -c 50 http://localhost/
```

This simulates:

* 1000 requests
* 50 concurrent users

---

# 10. Best Practices

* Use **OPcache**
* Keep **PHP-FPM workers balanced**
* Use **gzip compression**
* Enable **FastCGI buffering**
* Monitor CPU and memory regularly

---

# Example Optimized Stack

```
Client
   ↓
Nginx
   ↓
FastCGI
   ↓
PHP-FPM
   ↓
Application
```

---

# Notes

This configuration is designed for:

* Laravel
* WordPress
* PHP APIs
* Static + dynamic web applications

Always adjust settings based on:

* CPU cores
* RAM
* Traffic load

---

# Author Notes

Maintain this document as a reusable reference for configuring new servers with:

* Ubuntu
* Nginx
* PHP-FPM
* PHP 8.3
