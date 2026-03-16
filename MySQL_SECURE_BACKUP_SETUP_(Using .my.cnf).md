# 📘 MySQL Secure Backup Setup (Using `.my.cnf`)

## 🎯 Purpose

To run `mysqldump` without entering password manually and without exposing credentials in:

* Bash history
* Process list (`ps aux`)
* Scripts

---

# 1️⃣ Why Not Use `-pPassword`?

Example (❌ Not Secure):

```bash
mysqldump -u root -pMyPassword database_name
```

Problems:

* Password stored in `.bash_history`
* Visible via `ps aux`
* Risky in production

---

# 2️⃣ Recommended Secure Method: `.my.cnf`

MySQL automatically reads client credentials from:

```
~/.my.cnf
```

For user `ubuntu`, path is:

```
/home/ubuntu/.my.cnf
```

---

# 3️⃣ Step-by-Step Setup

## Step 1: Create Config File

Login as server user (example: ubuntu)

```bash
nano ~/.my.cnf
```

Add:

```ini
[client]
user=root
password=YOUR_DATABASE_PASSWORD
```

Save and exit.

---

## Step 2: Secure the File (IMPORTANT)

```bash
chmod 600 ~/.my.cnf
```

Verify:

```bash
ls -la ~/.my.cnf
```

Expected output:

```
-rw------- 1 ubuntu ubuntu ... .my.cnf
```

✔ Owner must be the same logged-in user
✔ Permission must be `600`

---

## Step 3: Test Configuration

```bash
mysql
```

If it logs in without password prompt → ✅ working

---

# 4️⃣ Running Secure Backup

Now run backup WITHOUT `-u` and `-p`.

```bash
mysqldump --single-transaction --quick --routines --triggers --events database_name \
| gzip > database_name_$(date +%F_%H-%M-%S).sql.gz
```

Example:

```bash
mysqldump --single-transaction --quick --routines --triggers --events horizondb_prod_from_ci \
| gzip > horizondb_prod_from_ci_$(date +%F_%H-%M-%S).sql.gz
```

✔ No password prompt
✔ Secure
✔ Production safe

---

# 5️⃣ Important Notes

### ⚠ Do NOT use sudo

If you run:

```bash
sudo mysqldump ...
```

MySQL will look for:

```
/root/.my.cnf
```

Not:

```
/home/ubuntu/.my.cnf
```

So always run as normal user.

---

# 6️⃣ How MySQL Reads Config Files

Order of priority:

1. `/etc/mysql/my.cnf`
2. `/etc/mysql/mysql.conf.d/*`
3. `~/.my.cnf`  ← User-specific config

The `[client]` section applies to:

* mysql
* mysqldump
* mysqladmin
* other client tools

---

# 7️⃣ (Recommended) Use Dedicated Backup User Instead of Root

## Create Backup User

Login to MySQL:

```sql
CREATE USER 'backupuser'@'localhost' IDENTIFIED BY 'StrongPassword';
GRANT SELECT, SHOW VIEW, TRIGGER, EVENT, LOCK TABLES ON database_name.* TO 'backupuser'@'localhost';
FLUSH PRIVILEGES;
```

Update `.my.cnf`:

```ini
[client]
user=backupuser
password=StrongPassword
```

✔ More secure
✔ Principle of least privilege
✔ Better production practice

---

# 8️⃣ Optional: Verify What MySQL Is Reading

```bash
mysql --print-defaults
```

This shows which defaults are loaded.

---

# 9️⃣ Quick Troubleshooting Checklist

| Problem                                | Cause                     | Fix               |
| -------------------------------------- | ------------------------- | ----------------- |
| Still asking password                  | File not readable         | Check `chmod 600` |
| Access denied                          | Wrong password            | Update `.my.cnf`  |
| Works without sudo but fails with sudo | Root using different home | Don’t use sudo    |

---

# 🔐 Security Summary

| Method          | Secure   | Recommended     |
| --------------- | -------- | --------------- |
| `-pPassword`    | ❌ No     | ❌               |
| `MYSQL_PWD` env | ⚠ Medium | ⚠               |
| `.my.cnf`       | ✅ Yes    | ✅ Best Practice |

---

# 🚀 Final Production Command Template

```bash
mysqldump --single-transaction --quick --routines --triggers --events DB_NAME \
| gzip > DB_NAME_$(date +%F_%H-%M-%S).sql.gz
```