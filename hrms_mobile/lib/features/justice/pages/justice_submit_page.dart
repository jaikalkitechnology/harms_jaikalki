import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/justice_api.dart';

const _categories = [
  ('sexual_harassment', 'Sexual harassment (POSH)'),
  ('discrimination', 'Discrimination (POSH)'),
  ('fraud', 'Fraud / financial misconduct'),
  ('manager_issue', 'Manager issue'),
  ('hr_issue', 'HR issue'),
  ('director_issue', 'Director issue'),
  ('safety', 'Safety / workplace harm'),
  ('general', 'General grievance'),
];

const _privacy = [
  ('anonymous', 'Anonymous',
      'Your identity is never linked to the complaint.'),
  ('confidential', 'Confidential',
      'Stored encrypted; only authorised members can decrypt.'),
  ('open', 'Open',
      'You agree to be identified to authorised members for follow-up.'),
];

const _severity = [
  ('low', 'Low'),
  ('medium', 'Medium'),
  ('high', 'High'),
  ('critical', 'Critical'),
];

class JusticeSubmitPage extends StatefulWidget {
  const JusticeSubmitPage({super.key});

  @override
  State<JusticeSubmitPage> createState() => _JusticeSubmitPageState();
}

class _JusticeSubmitPageState extends State<JusticeSubmitPage> {
  final _pageController = PageController();
  int _step = 0;

  // Form fields
  String _category = 'general';
  String _privacyLevel = 'confidential';
  String _severity = 'medium';
  final _subjectCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  final _outcomeCtrl = TextEditingController();
  DateTime? _incidentDate;
  final _locationCtrl = TextEditingController();
  final _accusedCtrl = TextEditingController();
  final _witnessCtrl = TextEditingController();
  final _evidenceCtrl = TextEditingController();

  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _pageController.dispose();
    _subjectCtrl.dispose();
    _descCtrl.dispose();
    _outcomeCtrl.dispose();
    _locationCtrl.dispose();
    _accusedCtrl.dispose();
    _witnessCtrl.dispose();
    _evidenceCtrl.dispose();
    super.dispose();
  }

  void _next() {
    if (_step >= 4) {
      _submit();
      return;
    }
    setState(() => _step++);
    _pageController.animateToPage(
      _step,
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
    );
  }

  void _back() {
    if (_step == 0) {
      Navigator.of(context).pop();
      return;
    }
    setState(() => _step--);
    _pageController.animateToPage(
      _step,
      duration: const Duration(milliseconds: 200),
      curve: Curves.easeOut,
    );
  }

  Future<void> _pickIncidentDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _incidentDate ?? DateTime.now(),
      firstDate: DateTime.now().subtract(const Duration(days: 365 * 2)),
      lastDate: DateTime.now(),
    );
    if (picked != null) setState(() => _incidentDate = picked);
  }

  Future<void> _submit() async {
    if (_subjectCtrl.text.trim().length < 3 ||
        _descCtrl.text.trim().length < 10) {
      setState(() {
        _error = 'Subject and description are required.';
        _step = 2;
      });
      _pageController.jumpToPage(2);
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await sl<JusticeApi>().submit(
        complaintType: _category,
        privacyLevel: _privacyLevel,
        severity: _severity,
        subject: _subjectCtrl.text.trim(),
        description: _descCtrl.text.trim(),
        desiredOutcome: _outcomeCtrl.text.trim().isEmpty
            ? null
            : _outcomeCtrl.text.trim(),
        incidentDate: _incidentDate != null
            ? DateFormat('yyyy-MM-dd').format(_incidentDate!)
            : null,
        incidentLocation: _locationCtrl.text.trim().isEmpty
            ? null
            : _locationCtrl.text.trim(),
        accused: _accusedCtrl.text.trim().isEmpty
            ? const []
            : [
                {
                  'name': _accusedCtrl.text.trim(),
                  'employee_id': null,
                  'relationship_type': null,
                }
              ],
        witnesses: _witnessCtrl.text.trim().isEmpty
            ? const []
            : [
                {
                  'name': _witnessCtrl.text.trim(),
                  'statement': null,
                  'is_anonymous': false,
                }
              ],
        evidence: _evidenceCtrl.text.trim().isEmpty
            ? const []
            : [
                {
                  'file_url': _evidenceCtrl.text.trim(),
                  'file_name': null,
                  'file_type': null,
                  'file_hash': null,
                }
              ],
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Complaint submitted')),
      );
      GoRouter.of(context).pop();
    } catch (e) {
      setState(() {
        _submitting = false;
        _error = 'Could not submit complaint.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('New complaint'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: _back,
        ),
      ),
      body: Column(
        children: [
          LinearProgressIndicator(
            value: (_step + 1) / 5,
            backgroundColor: AppColors.brandBrown100,
            color: AppColors.brandGoldDark,
          ),
          Expanded(
            child: PageView(
              controller: _pageController,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _stepCategory(),
                _stepPrivacy(),
                _stepDetails(),
                _stepPeople(),
                _stepReview(),
              ],
            ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
              child: Text(_error!,
                  style: const TextStyle(color: AppColors.error)),
            ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                if (_step > 0)
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _back,
                      child: const Text('Back'),
                    ),
                  ),
                if (_step > 0) const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: _submitting ? null : _next,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6),
                      child: _submitting
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : Text(_step == 4 ? 'Submit' : 'Next'),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _stepCategory() {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _stepHeader('1 of 5', 'What kind of complaint is this?'),
        const SizedBox(height: 12),
        ..._categories.map(
          (c) => RadioListTile<String>(
            value: c.$1,
            groupValue: _category,
            onChanged: (v) => setState(() => _category = v!),
            title: Text(c.$2),
          ),
        ),
        if (_category == 'sexual_harassment' || _category == 'discrimination')
          Container(
            margin: const EdgeInsets.only(top: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.brandGoldDark.withOpacity(0.08),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                const Icon(Icons.shield_outlined,
                    size: 16, color: AppColors.brandGoldDark),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'POSH Act case — routes to ICC, must resolve within 90 days.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _stepPrivacy() {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _stepHeader('2 of 5', 'How private should this be?'),
        const SizedBox(height: 12),
        ..._privacy.map(
          (p) => RadioListTile<String>(
            value: p.$1,
            groupValue: _privacyLevel,
            onChanged: (v) => setState(() => _privacyLevel = v!),
            title: Text(p.$2),
            subtitle: Text(p.$3),
          ),
        ),
      ],
    );
  }

  Widget _stepDetails() {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _stepHeader('3 of 5', 'What happened?'),
        const SizedBox(height: 12),
        TextField(
          controller: _subjectCtrl,
          decoration: const InputDecoration(
            labelText: 'Subject',
            helperText: 'A short title (3+ chars).',
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _descCtrl,
          maxLines: 6,
          minLines: 4,
          decoration: const InputDecoration(
            labelText: 'Description',
            helperText: 'Encrypted at rest.',
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _outcomeCtrl,
          maxLines: 3,
          minLines: 2,
          decoration: const InputDecoration(
            labelText: 'Desired outcome (optional)',
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: InkWell(
                onTap: _pickIncidentDate,
                child: InputDecorator(
                  decoration:
                      const InputDecoration(labelText: 'Incident date'),
                  child: Text(_incidentDate == null
                      ? 'Not set'
                      : DateFormat('d MMM yyyy').format(_incidentDate!)),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _locationCtrl,
                decoration:
                    const InputDecoration(labelText: 'Location'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          value: _severity,
          decoration: const InputDecoration(labelText: 'Severity'),
          items: _severity_items(),
          onChanged: (v) => setState(() => _severity = v!),
        ),
      ],
    );
  }

  List<DropdownMenuItem<String>> _severity_items() => _severity
      .map((s) => DropdownMenuItem(value: s.$1, child: Text(s.$2)))
      .toList();

  Widget _stepPeople() {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _stepHeader('4 of 5', 'People & evidence (optional)'),
        const SizedBox(height: 12),
        TextField(
          controller: _accusedCtrl,
          decoration: const InputDecoration(
            labelText: 'Accused person (name)',
            helperText:
                'Encrypted before storage. Leave blank if you prefer not to name.',
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _witnessCtrl,
          decoration: const InputDecoration(
            labelText: 'Witness (name)',
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _evidenceCtrl,
          decoration: const InputDecoration(
            labelText: 'Evidence URL (optional)',
            helperText: 'Paste a file link if you have evidence to attach.',
          ),
        ),
      ],
    );
  }

  Widget _stepReview() {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _stepHeader('5 of 5', 'Confirm and submit'),
        const SizedBox(height: 12),
        _reviewRow('Category', _categories
            .firstWhere((c) => c.$1 == _category, orElse: () => ('—', '—'))
            .$2),
        _reviewRow('Privacy', _privacy
            .firstWhere((p) => p.$1 == _privacyLevel,
                orElse: () => ('—', '—', ''))
            .$2),
        _reviewRow('Severity', _severity
            .firstWhere((s) => s.$1 == _severity,
                orElse: () => ('—', '—'))
            .$2),
        _reviewRow('Subject', _subjectCtrl.text),
        _reviewRow('Description',
            _descCtrl.text.isEmpty ? '—' : _descCtrl.text),
        if (_incidentDate != null)
          _reviewRow('Incident date',
              DateFormat('d MMM yyyy').format(_incidentDate!)),
        if (_locationCtrl.text.isNotEmpty)
          _reviewRow('Location', _locationCtrl.text),
        if (_accusedCtrl.text.isNotEmpty)
          _reviewRow('Accused', _accusedCtrl.text),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.brandGoldDark.withOpacity(0.08),
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Row(
            children: [
              Icon(Icons.lock_outline,
                  size: 16, color: AppColors.brandGoldDark),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'On submit, sensitive fields are encrypted with AES-GCM-256 server-side. The submission itself is recorded in the audit log.',
                  style: TextStyle(fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _stepHeader(String step, String title) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('★ ${step.toUpperCase()}',
            style: theme.textTheme.labelSmall
                ?.copyWith(color: AppColors.brandGoldDark)),
        const SizedBox(height: 4),
        Text(title, style: theme.textTheme.headlineSmall),
      ],
    );
  }

  Widget _reviewRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label.toUpperCase(),
              style: const TextStyle(
                fontSize: 10,
                fontFamily: 'monospace',
                letterSpacing: 1.5,
                color: AppColors.brandBrownLight,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value.isEmpty ? '—' : value,
              style: const TextStyle(color: AppColors.brandBrownDarker),
            ),
          ),
        ],
      ),
    );
  }
}
