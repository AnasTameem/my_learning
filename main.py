import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

load_dotenv()

provider = GoogleProvider(api_key=os.environ["LLM_API_KEY"])
model = GoogleModel(os.environ["LLM_MODEL"], provider=provider)


class Answer(BaseModel):
    definition: str = Field(description="A one-sentence definition")
    example: str = Field(description="A short concrete example of it in use")
    keywords: list[str] = Field(description="Exactly three keywords related to the topic")


agent = Agent(model, output_type=Answer)

result = agent.run_sync("In one sentence, what is a tool call in an LLM API?")

answer = result.output

print(answer.definition)
print()
print("Example:", answer.example)
print("Keywords:", ", ".join(answer.keywords))

import os

if os.environ.get("DEBUG") == "1":
    for message in result.all_messages():
        print(message)
        print("---")