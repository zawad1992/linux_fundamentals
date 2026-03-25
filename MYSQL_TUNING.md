# MySQL 8 Tuning Guide (RAM-Based VPS Optimization)

This guide explains how to tune **MySQL / MariaDB** for performance and
large database imports.

Configuration file:

    /etc/mysql/mysql.conf.d/mysqld.cnf

All changes go inside:

    [mysqld]

------------------------------------------------------------------------

# Critical Settings

## Large Imports

    max_allowed_packet = 512M

Allows importing large SQL dumps.

------------------------------------------------------------------------

## Timeouts

    wait_timeout = 28800
    interactive_timeout = 28800

Prevents disconnection during long imports.

------------------------------------------------------------------------

## Temporary Tables

    tmp_table_size = 256M
    max_heap_table_size = 256M

Improves large query performance.

------------------------------------------------------------------------

# InnoDB Performance Settings

## Buffer Pool

Most important MySQL setting.

Rule:

    60–70% of total RAM

------------------------------------------------------------------------

## Recommended Buffer Pool Size

### 1GB RAM

    innodb_buffer_pool_size = 512M

------------------------------------------------------------------------

### 2GB RAM

    innodb_buffer_pool_size = 1G

------------------------------------------------------------------------

### 4GB RAM

    innodb_buffer_pool_size = 2G

------------------------------------------------------------------------

### 8GB RAM

    innodb_buffer_pool_size = 5G

------------------------------------------------------------------------

## Log File Size

    innodb_log_file_size = 512M

Large values improve **import speed**.

------------------------------------------------------------------------

## Flush Method

    innodb_flush_method = O_DIRECT

Prevents double buffering.

------------------------------------------------------------------------

## Transaction Commit Mode

    innodb_flush_log_at_trx_commit = 2

Good balance of **performance vs safety**.

------------------------------------------------------------------------

# Example Production Configuration

    [mysqld]

    max_allowed_packet = 512M
    wait_timeout = 28800
    interactive_timeout = 28800

    tmp_table_size = 256M
    max_heap_table_size = 256M

    innodb_buffer_pool_size = 2G
    innodb_log_file_size = 512M
    innodb_flush_log_at_trx_commit = 2
    innodb_flush_method = O_DIRECT

------------------------------------------------------------------------

# Restart MySQL

After saving configuration:

    sudo systemctl restart mysql

------------------------------------------------------------------------

# Verify Settings

    SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
    SHOW VARIABLES LIKE 'max_allowed_packet';

------------------------------------------------------------------------

# Best Method for Large Imports

Instead of phpMyAdmin:

    mysql -u user -p database < dump.sql

CLI import is significantly faster.

------------------------------------------------------------------------

# Monitoring MySQL Memory Usage

    mysqladmin status

or

    SHOW ENGINE INNODB STATUS;

------------------------------------------------------------------------

# Summary

  RAM   Buffer Pool
  ----- -------------
  1GB   512MB
  2GB   1GB
  4GB   2GB
  8GB   5GB
