import sqlite3
import os
import time
import requests
from datetime import datetime
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "icu_agents.db")


class NurseAgent:
    """
    Agent for monitoring nurse workload and patient-nurse assignments.
    Tracks nurse shifts, workload levels, and raises alerts when nurses
    are overloaded or critical patients lack adequate coverage.
    """

    def __init__(self):
        self.agent_name = "ICU Nurse Assignment Manager"
        self.db_name = DB_NAME
        self.api = "http://127.0.0.1:5000/post_alert"
        self.max_beds_per_nurse = 3  # threshold for overload

    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_assignments(self) -> List[Dict[str, Any]]:
        """Get all nurse assignments."""
        conn = self.get_connection()
        rows = conn.execute('SELECT * FROM nurse_assignments ORDER BY nurse_id').fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_nurse_workload_summary(self) -> Dict[str, Any]:
        """Calculate overall workload summary across all nurses."""
        conn = self.get_connection()
        nurses = conn.execute('SELECT * FROM nurse_assignments').fetchall()
        patients = conn.execute('SELECT bed_id, status FROM patients').fetchall()
        conn.close()

        critical_beds = {p['bed_id'] for p in patients if p['status'] == 'Critical'}
        total_nurses = len(nurses)
        overloaded = 0
        high_workload = 0

        for n in nurses:
            beds = [b.strip() for b in n['assigned_beds'].split(',') if b.strip()]
            critical_count = sum(1 for b in beds if b in critical_beds)
            if len(beds) >= self.max_beds_per_nurse or critical_count >= 2:
                overloaded += 1
            elif n['workload'] == 'High':
                high_workload += 1

        return {
            'agent_name': self.agent_name,
            'total_nurses': total_nurses,
            'overloaded': overloaded,
            'high_workload': high_workload,
            'normal': total_nurses - overloaded - high_workload,
            'timestamp': datetime.now().isoformat(),
        }

    def update_workloads(self):
        """Recalculate and update workload levels based on current patient status."""
        conn = self.get_connection()
        nurses = conn.execute('SELECT * FROM nurse_assignments').fetchall()
        patients = conn.execute('SELECT bed_id, status FROM patients').fetchall()

        critical_beds = {p['bed_id'] for p in patients if p['status'] == 'Critical'}
        warning_beds = {p['bed_id'] for p in patients if p['status'] == 'Warning'}
        now = datetime.now().isoformat()

        for n in nurses:
            beds = [b.strip() for b in n['assigned_beds'].split(',') if b.strip()]
            critical_count = sum(1 for b in beds if b in critical_beds)
            warning_count = sum(1 for b in beds if b in warning_beds)

            if critical_count >= 2 or len(beds) >= self.max_beds_per_nurse:
                workload = 'Overloaded'
            elif critical_count >= 1 or warning_count >= 2:
                workload = 'High'
            else:
                workload = 'Normal'

            conn.execute(
                'UPDATE nurse_assignments SET workload = ?, last_updated = ? WHERE nurse_id = ?',
                (workload, now, n['nurse_id']),
            )

        conn.commit()
        conn.close()

    def check_and_alert(self):
        """Check for alert conditions and post to the dashboard."""
        conn = self.get_connection()
        nurses = conn.execute('SELECT * FROM nurse_assignments').fetchall()
        patients = conn.execute('SELECT bed_id, status FROM patients').fetchall()
        conn.close()

        critical_beds = {p['bed_id'] for p in patients if p['status'] == 'Critical'}

        for n in nurses:
            beds = [b.strip() for b in n['assigned_beds'].split(',') if b.strip()]
            critical_count = sum(1 for b in beds if b in critical_beds)

            if critical_count >= 2:
                try:
                    requests.post(self.api, json={
                        "bed_id": beds[0],
                        "alert": (f"Nurse Agent: {n['nurse_name']} has {critical_count} "
                                  f"critical patients — assistance required!")
                    }, timeout=3)
                except Exception:
                    pass

    def execute_task(self) -> Dict[str, Any]:
        """Execute the main nurse monitoring task."""
        print("\n" + "=" * 60)
        print(f"ICU NURSE AGENT — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        self.update_workloads()
        summary = self.get_nurse_workload_summary()
        assignments = self.get_all_assignments()

        print(f"\n👩‍⚕️ NURSE WORKLOAD SUMMARY:")
        print(f"   Total Nurses: {summary['total_nurses']}")
        print(f"   Overloaded:   {summary['overloaded']}")
        print(f"   High:         {summary['high_workload']}")
        print(f"   Normal:       {summary['normal']}")

        print(f"\n📋 ASSIGNMENTS:")
        for a in assignments:
            icon = "🔴" if a['workload'] == 'Overloaded' else "🟡" if a['workload'] == 'High' else "🟢"
            print(f"   {icon} {a['nurse_name']} [{a['shift']}] → {a['assigned_beds']}  ({a['workload']})")

        print("=" * 60)
        return summary

    def run_loop(self):
        """Continuous monitoring loop."""
        print("--- Nurse Agent is Active ---")
        while True:
            try:
                self.update_workloads()
                self.check_and_alert()
                time.sleep(5)
            except Exception as e:
                print(f"Nurse Agent Error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    agent = NurseAgent()
    agent.execute_task()
