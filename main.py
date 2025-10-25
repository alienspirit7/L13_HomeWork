"""Weather Data Agent - Main Orchestrator
LLM-powered agent for querying and visualizing NOAA weather data
"""

import anthropic
import google.generativeai as genai
from pathlib import Path
from config import Config
from tools import execute_bigquery_query, create_visualization
from typing import List, Dict, Any


# Tool definitions for Claude API
TOOL_DEFINITIONS = [
    {
        "name": "bigquery_query_tool",
        "description": "Queries NOAA weather data from BigQuery based on user-specified filters and saves results to CSV file. Use this when users want to retrieve, search, or filter weather data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date for query in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for query in YYYY-MM-DD format"
                },
                "country": {
                    "type": "string",
                    "description": "Two-letter country code (e.g., 'US', 'CA', 'GB')"
                },
                "state": {
                    "type": "string",
                    "description": "Two-letter state code for US states (e.g., 'CA', 'NY')"
                },
                "station_id": {
                    "type": "string",
                    "description": "Specific weather station ID"
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of metrics to retrieve: temp, max, min, prcp, wdsp, dewp, slp, sndp"
                },
                "aggregation": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly", "none"],
                    "description": "How to aggregate the data"
                },
                "metric_aggregation": {
                    "type": "string",
                    "enum": ["avg", "min", "max"],
                    "description": "Metric aggregation function (avg, min, max)",
                    "default": "avg"
                },
                "output_filename": {
                    "type": "string",
                    "description": "Name of the output CSV file",
                    "default": "weather_data.csv"
                }
            },
            "required": ["start_date", "end_date", "metrics"]
        }
    },
    {
        "name": "visualization_tool",
        "description": "Creates visualizations from CSV data files. Automatically chooses line charts for time series (continuous) data and bar charts for categorical (discrete) data. Use this when users want to see graphs or charts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "csv_filepath": {
                    "type": "string",
                    "description": "Path to the CSV file to visualize"
                },
                "chart_type": {
                    "type": "string",
                    "enum": ["line", "bar", "auto"],
                    "description": "Type of chart to create. 'auto' will detect based on data.",
                    "default": "auto"
                },
                "x_column": {
                    "type": "string",
                    "description": "Column name to use for x-axis"
                },
                "y_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Column name(s) to use for y-axis. Can be multiple for comparison."
                },
                "title": {
                    "type": "string",
                    "description": "Title for the chart"
                },
                "output_filename": {
                    "type": "string",
                    "description": "Name of the output PNG file",
                    "default": "visualization.png"
                }
            },
            "required": ["csv_filepath", "x_column", "y_columns"]
        }
    }
]


# Gemini tool definitions (converted format)
GEMINI_TOOLS = [
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="bigquery_query_tool",
                description="Queries NOAA weather data from BigQuery based on user-specified filters and saves results to CSV file. Use this when users want to retrieve, search, or filter weather data.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "start_date": genai.protos.Schema(type=genai.protos.Type.STRING, description="Start date for query in YYYY-MM-DD format"),
                        "end_date": genai.protos.Schema(type=genai.protos.Type.STRING, description="End date for query in YYYY-MM-DD format"),
                        "country": genai.protos.Schema(type=genai.protos.Type.STRING, description="Two-letter country code (e.g., 'US', 'CA', 'GB')"),
                        "state": genai.protos.Schema(type=genai.protos.Type.STRING, description="Two-letter state code for US states (e.g., 'CA', 'NY')"),
                        "station_id": genai.protos.Schema(type=genai.protos.Type.STRING, description="Specific weather station ID"),
                        "metrics": genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING), description="List of metrics to retrieve: temp, max, min, prcp, wdsp, dewp, slp, sndp"),
                        "aggregation": genai.protos.Schema(type=genai.protos.Type.STRING, description="How to aggregate the data: daily, weekly, monthly, none"),
                        "metric_aggregation": genai.protos.Schema(type=genai.protos.Type.STRING, description="Metric aggregation function (avg, min, max)"),
                        "output_filename": genai.protos.Schema(type=genai.protos.Type.STRING, description="Name of the output CSV file"),
                    },
                    required=["start_date", "end_date", "metrics"]
                )
            ),
            genai.protos.FunctionDeclaration(
                name="visualization_tool",
                description="Creates visualizations from CSV data files. Automatically chooses line charts for time series (continuous) data and bar charts for categorical (discrete) data. Use this when users want to see graphs or charts.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "csv_filepath": genai.protos.Schema(type=genai.protos.Type.STRING, description="Path to the CSV file to visualize"),
                        "chart_type": genai.protos.Schema(type=genai.protos.Type.STRING, description="Type of chart to create: line, bar, or auto"),
                        "x_column": genai.protos.Schema(type=genai.protos.Type.STRING, description="Column name to use for x-axis"),
                        "y_columns": genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING), description="Column name(s) to use for y-axis. Can be multiple for comparison."),
                        "title": genai.protos.Schema(type=genai.protos.Type.STRING, description="Title for the chart"),
                        "output_filename": genai.protos.Schema(type=genai.protos.Type.STRING, description="Name of the output PNG file"),
                    },
                    required=["csv_filepath", "x_column", "y_columns"]
                )
            )
        ]
    )
]


class LLMClient:
    """Unified interface for both Gemini and Anthropic LLMs"""

    def __init__(self, provider: str):
        self.provider = provider

        if provider == "gemini":
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                'gemini-2.5-pro',
                tools=GEMINI_TOOLS
            )
            self.chat = None
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def send_message(self, messages: List[Dict], system_prompt: str) -> Any:
        """Send a message and get a response"""
        if self.provider == "gemini":
            return self._send_gemini(messages, system_prompt)
        else:
            return self._send_anthropic(messages, system_prompt)

    def _send_gemini(self, messages: List[Dict], system_prompt: str) -> Dict:
        """Send message to Gemini"""
        # Initialize chat if needed
        if self.chat is None:
            self.chat = self.model.start_chat(history=[])

        # Get the last user message
        last_message = messages[-1]["content"]
        if isinstance(last_message, list):
            # Handle tool results
            last_message = "\n".join([str(item) for item in last_message])

        # Send message
        response = self.chat.send_message(last_message)

        # Parse response
        result = {
            "provider": "gemini",
            "content": [],
            "stop_reason": "end_turn"
        }

        # Check for function calls and text in parts
        has_function_call = False
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    has_function_call = True
                    fc = part.function_call
                    result["content"].append({
                        "type": "tool_use",
                        "name": fc.name,
                        "input": dict(fc.args),
                        "id": f"call_{fc.name}"
                    })
                    result["stop_reason"] = "tool_use"
                elif part.text:
                    result["content"].append({"type": "text", "text": part.text})

        return result

    def _send_anthropic(self, messages: List[Dict], system_prompt: str) -> Dict:
        """Send message to Anthropic"""
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=TOOL_DEFINITIONS,
            messages=messages
        )

        # Convert to unified format
        result = {
            "provider": "anthropic",
            "content": [],
            "stop_reason": response.stop_reason
        }

        for block in response.content:
            if hasattr(block, 'text'):
                result["content"].append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                result["content"].append({
                    "type": "tool_use",
                    "name": block.name,
                    "input": block.input,
                    "id": block.id
                })

        return result


def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """
    Execute the appropriate tool based on the tool name

    Args:
        tool_name: Name of the tool to execute
        tool_input: Dictionary of input parameters for the tool

    Returns:
        str: Result message from tool execution
    """

    if tool_name == "bigquery_query_tool":
        result = execute_bigquery_query(**tool_input)
    elif tool_name == "visualization_tool":
        result = create_visualization(**tool_input)
    else:
        result = {"success": False, "message": f"Unknown tool: {tool_name}"}

    # Format result as string
    if result["success"]:
        return result["message"]
    else:
        return f"Error: {result['message']}"


def load_system_prompt() -> str:
    """Load system prompt from file"""
    prompt_path = Config.PROMPTS_DIR / 'system_prompt.txt'
    if prompt_path.exists():
        return prompt_path.read_text()
    else:
        print(f"Warning: System prompt not found at {prompt_path}")
        return "You are a helpful weather data assistant."


def main():
    """Main conversation loop"""

    print("=" * 60)
    print("Weather Data Agent - NOAA GSOD 2024 Query & Visualization")
    print("=" * 60)
    print(f"Using LLM Provider: {Config.LLM_PROVIDER.upper()}")
    print("\nType 'exit', 'quit', or 'bye' to end the conversation.")
    print("Type 'help' to see what I can do.\n")

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return

    # Initialize LLM client
    try:
        llm_client = LLMClient(Config.LLM_PROVIDER)
    except Exception as e:
        print(f"Error initializing LLM client: {e}")
        return

    # Load system prompt
    system_prompt = load_system_prompt()

    # Initialize conversation history
    conversation_history = []

    # Main conversation loop
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nGoodbye! Thanks for using Weather Data Agent.")
                break

            # Add user message to history
            conversation_history.append({
                "role": "user",
                "content": user_input
            })

            # Send request to LLM
            response = llm_client.send_message(conversation_history, system_prompt)

            # Process response
            while response["stop_reason"] == "tool_use":
                # Add assistant's response to history
                conversation_history.append({
                    "role": "assistant",
                    "content": response["content"]
                })

                # Extract text content to display
                text_content = []
                for block in response["content"]:
                    if block["type"] == "text":
                        text_content.append(block["text"])

                if text_content:
                    print(f"\nAssistant: {' '.join(text_content)}")

                # Extract and execute tool calls
                tool_results = []
                for block in response["content"]:
                    if block["type"] == "tool_use":
                        print(f"\n[Executing {block['name']}...]")

                        # Execute tool
                        result = process_tool_call(block["name"], block["input"])

                        # Add result to tool_results
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": result
                        })

                        print(f"[Result: {result}]")

                # Add tool results to history
                conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })

                # Get next response from LLM
                response = llm_client.send_message(conversation_history, system_prompt)

            # Display final response
            final_text = []
            for block in response["content"]:
                if block["type"] == "text":
                    final_text.append(block["text"])

            if final_text:
                print(f"\nAssistant: {' '.join(final_text)}")

            # Add final response to history
            conversation_history.append({
                "role": "assistant",
                "content": response["content"]
            })

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'exit' to quit.")


if __name__ == "__main__":
    main()
