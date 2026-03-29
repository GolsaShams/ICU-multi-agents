import time, sqlite3, requests

def run_agent():
    print("AI Agent is watching bed_01...")
    while True:
        try:
            conn = sqlite3.connect('icu_database.db')
            conn.row_factory = sqlite3.Row
            p = conn.execute('SELECT * FROM patients WHERE bed_id = "bed_01"').fetchone()
            conn.close()

            if p and p['hr'] > 100 and p['temp'] > 38.0:
                requests.post("http://127.0.0.1:5000/post_alert", json={
                    "bed_id": "bed_01", 
                    "alert": f"CRITICAL: High HR ({p['hr']}) and Temp ({p['temp']})"
                })
            time.sleep(2)
        except:
            time.sleep(2)

if __name__ == "__main__":
    run_agent()
