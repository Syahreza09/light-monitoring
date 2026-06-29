# Light Monitoring

This Django project displays sensor data from InfluxDB (measurement `Sensor_Ldr` in bucket `Sensor`).

Quick setup:

1. Create a Python virtualenv and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill `INFLUX_ORG` and `DJANGO_SECRET_KEY`:

```powershell
copy .env.example .env
# then edit .env to set INFLUX_ORG and DJANGO_SECRET_KEY
```

3. Run check script:

```bash
python scripts/check_influx.py
```

4. Run Django dev server:

```bash
python manage.py runserver 0.0.0.0:8000
```

Open http://localhost:8000 to view the dashboard.

Security:
- Do not commit `.env` with your token. Use environment variables or secret manager.
