# Linux Fundamentals

A practical collection of Linux basics, server operations notes, and quick reference guides.

## Repository Index

This index is updated automatically when new files are pushed.

<!-- AUTO-INDEX-START -->
| File | Description |
| --- | --- |
| [CRON_MYSQL_BACKUP_SETUP.md](CRON_MYSQL_BACKUP_SETUP.md) | 📘 MySQL Automated Backup Setup (Cron + Singapore Timezone). |
| [MySQL_SECURE_BACKUP_SETUP_(Using .my.cnf).md](MySQL_SECURE_BACKUP_SETUP_%28Using%20.my.cnf%29.md) | 📘 MySQL Secure Backup Setup (Using `.my.cnf`). |
| [MYSQL_TUNING.md](MYSQL_TUNING.md) | MySQL 8 Tuning Guide (RAM-Based VPS Optimization). |
| [PHP_FPM_TUNING.md](PHP_FPM_TUNING.md) | PHP-FPM Tuning Guide (RAM-Based VPS Optimization). |
| [PORTFOLIO-SERVE-PERFORMANCE-INVESTIGATION-STORY.md](PORTFOLIO-SERVE-PERFORMANCE-INVESTIGATION-STORY.md) | Portfolio Server Investigation — Complete Chronological Story. |
| [PORTFOLIO_SERVER_SOLUTIONS/01-MYSQL-LOG-GROWTH-MY-013360.md](PORTFOLIO_SERVER_SOLUTIONS/01-MYSQL-LOG-GROWTH-MY-013360.md) | MySQL Log Growth Caused by Repeated MY-013360 Warnings. |
| [PORTFOLIO_SERVER_SOLUTIONS/02-NGINX-ACCESS-LOG-GROWTH.md](PORTFOLIO_SERVER_SOLUTIONS/02-NGINX-ACCESS-LOG-GROWTH.md) | Nginx Access Log Growth and Disk Consumption. |
| [PORTFOLIO_SERVER_SOLUTIONS/03-EXCESSIVE-CRAWLER-TRAFFIC.md](PORTFOLIO_SERVER_SOLUTIONS/03-EXCESSIVE-CRAWLER-TRAFFIC.md) | Investigating Excessive Crawler Traffic. |
| [PORTFOLIO_SERVER_SOLUTIONS/04-UNSTABLE-PORTFOLIO-URLS.md](PORTFOLIO_SERVER_SOLUTIONS/04-UNSTABLE-PORTFOLIO-URLS.md) | Stable Portfolio URLs Instead of Randomized Encryption. |
| [PORTFOLIO_SERVER_SOLUTIONS/05-VARNISH-CACHE-VERIFICATION.md](PORTFOLIO_SERVER_SOLUTIONS/05-VARNISH-CACHE-VERIFICATION.md) | Verifying Varnish Caching for Dynamic Portfolio Pages. |
| [PORTFOLIO_SERVER_SOLUTIONS/06-NGINX-RATE-LIMITING-WITHOUT-NODELAY.md](PORTFOLIO_SERVER_SOLUTIONS/06-NGINX-RATE-LIMITING-WITHOUT-NODELAY.md) | Nginx Rate Limiting: Throttle Rapid Requests Without Immediate 429s. |
| [RPM_VS_YUM_VS_DNF.md](RPM_VS_YUM_VS_DNF.md) | RPM: The Package Management Foundation. |
| [WEBSERVER_TUNING.md](WEBSERVER_TUNING.md) | Nginx + PHP-FPM Performance Tuning Guide (PHP 8.3). |
<!-- AUTO-INDEX-END -->

## How Auto-Update Works

When you push new files:

1. A GitHub Actions workflow runs.
2. The workflow regenerates the index section above.
3. If there are changes, it commits the updated README automatically.

## Contribution Note

Add new documentation files normally. The README index will stay in sync after push.
