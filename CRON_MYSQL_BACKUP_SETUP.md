# 📘 MySQL Automated Backup Setup (Cron + Singapore Timezone)

## 🎯 Purpose

This document explains how to:

* Create a MySQL backup script
* Configure automated daily backup using cron
* Run backup at **2:00 AM Singapore time**
* Auto-delete backups older than 7 days
* Store backups inside `/home/ubuntu/db_backup/`

---

# 1️⃣ Prerequisites

* Server user: `ubuntu`
* MySQL credentials stored in `~/.my.cnf`
* Backup directory:

```
/home/ubuntu/db_backup/
```

Verify:

```bash
ls -la ~/.my.cnf
```

Permissions must be:

```
-rw------- 1 ubuntu ubuntu ...
```

---

# 2️⃣ Create Backup Script

### Step 1: Navigate to directory

```bash
cd /home/ubuntu
```

### Step 2: Create script

```bash
nano db_backup/mysql_backup.sh
```

### Step 3: Add script content

```bash
#!/bin/bash

# ==============================
# MySQL Backup Script
# ==============================

BACKUP_DIR="/home/ubuntu/db_backup"
DATABASE_NAME="horizondb_prod_from_ci"
DATE=$(date +%F_%H-%M-%S)
FILENAME="${DATABASE_NAME}_${DATE}.sql.gz"

# Create backup
mysqldump --single-transaction --quick --routines --triggers --events $DATABASE_NAME \
| gzip > "$BACKUP_DIR/$FILENAME"

# Check backup status
if [ $? -eq 0 ]; then
    echo "[$(date)] Backup successful: $FILENAME" >> "$BACKUP_DIR/backup.log"
else
    echo "[$(date)] Backup FAILED!" >> "$BACKUP_DIR/backup.log"
fi

# Delete backups older than 7 days
find $BACKUP_DIR -name "*.sql.gz" -type f -mtime +7 -exec rm -f {} \;
```

Save and exit.

---

# 3️⃣ Make Script Executable

```bash
chmod +x /home/ubuntu/db_backup/mysql_backup.sh
```

---

# 4️⃣ Test Script Manually

```bash
/home/ubuntu/db_backup/mysql_backup.sh
```

Verify backup:

```bash
ls /home/ubuntu/db_backup
```

Check log:

```bash
cat /home/ubuntu/db_backup/backup.log
```

---

# 5️⃣ Setup Cron Job (2AM Singapore Time)

Since server runs in UTC, we will use timezone override.

### Open cron editor:

```bash
crontab -e
```

### Add:

```bash
# MySQL automated backup (2AM Singapore time)
TZ=Asia/Singapore

0 2 * * * /home/ubuntu/db_backup/mysql_backup.sh >> /home/ubuntu/db_backup/cron.log 2>&1
```

Save and exit.

---

# 6️⃣ Verify Cron Configuration

Check installed cron jobs:

```bash
crontab -l
```

Check cron service:

```bash
sudo systemctl status cron
```

It should show:

```
Active: active (running)
```

---

# 7️⃣ Timezone Explanation

Server Timezone: **UTC**

Cron configured with:

```
TZ=Asia/Singapore
```

Therefore:

* Cron runs at 2:00 AM Singapore time
* Server internally remains in UTC
* No system timezone change required

---

# 8️⃣ Log Files

| File         | Purpose                       |
| ------------ | ----------------------------- |
| `backup.log` | Backup success/failure status |
| `cron.log`   | Cron execution output         |
| `.sql.gz`    | Compressed database backups   |

---

# 9️⃣ Backup Retention Policy

This line in script:

```bash
find $BACKUP_DIR -name "*.sql.gz" -type f -mtime +7 -exec rm -f {} \;
```

Means:

* Keep backups for 7 days
* Automatically delete older files
* Prevent unlimited disk growth

---

# 🔐 Best Practices

✔ Keep server timezone in UTC
✔ Use `TZ=Asia/Singapore` inside crontab
✔ Always use absolute paths in cron
✔ Never use `sudo` inside cron job
✔ Store MySQL credentials in `~/.my.cnf`
✔ Regularly test restore from backup

---

# 🚀 Final Production Structure

```
/home/ubuntu/
│
├── .my.cnf
│
└── db_backup/
    ├── mysql_backup.sh
    ├── backup.log
    ├── cron.log
    ├── *.sql.gz
```

---

# ✅ System Status Checklist

* [x] Backup script created
* [x] Script executable
* [x] Cron job installed
* [x] Timezone set to Singapore
* [x] Auto-delete enabled
* [x] Logging enabled

---

# 📌 Maintenance Tips

* Check disk usage periodically:

```bash
df -h
```

* Test restore occasionally:

```bash
gunzip backup.sql.gz
mysql database_name < backup.sql
```

Backups are only useful if they can be restored.

---