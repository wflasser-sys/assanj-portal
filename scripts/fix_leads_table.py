import sqlite3
from datetime import datetime

DB = 'db.sqlite3'
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Create leads_lead table (matching migration)
cur.execute('''
CREATE TABLE IF NOT EXISTS leads_lead (
    id integer PRIMARY KEY AUTOINCREMENT,
    business_name varchar(255) NOT NULL,
    phone_number varchar(50) NOT NULL,
    category varchar(50) NOT NULL,
    other_category varchar(255),
    status varchar(50) NOT NULL,
    created_at datetime NOT NULL,
    assigned_sales_closer_id integer,
    created_by_id integer,
    FOREIGN KEY(assigned_sales_closer_id) REFERENCES auth_user(id) ON DELETE SET NULL,
    FOREIGN KEY(created_by_id) REFERENCES auth_user(id) ON DELETE SET NULL
)
''')

# Insert migration record into django_migrations if not present
cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='django_migrations'")
if cur.fetchone()[0] == 0:
    print('django_migrations table does not exist — run migrations after creating this table manually if needed')
else:
    cur.execute("SELECT COUNT(*) FROM django_migrations WHERE app='leads' AND name='0001_initial'")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)", ('leads', '0001_initial', datetime.utcnow().isoformat()))
        print('Inserted leads migration record into django_migrations')
    else:
        print('leads migration already recorded')

conn.commit()
conn.close()
print('Done')