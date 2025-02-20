"""AI Controller Module."""

from typing import List, Optional, Dict, Tuple
import os
import json
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
        
        self.prepare_parser = argparse.ArgumentParser(prog='prepare', add_help=False)
        self.prepare_parser.add_argument("-b", "--belief", help="Your market belief", dest="belief", required=True)
        
        # Initialize choices for command completion
        choices = self.choices_default
        choices["chat"] = {
            "--question": None,
            "-q": "--question",
            "--help": None,
            "-h": "--help",
        }
        choices["prepare"] = {
            "--belief": None,
            "-b": "--belief",
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

    def execute_trade_plan(self, trade_plan: Dict) -> bool:
        """Execute a trade plan.
        
        Parameters
        ----------
        trade_plan : Dict
            The trade plan to execute with keys:
            - action: "buy" or "sell"
            - symbol: ticker symbol
            - quantity: number of shares/contracts
            - type: "stock" or "option"
            - strike: strike price (for options)
            - expiry: expiration date (for options)
            
        Returns
        -------
        bool
            Whether the trade was executed successfully
        """
        try:
            if trade_plan["type"] == "stock":
                result = self.trading.place_order(
                    symbol=trade_plan["symbol"],
                    qty=trade_plan["quantity"],
                    side=trade_plan["action"]
                )
            else:
                # For options, we'd need to construct the OCC symbol
                option_symbol = f"{trade_plan['symbol']}{trade_plan['expiry']}{trade_plan['action'].upper()[0]}{trade_plan['strike']}"
                result = self.trading.place_order(
                    symbol=option_symbol,
                    qty=trade_plan["quantity"],
                    side=trade_plan["action"]
                )
            
            return not bool(result.get("error"))
            
        except Exception as e:
            session.console.print(f"[red]Error executing trade: {str(e)}[/red]")
            return False

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
        """Prepare and optionally execute optimal trade based on market belief."""
        if not other_args:
            session.console.print("Usage: prepare -b <belief>")
            return

        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--belief")
            
        try:
            ns_parser = self.prepare_parser.parse_args(other_args)
            
            if self.provider == "openai":
                # First get the trade plan
                response = self.client.chat.completions.create(
                    model="chatgpt-4o-latest",
                    messages=[
                        {"role": "system", "content": """You are a strategic trade planner.
                        Based on the user's market belief, respond with a JSON object containing ONE specific trade that would best capitalize on this view:
                        {
                            "trade_plan": {
                                "type": "stock" or "option",
                                "action": "buy" or "sell",
                                "symbol": "ticker symbol",
                                "quantity": number,
                                "strike": strike price (for options),
                                "expiry": "YYMMDD" (for options),
                                "reasoning": "1-2 sentences explaining the trade"
                            }
                        }
                        
                        Example 1: For "I think CPI will be very high":
                        {
                            "trade_plan": {
                                "type": "option",
                                "action": "buy",
                                "symbol": "TLT",
                                "quantity": 1,
                                "strike": 95,
                                "expiry": "240419",
                                "reasoning": "Buy TLT puts as bonds will likely sell off on high inflation data. The 95 strike gives good leverage while limiting downside."
                            }
                        }
                        
                        IMPORTANT: Return ONLY the raw JSON object, no markdown formatting or code blocks."""},
                        {"role": "user", "content": ns_parser.belief}
                    ]
                )
                
                try:
                    # Clean up the response - remove markdown code blocks if present
                    content = response.choices[0].message.content
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]
                    content = content.strip()
                    
                    # Parse the AI response as JSON
                    ai_response = json.loads(content)
                    trade_plan = ai_response["trade_plan"]
                    
                    # Display the trade plan
                    session.console.print("\n[yellow]Proposed Trade Plan:[/yellow]")
                    if trade_plan["type"] == "option":
                        option_type = "puts" if trade_plan["action"] == "buy" else "calls"
                        session.console.print(
                            f"[yellow]Buy {trade_plan['quantity']} {trade_plan['symbol']} "
                            f"${trade_plan['strike']} {option_type} "
                            f"expiring {trade_plan['expiry']}[/yellow]"
                        )
                    else:
                        session.console.print(
                            f"[yellow]{trade_plan['action'].upper()} {trade_plan['quantity']} "
                            f"shares of {trade_plan['symbol']}[/yellow]"
                        )
                    session.console.print(f"[yellow]Reasoning: {trade_plan['reasoning']}[/yellow]")
                    
                    # Ask for execution confirmation
                    session.console.print("\n[yellow]Would you like to execute this trade? (y/n)[/yellow]")
                    response = input().lower().strip()
                    
                    if response in ['y', 'yes']:
                        if self.execute_trade_plan(trade_plan):
                            session.console.print("[green]Trade executed successfully![/green]")
                        else:
                            session.console.print("[red]Failed to execute trade.[/red]")
                    elif response in ['n', 'no']:
                        session.console.print("Trade cancelled.")
                    else:
                        session.console.print("[red]Invalid response. Trade cancelled.[/red]")
                    
                except json.JSONDecodeError:
                    session.console.print("[red]Error: AI response was not in valid JSON format. Please try again.[/red]")
                    session.console.print(f"[red]AI response: {response.choices[0].message.content}[/red]")
                except KeyError as e:
                    session.console.print(f"[red]Error: Missing required field in trade plan: {str(e)}[/red]")
                except Exception as e:
                    session.console.print(f"[red]Error processing trade plan: {str(e)}[/red]")
            
            else:
                # Similar implementation for Anthropic
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": f"Based on this belief: '{ns_parser.belief}', what's the single best trade to make? Be very specific and concise (2-3 sentences max)."
                    }]
                )
                session.console.print(response.content[0].text)
                
        except Exception as e:
            session.console.print(f"[red]Error: {str(e)}[/red]")

    def call_suggest(self, _):
        """Get AI-driven investment suggestions based on market sentiment and trends."""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="chatgpt-4o-latest",
                    messages=[
                        {"role": "system", "content": """You are a concise investment advisor. 
                        Provide ONE specific investment suggestion in 2-3 short sentences:
                        1. What exact trade to make (be specific with strike prices for options)
                        2. Why this trade makes sense right now
                        
                        Example 1: "Buy AAPL $190 calls expiring next month. Apple's Vision Pro sales are exceeding expectations and the company is expected to announce expanded production."
                        
                        Example 2: "Short sell 100 shares of NFLX. Netflix's latest subscriber numbers show concerning trends in key markets and increased competition is hurting margins."
                        
                        Keep it brief and actionable. No disclaimers or additional analysis needed."""},
                        {"role": "user", "content": "What's your top investment suggestion right now?"}
                    ]
                )
                session.console.print(response.choices[0].message.content)
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": "What's your top investment suggestion right now? Be specific and concise (2-3 sentences max)."
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
        mt.add_cmd("suggest", "get a quick, specific investment suggestion")
        mt.add_cmd("prepare", "prepare and execute a trade based on your market view")
        
        session.console.print(text=mt.menu_text, menu="AI") 