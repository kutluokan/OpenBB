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
            # Use OpenBB's equity quote functionality
            quote_data = obb.equity.price.quote(symbol=symbol)
            
            if quote_data is None or quote_data.results is None:
                return None
                
            # Handle both list and single object responses
            if isinstance(quote_data.results, list):
                if not quote_data.results:  # Empty list
                    return None
                # Take the first result
                data = quote_data.results[0]
            else:
                data = quote_data.results
                
            # Extract relevant fields
            return {
                "symbol": symbol,
                "price": float(data.close) if hasattr(data, 'close') else float(data.price),
                "change_percent": float(data.change_percent) if hasattr(data, 'change_percent') else None,
                "volume": int(data.volume) if hasattr(data, 'volume') else None
            }
            
        except Exception as e:
            session.console.print(f"[red]Error fetching stock data: {str(e)}[/red]")
            return None

    def get_market_data(self) -> Optional[dict]:
        """Get market overview data using OpenBB's functionality."""
        try:
            # Use OpenBB's equity quote functionality for major indices
            indices = ["SPY", "QQQ", "DIA", "IWM"]
            market_data = {}
            
            for index in indices:
                quote = self.get_stock_data(index)
                if quote:
                    market_data[index] = quote
            
            return market_data
            
        except Exception as e:
            session.console.print(f"[red]Error fetching market data: {str(e)}[/red]")
            return None

    def get_stock_price(self, symbol: str) -> Optional[float]:
        """Get current stock price using OpenBB."""
        data = self.get_stock_data(symbol)
        return data["price"] if data else None

    def get_news_sentiment(self, symbol: str) -> Optional[Dict]:
        """Get news sentiment using OpenBB."""
        try:
            # For now, return None as news functionality is not critical
            return None
        except Exception as e:
            session.console.print(f"[red]Error fetching news data: {str(e)}[/red]")
            return None

    def get_option_chain(self, symbol: str) -> Optional[Dict]:
        """Get option chain data using OpenBB."""
        try:
            # Use OpenBB's options chain functionality
            options_data = obb.derivatives.options.chains(symbol=symbol)
            
            if options_data and options_data.results is not None:
                chain_data = options_data.results
                
                # Convert expiration dates to YYMMDD format
                expiries = []
                for exp in chain_data.expiration:
                    # Convert to string and extract relevant parts
                    exp_str = str(exp)[:10]  # Get YYYY-MM-DD part
                    exp_parts = exp_str.split('-')
                    if len(exp_parts) == 3:
                        yy = exp_parts[0][2:]  # Get last 2 digits of year
                        mm = exp_parts[1]
                        dd = exp_parts[2]
                        expiries.append(f"{yy}{mm}{dd}")
                
                # Get unique strikes and expiries
                strikes = sorted(list(set(chain_data.strike)))
                expiries = sorted(list(set(expiries)))
                
                session.console.print(f"[blue]Available expiries: {expiries}[/blue]")
                session.console.print(f"[blue]Available strikes: {strikes}[/blue]")
                
                return {
                    "strikes": strikes,
                    "expiries": expiries,
                    "chain": chain_data
                }
            return None
        except Exception as e:
            session.console.print(f"[red]Error fetching options data: {str(e)}[/red]")
            return None

    def validate_and_enrich_trade_plan(self, trade_plan: Dict) -> Dict:
        """Validate and enrich trade plan with real market data."""
        symbol = trade_plan["symbol"]
        
        # Get current stock price
        current_price = self.get_stock_price(symbol)
        if current_price is None:
            raise ValueError(f"Could not fetch current price for {symbol}")
            
        if trade_plan["type"] == "stock":
            trade_plan["current_price"] = current_price
            return trade_plan
            
        # For options, validate strike and expiry
        options_data = self.get_option_chain(symbol)
        if options_data is None:
            raise ValueError(f"Could not fetch options data for {symbol}")
            
        chain_data = options_data["chain"]
        
        # Convert target expiry to match OpenBB format (YYYY-MM-DD)
        target_expiry = trade_plan["expiry"]  # Format: YYMMDD
        target_expiry_full = f"20{target_expiry[:2]}-{target_expiry[2:4]}-{target_expiry[4:]}"
        
        # Filter chain for the specific expiry date
        expiry_chain = chain_data[chain_data.expiration == target_expiry_full]
        if expiry_chain.empty:
            # If no exact match, find closest valid expiry
            valid_expiries = sorted(list(set(chain_data.expiration)))
            valid_expiries = [exp for exp in valid_expiries if str(exp) >= target_expiry_full]
            if not valid_expiries:
                raise ValueError(f"No valid expiration dates found for {symbol} after {target_expiry}")
            target_expiry_full = valid_expiries[0]
            expiry_chain = chain_data[chain_data.expiration == target_expiry_full]
            
        # Convert full date back to YYMMDD format
        new_expiry = target_expiry_full[2:4] + target_expiry_full[5:7] + target_expiry_full[8:10]
        
        # Filter for puts or calls based on action
        is_put = trade_plan["action"] == "buy"  # We're buying puts or selling calls
        option_type = "puts" if is_put else "calls"
        type_chain = expiry_chain[expiry_chain.type == option_type]
        
        if type_chain.empty:
            raise ValueError(f"No {option_type} found for {symbol} at expiry {new_expiry}")
        
        # Find closest available strike with valid price
        target_strike = float(trade_plan["strike"])
        available_strikes = sorted(list(set(type_chain.strike)))
        if not available_strikes:
            raise ValueError(f"No strike prices available for {symbol} {option_type}")
            
        closest_strike = min(available_strikes, key=lambda x: abs(float(x) - target_strike))
        
        # Get the actual option price
        strike_chain = type_chain[type_chain.strike == closest_strike]
        if strike_chain.empty:
            raise ValueError(f"Could not find option price for {symbol} {option_type} at strike {closest_strike}")
            
        option_price = float(strike_chain.iloc[0].last_price)
        
        # Update trade plan with real market data
        trade_plan["strike"] = closest_strike
        trade_plan["expiry"] = new_expiry
        trade_plan["current_stock_price"] = current_price
        trade_plan["option_price"] = option_price
        
        session.console.print(f"[blue]Using strike price: ${closest_strike} (target was: ${target_strike})[/blue]")
        session.console.print(f"[blue]Using expiration date: {new_expiry} (target was: {target_expiry})[/blue]")
        session.console.print(f"[blue]Current option price: ${option_price:.2f}[/blue]")
        
        return trade_plan

    def execute_trade_plan(self, trade_plan: Dict) -> bool:
        """Execute a trade plan.
        
        Parameters
        ----------
        trade_plan : Dict
            The trade plan to execute
            
        Returns
        -------
        bool
            Whether the trade was executed successfully
        """
        try:
            # First validate and enrich the trade plan with real market data
            enriched_plan = self.validate_and_enrich_trade_plan(trade_plan)
            
            if enriched_plan["type"] == "stock":
                result = self.trading.place_order(
                    symbol=enriched_plan["symbol"],
                    qty=enriched_plan["quantity"],
                    side=enriched_plan["action"]
                )
            else:
                # Construct proper OCC option symbol for Alpaca
                # Format: SYMBOL + YYMMDD + C/P + STRIKE (padded to 8 digits, no decimal)
                # Example: For a $95.00 strike, it should be 00095000
                expiry = enriched_plan["expiry"]  # Format: YYMMDD
                strike = float(enriched_plan['strike'])
                strike_int = int(strike * 1000)  # Convert to integer (multiply by 1000 to preserve 3 decimal places)
                strike_padded = f"{strike_int:08d}"  # Pad to 8 digits with leading zeros
                option_type = "P" if enriched_plan["action"] == "buy" else "C"
                option_symbol = f"{enriched_plan['symbol']}{expiry}{option_type}{strike_padded}"
                
                session.console.print(f"[yellow]Attempting to execute option trade with symbol: {option_symbol}[/yellow]")
                
                result = self.trading.place_order(
                    symbol=option_symbol,
                    qty=enriched_plan["quantity"],
                    side=enriched_plan["action"]
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
            
            # Get current market data for context
            market_data = self.get_market_data()
            if market_data:
                session.console.print("\n[blue]Current Market Conditions:[/blue]")
                for index, data in market_data.items():
                    session.console.print(f"[blue]{index}: ${data['price']:.2f} ({data['change_percent']:.2f}%)[/blue]")
            
            if self.provider == "openai":
                # First get the trade plan
                response = self.client.chat.completions.create(
                    model="chatgpt-4o-latest",
                    messages=[
                        {"role": "system", "content": """You are a strategic trade planner.
                        Based on the user's market belief and current market conditions, respond with a JSON object containing ONE specific stock trade that would best capitalize on this view:
                        {
                            "trade_plan": {
                                "type": "stock",
                                "action": "buy" or "sell",
                                "symbol": "ticker symbol",
                                "quantity": number,
                                "reasoning": "1-2 sentences explaining the trade"
                            }
                        }
                        
                        Example 1: For "I think CPI will be very high":
                        {
                            "trade_plan": {
                                "type": "stock",
                                "action": "sell",
                                "symbol": "TLT",
                                "quantity": 100,
                                "reasoning": "Sell TLT as bonds will likely decline on high inflation data. Treasury ETFs typically move inversely to interest rates."
                            }
                        }
                        
                        Example 2: For "I think tech earnings will beat expectations":
                        {
                            "trade_plan": {
                                "type": "stock",
                                "action": "buy",
                                "symbol": "QQQ",
                                "quantity": 50,
                                "reasoning": "Buy QQQ to gain broad exposure to tech sector. Strong earnings could drive significant upside in major tech names."
                            }
                        }
                        
                        IMPORTANT: 
                        1. ONLY suggest stock trades (no options)
                        2. Use liquid ETFs or major stocks
                        3. Return ONLY the raw JSON object, no markdown formatting or code blocks"""},
                        {"role": "user", "content": f"Current market conditions: {market_data}\n\nUser belief: {ns_parser.belief}"}
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
            # Get current market data for context
            market_data = self.get_market_data()
            if market_data:
                session.console.print("\n[blue]Current Market Conditions:[/blue]")
                for index, data in market_data.items():
                    session.console.print(f"[blue]{index}: ${data['price']:.2f} ({data['change_percent']:.2f}%)[/blue]")
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="chatgpt-4o-latest",
                    messages=[
                        {"role": "system", "content": """You are a strategic trade planner.
                        Based on current market conditions, respond with a JSON object containing ONE specific stock trade that represents your best investment idea:
                        {
                            "trade_plan": {
                                "type": "stock",
                                "action": "buy" or "sell",
                                "symbol": "ticker symbol",
                                "quantity": number,
                                "reasoning": "2-3 sentences explaining why this trade makes sense right now"
                            }
                        }
                        
                        Guidelines:
                        1. ONLY suggest stock trades (no options)
                        2. Use liquid ETFs or major stocks
                        3. Include specific catalysts or reasons for the trade
                        4. Consider current market conditions in your reasoning
                        5. Return ONLY the raw JSON object, no markdown formatting or code blocks"""},
                        {"role": "user", "content": f"Current market conditions: {market_data}\n\nWhat is your top trade suggestion right now?"}
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
                    
                    # Get current price for the suggested stock
                    current_price = self.get_stock_price(trade_plan["symbol"])
                    
                    # Display the trade plan
                    session.console.print("\n[yellow]Proposed Trade Plan:[/yellow]")
                    session.console.print(
                        f"[yellow]{trade_plan['action'].upper()} {trade_plan['quantity']} "
                        f"shares of {trade_plan['symbol']}[/yellow]"
                    )
                    if current_price:
                        session.console.print(f"[yellow]Current price: ${current_price:.2f}[/yellow]")
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
                        "content": f"Based on these market conditions: {market_data}, what's your single best stock trade suggestion right now? Be specific and concise (2-3 sentences max)."
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