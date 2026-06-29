from django.shortcuts import render
from django.http import JsonResponse
import os

def dashboard(request):
    return render(request, 'Dashboard.html')


def sensor_lantai4(request):
    """API endpoint that returns latest Sensor_Ldr values from InfluxDB.

    Expects environment variables: INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG
    Optional: INFLUX_BUCKET (defaults to 'Sensor')
    """
    try:
        from influxdb_client import InfluxDBClient
    except Exception as e:
        return JsonResponse({'error': 'influxdb-client library not installed'}, status=500)

    # Hardcoded InfluxDB settings (use only in trusted/test environment)
    url = 'http://10.231.37.100:8086'
    token = 'ijJLIA2D7lhdbSSlkP9TBDpf8_DOUN1vMxMuPartF6k58BH-povcBun45eHqToXr4wr3nzhODKAm_3ifI_CZew=='
    # If your InfluxDB requires an org, set it here (or leave empty to omit)
    org = 'Sysware'
    bucket = 'Sensor'
    measurement = 'Sensor_Ldr'

    if not url or not token:
        return JsonResponse({'error': 'Missing InfluxDB configuration (url/token).'}, status=500)

    try:
        with InfluxDBClient(url=url, token=token, org=org or None) as client:
            query_api = client.query_api()
            flux = f'from(bucket:"{bucket}") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "{measurement}") |> last()'
            if org:
                tables = query_api.query(flux, org=org)
            else:
                tables = query_api.query(flux)

            # Collect last value per field
            values = {}
            for table in tables:
                for record in table.records:
                    field = record.get_field()
                    values[field] = record.get_value()

            lux = values.get('lux') or 0
            adc = values.get('adc') or 0
            lamp_status = int(values.get('lamp_status') or 0)

            # Normalize types
            try:
                lux = float(lux)
            except Exception:
                lux = 0
            try:
                adc = int(adc)
            except Exception:
                adc = 0

            return JsonResponse({
                'lux': lux,
                'adc': adc,
                'lamp_status': 1 if lamp_status == 1 else 0
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
