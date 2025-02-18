import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fwitit/providers/openbb_provider.dart';
import 'package:fwitit/widgets/investment_card.dart';
import 'package:fwitit/widgets/swipe_buttons.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
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
        title: const Text('FwitIt'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person),
            onPressed: () {
              // TODO: Implement profile/settings screen
            },
          ),
        ],
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
                onSwipeRight: () async {
                  await openbb.executeInvestment(
                    openbb.currentRecommendation!['symbol'],
                  );
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