import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/sales_api.dart';

const _sources = [
  'website',
  'referral',
  'cold_call',
  'exhibition',
  'campaign',
  'field_visit',
  'partner',
  'other',
];

class NewLeadPage extends StatefulWidget {
  const NewLeadPage({super.key});

  @override
  State<NewLeadPage> createState() => _NewLeadPageState();
}

class _NewLeadPageState extends State<NewLeadPage> {
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _email = TextEditingController();
  final _value = TextEditingController(text: '0');
  final _notes = TextEditingController();
  String _source = 'field_visit';
  bool _busy = false;
  Position? _myPos;

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    _email.dispose();
    _value.dispose();
    _notes.dispose();
    super.dispose();
  }

  Future<void> _captureSelfMap() async {
    setState(() => _busy = true);
    try {
      if (!await Geolocator.isLocationServiceEnabled()) {
        throw 'Location services are disabled.';
      }
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied ||
          perm == LocationPermission.deniedForever) {
        throw 'Location permission denied.';
      }
      final pos = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 12),
      );
      if (!mounted) return;
      setState(() => _myPos = pos);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Pinned ${pos.latitude.toStringAsFixed(5)}, '
            '${pos.longitude.toStringAsFixed(5)}',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$e')),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _submit() async {
    if (_name.text.trim().isEmpty && _phone.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Add a contact name or phone before saving.'),
        ),
      );
      return;
    }
    setState(() => _busy = true);
    try {
      final notes = _notes.text.trim();
      final notesWithGps = _myPos == null
          ? notes
          : (notes.isEmpty
              ? 'Captured @ ${_myPos!.latitude.toStringAsFixed(5)}, '
                  '${_myPos!.longitude.toStringAsFixed(5)}'
              : '$notes\n[GPS ${_myPos!.latitude.toStringAsFixed(5)}, '
                  '${_myPos!.longitude.toStringAsFixed(5)}]');
      await sl<SalesApi>().createLead({
        'contact_name':
            _name.text.trim().isEmpty ? null : _name.text.trim(),
        'contact_phone':
            _phone.text.trim().isEmpty ? null : _phone.text.trim(),
        'contact_email':
            _email.text.trim().isEmpty ? null : _email.text.trim(),
        'source': _source,
        'expected_value':
            double.tryParse(_value.text.trim()) ?? 0,
        if (notesWithGps.isNotEmpty) 'notes': notesWithGps,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lead created')),
      );
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not create lead: $e')),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('New lead')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _name,
            decoration: const InputDecoration(
              labelText: 'Contact name',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _phone,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(
              labelText: 'Contact phone',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(
              labelText: 'Contact email',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: _source,
            decoration: const InputDecoration(
              labelText: 'Source',
              border: OutlineInputBorder(),
            ),
            items: _sources
                .map((s) => DropdownMenuItem(
                      value: s,
                      child: Text(s.replaceAll('_', ' ')),
                    ))
                .toList(),
            onChanged: (v) => setState(() => _source = v ?? 'other'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _value,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Expected value (₹)',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _notes,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Notes',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            color: _myPos == null
                ? null
                : AppColors.success.withOpacity(0.08),
            child: ListTile(
              leading: Icon(
                _myPos == null ? Icons.location_off : Icons.location_on,
                color: _myPos == null
                    ? AppColors.brandBrownLight
                    : AppColors.success,
              ),
              title: Text(
                _myPos == null
                    ? 'Tag with my current location'
                    : '${_myPos!.latitude.toStringAsFixed(5)}, '
                        '${_myPos!.longitude.toStringAsFixed(5)}',
              ),
              subtitle: Text(
                _myPos == null
                    ? 'Helpful when you meet a lead in the field.'
                    : 'GPS appended to notes when you save.',
              ),
              trailing: TextButton(
                onPressed: _busy ? null : _captureSelfMap,
                child: Text(_myPos == null ? 'Capture' : 'Update'),
              ),
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _busy ? null : _submit,
            icon: const Icon(Icons.save),
            label: Text(_busy ? 'Saving…' : 'Save lead'),
          ),
        ],
      ),
    );
  }
}
