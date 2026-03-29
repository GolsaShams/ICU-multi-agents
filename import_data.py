import pandas as pd
import sqlite3
import gzip

def import_mimic_to_db():
    conn = sqlite3.connect('icu_database.db')
    print("Reading compressed MIMIC data...")

    try:
        # We read a chunk of chartevents.csv.gz (e.g., first 5000 rows) for testing
        # This table contains vital signs like Heart Rate and Temp
        df = pd.read_csv('chartevents.csv.gz', compression='gzip', nrows=5000)
        
        # Creating a new table in your SQL database for real clinical data
        df.to_sql('mimic_vitals', conn, if_exists='replace', index=False)
        print("Successfully imported 5000 rows into 'mimic_vitals' table.")
        
    except Exception as e:
        print(f"Error during import: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import_mimic_to_db()