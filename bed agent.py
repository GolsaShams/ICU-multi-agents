import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_engine, TABLE_BED_AVAILABILITY


class BedAvailabilityAgent:
    def __init__(self):
        self.agent_name = "ICU Bed Availability Manager"
        self.total_beds = 10
        self.engine = get_engine()

    def get_all_beds_status(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(text(f'SELECT bed_id, status, patient_name, admission_date FROM {TABLE_BED_AVAILABILITY} ORDER BY bed_id ASC')).mappings().all()
        return [dict(r) for r in rows]

    def get_available_beds(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(text(f"SELECT bed_id, status FROM {TABLE_BED_AVAILABILITY} WHERE status = 'Available' ORDER BY bed_id ASC")).mappings().all()
        return [dict(r) for r in rows]

    def get_occupied_beds(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(text(f"SELECT bed_id, patient_name, admission_date, status FROM {TABLE_BED_AVAILABILITY} WHERE status = 'Occupied' ORDER BY bed_id ASC")).mappings().all()
        return [dict(r) for r in rows]

    def get_bed_occupancy_rate(self) -> float:
        with self.engine.connect() as conn:
            occupied = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_BED_AVAILABILITY} WHERE status = 'Occupied'")).scalar()
        return (occupied / self.total_beds) * 100

    def find_nearest_available_bed(self) -> str:
        available = self.get_available_beds()
        if not available:
            return None
        available.sort(key=lambda x: x['bed_id'])
        return available[0]['bed_id']

    def generate_occupancy_report(self) -> Dict[str, Any]:
        all_beds = self.get_all_beds_status()
        available_beds = self.get_available_beds()
        occupied_beds = self.get_occupied_beds()
        occupancy_rate = self.get_bed_occupancy_rate()
        return {
            'agent_name': self.agent_name, 'timestamp': datetime.now().isoformat(),
            'total_beds': self.total_beds, 'occupied_beds': len(occupied_beds),
            'available_beds': len(available_beds), 'occupancy_rate': round(occupancy_rate, 2),
            'critical_status': 'CRITICAL' if occupancy_rate >= 90 else 'WARNING' if occupancy_rate >= 70 else 'NORMAL',
            'all_beds': all_beds, 'availability': 'AVAILABLE' if len(available_beds) > 0 else 'NO BEDS AVAILABLE'
        }

    def execute_task(self) -> Dict[str, Any]:
        print("\n" + "="*60)
        print(f"ICU BED AVAILABILITY AGENT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        report = self.generate_occupancy_report()
        print(f"\n  BED AVAILABILITY SUMMARY:")
        print(f"   Total Beds: {report['total_beds']}")
        print(f"   Occupied: {report['occupied_beds']}")
        print(f"   Available: {report['available_beds']}")
        print(f"   Occupancy Rate: {report['occupancy_rate']}%")
        print(f"\n  BED STATUS ({report['total_beds']} beds):")
        for bed in report['all_beds']:
            is_occ = bed['status'] == 'Occupied'
            status_icon = "[X]" if is_occ else "[O]"
            patient_info = bed['patient_name'] if is_occ else "AVAILABLE"
            print(f"   {status_icon} {bed['bed_id']}: {patient_info}")
        print("="*60)
        return report


if __name__ == "__main__":
    agent = BedAvailabilityAgent()
    agent.execute_task()
