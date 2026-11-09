# WaterGuard App V2 — FIRST SPARK / JJM Pipe Stress Monitoring

This is a **demo-first** Flask web app with an Android WebView wrapper. It includes the required five node states, zone overview, node detail, 24-hour pressure history, alert list/detail, battery and heartbeat status, and the teammate's original 3D chamber viewer.

## 1. Run the web app

Requires Python 3.10+.

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 . The app is clearly labelled DEMO DATA.

## 2. Routes

- `/` — zone overview and five node states
- `/nodes/NODE-01` — node details and 24-hour pressure graph
- `/alerts` — WARNING/CRITICAL alert list
- `/alerts/ALT-0003` — full alert detail
- `/viewer` — original 3D chamber viewer

## 3. API

- `GET /api/overview`
- `GET /api/nodes`
- `GET /api/nodes/<node_id>`
- `GET /api/nodes/<node_id>/history`
- `GET /api/alerts`
- `GET /api/alerts/<alert_id>`
- `GET /api/config`
- `POST /api/ingest`

Example ingest payload (illustrative only):

```json
{
  "node_id": "NODE-06",
  "zone": "ZONE-01",
  "pipe_section_id": "ZONE-N-P08",
  "pressure_Pa": 2500,
  "battery_pct": 90,
  "timestamp": "2026-11-05T10:30:00Z"
}
```

## 4. Important scope and limitations

- Sample readings and 24-hour history are generated for demonstration. They are not actual sensor measurements.
- Alert tiers are sample data supplied by the demo layer. This app does not implement or validate the engineering algorithm.
- Exact WARNING/CRITICAL thresholds remain TBD and are exposed as null in `/api/config`; the app does not hardcode operational thresholds.
- The 3–7 day lead time and under-5-minute alert delivery are project targets, not proven by this demo.
- This starter currently uses in-memory demo data. It does **not** provide cloud persistence, MQTT, Firebase/ThingsBoard, or real push notifications yet. Do not describe those as completed.
- `/api/ingest` is an unauthenticated prototype endpoint. Add authentication, validation, secure transport, and a cloud/MQTT bridge before field use.
- No resident names, phone numbers, or addresses are collected.

## 5. Android app

Open the `android` folder in Android Studio. In `MainActivity.kt`, set `WEB_APP_URL` to the URL where this Flask app is hosted. For Android Emulator, use `http://10.0.2.2:5000/`. For a physical phone, use your computer's LAN IP (both devices on same Wi-Fi), e.g. `http://192.168.1.10:5000/`. For release, use HTTPS hosting.

The Android app is a WebView shell around the same web app, so both platforms share the interface and backend.

## 6. Next integration tasks

1. Team agrees final cloud provider (Firebase or ThingsBoard), MQTT topics, node/zone IDs and pipe-section ID convention.
2. Add cloud persistence and authenticated MQTT/cloud ingestion.
3. Fetch threshold configuration from cloud; algorithm/ECE team defines validated values.
4. Add Firebase Cloud Messaging or ThingsBoard push notifications and verify end-to-end delivery under 5 minutes.
5. Implement real 7-day baseline status from cloud/algorithm output and real offline heartbeat timeout configuration.
6. Validate the 128 Hz transition sampling and pressure unit conversion with the hardware team.
