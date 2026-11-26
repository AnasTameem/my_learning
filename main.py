import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.capabilities import ModelFallback

load_dotenv()

provider = GoogleProvider(api_key=os.environ["LLM_API_KEY"])
primary_model = GoogleModel(os.environ["LLM_MODEL"], provider=provider)
backup_model = GroqModel(
    os.environ["FALLBACK_MODEL"],
    provider=GroqProvider(api_key=os.environ["GROQ_API_KEY"]),
)
agent = Agent(primary_model, capabilities=[ModelFallback(backup_model)])

FAKE_RATES = {("INR", "USD"): 0.5, ("USD", "INR"): 2.0}  # fake on purpose


@agent.tool_plain
def convert_currency(amount: float, from_code: str, to_code: str) -> str:
    """Convert an amount of money from one currency to another.

    Args:
        amount: The amount to convert.
        from_code: Three-letter ISO currency code to convert from, e.g. INR.
        to_code: Three-letter ISO currency code to convert to, e.g. USD.
    """
    rate = FAKE_RATES.get((from_code.upper(), to_code.upper()))
    if rate is None:
        return f"No rate available for {from_code}->{to_code}."
    return f"{amount} {from_code.upper()} = {amount * rate:.2f} {to_code.upper()}"


result = agent.run_sync("How much is 2000 INR in USD?")
print(result.output)
print("answered by:", result.response.model_name)
print("model requests:", result.usage.requests)
for attempt in result.response.failed_attempts or []:
    print("failed attempt:", attempt.model_name, attempt.outcome)

if os.environ.get("DEBUG") == "1":
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                print("TOOL CALL  :", part.tool_name, part.args)
            elif isinstance(part, ToolReturnPart):
                print("TOOL RETURN:", part.tool_name, part.content)