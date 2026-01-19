# Custom Tools

> Pulled: 2026-01-17 11:01:55 -03
> Source: https://platform.claude.com/docs/en/agent-sdk/custom-tools

Build and integrate custom tools via in-process MCP servers.

## Creating Custom Tools

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions
from typing import Any
import aiohttp

@tool("get_weather", "Get current temperature for a location", {"latitude": float, "longitude": float})
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={args['latitude']}&longitude={args['longitude']}&current=temperature_2m&temperature_unit=fahrenheit"
        ) as response:
            data = await response.json()

    return {
        "content": [{
            "type": "text",
            "text": f"Temperature: {data['current']['temperature_2m']}F"
        }]
    }

custom_server = create_sdk_mcp_server(
    name="my-custom-tools",
    version="1.0.0",
    tools=[get_weather]
)
```

## Using Custom Tools

**Important**: Custom MCP tools require streaming input mode.

```python
async def message_generator():
    yield {
        "type": "user",
        "message": {
            "role": "user",
            "content": "What's the weather in San Francisco?"
        }
    }

options = ClaudeAgentOptions(
    mcp_servers={"my-custom-tools": custom_server},
    allowed_tools=["mcp__my-custom-tools__get_weather"]
)

async with ClaudeSDKClient(options=options) as client:
    await client.query(message_generator())
    async for msg in client.receive_response():
        print(msg)
```

## Tool Naming Format

Pattern: `mcp__{server_name}__{tool_name}`

Example: `mcp__my-custom-tools__get_weather`

## Schema Options

### Simple type mapping

```python
@tool("process_data", "Process data", {"name": str, "age": int, "email": str})
async def process_data(args: dict[str, Any]) -> dict[str, Any]:
    ...
```

### JSON Schema format

```python
@tool(
    "advanced_process",
    "Process with validation",
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0, "maximum": 150},
            "format": {"type": "string", "enum": ["json", "csv", "xml"]}
        },
        "required": ["name", "age"]
    }
)
async def advanced_process(args: dict[str, Any]) -> dict[str, Any]:
    ...
```

## Error Handling

```python
@tool("fetch_data", "Fetch data from an API", {"endpoint": str})
async def fetch_data(args: dict[str, Any]) -> dict[str, Any]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(args["endpoint"]) as response:
                if response.status != 200:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"API error: {response.status}"
                        }]
                    }
                data = await response.json()
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(data, indent=2)
                    }]
                }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to fetch data: {str(e)}"
            }]
        }
```

## Multiple Tools

```python
@tool("calculate", "Perform calculations", {"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    result = eval(args["expression"], {"__builtins__": {}})
    return {"content": [{"type": "text", "text": f"Result: {result}"}]}

@tool("translate", "Translate text", {"text": str, "target_lang": str})
async def translate(args: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": f"Translated: {args['text']}"}]}

multi_tool_server = create_sdk_mcp_server(
    name="utilities",
    version="1.0.0",
    tools=[calculate, translate]
)

allowed_tools=[
    "mcp__utilities__calculate",
    "mcp__utilities__translate"
]
```
