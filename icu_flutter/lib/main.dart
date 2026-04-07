import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const ICUDashboardApp());
}

class ICUDashboardApp extends StatelessWidget {
  const ICUDashboardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ICU Multi-Agent Virtual Assistant',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Segoe UI',
        brightness: Brightness.light,
        colorSchemeSeed: const Color(0xFF312E81),
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Data Models
// ═══════════════════════════════════════════════════════════════════════════

class Patient {
  final String bedId;
  final int hr;
  final int spo2;
  final double temp;
  final String heartRhythm;
  final String status;

  Patient({
    required this.bedId,
    required this.hr,
    required this.spo2,
    required this.temp,
    required this.heartRhythm,
    required this.status,
  });

  factory Patient.fromJson(Map<String, dynamic> json) {
    return Patient(
      bedId: json['bed_id'] ?? '',
      hr: json['hr'] ?? 0,
      spo2: json['spo2'] ?? 0,
      temp: (json['temp'] ?? 0).toDouble(),
      heartRhythm: json['heart_rhythm'] ?? '',
      status: json['status'] ?? '',
    );
  }
}

class AlertItem {
  final int id;
  final String bedId;
  final String message;
  final String timestamp;

  AlertItem({
    required this.id,
    required this.bedId,
    required this.message,
    required this.timestamp,
  });

  factory AlertItem.fromJson(Map<String, dynamic> json) {
    return AlertItem(
      id: json['id'] ?? 0,
      bedId: json['bed_id'] ?? '',
      message: json['message'] ?? '',
      timestamp: json['timestamp'] ?? '',
    );
  }
}

class BedAvailability {
  final String bedId;
  final bool isOccupied;
  final String? patientName;
  final String? admissionDate;
  final String? expectedDischarge;
  final String status;
  final String? lastUpdated;

  BedAvailability({
    required this.bedId,
    required this.isOccupied,
    this.patientName,
    this.admissionDate,
    this.expectedDischarge,
    required this.status,
    this.lastUpdated,
  });

  factory BedAvailability.fromJson(Map<String, dynamic> json) {
    return BedAvailability(
      bedId: json['bed_id'] ?? '',
      isOccupied: (json['is_occupied'] ?? 0) == 1,
      patientName: json['patient_name'],
      admissionDate: json['admission_date'],
      expectedDischarge: json['expected_discharge'],
      status: json['status'] ?? 'Available',
      lastUpdated: json['last_updated'],
    );
  }
}

class NurseAssignment {
  final String nurseId;
  final String nurseName;
  final String assignedBeds;
  final String shift;
  final String workload;
  final String? lastUpdated;

  NurseAssignment({
    required this.nurseId,
    required this.nurseName,
    required this.assignedBeds,
    required this.shift,
    required this.workload,
    this.lastUpdated,
  });

  factory NurseAssignment.fromJson(Map<String, dynamic> json) {
    return NurseAssignment(
      nurseId: json['nurse_id'] ?? '',
      nurseName: json['nurse_name'] ?? '',
      assignedBeds: json['assigned_beds'] ?? '',
      shift: json['shift'] ?? '',
      workload: json['workload'] ?? 'Normal',
      lastUpdated: json['last_updated'],
    );
  }

  List<String> get bedList =>
      assignedBeds.split(',').map((b) => b.trim()).where((b) => b.isNotEmpty).toList();
}

// ═══════════════════════════════════════════════════════════════════════════
// Dashboard Screen (with bottom navigation)
// ═══════════════════════════════════════════════════════════════════════════

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with SingleTickerProviderStateMixin {
  static const String apiUrl = 'https://icu-multi-agents-dashboard.onrender.com/view';

  List<Patient> patients = [];
  List<AlertItem> alerts = [];
  List<BedAvailability> beds = [];
  List<NurseAssignment> nurses = [];
  bool loading = true;
  String? error;
  Timer? _timer;
  late AnimationController _pulseController;
  int _currentTab = 0;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _fetchData();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchData());
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _fetchData() async {
    try {
      final response = await http.get(Uri.parse(apiUrl));
      if (response.statusCode != 200) {
        throw Exception('Backend error: ${response.statusCode}');
      }
      final data = json.decode(response.body);
      if (!mounted) return;
      setState(() {
        patients =
            (data['patients'] as List).map((p) => Patient.fromJson(p)).toList();
        alerts =
            (data['alerts'] as List).map((a) => AlertItem.fromJson(a)).toList();
        beds = (data['beds'] as List? ?? [])
            .map((b) => BedAvailability.fromJson(b))
            .toList();
        nurses = (data['nurses'] as List? ?? [])
            .map((n) => NurseAssignment.fromJson(n))
            .toList();
        loading = false;
        error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = 'Cannot reach backend at $apiUrl.\nMake sure Flask is running.';
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return _buildLoading();
    if (error != null) return _buildError();
    return _buildDashboard();
  }

  // ── Loading ──

  Widget _buildLoading() {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 48,
              height: 48,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                color: Color(0xFF312E81),
              ),
            ),
            const SizedBox(height: 24),
            const Text('Initializing System...',
                style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF334155))),
            const SizedBox(height: 8),
            Text('Ensure the Flask backend is running on port 5000.',
                style: TextStyle(fontSize: 14, color: Colors.grey.shade500)),
          ],
        ),
      ),
    );
  }

  // ── Error ──

  Widget _buildError() {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 420),
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off_rounded,
                  size: 56, color: Color(0xFFEF4444)),
              const SizedBox(height: 20),
              const Text('Dashboard Offline',
                  style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF334155))),
              const SizedBox(height: 12),
              Text(error!,
                  textAlign: TextAlign.center,
                  style:
                      const TextStyle(fontSize: 14, color: Color(0xFFEF4444))),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: () {
                  setState(() {
                    loading = true;
                    error = null;
                  });
                  _fetchData();
                },
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Main Dashboard ──

  Widget _buildDashboard() {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              _buildHeader(),
              const SizedBox(height: 28),
              Expanded(child: _buildTabContent()),
            ],
          ),
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentTab,
        onDestinationSelected: (i) => setState(() => _currentTab = i),
        backgroundColor: Colors.white,
        indicatorColor: const Color(0xFF312E81).withValues(alpha: 0.12),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.monitor_heart_outlined),
            selectedIcon: Icon(Icons.monitor_heart, color: Color(0xFF312E81)),
            label: 'Monitors',
          ),
          NavigationDestination(
            icon: Icon(Icons.bed_outlined),
            selectedIcon: Icon(Icons.bed, color: Color(0xFF312E81)),
            label: 'Bed Availability',
          ),
          NavigationDestination(
            icon: Icon(Icons.people_outline),
            selectedIcon: Icon(Icons.people, color: Color(0xFF312E81)),
            label: 'Nurse Assignments',
          ),
        ],
      ),
    );
  }

  // ── Tab Content ──

  Widget _buildTabContent() {
    switch (_currentTab) {
      case 0:
        return _buildMonitorsBody();
      case 1:
        return _buildBedAvailabilityTab();
      case 2:
        return _buildNurseAssignmentsTab();
      default:
        return _buildMonitorsBody();
    }
  }

  // ── Header ──

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.04),
              blurRadius: 12,
              offset: const Offset(0, 4)),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                    colors: [Color(0xFF312E81), Color(0xFF4F46E5)]),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.monitor_heart,
                  color: Colors.white, size: 26),
            ),
            const SizedBox(width: 16),
            const Text('ICU MULTI-AGENT VIRTUAL ASSISTANT',
                style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                    color: Color(0xFF1E1B4B),
                    letterSpacing: -0.5)),
          ]),
          Row(children: [
            FadeTransition(
              opacity: _pulseController,
              child: Container(
                width: 10,
                height: 10,
                decoration: const BoxDecoration(
                    color: Color(0xFF22C55E), shape: BoxShape.circle),
              ),
            ),
            const SizedBox(width: 8),
            const Text('LIVE FEED',
                style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF16A34A),
                    letterSpacing: 0.5)),
          ]),
        ],
      ),
    );
  }

  // ── Tab 0: Monitors Body ──

  Widget _buildMonitorsBody() {
    return LayoutBuilder(builder: (context, constraints) {
      if (constraints.maxWidth >= 900) {
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(flex: 2, child: _buildMonitorsSection()),
            const SizedBox(width: 28),
            Expanded(flex: 1, child: _buildAlertsSection()),
          ],
        );
      } else {
        return SingleChildScrollView(
          child: Column(children: [
            _buildMonitorsSection(),
            const SizedBox(height: 24),
            SizedBox(height: 500, child: _buildAlertsSection()),
          ]),
        );
      }
    });
  }

  // ── Bedside Monitors ──

  Widget _buildMonitorsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Bedside Monitors',
            style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: Color(0xFF334155))),
        const SizedBox(height: 16),
        if (patients.isEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 40),
            child: Center(
              child: Text('No patients found in database.',
                  style:
                      TextStyle(fontSize: 14, color: Colors.grey.shade500)),
            ),
          )
        else
          Expanded(
            child: GridView.builder(
              gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                maxCrossAxisExtent: 440,
                mainAxisExtent: 280,
                crossAxisSpacing: 20,
                mainAxisSpacing: 20,
              ),
              itemCount: patients.length,
              itemBuilder: (context, index) => _PatientCard(
                patient: patients[index],
                onTap: () => _openPatientDetail(patients[index]),
              ),
            ),
          ),
      ],
    );
  }

  // ── Alerts Log ──

  Widget _buildAlertsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Agent Communication Log',
            style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: Color(0xFF334155))),
        const SizedBox(height: 16),
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF0F172A),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                    color: Colors.black.withValues(alpha: 0.25),
                    blurRadius: 24,
                    offset: const Offset(0, 8)),
              ],
            ),
            child: alerts.isEmpty
                ? Center(
                    child: Text('Scanning patient data...',
                        style: TextStyle(
                            fontSize: 14,
                            fontStyle: FontStyle.italic,
                            color: Colors.grey.shade600)))
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: alerts.length,
                    itemBuilder: (context, index) =>
                        _AlertCard(alert: alerts[index]),
                  ),
          ),
        ),
      ],
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // Tab 1: Bed Availability
  // ══════════════════════════════════════════════════════════════════════

  Widget _buildBedAvailabilityTab() {
    final occupied = beds.where((b) => b.isOccupied).length;
    final available = beds.length - occupied;
    final rate = beds.isEmpty ? 0.0 : (occupied / beds.length);

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Summary cards row
          Row(
            children: [
              _summaryCard('Total Beds', '${beds.length}', Icons.bed_rounded,
                  const Color(0xFF6366F1)),
              const SizedBox(width: 16),
              _summaryCard('Occupied', '$occupied', Icons.person_rounded,
                  const Color(0xFFEF4444)),
              const SizedBox(width: 16),
              _summaryCard('Available', '$available',
                  Icons.check_circle_rounded, const Color(0xFF22C55E)),
            ],
          ),
          const SizedBox(height: 24),

          // Occupancy rate bar
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                    color: Colors.black.withValues(alpha: 0.04),
                    blurRadius: 12,
                    offset: const Offset(0, 4)),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Occupancy Rate',
                        style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                            color: Colors.grey.shade800)),
                    Text('${(rate * 100).toStringAsFixed(1)}%',
                        style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w800,
                            color: rate >= 0.9
                                ? const Color(0xFFEF4444)
                                : rate >= 0.7
                                    ? const Color(0xFFF59E0B)
                                    : const Color(0xFF22C55E))),
                  ],
                ),
                const SizedBox(height: 10),
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: rate,
                    minHeight: 10,
                    backgroundColor: const Color(0xFFE2E8F0),
                    valueColor: AlwaysStoppedAnimation<Color>(rate >= 0.9
                        ? const Color(0xFFEF4444)
                        : rate >= 0.7
                            ? const Color(0xFFF59E0B)
                            : const Color(0xFF22C55E)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Bed grid
          const Text('All Beds',
              style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF334155))),
          const SizedBox(height: 16),

          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
              maxCrossAxisExtent: 340,
              mainAxisExtent: 200,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
            ),
            itemCount: beds.length,
            itemBuilder: (context, index) => _BedCard(bed: beds[index]),
          ),
        ],
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // Tab 2: Nurse Assignments
  // ══════════════════════════════════════════════════════════════════════

  Widget _buildNurseAssignmentsTab() {
    final overloaded = nurses.where((n) => n.workload == 'Overloaded').length;
    final high = nurses.where((n) => n.workload == 'High').length;
    final normal = nurses.length - overloaded - high;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Summary
          Row(
            children: [
              _summaryCard('Nurses', '${nurses.length}',
                  Icons.people_rounded, const Color(0xFF6366F1)),
              const SizedBox(width: 16),
              _summaryCard('Overloaded', '$overloaded',
                  Icons.warning_amber_rounded, const Color(0xFFEF4444)),
              const SizedBox(width: 16),
              _summaryCard('High', '$high', Icons.trending_up_rounded,
                  const Color(0xFFF59E0B)),
              const SizedBox(width: 16),
              _summaryCard('Normal', '$normal',
                  Icons.check_circle_rounded, const Color(0xFF22C55E)),
            ],
          ),
          const SizedBox(height: 24),

          const Text('Nurse Roster',
              style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF334155))),
          const SizedBox(height: 16),

          ...nurses.map((n) => _NurseCard(nurse: n)),
        ],
      ),
    );
  }

  // ── Shared summary card widget ──

  Widget _summaryCard(
      String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
                color: Colors.black.withValues(alpha: 0.04),
                blurRadius: 12,
                offset: const Offset(0, 4)),
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(width: 14),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(value,
                    style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: color)),
                Text(label,
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey.shade500)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ── Navigate to patient detail ──

  void _openPatientDetail(Patient patient) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PatientDetailScreen(bedId: patient.bedId),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Bed Card Widget
// ═══════════════════════════════════════════════════════════════════════════

class _BedCard extends StatelessWidget {
  final BedAvailability bed;
  const _BedCard({required this.bed});

  @override
  Widget build(BuildContext context) {
    final isOccupied = bed.isOccupied;
    final accent =
        isOccupied ? const Color(0xFFEF4444) : const Color(0xFF22C55E);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border(top: BorderSide(color: accent, width: 4)),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 14,
              offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(bed.bedId.toUpperCase().replaceAll('_', ' '),
                  style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF1E293B))),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(bed.status,
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: accent)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (isOccupied) ...[
            Row(
              children: [
                const Icon(Icons.person, size: 16, color: Color(0xFF64748B)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(bed.patientName ?? 'Unknown',
                      style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF334155))),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.schedule, size: 14, color: Color(0xFF94A3B8)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                      'Admitted: ${_formatDate(bed.admissionDate)}',
                      style: TextStyle(
                          fontSize: 11, color: Colors.grey.shade500)),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFFF0FDF4),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF86EFAC), width: 1),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.event_available, size: 13, color: Color(0xFF16A34A)),
                  const SizedBox(width: 4),
                  Text(
                    'Available by: ${_formatDischargeDate(bed.expectedDischarge)}',
                    style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF16A34A)),
                  ),
                ],
              ),
            ),
          ] else
            Expanded(
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.check_circle_outline,
                        size: 32, color: accent.withValues(alpha: 0.6)),
                    const SizedBox(height: 6),
                    Text('Ready for patient',
                        style: TextStyle(
                            fontSize: 12, color: Colors.grey.shade500)),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  String _formatDate(String? isoDate) {
    if (isoDate == null) return 'N/A';
    try {
      final dt = DateTime.parse(isoDate);
      return '${dt.month}/${dt.day} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return isoDate;
    }
  }

  String _formatDischargeDate(String? isoDate) {
    if (isoDate == null) return 'TBD';
    try {
      final dt = DateTime.parse(isoDate);
      final now = DateTime.now();
      final diff = dt.difference(now);
      final days = diff.inDays;
      final hours = diff.inHours % 24;
      final dateStr = '${dt.month}/${dt.day}';
      if (days > 0) {
        return '$dateStr (in ${days}d ${hours}h)';
      } else if (diff.inHours > 0) {
        return '$dateStr (in ${hours}h)';
      } else {
        return '$dateStr (imminent)';
      }
    } catch (_) {
      return isoDate ?? 'TBD';
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Nurse Card Widget
// ═══════════════════════════════════════════════════════════════════════════

class _NurseCard extends StatelessWidget {
  final NurseAssignment nurse;
  const _NurseCard({required this.nurse});

  @override
  Widget build(BuildContext context) {
    final Color wlColor;
    final IconData wlIcon;
    switch (nurse.workload) {
      case 'Overloaded':
        wlColor = const Color(0xFFEF4444);
        wlIcon = Icons.error_rounded;
        break;
      case 'High':
        wlColor = const Color(0xFFF59E0B);
        wlIcon = Icons.warning_amber_rounded;
        break;
      default:
        wlColor = const Color(0xFF22C55E);
        wlIcon = Icons.check_circle_rounded;
    }

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border(left: BorderSide(color: wlColor, width: 4)),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.04),
              blurRadius: 12,
              offset: const Offset(0, 4)),
        ],
      ),
      child: Row(
        children: [
          // Avatar
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [
                wlColor.withValues(alpha: 0.15),
                wlColor.withValues(alpha: 0.05),
              ]),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Text(
                nurse.nurseName.split(' ').map((w) => w[0]).take(2).join(),
                style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: wlColor),
              ),
            ),
          ),
          const SizedBox(width: 16),

          // Info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(nurse.nurseName,
                    style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF1E293B))),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Icon(Icons.schedule, size: 13, color: Colors.grey.shade400),
                    const SizedBox(width: 4),
                    Text(nurse.shift,
                        style: TextStyle(
                            fontSize: 12, color: Colors.grey.shade500)),
                  ],
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: nurse.bedList
                      .map((b) => Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF1F5F9),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(b.toUpperCase().replaceAll('_', ' '),
                                style: const TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w600,
                                    color: Color(0xFF475569))),
                          ))
                      .toList(),
                ),
              ],
            ),
          ),

          // Workload badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: wlColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(wlIcon, size: 14, color: wlColor),
                const SizedBox(width: 4),
                Text(nurse.workload,
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: wlColor)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Patient Detail Screen
// ═══════════════════════════════════════════════════════════════════════════

class PatientDetailScreen extends StatefulWidget {
  final String bedId;
  const PatientDetailScreen({super.key, required this.bedId});

  @override
  State<PatientDetailScreen> createState() => _PatientDetailScreenState();
}

class _PatientDetailScreenState extends State<PatientDetailScreen> {
  Patient? patient;
  List<AlertItem> alerts = [];
  List<double> ecgData = [];
  bool loading = true;
  String? error;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _fetchDetail();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchDetail());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetchDetail() async {
    try {
      final url = 'https://icu-multi-agents-dashboard.onrender.com/patient/${widget.bedId}';
      final response = await http.get(Uri.parse(url));
      if (response.statusCode != 200) {
        throw Exception('Server returned ${response.statusCode}');
      }
      final data = json.decode(response.body);
      if (!mounted) return;
      setState(() {
        patient = Patient.fromJson(data['patient']);
        alerts = (data['alerts'] as List)
            .map((a) => AlertItem.fromJson(a))
            .toList();
        ecgData =
            (data['ecg'] as List).map((v) => (v as num).toDouble()).toList();
        loading = false;
        error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = 'Failed to load patient data: $e';
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isCritical = patient?.status == 'Critical';
    final isWarning = patient?.status == 'Warning';
    final accentColor = isCritical
        ? const Color(0xFFEF4444)
        : isWarning
            ? const Color(0xFFF59E0B)
            : const Color(0xFF6366F1);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
        elevation: 1,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: Color(0xFF1E1B4B)),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(
          loading ? 'Loading...' : '${patient?.bedId ?? widget.bedId} — Patient Detail',
          style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: Color(0xFF1E1B4B)),
        ),
        actions: [
          if (!loading)
            Container(
              margin: const EdgeInsets.only(right: 16),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                color: accentColor.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(patient?.status ?? '',
                  style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: accentColor)),
            ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.error_outline,
                            size: 48, color: Color(0xFFEF4444)),
                        const SizedBox(height: 16),
                        Text(error!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Color(0xFFEF4444))),
                        const SizedBox(height: 16),
                        FilledButton.icon(
                          onPressed: () {
                            setState(() {
                              loading = true;
                              error = null;
                            });
                            _fetchDetail();
                          },
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                )
              : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildSummaryCard(accentColor),
                  const SizedBox(height: 24),
                  _buildEcgCard(),
                  const SizedBox(height: 24),
                  _buildAlertsCard(),
                ],
              ),
            ),
    );
  }

  // ── Patient Summary Card ──

  Widget _buildSummaryCard(Color accent) {
    final p = patient!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border(top: BorderSide(color: accent, width: 4)),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.06),
              blurRadius: 16,
              offset: const Offset(0, 6)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Patient Summary',
              style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: Colors.grey.shade800)),
          const SizedBox(height: 6),
          Text(p.heartRhythm,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade500)),
          const SizedBox(height: 20),
          Row(
            children: [
              _buildVitalTile('Heart Rate', '${p.hr}', 'bpm',
                  Icons.favorite_rounded, p.hr > 100),
              const SizedBox(width: 16),
              _buildVitalTile('SpO\u2082', '${p.spo2}', '%',
                  Icons.air_rounded, p.spo2 < 90),
              const SizedBox(width: 16),
              _buildVitalTile('Temp', p.temp.toStringAsFixed(1), '\u00b0C',
                  Icons.thermostat_rounded, p.temp > 38.0),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildVitalTile(
      String label, String value, String unit, IconData icon, bool isAlert) {
    final color = isAlert ? const Color(0xFFEF4444) : const Color(0xFF334155);
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isAlert ? const Color(0xFFFEF2F2) : const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 18, color: color.withValues(alpha: 0.6)),
            const SizedBox(height: 8),
            Text(label.toUpperCase(),
                style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey.shade400,
                    letterSpacing: 0.8)),
            const SizedBox(height: 2),
            RichText(
              text: TextSpan(children: [
                TextSpan(
                    text: value,
                    style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                        color: color)),
                TextSpan(
                    text: ' $unit',
                    style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Colors.grey.shade400)),
              ]),
            ),
          ],
        ),
      ),
    );
  }

  // ── ECG Waveform Card ──

  Widget _buildEcgCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.2),
              blurRadius: 20,
              offset: const Offset(0, 8)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('ECG Waveform',
                  style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: Colors.white)),
              Row(children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                      color: Color(0xFF22C55E), shape: BoxShape.circle),
                ),
                const SizedBox(width: 6),
                Text('${patient!.hr} bpm',
                    style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF22C55E))),
              ]),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 180,
            child: ecgData.isEmpty
                ? Center(
                    child: Text('No ECG data',
                        style: TextStyle(color: Colors.grey.shade600)))
                : CustomPaint(
                    size: const Size(double.infinity, 180),
                    painter: EcgPainter(ecgData),
                  ),
          ),
        ],
      ),
    );
  }

  // ── Alert Messages Card ──

  Widget _buildAlertsCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.06),
              blurRadius: 16,
              offset: const Offset(0, 6)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Alert Messages',
              style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: Colors.grey.shade800)),
          const SizedBox(height: 16),
          if (alerts.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 20),
              child: Center(
                child: Text('No alerts for this patient.',
                    style: TextStyle(
                        fontSize: 13,
                        fontStyle: FontStyle.italic,
                        color: Colors.grey.shade500)),
              ),
            )
          else
            ...alerts.map((a) => Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF2F2),
                    borderRadius: BorderRadius.circular(12),
                    border: const Border(
                        left: BorderSide(color: Color(0xFFEF4444), width: 3)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(a.message,
                          style: const TextStyle(
                              fontSize: 13,
                              color: Color(0xFF1E293B),
                              height: 1.4)),
                      const SizedBox(height: 4),
                      Text(a.timestamp,
                          style: TextStyle(
                              fontSize: 10, color: Colors.grey.shade500)),
                    ],
                  ),
                )),
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// ECG Waveform Painter
// ═══════════════════════════════════════════════════════════════════════════

class EcgPainter extends CustomPainter {
  final List<double> data;
  EcgPainter(this.data);

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;

    // Draw subtle grid
    final gridPaint = Paint()
      ..color = const Color(0xFF1E293B)
      ..strokeWidth = 0.5;
    for (int i = 0; i <= 8; i++) {
      final x = size.width * i / 8;
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), gridPaint);
    }
    for (int i = 0; i <= 4; i++) {
      final y = size.height * i / 4;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    // Draw ECG trace
    final paint = Paint()
      ..color = const Color(0xFF22C55E)
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke
      ..strokeJoin = StrokeJoin.round;

    // Glow effect
    final glowPaint = Paint()
      ..color = const Color(0xFF22C55E).withValues(alpha: 0.3)
      ..strokeWidth = 5.0
      ..style = PaintingStyle.stroke
      ..strokeJoin = StrokeJoin.round
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 3);

    final path = Path();
    final midY = size.height / 2;
    final scaleY = size.height * 0.4;

    for (int i = 0; i < data.length; i++) {
      final x = (i / (data.length - 1)) * size.width;
      final y = midY - data[i] * scaleY;
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    canvas.drawPath(path, glowPaint);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant EcgPainter oldDelegate) => true;
}

// ═══════════════════════════════════════════════════════════════════════════
// Patient Card Widget (clickable)
// ═══════════════════════════════════════════════════════════════════════════

class _PatientCard extends StatelessWidget {
  final Patient patient;
  final VoidCallback onTap;
  const _PatientCard({required this.patient, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isCritical = patient.status == 'Critical';
    final borderColor =
        isCritical ? const Color(0xFFEF4444) : const Color(0xFF6366F1);
    final statusBg =
        isCritical ? const Color(0xFFFEE2E2) : const Color(0xFFDBEAFE);
    final statusFg =
        isCritical ? const Color(0xFFDC2626) : const Color(0xFF2563EB);

    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border(top: BorderSide(color: borderColor, width: 4)),
            boxShadow: [
              BoxShadow(
                  color: Colors.black.withValues(alpha: 0.06),
                  blurRadius: 16,
                  offset: const Offset(0, 6)),
            ],
          ),
          padding: const EdgeInsets.all(22),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(patient.bedId,
                      style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                          color: Color(0xFF1E293B))),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                        color: statusBg,
                        borderRadius: BorderRadius.circular(20)),
                    child: Text(patient.status,
                        style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: statusFg)),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(patient.heartRhythm,
                  style:
                      TextStyle(fontSize: 12, color: Colors.grey.shade500)),
              const SizedBox(height: 18),
              Expanded(
                child: Row(children: [
                  Expanded(
                      child: _VitalTile(
                          label: 'Heart Rate',
                          value: '${patient.hr}',
                          unit: 'bpm',
                          isAlert: patient.hr > 100,
                          icon: Icons.favorite_rounded)),
                  const SizedBox(width: 12),
                  Expanded(
                      child: _VitalTile(
                          label: 'SpO\u2082',
                          value: '${patient.spo2}',
                          unit: '%',
                          isAlert: patient.spo2 < 90,
                          icon: Icons.air_rounded)),
                  const SizedBox(width: 12),
                  Expanded(
                      child: _VitalTile(
                          label: 'Temp',
                          value: patient.temp.toStringAsFixed(1),
                          unit: '\u00b0C',
                          isAlert: patient.temp > 38.0,
                          icon: Icons.thermostat_rounded)),
                ]),
              ),
              const SizedBox(height: 8),
              Center(
                child: Text('Tap for details  \u203A',
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey.shade400)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Vital Tile Widget
// ═══════════════════════════════════════════════════════════════════════════

class _VitalTile extends StatelessWidget {
  final String label;
  final String value;
  final String unit;
  final bool isAlert;
  final IconData icon;

  const _VitalTile({
    required this.label,
    required this.value,
    required this.unit,
    required this.isAlert,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final color = isAlert ? const Color(0xFFEF4444) : const Color(0xFF334155);
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: isAlert ? const Color(0xFFFEF2F2) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 16, color: color.withValues(alpha: 0.6)),
          const SizedBox(height: 4),
          Text(label.toUpperCase(),
              style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey.shade400,
                  letterSpacing: 0.8)),
          const SizedBox(height: 4),
          Flexible(
            child: FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: RichText(
                text: TextSpan(children: [
                  TextSpan(
                      text: value,
                      style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.w800,
                          color: color)),
              TextSpan(
                  text: ' $unit',
                  style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: Colors.grey.shade400)),
                ]),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Alert Card Widget
// ═══════════════════════════════════════════════════════════════════════════

class _AlertCard extends StatelessWidget {
  final AlertItem alert;
  const _AlertCard({required this.alert});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: const BoxDecoration(
        color: Color(0xFF1E293B),
        borderRadius: BorderRadius.horizontal(right: Radius.circular(10)),
        border: Border(left: BorderSide(color: Color(0xFFEF4444), width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(alert.bedId.toUpperCase(),
              style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFFF87171),
                  letterSpacing: 0.5)),
          const SizedBox(height: 6),
          Text(alert.message,
              style: const TextStyle(
                  fontSize: 13, color: Colors.white, height: 1.4)),
          const SizedBox(height: 6),
          Text(alert.timestamp,
              style: TextStyle(fontSize: 10, color: Colors.grey.shade600)),
        ],
      ),
    );
  }
}
