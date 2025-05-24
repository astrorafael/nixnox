# LibSQL configuration
1. Entry in /etc/hosts

```bash
127.0.0.1 *.db.sarna.dev
```

2. .env file for cli commands
DATABASE_URL=sqlite+libsql://nixnox.db.sarna.dev:8080

3. .streamlit/secrets.toml
url="sqlite+libsql://nixnox.db.sarna.dev:8080"

4. make sure the server is up and running (justfile recipe)

5. Create namespace (justfile recipe)
