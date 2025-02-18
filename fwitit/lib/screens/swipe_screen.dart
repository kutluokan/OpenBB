import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fwitit/providers/openbb_provider.dart';

class SwipeScreen extends StatefulWidget {
  const SwipeScreen({super.key});

  @override
  State<SwipeScreen> createState() => _SwipeScreenState();
}

class _SwipeScreenState extends State<SwipeScreen> with SingleTickerProviderStateMixin {
  double _dragPosition = 0;
  double _dragPercentage = 0;
  late AnimationController _animationController;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _animation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeOut,
      ),
    );
    Future.microtask(() => 
      Provider.of<OpenBBProvider>(context, listen: false).fetchNextRecommendation()
    );
  }

  void _onDragUpdate(DragUpdateDetails details) {
    setState(() {
      _dragPosition += details.delta.dx;
      _dragPercentage = _dragPosition / MediaQuery.of(context).size.width;
    });
  }

  void _onDragEnd(DragEndDetails details) async {
    final velocity = details.primaryVelocity ?? 0;
    final OpenBBProvider openbb = Provider.of<OpenBBProvider>(context, listen: false);
    
    if (_dragPercentage.abs() > 0.4 || velocity.abs() > 300) {
      _animationController.forward();
      if (_dragPercentage > 0 || velocity > 0) {
        // Swiped right - Invest
        await openbb.executeInvestment(
          openbb.currentRecommendation!['symbol'],
        );
      }
      await Future.delayed(const Duration(milliseconds: 200));
      openbb.fetchNextRecommendation();
      _animationController.reset();
    }
    
    setState(() {
      _dragPosition = 0;
      _dragPercentage = 0;
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
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

          return Stack(
            children: [
              // Animated Background
              AnimatedBuilder(
                animation: _animation,
                builder: (context, child) {
                  return Container(
                    color: _dragPercentage < 0
                        ? Colors.red.withOpacity((_dragPercentage.abs() * 0.7 + _animation.value * 0.3).clamp(0, 1))
                        : Colors.green.withOpacity((_dragPercentage * 0.7 + _animation.value * 0.3).clamp(0, 1)),
                  );
                },
              ),
              // Background Icons
              Positioned.fill(
                child: Row(
                  children: [
                    Expanded(
                      child: Center(
                        child: Icon(
                          Icons.close,
                          color: Colors.white.withOpacity(_dragPercentage < 0 ? _dragPercentage.abs() : 0),
                          size: 100,
                        ),
                      ),
                    ),
                    Expanded(
                      child: Center(
                        child: Icon(
                          Icons.check,
                          color: Colors.white.withOpacity(_dragPercentage > 0 ? _dragPercentage : 0),
                          size: 100,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              // Card
              Positioned(
                left: 16 + _dragPosition,
                right: 16 - _dragPosition,
                top: 16,
                bottom: 100,
                child: GestureDetector(
                  onHorizontalDragUpdate: _onDragUpdate,
                  onHorizontalDragEnd: _onDragEnd,
                  child: Transform.rotate(
                    angle: _dragPercentage * 0.2,
                    child: Card(
                      elevation: 8,
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
                            const SizedBox(height: 16),
                            const Center(
                              child: Text(
                                '← Swipe left to skip\nSwipe right to invest →',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: Colors.grey,
                                  fontSize: 14,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              // Buttons
              Positioned(
                left: 0,
                right: 0,
                bottom: 16,
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