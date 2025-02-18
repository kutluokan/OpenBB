import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fwitit/providers/openbb_provider.dart';

class BetScreen extends StatefulWidget {
  const BetScreen({super.key});

  @override
  State<BetScreen> createState() => _BetScreenState();
}

class _BetScreenState extends State<BetScreen> {
  final _predictionController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Bet-4-Me'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'What\'s your market prediction?',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _predictionController,
              decoration: const InputDecoration(
                hintText: 'e.g., CPI will be higher than expected',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                // TODO: Implement prediction-based investing
              },
              child: const Text('Generate Investment Strategy'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _predictionController.dispose();
    super.dispose();
  }
} 