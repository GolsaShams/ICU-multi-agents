import sqlite3

def create_fresh_db():
    # We use a new name to avoid any conflict with old databases
    conn = sqlite3.connect('icu_agents.db')
    cursor = conn.cursor()
    
    # Create the patients table with all required columns
    cursor.execute('DROP TABLE IF EXISTS patients')
    cursor.execute('''
        CREATE TABLE patients (
            bed_id TEXT PRIMARY KEY,
            hr INTEGER,
            spo2 INTEGER,
            temp REAL,
            status TEXT
        )
    ''')
    
    # Create the alerts table for the dashboard
    cursor.execute('DROP TABLE IF EXISTS alerts')
    cursor.execute('''
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bed_id TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add 4 test patients with different clinical data
    patients_data = [
        ('bed_01', 110, 88, 38.5, 'Critical'), # Will trigger both Agents
        ('bed_02', 75, 98, 36.6, 'Stable'),   # Normal
        ('bed_03', 95, 85, 37.0, 'Critical'), # Will trigger SpO2 Agent
        ('bed_04', 125, 95, 39.2, 'Critical') # Will trigger Vitals Agent
    ]
    
    cursor.executemany('INSERT INTO patients VALUES (?, ?, ?, ?, ?)', patients_data)
    
    conn.commit()
    conn.close()
    print("New Database 'icu_agents.db' created successfully with all columns.")

if __name__ == "__main__":
    create_fresh_db()