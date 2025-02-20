"""AI Controller Module."""

from typing import List, Optional, Dict, Tuple
import os
from pathlib import Path
import re
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
from openbb_cli.controllers.base_controller import BaseController
from openbb_cli.controllers.trading_controller import TradingController
from openbb_cli.session import Session
from openbb_cli.config.menu_text import MenuText
from openbb_cli.config.constants import ENV_FILE_SETTINGS
from openbb_core.app.constants import OPENBB_DIRECTORY
from openbb import obb
import argparse

session = Session()

# Try to load .env from multiple possible locations
possible_env_paths = [
    ENV_FILE_SETTINGS,
    Path(OPENBB_DIRECTORY, '.env'),
    Path(os.getcwd()).parent.parent / '.env',  # OpenBB root folder
    Path('.env'),
]

for env_path in possible_env_paths:
    if Path(env_path).exists():
        load_dotenv(env_path)
        break

class AIController(BaseController):
    """AI Controller class."""
    
    CHOICES_COMMANDS = ["chat", "suggest", "prepare"]
    PATH = "/ai/"
    CHOICES_GENERATION = True
    
    def __init__(self, queue: Optional[List[str]] = None):
        """Initialize controller."""
        super().__init__(queue)
        
        # Initialize trading controller
        self.trading = TradingController()
        
        # Set up argument parsers for each command
        self.chat_parser = argparse.ArgumentParser(prog='chat', add_help=False)
        self.chat_parser.add_argument("-q", "--question", help="Question to ask", dest="question", required=True)
        
        self.suggest_parser = argparse.ArgumentParser(prog='suggest', add_help=False)
        self.suggest_parser.add_argument("-t", "--timeframe", help="Investment timeframe (short/medium/long)", dest="timeframe", choices=["short", "medium", "long"], default="short")
        self.suggest_parser.add_argument("-r", "--risk", help="Risk level (1-5)", dest="risk", type=int, choices=range(1, 6), default=3)
        
        self.prepare_parser = argparse.ArgumentParser(prog='prepare', add_help=False)
        self.prepare_parser.add_argument("-b", "--belief", help="Your market belief or prediction", dest="belief", required=True)
        self.prepare_parser.add_argument("-c", "--confidence", help="Confidence level (0-100)", dest="confidence", type=int, choices=range(0, 101), default=90)
        
        # Initialize choices for command completion
        choices = self.choices_default
        choices["chat"] = {
            "--question": None,
            "-q": "--question",
            "--help": None,
            "-h": "--help",
        }
        choices["suggest"] = {
            "--timeframe": {"short": None, "medium": None, "long": None},
            "-t": "--timeframe",
            "--risk": {str(i): None for i in range(1, 6)},
            "-r": "--risk",
            "--help": None,
            "-h": "--help",
        }
        choices["prepare"] = {
            "--belief": None,
            "-b": "--belief",
            "--confidence": {str(i): None for i in range(0, 101)},
            "-c": "--confidence",
            "--help": None,
            "-h": "--help",
        }
        self.update_completer(choices)
        
        # Get API key and provider
        self.api_key = os.getenv("OPENBB_AI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.provider = os.getenv("OPENBB_AI_PROVIDER", "openai")
        
        if not self.api_key:
            session.console.print(
                "[red]Error: AI API key not set. Please set OPENBB_AI_API_KEY in your .env file "
                "or use an existing OPENAI_API_KEY.[/red]"
            )
            return
            
        if self.provider == "openai":
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.anthropic = Anthropic(api_key=self.api_key)

    def parse_trading_command(self, text: str) -> Optional[Tuple[str, str, int]]:
        """Parse trading command from text.
        
        Parameters
        ----------
        text : str
            The text to parse
            
        Returns
        -------
        Optional[Tuple[str, str, int]]
            Tuple of (action, symbol, quantity) if trading command found, None otherwise
        """
        # Map common company names to their ticker symbols
        company_to_ticker = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "amd": "AMD",
            "intel": "INTC"
        }
        
        # Common trading command patterns
        buy_patterns = [
            r'(?:buy|purchase|long)\s+(\d+)\s+(?:share(?:s)?\s+(?:of\s+)?)?([A-Za-z]+)(?:\s+share(?:s)?)?',
            r'(?:buy|purchase|long)\s+([A-Za-z]+)\s+(\d+)\s+share(?:s)?',
        ]
        
        sell_patterns = [
            r'(?:sell|short)\s+(\d+)\s+(?:share(?:s)?\s+(?:of\s+)?)?([A-Za-z]+)(?:\s+share(?:s)?)?',
            r'(?:sell|short)\s+([A-Za-z]+)\s+(\d+)\s+share(?:s)?',
        ]
        
        # Try buy patterns
        for pattern in buy_patterns:
            match = re.search(pattern, text.lower())
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    qty, symbol = groups if groups[0].isdigit() else (groups[1], groups[0])
                    # Clean up the symbol/company name
                    symbol = symbol.strip().lower()
                    # Try to map company name to ticker
                    symbol = company_to_ticker.get(symbol, symbol.upper())
                    return ("buy", symbol, int(qty))
        
        # Try sell patterns
        for pattern in sell_patterns:
            match = re.search(pattern, text.lower())
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    qty, symbol = groups if groups[0].isdigit() else (groups[1], groups[0])
                    # Clean up the symbol/company name
                    symbol = symbol.strip().lower()
                    # Try to map company name to ticker
                    symbol = company_to_ticker.get(symbol, symbol.upper())
                    return ("sell", symbol, int(qty))
        
        return None

    def handle_trading_command(self, text: str) -> Optional[Dict]:
        """Handle trading command from chat.
        
        Parameters
        ----------
        text : str
            The chat text containing trading command
            
        Returns
        -------
        Optional[Dict]
            The order response if trading command executed, None otherwise
        """
        trading_command = self.parse_trading_command(text)
        if trading_command:
            side, symbol, qty = trading_command
            
            # Get current position if selling
            if side == "sell":
                position = self.trading.get_position(symbol)
                if not position:
                    session.console.print(
                        f"[red]Error: No position found for {symbol}[/red]"
                    )
                    return None
                
                current_qty = float(position.get("qty", 0))
                if current_qty < qty:
                    session.console.print(
                        f"[red]Error: Insufficient shares. You only have {current_qty} shares of {symbol}[/red]"
                    )
                    return None
            
            # Execute the trade
            return self.trading.place_order(symbol=symbol, qty=qty, side=side)
        
        return None

    def get_stock_data(self, symbol: str) -> Optional[dict]:
        """Get stock data using OpenBB's functionality."""
        try:
            # Use OpenBB's equity quote functionality with the same approach as /equity/price/quote
            quote_data = obb.equity.price.quote(symbol=symbol)
            
            if quote_data is None or quote_data.results is None:
                return None
                
            # Handle both list and single object responses
            if isinstance(quote_data.results, list):
                if not quote_data.results:  # Empty list
                    return None
                # Take the first result if it's a list
                data = quote_data.results[0].model_dump()
            else:
                # Handle single object response
                data = quote_data.results.model_dump()
                
            return data
            
        except Exception as e:
            return None

    def get_market_data(self) -> Optional[dict]:
        """Get market overview data using OpenBB's functionality."""
        try:
            # Use OpenBB's market overview functionality with yfinance provider
            market_data = obb.market.overview(provider="yfinance", use_cache=False)
            if market_data and market_data.results is not None:
                return market_data.results.model_dump()
            return None
        except TimeoutError:
            session.console.print("[red]Error: Request timed out while fetching market data. Please try again.[/red]")
            return None
        except Exception as e:
            session.console.print(f"[red]Error fetching market data: {str(e)}[/red]")
            return None

    def call_chat(self, other_args: List[str]):
        """Chat with AI about financial topics and investment strategies."""
        if not other_args:
            session.console.print("Usage: chat -q <question>")
            return

        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--question")
            
        try:
            ns_parser = self.chat_parser.parse_args(other_args)
            
            # First try direct trading command parsing
            trading_result = self.handle_trading_command(ns_parser.question)
            if trading_result:
                return trading_result
                
            # If not a direct trading command, use AI to interpret the request
            if self.provider == "openai":
                # First, ask AI to interpret if this is a trading request
                response = self.client.chat.completions.create(
                    model="chatgpt-4o-latest",
                    messages=[
                        {"role": "system", "content": """You are a trading assistant that helps convert natural language requests into trading actions.
                        If the user's request implies a trading action, respond with a JSON object containing:
                        {
                            "is_trade": true,
                            "action": "buy" or "sell",
                            "symbol": "the ticker symbol",
                            "quantity": number of shares,
                            "reason": "brief explanation of interpretation"
                        }
                        
                        If it's not a trading request, respond with:
                        {
                            "is_trade": false
                        }
                        
                        Examples of trading requests:
                        - "I want to invest $1000 in Apple"
                        - "Help me buy some Tesla stock"
                        - "I think Microsoft is going down, I should get out"
                        - "Get rid of my Amazon position"
                        
                        For quantity, if not specified:
                        - For buy: suggest 1 share
                        - For sell: suggest selling entire position
                        
                        Only respond with the JSON object, nothing else."""},
                        {"role": "user", "content": ns_parser.question}
                    ]
                )
                
                try:
                    ai_response = eval(response.choices[0].message.content)
                    if isinstance(ai_response, dict) and ai_response.get("is_trade"):
                        # Execute the trade
                        trade_result = self.trading.place_order(
                            symbol=ai_response["symbol"],
                            qty=ai_response["quantity"],
                            side=ai_response["action"]
                        )
                        
                        if trade_result and not trade_result.get("error"):
                            session.console.print(f"\n[green]Trade executed based on your request:[/green]")
                            session.console.print(f"[green]Reason: {ai_response['reason']}[/green]")
                        return trade_result
                except:
                    pass  # If AI response isn't valid JSON, proceed with normal chat
                
            # If not a trading request or using Anthropic, proceed with normal chat
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="chatgpt-4o-latest",
                    messages=[
                        {"role": "system", "content": """You are a sophisticated financial assistant with expertise in:
                        1. Market analysis and trading strategies
                        2. Risk management and portfolio optimization
                        3. Technical and fundamental analysis
                        4. Current market trends and news impact
                        
                        If the user wants to make trades, explain that they can use natural language commands like:
                        - "Buy 2 shares of Apple"
                        - "I want to invest in Tesla"
                        - "Sell my Microsoft shares"
                        - "Get out of my Amazon position"
                        
                        Otherwise, provide clear, actionable advice while being mindful of risks."""},
                        {"role": "user", "content": ns_parser.question}
                    ]
                )
                response_text = response.choices[0].message.content
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": ns_parser.question
                    }]
                )
                response_text = response.content[0].text

            # Print and return the response
            if response_text:
                session.console.print(response_text)
            return response_text
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            session.console.print(error_msg)
            return error_msg

    def call_prepare(self, other_args: List[str]):
        """Prepare optimal investment strategy based on user's market belief."""
        if not other_args:
            session.console.print("Usage: prepare -b <belief> -c <confidence_level>")
            return

        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--belief")
            
        try:
            ns_parser = self.prepare_parser.parse_args(other_args)
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="chatgpt-4o-latest",
                    messages=[
                        {"role": "system", "content": """You are an AI investment strategist. 
                        Analyze the user's market belief and suggest the optimal short-term investment strategy.
                        Consider various instruments including stocks, options, and crypto.
                        Provide specific trade suggestions with clear entry/exit points and risk assessment."""},
                        {"role": "user", "content": f"""Based on this market belief (confidence: {ns_parser.confidence}%):
                        '{ns_parser.belief}'
                        
                        What's the optimal short-term investment strategy? Consider:
                        1. Best instruments to trade
                        2. Specific entry/exit points
                        3. Risk assessment
                        4. Potential profit/loss scenarios
                        5. Alternative strategies"""}
                    ]
                )
                session.console.print(response.choices[0].message.content)
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": f"""Based on this market belief (confidence: {ns_parser.confidence}%):
                        '{ns_parser.belief}'
                        
                        What's the optimal short-term investment strategy? Consider:
                        1. Best instruments to trade
                        2. Specific entry/exit points
                        3. Risk assessment
                        4. Potential profit/loss scenarios
                        5. Alternative strategies"""
                    }]
                )
                session.console.print(response.content[0].text)
        except Exception as e:
            session.console.print(f"Error: {str(e)}")

    def call_suggest(self, other_args: List[str]):
        """Get AI-driven investment suggestions based on market sentiment and trends."""
        if not other_args:
            session.console.print("Usage: suggest -t <timeframe> -r <risk_level>")
            return

        try:
            ns_parser = self.suggest_parser.parse_args(other_args)
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="chatgpt-4o-latest",
                    messages=[
                        {"role": "system", "content": """You are an AI investment advisor specializing in trend detection
                        and sentiment analysis. Analyze market data, news, and social media sentiment to suggest
                        promising investment opportunities."""},
                        {"role": "user", "content": f"""Generate investment suggestions for:
                        Timeframe: {ns_parser.timeframe}
                        Risk Level: {ns_parser.risk}/5
                        
                        Consider:
                        1. Current market trends
                        2. Social media sentiment
                        3. News impact
                        4. Technical indicators
                        5. Risk/reward ratio"""}
                    ]
                )
                session.console.print(response.choices[0].message.content)
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": f"""Generate investment suggestions for:
                        Timeframe: {ns_parser.timeframe}
                        Risk Level: {ns_parser.risk}/5
                        
                        Consider:
                        1. Current market trends
                        2. Social media sentiment
                        3. News impact
                        4. Technical indicators
                        5. Risk/reward ratio"""
                    }]
                )
                session.console.print(response.content[0].text)
        except Exception as e:
            session.console.print(f"Error: {str(e)}")

    def print_help(self):
        """Print help."""
        mt = MenuText("ai/")
        mt.add_info("AI Assistant Features")
        mt.add_cmd("chat", "discuss financial topics with AI assistant")
        mt.add_cmd("suggest", "get AI-driven investment suggestions")
        mt.add_cmd("prepare", "get optimal trade strategy based on your market belief")
        
        session.console.print(text=mt.menu_text, menu="AI") 