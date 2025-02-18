import 'package:flutter/material.dart';

class SwipeButtons extends StatelessWidget {
  final VoidCallback onSwipeLeft;
  final VoidCallback onSwipeRight;

  const SwipeButtons({
    super.key,
    required this.onSwipeLeft,
    required this.onSwipeRight,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          FloatingActionButton(
            onPressed: onSwipeLeft,
            backgroundColor: Colors.red,
            child: const Icon(Icons.close),
          ),
          FloatingActionButton(
            onPressed: onSwipeRight,
            backgroundColor: Colors.green,
            child: const Icon(Icons.check),
          ),
        ],
      ),
    );
  }
} 