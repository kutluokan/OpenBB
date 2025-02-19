"""AI Controller Module."""

from typing import List, Optional
import os
from pathlib import Path
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
from openbb_cli.controllers.base_controller import BaseController
from openbb_cli.session import Session
from openbb_cli.config.menu_text import MenuText
from openbb_cli.config.constants import ENV_FILE_SETTINGS
from openbb_core.app.constants import OPENBB_DIRECTORY
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
        session.console.print(f"Loading .env from: {env_path}")
        load_dotenv(env_path)
        break

class AIController(BaseController):
    """AI Controller class."""
    
    CHOICES_COMMANDS = ["chat", "suggest", "prepare"]
    PATH = "/ai/"
    CHOICES_GENERATION = True
    
    CHOICES_COMMANDS_CUSTOM = {
        "chat": ["-q"],
        "suggest": ["-t", "-r"],
        "prepare": ["-b", "-c"],
    }
    
    def __init__(self, queue: Optional[List[str]] = None):
        """Initialize controller."""
        super().__init__(queue)
        self.update_completer(self.choices_default)
        
        # Debug information
        session.console.print(f"ENV_FILE_SETTINGS path: {ENV_FILE_SETTINGS}")
        session.console.print(f"OPENBB_DIRECTORY path: {OPENBB_DIRECTORY}")
        session.console.print(f"Current working directory: {os.getcwd()}")
        session.console.print(f"Root .env path: {Path(os.getcwd()).parent.parent / '.env'}")
        session.console.print(f"Current .env exists: {Path(ENV_FILE_SETTINGS).exists()}")
        session.console.print(f"OPENBB .env exists: {Path(OPENBB_DIRECTORY, '.env').exists()}")
        session.console.print(f"Root .env exists: {(Path(os.getcwd()).parent.parent / '.env').exists()}")
        
        # Print all environment variables starting with OPENBB or OPENAI
        for key, value in os.environ.items():
            if key.startswith(("OPENBB_", "OPENAI_")):
                session.console.print(f"Found env var: {key}")
        
        # Get API key directly from environment variables
        self.api_key = os.getenv("OPENBB_AI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.provider = os.getenv("OPENBB_AI_PROVIDER", "openai")
        
        session.console.print(f"Found API key: {'Yes' if self.api_key else 'No'}")
        session.console.print(f"Provider: {self.provider}")
        
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
            
    def call_prepare(self, other_args: List[str]):
        """Prepare optimal investment strategy based on user's market belief."""
        if not other_args:
            session.console.print("Usage: prepare -b <belief> -c <confidence_level>")
            return

        parser = argparse.ArgumentParser(prog='prepare', add_help=False)
        parser.add_argument("-b", "--belief", help="Your market belief or prediction", dest="belief", required=True)
        parser.add_argument("-c", "--confidence", help="Confidence level (0-100)", dest="confidence", type=int, default=90)
        
        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--belief")
            
        try:
            ns_parser = parser.parse_args(other_args)
            
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

        parser = argparse.ArgumentParser(prog='suggest', add_help=False)
        parser.add_argument("-t", "--timeframe", help="Investment timeframe (short/medium/long)", dest="timeframe", default="short")
        parser.add_argument("-r", "--risk", help="Risk level (1-5)", dest="risk", type=int, default=3)
        
        try:
            ns_parser = parser.parse_args(other_args)
            
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

    def call_chat(self, other_args: List[str]):
        """Chat with AI about financial topics and investment strategies."""
        if not other_args:
            session.console.print("Usage: chat -q <question>")
            return

        parser = argparse.ArgumentParser(prog='chat', add_help=False)
        parser.add_argument("-q", "--question", help="Question to ask", dest="question", required=True)
        
        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--question")
            
        try:
            ns_parser = parser.parse_args(other_args)
            
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
                session.console.print(response.choices[0].message.content)
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": ns_parser.question
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