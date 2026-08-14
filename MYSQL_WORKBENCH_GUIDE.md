# MySQL Workbench Setup Guide for SAEROS

## ✅ Yes, SAEROS works with MySQL Workbench!

This guide shows you how to set up the database using MySQL Workbench.

---

## Step 1: Find Your MySQL Root Password

### Option A: Check if you remember it
Try logging into MySQL Workbench with your usual password.

### Option B: Reset MySQL root password (if forgotten)

**Windows:**
1. Stop MySQL service:
   - Open Services (Win+R → `services.msc`)
   - Find "MySQL80" or "MySQL"
   - Right-click → Stop

2. Start MySQL in safe mode:
   ```cmd
   cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"
   mysqld --console --skip-grant-tables --shared-memory
   ```

3. Open a new command prompt and connect:
   ```cmd
   mysql -u root
   ```

4. Reset password:
   ```sql
   FLUSH PRIVILEGES;
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourNewPassword123';
   FLUSH PRIVILEGES;
   EXIT;
   ```

5. Stop the safe mode MySQL (Ctrl+C in first window)
6. Start MySQL service normally from Services

---

## Step 2: Run the Schema in MySQL Workbench

### Method 1: Using the SQL Script (Recommended)

1. **Open MySQL Workbench**
2. **Connect to your MySQL server** (localhost)
3. **Open the schema file**:
   - Click `File` → `Open SQL Script...`
   - Navigate to your project folder
   - Select `schema.sql`
   - Click `Open`

4. **Execute the script**:
   - Click the **lightning bolt** icon (⚡) or press `Ctrl+Shift+Enter`
   - This will execute all statements

5. **Verify success**:
   - You should see "Action Output" showing successful execution
   - Check the left sidebar under "Schemas" → you should see `saeros_db`

### Method 2: Copy-Paste (Alternative)

1. Open `schema.sql` in a text editor
2. Copy all the content
3. In MySQL Workbench, paste into a new query tab
4. Click the lightning bolt to execute

---

## Step 3: Verify Database Creation

In MySQL Workbench, run these queries to verify:

```sql
-- Check database exists
SHOW DATABASES LIKE 'saeros_db';

-- Use the database
USE saeros_db;

-- Check all tables were created
SHOW TABLES;

-- Should show 8 tables:
-- admin_logs, batches, bayer_process_log, byproducts,
-- raw_materials, roles, users, yield_predictions

-- Check default users
SELECT username, email, full_name, is_admin FROM users;

-- Should show:
-- admin  | admin@saeros.com  | System Administrator | 1
-- agent1 | agent1@saeros.com | John Smith          | 0
-- scrap1 | scrap1@saeros.com | Maria Garcia        | 0
```

---

## Step 4: Update .env File

1. Open `.env` in your project folder
2. Update `DB_PASSWORD` to match your MySQL root password:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YourActualMySQLPassword
DB_NAME=saeros_db
```

**Important**: Use `127.0.0.1` instead of `localhost` to avoid socket connection issues on Windows.

---

## Step 5: Test Connection from Python

Run this to verify Python can connect:

```bash
.venv\Scripts\python.exe -c "import pymysql; conn = pymysql.connect(host='127.0.0.1', user='root', password='YourPassword', database='saeros_db', ssl_disabled=True); print('✓ Connection successful!'); conn.close()"
```

Replace `YourPassword` with your actual MySQL password.

---

## Step 6: Run the Application

```bash
python run.py
```

Open your browser to: **http://localhost:5000**

---

## Default Login Credentials

| Role | Username | Password | Access |
|------|----------|----------|--------|
| **Admin** | admin | admin123 | Full system access |
| **Agent** | agent1 | agent123 | Submit batches |
| **Scrap Team** | scrap1 | scrap123 | Process by-products |

---

## Troubleshooting

### Error: "Access denied for user 'root'@'localhost'"

**Solution**: Your MySQL password in `.env` doesn't match your actual MySQL password.

1. Try logging into MySQL Workbench manually
2. If successful, use that same password in `.env`
3. If you can't login, reset your password (see Step 1)

### Error: "Can't connect to MySQL server on 'localhost'"

**Solution**: MySQL service is not running.

1. Open Services (Win+R → `services.msc`)
2. Find "MySQL80" or "MySQL"
3. Right-click → Start

### Error: "Unknown database 'saeros_db'"

**Solution**: The schema wasn't executed properly.

1. Open MySQL Workbench
2. Run the schema.sql file again (Step 2)
3. Verify with `SHOW DATABASES;`

### Error: "Table 'saeros_db.users' doesn't exist"

**Solution**: Tables weren't created.

1. In MySQL Workbench, run:
   ```sql
   USE saeros_db;
   SHOW TABLES;
   ```
2. If empty, re-run the schema.sql file

### Error: Login fails with "Invalid username or password"

**Solution**: Password hashes might be wrong.

1. In MySQL Workbench, check users:
   ```sql
   SELECT username, password_hash FROM users;
   ```
2. If password_hash looks wrong, re-run the schema.sql (it will update them)

---

## MySQL Workbench Tips

### View Table Structure
```sql
DESCRIBE users;
```

### View All Data in a Table
```sql
SELECT * FROM users;
SELECT * FROM raw_materials;
SELECT * FROM batches;
```

### Clear All Data (Keep Tables)
```sql
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE admin_logs;
TRUNCATE TABLE yield_predictions;
TRUNCATE TABLE byproducts;
TRUNCATE TABLE bayer_process_log;
TRUNCATE TABLE batches;
TRUNCATE TABLE raw_materials;
TRUNCATE TABLE users;
TRUNCATE TABLE roles;
SET FOREIGN_KEY_CHECKS = 1;

-- Re-run the INSERT statements from schema.sql to restore default users
```

### Drop and Recreate Database
```sql
DROP DATABASE IF EXISTS saeros_db;
-- Then re-run schema.sql
```

---

## Visual Guide

### MySQL Workbench Interface

```
┌─────────────────────────────────────────────────┐
│ File  Edit  View  Query  Database  Server      │
├─────────────────────────────────────────────────┤
│ [⚡ Execute] [💾 Save] [📂 Open]                │
├──────────┬──────────────────────────────────────┤
│ Schemas  │  Query Tab                           │
│          │                                       │
│ ▼ saeros_db │  -- Your SQL code here          │
│   ▼ Tables  │                                   │
│     users   │                                   │
│     roles   │                                   │
│     batches │                                   │
│     ...     │                                   │
└──────────┴──────────────────────────────────────┘
```

### Executing schema.sql

1. Click **File** → **Open SQL Script**
2. Select `schema.sql`
3. Click the **⚡ lightning bolt** icon
4. Check "Action Output" panel for success messages

---

## Next Steps

Once the database is set up:

1. ✅ Database created in MySQL Workbench
2. ✅ `.env` file updated with correct password
3. ✅ Connection tested
4. ▶️ Run `python run.py`
5. 🌐 Open http://localhost:5000
6. 🔐 Login with `admin` / `admin123`

---

## Support

If you encounter issues:

1. Check MySQL service is running
2. Verify password in `.env` matches MySQL
3. Ensure `saeros_db` database exists
4. Check all 8 tables were created
5. Verify default users exist

For more help, see `SETUP_GUIDE.md` or `README.md`.
