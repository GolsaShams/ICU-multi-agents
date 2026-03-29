import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "icu_agents.db")


class BedAvailabilityAgent:
    """
    Agent for tracking ICU bed availability and patient status across all 10 beds.
    Monitors occupancy, manages admissions/discharges, and provides bed status alerts.
    """
    
    def __init__(self):
        self.agent_name = "ICU Bed Availability Manager"
        self.db_name = DB_NAME
        self.total_beds = 10
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_name)
    
    def get_all_beds_status(self) -> List[Dict[str, Any]]:
        """
        Get the status of all ICU beds.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bed_id, is_occupied, patient_name, admission_date, status, last_updated
            FROM bed_availability
            ORDER BY bed_id ASC
        ''')
        
        columns = ['bed_id', 'is_occupied', 'patient_name', 'admission_date', 'status', 'last_updated']
        beds = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return beds
    
    def get_available_beds(self) -> List[Dict[str, Any]]:
        """
        Get all available (unoccupied) beds.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bed_id, status, last_updated
            FROM bed_availability
            WHERE is_occupied = 0
            ORDER BY bed_id ASC
        ''')
        
        columns = ['bed_id', 'status', 'last_updated']
        available_beds = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return available_beds
    
    def get_occupied_beds(self) -> List[Dict[str, Any]]:
        """
        Get all occupied beds with patient information.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bed_id, patient_name, admission_date, status, last_updated
            FROM bed_availability
            WHERE is_occupied = 1
            ORDER BY bed_id ASC
        ''')
        
        columns = ['bed_id', 'patient_name', 'admission_date', 'status', 'last_updated']
        occupied_beds = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return occupied_beds
    
    def admit_patient(self, bed_id: str, patient_name: str) -> bool:
        """
        Admit a patient to a specific bed.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if bed is available
            cursor.execute('SELECT is_occupied FROM bed_availability WHERE bed_id = ?', (bed_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
            
            if result[0] == 1:  # Bed is already occupied
                conn.close()
                return False
            
            # Update bed with patient info
            current_time = datetime.now()
            cursor.execute('''
                UPDATE bed_availability
                SET is_occupied = 1, patient_name = ?, admission_date = ?, status = 'Occupied', last_updated = ?
                WHERE bed_id = ?
            ''', (patient_name, current_time, current_time, bed_id))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error admitting patient: {e}")
            return False
    
    def discharge_patient(self, bed_id: str) -> bool:
        """
        Discharge a patient from a bed and make it available.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            current_time = datetime.now()
            cursor.execute('''
                UPDATE bed_availability
                SET is_occupied = 0, patient_name = NULL, admission_date = NULL, status = 'Available', last_updated = ?
                WHERE bed_id = ?
            ''', (current_time, bed_id))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error discharging patient: {e}")
            return False
    
    def get_patient_length_of_stay(self, bed_id: str) -> str:
        """
        Calculate patient length of stay in a specific bed.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT admission_date FROM bed_availability WHERE bed_id = ?', (bed_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return "N/A"
        
        admission_date = datetime.fromisoformat(result[0])
        length_of_stay = datetime.now() - admission_date
        
        days = length_of_stay.days
        hours = length_of_stay.seconds // 3600
        minutes = (length_of_stay.seconds % 3600) // 60
        
        return f"{days}d {hours}h {minutes}m"
    
    def get_bed_occupancy_rate(self) -> float:
        """
        Get the current ICU occupancy rate as a percentage.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM bed_availability WHERE is_occupied = 1')
        occupied = cursor.fetchone()[0]
        conn.close()
        
        return (occupied / self.total_beds) * 100
    
    def find_nearest_available_bed(self) -> str:
        """
        Find the nearest available bed (by bed number).
        """
        available = self.get_available_beds()
        
        if not available:
            return None
        
        # Sort by bed number and return the first (lowest number) available bed
        available.sort(key=lambda x: int(x['bed_id'].split('_')[1]))
        return available[0]['bed_id']
    
    def get_bed_status(self, bed_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a specific bed.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bed_id, is_occupied, patient_name, admission_date, status, last_updated
            FROM bed_availability
            WHERE bed_id = ?
        ''', (bed_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        columns = ['bed_id', 'is_occupied', 'patient_name', 'admission_date', 'status', 'last_updated']
        bed_info = dict(zip(columns, result))
        
        # Add length of stay
        if bed_info['is_occupied']:
            bed_info['length_of_stay'] = self.get_patient_length_of_stay(bed_id)
        else:
            bed_info['length_of_stay'] = "N/A"
        
        return bed_info
    
    def generate_occupancy_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive occupancy report for all beds.
        """
        all_beds = self.get_all_beds_status()
        available_beds = self.get_available_beds()
        occupied_beds = self.get_occupied_beds()
        
        occupancy_rate = self.get_bed_occupancy_rate()
        
        return {
            'agent_name': self.agent_name,
            'timestamp': datetime.now().isoformat(),
            'total_beds': self.total_beds,
            'occupied_beds': len(occupied_beds),
            'available_beds': len(available_beds),
            'occupancy_rate': round(occupancy_rate, 2),
            'critical_status': 'CRITICAL' if occupancy_rate >= 90 else 'WARNING' if occupancy_rate >= 70 else 'NORMAL',
            'all_beds': all_beds,
            'availability': 'AVAILABLE' if len(available_beds) > 0 else 'NO BEDS AVAILABLE'
        }
    
    def execute_task(self) -> Dict[str, Any]:
        """
        Execute the main task of the agent - monitor bed availability and status.
        """
        print("\n" + "="*60)
        print(f"ICU BED AVAILABILITY AGENT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        report = self.generate_occupancy_report()
        
        print(f"\n🛏️  BED AVAILABILITY SUMMARY:")
        print(f"   Total Beds: {report['total_beds']}")
        print(f"   Occupied: {report['occupied_beds']}")
        print(f"   Available: {report['available_beds']}")
        print(f"   Occupancy Rate: {report['occupancy_rate']}%")
        
        print(f"\n📊 BED STATUS ({report['total_beds']} beds):")
        for bed in report['all_beds']:
            status_icon = "🔴" if bed['is_occupied'] else "🟢"
            patient_info = bed['patient_name'] if bed['is_occupied'] else "AVAILABLE"
            los = ""
            if bed['is_occupied']:
                los = f" | {self.get_patient_length_of_stay(bed['bed_id'])}"
            print(f"   {status_icon} {bed['bed_id']}: {patient_info}{los}")
        
        print(f"\n⚠️  CRITICAL ALERT:" if report['critical_status'] != 'NORMAL' else f"\n✅ STATUS:")
        print(f"   {report['critical_status']}")
        
        if report['available_beds'] == 0:
            print(f"   🚨 NO BEDS AVAILABLE - Urgent bed management needed!")
        elif report['available_beds'] <= 2:
            print(f"   ⚠️  Only {report['available_beds']} bed(s) available")
        else:
            nearest = self.find_nearest_available_bed()
            print(f"   Nearest available bed: {nearest}")
        
        print("="*60)
        
        return report


if __name__ == "__main__":
    agent = BedAvailabilityAgent()
    agent.execute_task()
