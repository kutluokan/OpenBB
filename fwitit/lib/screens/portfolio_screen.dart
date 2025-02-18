import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fwitit/providers/openbb_provider.dart';

class PortfolioScreen extends StatelessWidget {
  const PortfolioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Investments'),
      ),
      body: Consumer<OpenBBProvider>(
        builder: (context, openbb, child) {
          // TODO: Implement portfolio view
          return const Center(
            child: Text('Portfolio coming soon...'),
          );
        },
      ),
    );
  }
} 