import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class OpenBBProvider with ChangeNotifier {
  bool _isLoading = false;
  String? _error;
  final String _baseUrl = 'http://localhost:8000'; // Replace with your OpenBB API endpoint
  
  bool get isLoading => _isLoading;
  String? get error => _error;

  // Investment recommendation data
  Map<String, dynamic>? _currentRecommendation;
  Map<String, dynamic>? get currentRecommendation => _currentRecommendation;

  Future<void> fetchNextRecommendation() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // Get stock sentiment from OpenBB
      final response = await http.get(Uri.parse('$_baseUrl/api/stocks/recommendation'));
      
      if (response.statusCode != 200) {
        throw Exception('Failed to fetch recommendation: ${response.statusCode}');
      }

      final data = json.decode(response.body);
      
      // Transform OpenBB data into app format
      _currentRecommendation = {
        'symbol': data['symbol'],
        'recommendation': _getRecommendation(data['sentiment_score']),
        'confidence': data['confidence'],
        'sentiment': _getSentimentLabel(data['sentiment_score']),
        'price': data['current_price'],
        'riskLevel': _calculateRiskLevel(data['volatility'], data['beta']),
      };
    } catch (e) {
      _error = e.toString();
      // Fallback to demo data if API is not available
      if (_error!.contains('Failed host lookup')) {
        _currentRecommendation = {
          'symbol': 'AAPL',
          'recommendation': 'Buy',
          'confidence': 0.85,
          'sentiment': 'Positive',
          'price': 150.25,
          'riskLevel': 'High',
        };
        _error = null;
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  String _getRecommendation(double sentimentScore) {
    if (sentimentScore > 0.6) return 'Strong Buy';
    if (sentimentScore > 0.2) return 'Buy';
    if (sentimentScore > -0.2) return 'Hold';
    if (sentimentScore > -0.6) return 'Sell';
    return 'Strong Sell';
  }

  String _getSentimentLabel(double score) {
    if (score > 0.3) return 'Positive';
    if (score > -0.3) return 'Neutral';
    return 'Negative';
  }

  String _calculateRiskLevel(double volatility, double beta) {
    final riskScore = (volatility * 0.7) + (beta * 0.3);
    if (riskScore > 1.5) return 'Very High';
    if (riskScore > 1.0) return 'High';
    if (riskScore > 0.5) return 'Medium';
    return 'Low';
  }

  Future<void> executeInvestment(String symbol) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/api/trade/execute'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'symbol': symbol,
          'action': 'buy',
          'quantity': 1, // TODO: Make quantity configurable
        }),
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to execute trade: ${response.statusCode}');
      }

      // TODO: Handle successful trade response
      await Future.delayed(const Duration(seconds: 1)); // Temporary delay for demo
    } catch (e) {
      _error = e.toString();
      // Silently continue if API is not available (demo mode)
      if (_error!.contains('Failed host lookup')) {
        _error = null;
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
} 