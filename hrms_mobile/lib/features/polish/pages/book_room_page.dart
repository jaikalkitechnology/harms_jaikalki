import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/polish_api.dart';
import '../data/polish_models.dart';

class BookRoomPage extends StatefulWidget {
  const BookRoomPage({super.key});

  @override
  State<BookRoomPage> createState() => _BookRoomPageState();
}

class _BookRoomPageState extends State<BookRoomPage> {
  late Future<({List<MeetingRoom> rooms, List<RoomBooking> mine})> _future;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<({List<MeetingRoom> rooms, List<RoomBooking> mine})> _load() async {
    final api = sl<PolishApi>();
    final rooms = await api.rooms();
    final mine = await api.myBookings();
    return (rooms: rooms, mine: mine);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _toast(String msg, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: error ? AppColors.error : AppColors.success,
      ),
    );
  }

  Future<void> _bookRoom(MeetingRoom room) async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => _BookRoomDialog(room: room),
    );
    if (result == null) return;
    setState(() => _busy = true);
    try {
      await sl<PolishApi>().bookRoom(
        roomId: room.id,
        title: result['title'] as String,
        startTime: (result['start'] as DateTime).toIso8601String(),
        endTime: (result['end'] as DateTime).toIso8601String(),
      );
      _toast('Booked ${room.name}');
      await _refresh();
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Could not book')
          : 'Could not book';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _cancel(int id) async {
    setState(() => _busy = true);
    try {
      await sl<PolishApi>().cancelBooking(id);
      _toast('Cancelled');
      await _refresh();
    } catch (_) {
      _toast('Could not cancel', error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Meeting Rooms')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<({List<MeetingRoom> rooms, List<RoomBooking> mine})>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final rooms = snap.data!.rooms;
            final mine = snap.data!.mine
                .where((b) => b.status != 'cancelled')
                .toList();
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (mine.isNotEmpty) ...[
                  Text('★ MY BOOKINGS',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: AppColors.brandGoldDark,
                      )),
                  const SizedBox(height: 8),
                  ...mine.map(
                    (b) => Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: const Icon(Icons.event,
                            color: AppColors.brandGoldDark),
                        title: Text(b.title),
                        subtitle: Text(
                          '${b.startTime} → ${b.endTime}\nStatus: ${b.status}',
                          style: theme.textTheme.bodySmall,
                        ),
                        trailing: TextButton(
                          onPressed: _busy ? null : () => _cancel(b.id),
                          child: const Text('Cancel'),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                Text('★ AVAILABLE ROOMS',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    )),
                const SizedBox(height: 8),
                ...rooms.map(
                  (r) => Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: AppColors.brandGoldPale,
                        child: const Icon(Icons.meeting_room,
                            color: AppColors.brandGoldDark),
                      ),
                      title: Text(r.name),
                      subtitle: Text(
                        '${r.location ?? "—"} · ${r.capacity} seats'
                        '${r.hasVideo ? " · video" : ""}',
                        style: theme.textTheme.bodySmall,
                      ),
                      trailing: ElevatedButton(
                        onPressed: _busy ? null : () => _bookRoom(r),
                        child: const Text('Book'),
                      ),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _BookRoomDialog extends StatefulWidget {
  const _BookRoomDialog({required this.room});
  final MeetingRoom room;

  @override
  State<_BookRoomDialog> createState() => _BookRoomDialogState();
}

class _BookRoomDialogState extends State<_BookRoomDialog> {
  String _title = '';
  DateTime _start = DateTime.now().add(const Duration(hours: 1));
  Duration _duration = const Duration(minutes: 30);

  Future<void> _pickStart() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _start,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 60)),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_start),
    );
    if (time == null) return;
    setState(() {
      _start = DateTime(
        date.year, date.month, date.day, time.hour, time.minute,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final end = _start.add(_duration);
    return AlertDialog(
      title: Text('Book ${widget.room.name}'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              decoration: const InputDecoration(labelText: 'Meeting title'),
              onChanged: (v) => _title = v,
            ),
            const SizedBox(height: 12),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.access_time),
              title: Text('Start: ${_start.toString().substring(0, 16)}'),
              trailing: TextButton(
                onPressed: _pickStart,
                child: const Text('Change'),
              ),
            ),
            DropdownButtonFormField<Duration>(
              value: _duration,
              decoration: const InputDecoration(labelText: 'Duration'),
              items: const [
                DropdownMenuItem(
                  value: Duration(minutes: 30),
                  child: Text('30 min'),
                ),
                DropdownMenuItem(
                  value: Duration(hours: 1),
                  child: Text('1 hour'),
                ),
                DropdownMenuItem(
                  value: Duration(hours: 2),
                  child: Text('2 hours'),
                ),
              ],
              onChanged: (v) =>
                  setState(() => _duration = v ?? const Duration(hours: 1)),
            ),
            const SizedBox(height: 8),
            Text('Ends ${end.toString().substring(0, 16)}',
                style: const TextStyle(color: AppColors.textMuted)),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _title.trim().isEmpty
              ? null
              : () => Navigator.pop(context, {
                    'title': _title.trim(),
                    'start': _start,
                    'end': end,
                  }),
          child: const Text('Book'),
        ),
      ],
    );
  }
}
