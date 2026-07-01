from django.shortcuts import render
from django.http import JsonResponse
import os
from datetime import datetime

def dashboard(request):
    return render(request, 'Dashboard.html')


def sensor_lantai4(request):
    """API endpoint that returns latest Sensor_Ldr values from InfluxDB.
    
    Jika data terakhir lebih dari 15 detik yang lalu, anggap sensor offline.
    """
    try:
        from influxdb_client import InfluxDBClient
    except Exception as e:
        return JsonResponse({'error': 'influxdb-client library not installed'}, status=500)

    # Hardcoded InfluxDB settings
    url = 'http://10.231.37.100:8086'
    token = 'ijJLIA2D7lhdbSSlkP9TBDpf8_DOUN1vMxMuPartF6k58BH-povcBun45eHqToXr4wr3nzhODKAm_3ifI_CZew=='
    org = 'Sysware'
    bucket = 'Sensor'
    measurement = 'Sensor_Ldr'
    
    # ============================================================
    # TIMEOUT - 15 detik (lebih toleran)
    # ============================================================
    SENSOR_TIMEOUT_SECONDS = 15

    if not url or not token:
        return JsonResponse({'error': 'Missing InfluxDB configuration (url/token).'}, status=500)

    try:
        with InfluxDBClient(url=url, token=token, org=org or None) as client:
            query_api = client.query_api()
            
            # ============================================================
            # QUERY: Ambil data terbaru per field
            # ============================================================
            lux_query = f'''
                from(bucket: "{bucket}")
                |> range(start: -10m)
                |> filter(fn: (r) => r._measurement == "{measurement}" and r._field == "lux")
                |> last()
            '''
            
            adc_query = f'''
                from(bucket: "{bucket}")
                |> range(start: -10m)
                |> filter(fn: (r) => r._measurement == "{measurement}" and r._field == "adc")
                |> last()
            '''
            
            status_query = f'''
                from(bucket: "{bucket}")
                |> range(start: -10m)
                |> filter(fn: (r) => r._measurement == "{measurement}" and r._field == "lamp_status")
                |> last()
            '''
            
            # Ambil data
            lux_value = 0
            adc_value = 0
            status_value = 0
            last_timestamp = None
            
            # Query Lux
            try:
                tables = query_api.query(lux_query, org=org) if org else query_api.query(lux_query)
                for table in tables:
                    for record in table.records:
                        lux_value = record.get_value() or 0
                        if last_timestamp is None:
                            last_timestamp = record.get_time()
                        break
                    if last_timestamp:
                        break
            except Exception as e:
                print(f"⚠️ Error query lux: {e}")
            
            # Query ADC
            try:
                tables = query_api.query(adc_query, org=org) if org else query_api.query(adc_query)
                for table in tables:
                    for record in table.records:
                        adc_value = record.get_value() or 0
                        if last_timestamp is None:
                            last_timestamp = record.get_time()
                        break
                    if last_timestamp:
                        break
            except Exception as e:
                print(f"⚠️ Error query adc: {e}")
            
            # Query Status
            try:
                tables = query_api.query(status_query, org=org) if org else query_api.query(status_query)
                for table in tables:
                    for record in table.records:
                        status_value = int(record.get_value() or 0)
                        if last_timestamp is None:
                            last_timestamp = record.get_time()
                        break
                    if last_timestamp:
                        break
            except Exception as e:
                print(f"⚠️ Error query status: {e}")
            
            # ============================================================
            # VALIDASI DATA
            # ============================================================
            try:
                lux_value = float(lux_value)
            except Exception:
                lux_value = 0
            try:
                adc_value = int(adc_value)
            except Exception:
                adc_value = 0
            try:
                status_value = 1 if int(status_value) == 1 else 0
            except Exception:
                status_value = 0
            
            # ============================================================
            # CEK APAKAH ADA DATA
            # ============================================================
            if last_timestamp is None:
                print("⚠️ [Sensor] Tidak ada data di InfluxDB")
                return JsonResponse({
                    'lux': 0,
                    'adc': 0,
                    'lamp_status': 0,
                    'status': 'offline',
                    'message': 'No data in InfluxDB'
                })
            
            # ============================================================
            # HITUNG SELISIH WAKTU
            # ============================================================
            if last_timestamp.tzinfo is not None:
                last_timestamp = last_timestamp.replace(tzinfo=None)
            
            current_time = datetime.utcnow()
            time_diff = (current_time - last_timestamp).total_seconds()
            
            # ============================================================
            # JIKA LEBIH DARI 15 DETIK → OFFLINE
            # ============================================================
            if time_diff > SENSOR_TIMEOUT_SECONDS:
                print(f"🔴 [Sensor] TIMEOUT! ({time_diff:.1f}s) → OFFLINE")
                return JsonResponse({
                    'lux': 0,
                    'adc': 0,
                    'lamp_status': 0,
                    'status': 'offline',
                    'message': f'Sensor offline (no data for {time_diff:.1f}s)'
                })
            
            # ============================================================
            # SENSOR ONLINE → kirim data real
            # ============================================================
            print(f"✅ [Sensor] ONLINE: Lux={lux_value}, Status={status_value}, Age={time_diff:.1f}s")
            
            return JsonResponse({
                'lux': lux_value,
                'adc': adc_value,
                'lamp_status': status_value,
                'status': 'online'
            })
            
    except Exception as e:
        print(f"❌ [Sensor] Error: {e}")
        return JsonResponse({
            'lux': 0,
            'adc': 0,
            'lamp_status': 0,
            'status': 'offline',
            'error': str(e)
        }, status=500)