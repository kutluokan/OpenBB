import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fwitit/providers/openbb_provider.dart';

class SwipeScreen extends StatefulWidget {
  const SwipeScreen({super.key});

  @override
  State<SwipeScreen> createState() => _SwipeScreenState();
}

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
                child: Card(
                  margin: const EdgeInsets.all(16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          openbb.currentRecommendation!['symbol'],
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Recommendation: ${openbb.currentRecommendation!['recommendation']}',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    FloatingActionButton(
                      onPressed: () {
                        openbb.fetchNextRecommendation();
                      },
                      backgroundColor: Colors.red,
                      child: const Icon(Icons.close),
                    ),
                    FloatingActionButton(
                      onPressed: () async {
                        await openbb.executeInvestment(
                          openbb.currentRecommendation!['symbol'],
                        );
                        openbb.fetchNextRecommendation();
                      },
                      backgroundColor: Colors.green,
                      child: const Icon(Icons.check),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
} 