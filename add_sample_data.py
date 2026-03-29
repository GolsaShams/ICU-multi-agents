import sqlite3

def setup_database_samples():
    conn = sqlite3.connect('icu_database.db')
    cursor = conn.cursor()
    
    # Create the standardized patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            bed_id TEXT PRIMARY KEY, 
            hr INTEGER, 
            spo2 INTEGER, 
            temp REAL, 
            status TEXT
        )
    ''')

    # Adding 4 different samples for a better demo
    # Bed 01 & 04 are designed to trigger the SpO2 Agent
    samples = [
        ('bed_01', 105, 88, 38.2, 'Stable'),
        ('bed_02', 72, 98, 36.5, 'Stable'),
        ('bed_03', 90, 94, 37.0, 'Stable'),
        ('bed_04', 115, 82, 39.1, 'Stable')
    ]

    for sample in samples:
        cursor.execute('''
            INSERT OR REPLACE INTO patients (bed_id, hr, spo2, temp, status) 
            VALUES (?, ?, ?, ?, ?)
        ''', sample)
    
    conn.commit()
    conn.close()
    print("Database updated with 4 clinical samples.")

if __name__ == "__main__":
    setup_database_samples()