from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, render_template, request, abort
import random

app = Flask(__name__)

# Review demo only. The values below are illustrative, not calibrated sensor data.
# The app displays alert tiers supplied by the demo/cloud layer; it does not invent
# engineering thresholds or claim to detect cracks.
NOW = datetime.now(timezone.utc).replace(microsecond=0)

NODE_SEED = [
    {"node_id":"NODE-01", "zone":"ZONE-01", "chamber":"CH-01", "pipe_section_id":"ZONE-N-P03", "pressure_Pa":2500, "battery_pct":92, "status":"NORMAL", "signal_status":"Good", "last_seen_minutes":2, "baseline_day":7, "baseline_active":True},
    {"node_id":"NODE-02", "zone":"ZONE-01", "chamber":"CH-02", "pipe_section_id":"ZONE-N-P04", "pressure_Pa":-3200, "battery_pct":84, "status":"WARNING", "signal_status":"Good", "last_seen_minutes":1, "baseline_day":7, "baseline_active":True},
    {"node_id":"NODE-03", "zone":"ZONE-01", "chamber":"CH-03", "pipe_section_id":"ZONE-N-P05", "pressure_Pa":8700, "battery_pct":76, "status":"CRITICAL", "signal_status":"Fair", "last_seen_minutes":1, "baseline_day":7, "baseline_active":True},
    {"node_id":"NODE-04", "zone":"ZONE-01", "chamber":"CH-04", "pipe_section_id":"ZONE-N-P06", "pressure_Pa":1800, "battery_pct":41, "status":"OFFLINE", "signal_status":"No signal", "last_seen_minutes":1500, "baseline_day":7, "baseline_active":True},
    {"node_id":"NODE-05", "zone":"ZONE-01", "chamber":"CH-05", "pipe_section_id":"ZONE-N-P07", "pressure_Pa":1200, "battery_pct":98, "status":"LEARNING", "signal_status":"Good", "last_seen_minutes":3, "baseline_day":4, "baseline_active":False},
]

nodes = [dict(n) for n in NODE_SEED]

def iso_minutes_ago(minutes):
    return (NOW - timedelta(minutes=minutes)).isoformat().replace('+00:00','Z')

def node_payload(n):
    item = dict(n)
    item['timestamp'] = iso_minutes_ago(item['last_seen_minutes'])
    item['last_seen'] = item['timestamp']
    item['location'] = {"zone": item['zone'], "chamber": item['chamber'], "pipe_point": item['pipe_section_id']}
    item['status_led'] = {"NORMAL":"Green", "WARNING":"Amber", "CRITICAL":"Red", "OFFLINE":"Grey", "LEARNING":"Blue"}[item['status']]
    return item

# Prebuilt illustrative alerts. No personal data is stored or displayed.
alerts = [
    {"alert_id":"ALT-0003", "alert_tier":"CRITICAL", "zone":"ZONE-01", "node_id":"NODE-03", "pipe_section_id":"ZONE-N-P05", "pressure_Pa":8700, "battery_pct":76, "timestamp":iso_minutes_ago(12), "message":"Strong stress-pattern demo event. Inspect the indicated pipe section.", "suggested_action":"Inspect pipe section ZONE-N-P05.", "lead_time_estimate":"3–7 days (project target; not validated by demo data)"},
    {"alert_id":"ALT-0002", "alert_tier":"WARNING", "zone":"ZONE-01", "node_id":"NODE-02", "pipe_section_id":"ZONE-N-P04", "pressure_Pa":-3200, "battery_pct":84, "timestamp":iso_minutes_ago(28), "message":"Early stress-pattern demo event. Review the pressure history.", "suggested_action":"Review and inspect pipe section ZONE-N-P04.", "lead_time_estimate":"3–7 days (project target; not validated by demo data)"},
]

# Example cloud configuration shape. Threshold values are deliberately TBD.
cloud_config = {"pressure_unit":"Pa", "gauge_range_kPa":[-10,10], "warning_threshold":None, "critical_threshold":None, "offline_after_hours":24, "sampling_hz_during_transitions":128, "alert_delivery_target_minutes":5}

# 24-hour demo history, one illustrative point per hour per node.
history = {}
for n in nodes:
    series=[]
    for h in range(23,-1,-1):
        variation = ((h*37 + int(n['node_id'][-2:])*19) % 900) - 450
        value = n['pressure_Pa'] + variation
        series.append({"timestamp":(NOW-timedelta(hours=h)).isoformat().replace('+00:00','Z'), "pressure_Pa":value})
    history[n['node_id']] = series

@app.get('/')
def dashboard():
    return render_template('index.html', page='overview', title='Zone overview')

@app.get('/nodes/<node_id>')
def node_detail(node_id):
    if not any(n['node_id']==node_id for n in nodes): abort(404)
    return render_template('index.html', page='node', title='Node details', selected_node=node_id)

@app.get('/alerts')
def alerts_page():
    return render_template('index.html', page='alerts', title='Alerts')

@app.get('/alerts/<alert_id>')
def alert_detail(alert_id):
    if not any(a['alert_id']==alert_id for a in alerts): abort(404)
    return render_template('index.html', page='alert', title='Alert details', selected_alert=alert_id)

@app.get('/viewer')
def viewer():
    return app.send_static_file('chamber_viewer.html')

@app.get('/api/overview')
def api_overview():
    payload=[node_payload(n) for n in nodes]
    counts={s:sum(1 for n in payload if n['status']==s) for s in ['NORMAL','WARNING','CRITICAL','OFFLINE','LEARNING']}
    return jsonify({"demo_data":True,"zone":"ZONE-01","counts":counts,"nodes":payload,"config":cloud_config})

@app.get('/api/nodes')
def api_nodes():
    return jsonify([node_payload(n) for n in nodes])

@app.get('/api/nodes/<node_id>')
def api_node(node_id):
    n=next((x for x in nodes if x['node_id']==node_id),None)
    if not n: abort(404)
    return jsonify(node_payload(n))

@app.get('/api/nodes/<node_id>/history')
def api_node_history(node_id):
    if node_id not in history: abort(404)
    return jsonify({"node_id":node_id,"unit":"Pa","period":"24h","points":history[node_id]})

@app.get('/api/alerts')
def api_alerts():
    return jsonify(sorted(alerts,key=lambda a:a['timestamp'],reverse=True))

@app.get('/api/alerts/<alert_id>')
def api_alert(alert_id):
    a=next((x for x in alerts if x['alert_id']==alert_id),None)
    if not a: abort(404)
    return jsonify(a)

@app.get('/api/config')
def api_config():
    return jsonify(cloud_config)

@app.post('/api/demo/reset')
def demo_reset():
    global nodes, alerts
    nodes=[dict(n) for n in NODE_SEED]
    return jsonify({"ok":True,"message":"Demo states restored."})

@app.post('/api/ingest')
def ingest():
    """Prototype cloud-ingest contract. Expected keys: node_id, zone,
    pipe_section_id, pressure_Pa, battery_pct, timestamp. In production,
    authenticate this endpoint and forward MQTT/cloud messages here.
    """
    data=request.get_json(silent=True) or {}
    required=['node_id','zone','pipe_section_id','pressure_Pa','battery_pct','timestamp']
    missing=[key for key in required if key not in data]
    if missing: return jsonify({"error":"Missing required fields", "fields":missing}),400
    try:
        pressure=float(data['pressure_Pa']); battery=float(data['battery_pct'])
        if not 0 <= battery <= 100: raise ValueError()
    except (TypeError,ValueError):
        return jsonify({"error":"pressure_Pa must be numeric and battery_pct must be between 0 and 100"}),400
    existing=next((n for n in nodes if n['node_id']==str(data['node_id'])),None)
    if existing is None:
        existing={"node_id":str(data['node_id']),"zone":str(data['zone']),"chamber":"CH-NEW","pipe_section_id":str(data['pipe_section_id']),"baseline_day":0,"baseline_active":False}
        nodes.append(existing)
        history[existing['node_id']]=[]
    existing.update({"zone":str(data['zone']),"pipe_section_id":str(data['pipe_section_id']),"pressure_Pa":pressure,"battery_pct":battery,"status":"LEARNING" if not existing.get('baseline_active') else "NORMAL","signal_status":"Good","last_seen_minutes":0})
    return jsonify({"ok":True,"accepted":{k:data[k] for k in required}}),202

@app.get('/api/health')
def health(): return jsonify({"ok":True,"mode":"demo","storage":"in-memory; not cloud persistence"})

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
