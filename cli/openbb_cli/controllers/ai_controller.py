"""AI Controller Module."""

from typing import List, Optional
import openai
from anthropic import Anthropic
from openbb_cli.controllers.base_controller import BaseController
from openbb_cli.session import Session

session = Session()

class AIController(BaseController):
    """AI Controller class."""
    
    CHOICES_COMMANDS = ["analyze", "explain", "suggest", "chat"]
    PATH = "/ai/"
    
    def __init__(self, queue: Optional[List[str]] = None):
        """Initialize controller."""
        super().__init__(queue)
        
        if session.settings.AI_PROVIDER == "openai":
            openai.api_key = session.env.AI_API_KEY
        else:
            self.anthropic = Anthropic(api_key=session.env.AI_API_KEY)
            
    def call_analyze(self, other_args: List[str]):
        """Analyze data using AI."""
        parser = self.parse_simple_args(other_args)
        parser.add_argument("-d", "--data", help="Data to analyze", dest="data", required=True)
        
        if other_args and not other_args[0].startswith("-"):
            other_args.insert(0, "--data")
            
        ns_parser = self.parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            if session.settings.AI_PROVIDER == "openai":
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
            if session.settings.AI_PROVIDER == "openai":
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
            if session.settings.AI_PROVIDER == "openai":
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
            if session.settings.AI_PROVIDER == "openai":
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