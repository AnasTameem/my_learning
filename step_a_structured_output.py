import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai import Agent, ToolOutput
from pydantic_ai.exceptions import UnexpectedModelBehavior

load_dotenv()

provider = GoogleProvider(api_key=os.environ["LLM_API_KEY"])
model = GoogleModel(os.environ["LLM_MODEL"], provider=provider)


class Answer(BaseModel):
    definition: str = Field(description="A detailed definition of the concept asked in 10 characters", max_length=10)
    example: str = Field(description="A short concrete example of it in use")
    keywords: list[str] = Field(description="Exactly three keywords related to the topic", min_length=3, max_length=3)


agent = Agent(model, output_type=ToolOutput(Answer, max_retries=1))

try:
    result = agent.run_sync(input("Query: "))
except UnexpectedModelBehavior as e:
    print("FAILED:", type(e).__name__)
    print(e)
    print("cause:", repr(e.__cause__))
    print("body:", e.body)
    raise SystemExit(1)

answer = result.output
print(answer.definition)
print()
print("Example:", answer.example)
print("Keywords:", ", ".join(answer.keywords))
print("model requests:", result.usage.requests)
print("model tokens:", result.usage.total_tokens)

if os.environ.get("DEBUG") == "1":
    for message in result.all_messages():
        print(message)
        print("---")

