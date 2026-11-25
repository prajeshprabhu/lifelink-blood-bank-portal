# LifeLink Blood Bank Inventory Portal

An independently deployable Flask/MySQL portal for one blood bank. It does not modify or require changes to the LifeLink application.

## Setup

### Configure TiDB Cloud

The application uses `mysql-connector-python`, which connects to TiDB through its MySQL-compatible protocol.

1. In TiDB Cloud, create or select a cluster and open its **Connect** details. Use the connection method for a standard MySQL client. Make sure your current IP is allowed by the cluster's network access settings.
2. Copy the host, port, username, and password shown by TiDB. Use the **TiDB** username (not your local MySQL `root` account). Use the port shown by the console; do not use `localhost` for a remote cluster.
3. Download the CA certificate specified by the TiDB connection instructions if TLS is required.
4. From PowerShell in this project folder, copy the example environment file:
   ```powershell
   Copy-Item .env.example .env
   ```
5. Edit `.env` and replace the local MySQL values with the TiDB connection details:
   ```dotenv
   MYSQL_HOST=the-host-from-tidb-connect-details
   MYSQL_PORT=the-port-from-tidb-connect-details
   MYSQL_USER=the-tidb-username
   MYSQL_PASSWORD=the-tidb-password
   MYSQL_DATABASE=blood_bank_portal
   MYSQL_SSL_CA=D:\HemoCare\certs\tidb-ca.pem
   MYSQL_SSL_VERIFY_CERT=true
   MYSQL_SSL_VERIFY_IDENTITY=true
   ```
   The host, port, username, password, and certificate path above are examples of what to enter, not real credentials. Replace them with values from your TiDB console. If TiDB provides a different CA file location, use that actual path. Quote the password in `.env` if it contains characters that dotenv treats specially.
6. The initializer creates the database named by `MYSQL_DATABASE` if it does not exist, then creates the tables inside it. The database account needs permission to create the database when it is missing, and to create tables. If TiDB has already provisioned the database and the account cannot create databases, it can connect directly to that database; the account still needs permission to create the tables.
7. Install dependencies and initialize the schema:
   ```powershell
   python -m pip install -r requirements.txt
   python database\init_db.py
   ```
8. Start the portal and open `http://localhost:5001/login`:
   ```powershell
   python app.py
   ```

`MYSQL_SSL_CA` enables TLS certificate and hostname verification. Leave it empty for a local MySQL server that does not require a CA file. Keep `.env` private and never commit it.

For production, set `JWT_COOKIE_SECURE=true`, restrict `CORS_ALLOWED_ORIGINS`, place Flask behind HTTPS, and use a strong random API secret.

## LifeLink integration

LifeLink should call the availability endpoint only when a blood request is raised or a fresh check is requested:

```python
import requests

response = requests.get(
    "https://blood-bank.example/api/v1/inventory/availability",
    params={"blood_group": "O+", "city": "Mangaluru"},
    headers={"Authorization": "Bearer YOUR_API_SECRET"},
    timeout=10,
)
response.raise_for_status()
print(response.json())
```

Availability checks do not deduct stock. Inventory POST/PUT operations require the LifeLink bearer secret. Dashboard routes use a secure HTTP-only JWT cookie.

## API tests

```bash
curl -H "Authorization: Bearer YOUR_API_SECRET" \
  "http://localhost:5001/api/v1/inventory/availability?blood_group=O%2B&city=Mangaluru"
```