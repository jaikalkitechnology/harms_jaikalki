import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../data/dwp_models.dart';

/// Renders a DWP field according to its `field_type`.
class DwpFieldWidget extends StatelessWidget {
  const DwpFieldWidget({
    super.key,
    required this.field,
    required this.value,
    required this.onChanged,
  });

  final DwpField field;
  final dynamic value;
  final ValueChanged<dynamic> onChanged;

  @override
  Widget build(BuildContext context) {
    switch (field.fieldType) {
      case 'textarea':
      case 'tasks':
        return _textareaField();
      case 'number':
        return _numberField();
      case 'percent':
        return _percentField(context);
      case 'rating':
        return _ratingField();
      case 'select':
        return _selectField();
      case 'photo_url':
      case 'voice_url':
      case 'text':
      default:
        return _textField();
    }
  }

  Widget _textField() {
    return TextFormField(
      initialValue: value?.toString(),
      decoration: _decoration(),
      validator: _required,
      onChanged: onChanged,
    );
  }

  Widget _textareaField() {
    return TextFormField(
      initialValue: value?.toString(),
      maxLines: 4,
      minLines: 2,
      decoration: _decoration(),
      validator: _required,
      onChanged: onChanged,
    );
  }

  Widget _numberField() {
    return TextFormField(
      initialValue: value?.toString(),
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: _decoration(),
      validator: _required,
      onChanged: onChanged,
    );
  }

  Widget _percentField(BuildContext context) {
    final current = double.tryParse('${value ?? 0}') ?? 0.0;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(field.label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.brandBrownLight,
                  )),
          Slider(
            value: current.clamp(0, 100).toDouble(),
            min: 0,
            max: 100,
            divisions: 20,
            label: '${current.round()}%',
            onChanged: (v) => onChanged(v.round()),
          ),
        ],
      ),
    );
  }

  Widget _ratingField() {
    final current = int.tryParse('${value ?? 0}') ?? 0;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(field.label,
              style: const TextStyle(color: AppColors.brandBrownLight)),
          const SizedBox(height: 4),
          Row(
            children: List.generate(5, (i) {
              final star = i + 1;
              return IconButton(
                onPressed: () => onChanged(star),
                icon: Icon(
                  star <= current ? Icons.star : Icons.star_border,
                  color: AppColors.brandGoldDark,
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _selectField() {
    final opts =
        (field.options ?? const []).map((e) => e.toString()).toList();
    return DropdownButtonFormField<String>(
      value: value?.toString().isNotEmpty == true ? value.toString() : null,
      decoration: _decoration(),
      items: opts
          .map((o) => DropdownMenuItem(value: o, child: Text(o)))
          .toList(),
      onChanged: onChanged,
      validator: (v) {
        if (field.isRequired && (v == null || v.isEmpty)) return 'Required';
        return null;
      },
    );
  }

  InputDecoration _decoration() => InputDecoration(
        labelText: field.label,
        helperText: field.helpText,
      );

  String? _required(String? v) {
    if (!field.isRequired) return null;
    if (v == null || v.trim().isEmpty) return 'Required';
    return null;
  }
}
