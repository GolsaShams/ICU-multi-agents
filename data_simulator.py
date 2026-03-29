import requests, time, random

def start_sim():
    print("Streaming live vitals...")
    while True:
        vitals = {
            "bed_id": "bed_01",
            "hr": random.randint(70, 115), 
            "temp": round(random.uniform(36.0, 39.5), 1)
        }
        try:
            requests.post("http://127.0.0.1:5000/post_vitals", json=vitals)
        except: pass
        time.sleep(3)

if __name__ == "__main__":
    start_sim()