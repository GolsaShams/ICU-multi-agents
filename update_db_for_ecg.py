import sqlite3

def update_database_with_ecg():
    conn = sqlite3.connect('icu_agents.db')
    cursor = conn.cursor()
    
    # Add heart_rhythm column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE patients ADD COLUMN heart_rhythm TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Update samples with ECG data
    ecg_samples = [
        ('Sinus Tachycardia', 'bed_01'), # High HR + Fever
        ('Normal Sinus Rhythm', 'bed_02'), # Healthy
        ('Bradycardia', 'bed_03'),         # Slow rhythm
        ('Atrial Fibrillation', 'bed_04')  # Irregular/Critical
    ]
    
    for rhythm, bed in ecg_samples:
        cursor.execute('UPDATE patients SET heart_rhythm = ? WHERE bed_id = ?', (rhythm, bed))
    
    conn.commit()
    conn.close()
    print("Database updated with ECG rhythm samples.")

if __name__ == "__main__":
    update_database_with_ecg()