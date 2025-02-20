"""Trading Controller Module for Alpaca API integration."""

from typing import Dict, Optional
import os
from pathlib import Path
import requests
from openbb_cli.controllers.base_controller import BaseController
from openbb_cli.session import Session
from openbb_cli.config.constants import ENV_FILE_SETTINGS

session = Session()

class TradingController:
    """Trading Controller class for executing trades via Alpaca API."""
    
    def __init__(self):
        """Initialize controller."""
        self.api_key = os.getenv("OPENBB_ALPACA_API_KEY")
        self.api_secret = os.getenv("OPENBB_ALPACA_SECRET_KEY")
        self.base_url = "https://paper-api.alpaca.markets/v2"
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Content-Type": "application/json"
        }
        
        if not self.api_key or not self.api_secret:
            session.console.print(
                "[red]Error: Alpaca API credentials not set. Please set OPENBB_ALPACA_API_KEY and "
                "OPENBB_ALPACA_SECRET_KEY in your .env file.[/red]"
            )
            return

    def place_order(self, symbol: str, qty: int, side: str = "buy", type: str = "market", time_in_force: str = "day") -> Dict:
        """Place an order via Alpaca API.
        
        Parameters
        ----------
        symbol : str
            The stock symbol
        qty : int
            Number of shares
        side : str
            buy or sell
        type : str
            market or limit
        time_in_force : str
            day, gtc, opg, cls, ioc, fok
            
        Returns
        -------
        Dict
            The order response from Alpaca API
        """
        endpoint = f"{self.base_url}/orders"
        
        data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": type,
            "time_in_force": time_in_force
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=data)
            response.raise_for_status()
            order_data = response.json()
            
            # Print order confirmation
            status_color = "green" if order_data.get("status") == "accepted" else "yellow"
            session.console.print(
                f"[{status_color}]Order {order_data.get('status', 'submitted')}: "
                f"{side.upper()} {qty} shares of {symbol}[/{status_color}]"
            )
            
            return order_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error placing order: {str(e)}"
            if hasattr(e.response, 'json'):
                error_msg = f"Error placing order: {e.response.json().get('message', str(e))}"
            session.console.print(f"[red]{error_msg}[/red]")
            return {"error": error_msg}

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position for a symbol.
        
        Parameters
        ----------
        symbol : str
            The stock symbol
            
        Returns
        -------
        Optional[Dict]
            The position data if exists, None otherwise
        """
        endpoint = f"{self.base_url}/positions/{symbol}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None

    def get_account(self) -> Dict:
        """Get account information.
        
        Returns
        -------
        Dict
            The account information
        """
        endpoint = f"{self.base_url}/account"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Error getting account info: {str(e)}"
            session.console.print(f"[red]{error_msg}[/red]")
            return {"error": error_msg} 