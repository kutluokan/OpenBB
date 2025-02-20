"""AI Controller Module."""

from typing import List, Optional
import os
from pathlib import Path
import re
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
from openbb_cli.controllers.base_controller import BaseController
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
            
            # Check if the question is about stock price or market data
            stock_pattern = r'(?:what(?:\'s| is) (?:the )?(?:latest |current )?(?:stock )?price (?:of |for )?|(?:how much is |get |show )(?:the )?(?:stock )?price (?:of |for )?)([A-Za-z]+)(?:\s|$|\?|\.)'
            market_pattern = r'(?:how is |what\'s |what is |show |tell me about )(?:the )?(?:current )?(?:market|stock market|overall market)'
            
            stock_match = re.search(stock_pattern, ns_parser.question.lower())
            market_match = re.search(market_pattern, ns_parser.question.lower())
            
            response_text = None
            
            if stock_match:
                symbol = stock_match.group(1).upper()
                quote_data = self.get_stock_data(symbol)
                
                if quote_data:
                    response_text = f"The latest price for {symbol} is ${quote_data.get('price', quote_data.get('last_price', 0)):.2f}. "
                    if 'bid' in quote_data and 'ask' in quote_data:
                        response_text += f"Current bid: ${quote_data['bid']:.2f}, ask: ${quote_data['ask']:.2f}. "
                    if 'volume' in quote_data:
                        response_text += f"Today's volume: {quote_data['volume']:,}."
                    if 'change_percentage' in quote_data:
                        response_text += f" Change: {quote_data['change_percentage']:.2f}%"
                    elif 'change_percent' in quote_data:
                        response_text += f" Change: {quote_data['change_percent']:.2f}%"
                else:
                    response_text = "Unable to fetch stock data at this time."
            
            elif market_match:
                market_data = self.get_market_data()
                if market_data:
                    # Format market data response based on available fields
                    response_text = "Current Market Overview:\n"
                    for field, value in market_data.items():
                        if value is not None:
                            description = field.replace('_', ' ').title()
                            response_text += f"- {description}: {value}\n"
                else:
                    response_text = "Unable to fetch market data at this time."
            
            # If not a stock/market question or if data fetch failed, proceed with normal chat
            if response_text is None:
                if self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model="chatgpt-4o-latest",
                        messages=[
                            {"role": "system", "content": """You are a sophisticated financial assistant with expertise in:
                            1. Market analysis and trading strategies
                            2. Risk management and portfolio optimization
                            3. Technical and fundamental analysis
                            4. Current market trends and news impact
                            Provide clear, actionable advice while being mindful of risks."""},
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