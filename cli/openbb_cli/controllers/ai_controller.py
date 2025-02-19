"""AI Controller Module."""

from typing import List, Optional
import os
from pathlib import Path
import openai
from anthropic import Anthropic
from openbb_cli.controllers.base_controller import BaseController
from openbb_cli.session import Session
from openbb_cli.config.menu_text import MenuText
from openbb_cli.config.constants import ENV_FILE_SETTINGS
from openbb_core.app.constants import OPENBB_DIRECTORY

session = Session()

class AIController(BaseController):
    """AI Controller class."""
    
    CHOICES_COMMANDS = ["analyze", "explain", "suggest", "chat"]
    PATH = "/ai/"
    
    def __init__(self, queue: Optional[List[str]] = None):
        """Initialize controller."""
        super().__init__(queue)
        
        # Debug information
        session.console.print(f"ENV_FILE_SETTINGS path: {ENV_FILE_SETTINGS}")
        session.console.print(f"OPENBB_DIRECTORY path: {OPENBB_DIRECTORY}")
        session.console.print(f"Current .env exists: {Path(ENV_FILE_SETTINGS).exists()}")
        
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
            openai.api_key = self.api_key
        else:
            self.anthropic = Anthropic(api_key=self.api_key)
            
    def call_analyze(self, other_args: List[str]):
        """Analyze data using AI."""
        parser = self.parse_simple_args(other_args)
        parser.add_argument("-d", "--data", help="Data to analyze", dest="data", required=True)
        
        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--data")
            
        ns_parser = self.parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            if self.provider == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a financial analysis assistant."},
                        {"role": "user", "content": f"Analyze this financial data: {ns_parser.data}"}
                    ]
                )
                session.console.print(response.choices[0].message.content)
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": f"Analyze this financial data: {ns_parser.data}"
                    }]
                )
                session.console.print(response.content[0].text)

    def call_explain(self, other_args: List[str]):
        """Explain financial concepts using AI."""
        parser = self.parse_simple_args(other_args)
        parser.add_argument("-t", "--term", help="Term to explain", dest="term", required=True)
        
        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--term")
            
        ns_parser = self.parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            if self.provider == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a financial education assistant."},
                        {"role": "user", "content": f"Explain this financial term: {ns_parser.term}"}
                    ]
                )
                session.console.print(response.choices[0].message.content)
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": f"Explain this financial term: {ns_parser.term}"
                    }]
                )
                session.console.print(response.content[0].text)

    def call_suggest(self, other_args: List[str]):
        """Get investment suggestions using AI."""
        parser = self.parse_simple_args(other_args)
        parser.add_argument("-c", "--context", help="Investment context", dest="context", required=True)
        
        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--context")
            
        ns_parser = self.parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            if self.provider == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an investment suggestion assistant."},
                        {"role": "user", "content": f"Suggest investments based on: {ns_parser.context}"}
                    ]
                )
                session.console.print(response.choices[0].message.content)
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": f"Suggest investments based on: {ns_parser.context}"
                    }]
                )
                session.console.print(response.content[0].text)

    def call_chat(self, other_args: List[str]):
        """Chat with AI about financial topics."""
        parser = self.parse_simple_args(other_args)
        parser.add_argument("-q", "--question", help="Question to ask", dest="question", required=True)
        
        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--question")
            
        ns_parser = self.parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            if self.provider == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a financial assistant."},
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

    def print_help(self):
        """Print help."""
        mt = MenuText("ai/")
        mt.add_info("AI Assistant Features")
        mt.add_cmd("analyze", "analyze financial data using AI")
        mt.add_cmd("explain", "get explanations of financial terms and concepts")
        mt.add_cmd("suggest", "get investment suggestions based on context")
        mt.add_cmd("chat", "have a conversation with AI about financial topics")
        
        session.console.print(text=mt.menu_text, menu="AI") 