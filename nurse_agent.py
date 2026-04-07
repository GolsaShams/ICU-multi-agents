import os
import sys
import time
import requests
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_engine, TABLE_PATIENTS, TABLE_NURSE_ASSIGNMENTS


class NurseAgent:
    def __init__(self):
        self.agent_name = "ICU Nurse Assignment Manager"
        self.engine = get_engine()
        self.api = "http://127.0.0.1:5000/post_alert"
        self.max_beds_per_nurse = 3

    def get_all_assignments(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(text(f'SELECT * FROM {TABLE_NURSE_ASSIGNMENTS} ORDER BY nurse_id')).mappings().all()
        return [dict(r) for r in rows]

    def get_nurse_workload_summary(self) -> Dict[str, Any]:
        with self.engine.connect() as conn:
            nurses = conn.execute(text(f'SELECT * FROM {TABLE_NURSE_ASSIGNMENTS}')).mappings().all()
            patients = conn.execute(text(f'SELECT bed_id, status FROM {TABLE_PATIENTS}')).mappings().all()
        critical_beds = {p['bed_id'] for p in patients if p['status'] == 'Critical'}
        total_nurses = len(nurses)
        overloaded = 0
        high_workload = 0
        for n in nurses:
            assigned = n['assigned_beds'] or ''
            beds = [b.strip() for b in assigned.split(',') if b.strip()]
            critical_count = sum(1 for b in beds if b in critical_beds)
            if len(beds) >= self.max_beds_per_nurse or critical_count >= 2:
                overloaded += 1
            elif n['workload'] == 'High':
                high_workload += 1
        return {'agent_name': self.agent_name, 'total_nurses': total_nurses, 'overloaded': overloaded,
            'high_workload': high_workload, 'normal': total_nurses - overloaded - high_workload,
            'timestamp': datetime.now().isoformat()}

    def update_workloads(self):
        with self.engine.begin() as conn:
            nurses = conn.execute(text(f'SELECT * FROM {TABLE_NURSE_ASSIGNMENTS}')).mappings().all()
            patients = conn.execute(text(f'SELECT bed_id, status FROM {TABLE_PATIENTS}')).mappings().all()
            critical_beds = {p['bed_id'] for p in patients if p['status'] == 'Critical'}
            warning_beds = {p['bed_id'] for p in patients if p['status'] == 'Warning'}
            for n in nurses:
                assigned = n['assigned_beds'] or ''
                beds = [b.strip() for b in assigned.split(',') if b.strip()]
                critical_count = sum(1 for b in beds if b in critical_beds)
                warning_count = sum(1 for b in beds if b in warning_beds)
                if critical_count >= 2 or len(beds) >= self.max_beds_per_nurse:
                    workload = 'Overloaded'
                elif critical_count >= 1 or warning_count >= 2:
                    workload = 'High'
                else:
                    workload = 'Normal'
                conn.execute(text(f'UPDATE {TABLE_NURSE_ASSIGNMENTS} SET workload=:wl WHERE nurse_id=:nid'),
                    {'wl': workload, 'nid': n['nurse_id']})

    def execute_task(self) -> Dict[str, Any]:
        print("\n" + "=" * 60)
        print(f"ICU NURSE AGENT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        self.update_workloads()
        summary = self.get_nurse_workload_summary()
        assignments = self.get_all_assignments()
        print(f"\n  NURSE WORKLOAD SUMMARY:")
        print(f"   Total Nurses: {summary['total_nurses']}")
        print(f"   Overloaded:   {summary['overloaded']}")
        print(f"   High:         {summary['high_workload']}")
        print(f"   Normal:       {summary['normal']}")
        print(f"\n  ASSIGNMENTS:")
        for a in assignments:
            icon = "[!]" if a['workload'] == 'Overloaded' else "[*]" if a['workload'] == 'High' else "[o]"
            print(f"   {icon} {a['nurse_name']} [{a['shift']}] -> {a['assigned_beds']}  ({a['workload']})")
        print("=" * 60)
        return summary


if __name__ == "__main__":
    agent = NurseAgent()
    agent.execute_task()
