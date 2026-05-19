import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../cubit/dwp_cubit.dart';
import '../data/dwp_api.dart';
import '../widgets/dwp_field_widget.dart';

class DwpFormPage extends StatelessWidget {
  const DwpFormPage({super.key, required this.type});

  /// 'morning' or 'eod'
  final String type;

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => DwpFormCubit(sl<DwpApi>(), type)..load(),
      child: _DwpFormView(type: type),
    );
  }
}

class _DwpFormView extends StatefulWidget {
  const _DwpFormView({required this.type});
  final String type;

  @override
  State<_DwpFormView> createState() => _DwpFormViewState();
}

class _DwpFormViewState extends State<_DwpFormView> {
  final _formKey = GlobalKey<FormState>();
  final Map<String, dynamic> _values = {};

  @override
  Widget build(BuildContext context) {
    final isMorning = widget.type == 'morning';
    return Scaffold(
      appBar: AppBar(
        title: Text(isMorning ? 'Morning plan' : 'EOD summary'),
      ),
      body: BlocConsumer<DwpFormCubit, DwpFormState>(
        listener: (context, state) {
          if (state.error != null && !state.submitting) {
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(state.error!)));
          }
        },
        builder: (context, state) {
          if (state.status == LoadStatus.loading && state.template == null) {
            return const Center(child: CircularProgressIndicator());
          }
          final t = state.template;
          if (t == null) {
            return Center(child: Text(state.error ?? 'No template'));
          }
          // Initialize values from prefill (only first build)
          if (_values.isEmpty && state.prefill.isNotEmpty) {
            _values.addAll(state.prefill);
          }
          return Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  '★ ${widget.type.toUpperCase()} · ${t.name.toUpperCase()}',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: AppColors.brandGoldDark,
                      ),
                ),
                if (t.description != null) ...[
                  const SizedBox(height: 4),
                  Text(t.description!,
                      style: TextStyle(
                          color: context.textMuted, fontSize: 13)),
                ],
                if (state.linkedMorningId != null) ...[
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppColors.info.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.link, size: 14, color: AppColors.info),
                        const SizedBox(width: 6),
                        Text('Pre-filled from morning plan',
                            style:
                                TextStyle(color: AppColors.info, fontSize: 12)),
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                ...t.fields.map((f) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: DwpFieldWidget(
                        field: f,
                        value: _values[f.key],
                        onChanged: (v) => setState(() => _values[f.key] = v),
                      ),
                    )),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: state.submitting
                      ? null
                      : () async {
                          if (!(_formKey.currentState?.validate() ?? false)) {
                            return;
                          }
                          final ok =
                              await context.read<DwpFormCubit>().submit(_values);
                          if (!mounted) return;
                          if (ok) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                  content: Text(isMorning
                                      ? 'Morning plan submitted'
                                      : 'EOD summary submitted')),
                            );
                            GoRouter.of(context).pop();
                          }
                        },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: state.submitting
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : Text(isMorning ? 'Submit plan' : 'Submit EOD'),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
