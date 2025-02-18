import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fwitit/providers/openbb_provider.dart';
import 'package:fwitit/widgets/investment_card.dart';
import 'package:fwitit/widgets/swipe_buttons.dart';

// Rename HomeScreen to SwipeScreen
class SwipeScreen extends StatefulWidget {
  const SwipeScreen({super.key});

  @override
  State<SwipeScreen> createState() => _SwipeScreenState();
}

// Update the state class name
class _SwipeScreenState extends State<SwipeScreen> {
  @override
  void initState() {
    super.initState();
    // Fetch initial recommendation
    Future.microtask(() => 
      Provider.of<OpenBBProvider>(context, listen: false).fetchNextRecommendation()
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Swipe-2-Invest'),
      ),
      body: Consumer<OpenBBProvider>(
        builder: (context, openbb, child) {
          if (openbb.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (openbb.error != null) {
            return Center(child: Text('Error: ${openbb.error}'));
          }

          if (openbb.currentRecommendation == null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('No recommendations available'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      openbb.fetchNextRecommendation();
                    },
                    child: const Text('Get Recommendations'),
                  ),
                ],
              ),
            );
          }

          return Column(
            children: [
              Expanded(
                child: InvestmentCard(
                  recommendation: openbb.currentRecommendation!,
                ),
              ),
              SwipeButtons(
                onSwipeLeft: () {
                  openbb.fetchNextRecommendation();
                },
                onSwipeRight: () {
                  // TODO: Implement investment execution
                  openbb.fetchNextRecommendation();
                },
              ),
            ],
          );
        },
      ),
    );
  }
} 