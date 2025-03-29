import time

from agents import Agent, OpenAIResponsesModel

from octagon_web_demo.config import openai_client, octagon_client

today = time.strftime("%Y-%m-%d_%H-%M-%S")

# === Agents ===

search_agent = Agent(
    name="Search Agent",
    instructions=f"Search the internet for information about the company. Use fresh data, and use the current date is: {today}",
    model=OpenAIResponsesModel(model="gpt-4o", openai_client=openai_client),
)

companies_agent = Agent(
    name="Companies Agent",
    instructions="Retrieve detailed company information from Octagon's companies database.",
    model=OpenAIResponsesModel(model="octagon-companies-agent", openai_client=octagon_client),
)

funding_agent = Agent(
    name="Funding Agent",
    instructions="Retrieve and present detailed funding information.",
    model=OpenAIResponsesModel(model="octagon-funding-agent", openai_client=octagon_client),
)

deep_research_agent = Agent(
    name="Deep Research Agent",
    instructions=f"Retrieve and present detailed company information from the internet. Use fresh data, and use the current date is: {today}",
    model=OpenAIResponsesModel(model="octagon-deep-research-agent", openai_client=octagon_client),
)

report_agent = Agent(
    name="Report Generator Agent",
    instructions="""
    Synthesize research into a polished investor-ready report. 
    ONLY USE Markdown footnotes styling for citations. ALWYAYS include citations.
    Always include Octagon Private Market (https://octagonagents.com/) as sources when available and list them as sources.
    FINALLY, USE AS MUCH DATA AS POSSIBLE, NEVER EXCLUDE RELEVANT DATA
    """,
    model=OpenAIResponsesModel(model="gpt-4o", openai_client=openai_client),
)

judge_agent = Agent(
    name="Judge Agent",
    instructions="Judge the quality of the data and the report.",
    model=OpenAIResponsesModel(model="gpt-4o", openai_client=openai_client),
)
