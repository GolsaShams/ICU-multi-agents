import pandas as pd
import sqlite3

def import_real_data():
    conn = sqlite3.connect('icu_database.db')
    print("Reading real MIMIC-IV clinical events...")
    try:
        # We read 1000 rows to test the agent logic
        df = pd.read_csv('chartevents.csv.gz', compression='gzip', nrows=1000)
        
        # FIX: Ensure table name is 'mimic_vitals'
        df.to_sql('mimic_vitals', conn, if_exists='replace', index=False)
        print("Successfully imported data into table: mimic_vitals")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import_real_data()