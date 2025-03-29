import json
import re
from typing import Union
from dataclasses import dataclass

from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

from octagon_web_demo.utils import (
    build_llm_report_input,
    extract_report_text,
    generate_report_path,
    save_report
)

@dataclass
class JudgeOutput:
    decision: bool
    selected_data: Union[str, dict]

class ResearchPipeline:
    def __init__(
        self,
        search_agent: Agent,
        deep_research_agent: Agent,
        companies_agent: Agent,
        funding_agent: Agent,
        report_agent: Agent,
        judge_agent: Agent,
        template: str
    ):
        self.search_agent = search_agent
        self.companies_agent = companies_agent
        self.funding_agent = funding_agent
        self.deep_research_agent = deep_research_agent
        self.report_agent = report_agent
        self.judge_agent = judge_agent
        self.template = template

    async def run(self, query: str, filename_hint: str) -> str:
        print(f"\n🔍 Query: {query}")
        print(f"📝 Template Preview:\n{self.template[:300]}...\n")

        collected_data = {}
        temp_report = ""

        # --- Process Search Agent (no judge) ---
        search_data = await self._run_agent_streamed(self.search_agent, "Search Agent", query)
        print(f"\n📦 Search Agent Data:\n{search_data}\n")
        if not self._is_invalid(search_data):
            collected_data["search"] = search_data
            temp_report = await self._update_report(collected_data, temp_report)
            debug_path = self._save_debug_report(temp_report, filename_hint)
            print(f"\n📝 Temp Report after Search Agent (debug saved at {debug_path}):\n{temp_report[:500]}...\n")
        else:
            print("⚠️ Search agent returned invalid data.")

        # --- Companies Agent ---
        companies_data = await self._run_agent_streamed(self.companies_agent, "Companies Agent", query)
        print(f"\n📦 Companies Agent Data:\n{companies_data}\n")
        if not self._is_invalid(companies_data):
            if temp_report:
                judge_result = await self._judge_data(new_data=companies_data, base_report=temp_report)
                if not judge_result["decision"]:
                    print("Judge determined Companies Agent data is not relevant. Skipping this data source.")
                else:
                    companies_data = judge_result["selected_data"] or companies_data
                    collected_data["companies"] = companies_data
                    temp_report = await self._update_report(collected_data, temp_report)
                    debug_path = self._save_debug_report(temp_report, filename_hint)
                    print(f"\n📝 Temp Report after Companies Agent (debug saved at {debug_path}):\n{temp_report[:500]}...\n")
            else:
                collected_data["companies"] = companies_data
                temp_report = await self._update_report(collected_data, temp_report)
        else:
            print("⚠️ Companies agent returned invalid data.")

        # --- Funding Agent ---
        funding_data = await self._run_agent_streamed(self.funding_agent, "Funding Agent", query)
        print(f"\n📦 Funding Agent Data:\n{funding_data}\n")
        if not self._is_invalid(funding_data):
            if temp_report:
                judge_result = await self._judge_data(new_data=funding_data, base_report=temp_report)
                if not judge_result["decision"]:
                    print("Judge determined Funding Agent data is not relevant. Skipping this data source.")
                else:
                    funding_data = judge_result["selected_data"] or funding_data
                    collected_data["funding"] = funding_data
                    temp_report = await self._update_report(collected_data, temp_report)
                    debug_path = self._save_debug_report(temp_report, filename_hint)
                    print(f"\n📝 Temp Report after Funding Agent (debug saved at {debug_path}):\n{temp_report[:500]}...\n")
            else:
                collected_data["funding"] = funding_data
                temp_report = await self._update_report(collected_data, temp_report)
        else:
            print("⚠️ Funding agent returned invalid data.")

        # --- Deep Research Agent (no judge) ---
        deep_research_query = (
            f"Using the following template, collect all the required information to populate it:\n\n"
            f"For this company: {query}\n\n"
            f"Here is the template:\n\n"
            f"{self.template}\n\n"
        )
        deep_research_data = await self._run_agent_streamed(self.deep_research_agent, "Deep Research Agent", deep_research_query)
        print(f"\n📦 Deep Research Agent Data:\n{deep_research_data}\n")
        if not self._is_invalid(deep_research_data):
            collected_data["deep_research"] = deep_research_data
            temp_report = await self._update_report(collected_data, temp_report)
            debug_path = self._save_debug_report(temp_report, filename_hint)
            print(f"\n📝 Temp Report after Deep Research Agent (debug saved at {debug_path}):\n{temp_report[:500]}...\n")
        else:
            print("⚠️ Deep research agent returned invalid data.")

        if not collected_data:
            company_name = self._extract_company_name_from_query(query)
            fallback_path = generate_report_path(filename_hint)
            fallback_md = (
                f"# No Data Found for {company_name}\n\n"
                "Unfortunately, no meaningful data could be retrieved for this company.\n\n"
            )
            save_report(fallback_md, fallback_path)
            print(f"⚠️ No valid data found. Fallback report saved to: {fallback_path}")
            return fallback_path

        company_name = extract_report_text(temp_report)
        report_path = generate_report_path(filename_hint)
        save_report(temp_report, report_path)
        print(f"\n✅ Final report saved to: {report_path}")
        return report_path

    async def run_streamed(self, query: str):
        collected_data = {}
        temp_report = ""

        yield "\n\n🚀 Running Search Agent...\n"
        search_data = ""
        async for chunk in self._run_agent_streamed_yielding(self.search_agent, query):
            search_data += chunk
            yield chunk
        if not self._is_invalid(search_data):
            collected_data["search"] = search_data
            temp_report = await self._update_report(collected_data, temp_report)
            debug_hint = self._extract_company_name_from_query(query)
            debug_path = self._save_debug_report(temp_report, debug_hint)
            yield f"\n\n📝 Temp Report after Search Agent (debug saved at {debug_path}):\n{temp_report[:500]}...\n"

        yield "\n\n🚀 Running Companies Agent...\n"
        company_data = ""
        async for chunk in self._run_agent_streamed_yielding(self.companies_agent, query):
            company_data += chunk
            yield chunk
        if not self._is_invalid(company_data):
            if temp_report:
                judge_result = await self._judge_data(new_data=company_data, base_report=temp_report)
                if not judge_result["decision"]:
                    yield "\n⚠️ Judge determined Companies Agent data is not relevant. Skipping this data source.\n"
                else:
                    company_data = judge_result["selected_data"] or company_data
                    collected_data["companies"] = company_data
                    temp_report = await self._update_report(collected_data, temp_report)
                    debug_hint = self._extract_company_name_from_query(query)
                    debug_path = self._save_debug_report(temp_report, debug_hint)
                    yield f"\n\n📝 Temp Report after Companies Agent (debug saved at {debug_path}):\n{temp_report[:500]}...\n"
            else:
                collected_data["companies"] = company_data
                temp_report = await self._update_report(collected_data, temp_report)
        else:
            yield "\n⚠️ Companies agent returned invalid data.\n"

        yield "\n\n🚀 Running Funding Agent...\n"
        funding_data = ""
        async for chunk in self._run_agent_streamed_yielding(self.funding_agent, query):
            funding_data += chunk
            yield chunk
        if not self._is_invalid(funding_data):
            if temp_report:
                judge_result = await self._judge_data(new_data=funding_data, base_report=temp_report)
                if not judge_result["decision"]:
                    yield "\n⚠️ Judge determined Funding Agent data is not relevant. Skipping this data source.\n"
                else:
                    funding_data = judge_result["selected_data"] or funding_data
                    collected_data["funding"] = funding_data
                    temp_report = await self._update_report(collected_data, temp_report)
                    debug_hint = self._extract_company_name_from_query(query)
                    debug_path = self._save_debug_report(temp_report, debug_hint)
                    yield f"\n\n📝 Temp Report after Funding Agent (debug saved at {debug_path}):\n{temp_report[:500]}...\n"
            else:
                collected_data["funding"] = funding_data
                temp_report = await self._update_report(collected_data, temp_report)
        else:
            yield "\n⚠️ Funding agent returned invalid data.\n"

        yield "\n\n🚀 Running Deep Research Agent...\n"
        deep_research_query = (
            f"Using the following template, collect all the required information to populate it:\n\n"
            f"For this company: {query}\n\n"
            f"Here is the template:\n\n"
            f"{self.template}\n\n"
        )
        deep_research_data = ""
        async for chunk in self._run_agent_streamed_yielding(self.deep_research_agent, deep_research_query):
            deep_research_data += chunk
            yield chunk
        if not self._is_invalid(deep_research_data):
            collected_data["deep_research"] = deep_research_data
            temp_report = await self._update_report(collected_data, temp_report)
            debug_hint = self._extract_company_name_from_query(query)
            debug_path = self._save_debug_report(temp_report, debug_hint)
            yield f"\n\n📝 Temp Report after Deep Research Agent (debug saved at {debug_path}):\n{temp_report[:500]}...\n"
        else:
            yield "\n⚠️ Deep research agent returned invalid data.\n"

        if not collected_data:
            company_name = self._extract_company_name_from_query(query)
            fallback_path = generate_report_path(company_name)
            fallback_md = (
                f"# No Data Found for {company_name}\n\n"
                "Unfortunately, no meaningful data could be retrieved for this company.\n\n"
            )
            save_report(fallback_md, fallback_path)
            yield f"\n⚠️ No valid data found. Fallback report saved.\n"
            yield f"[DOWNLOAD_LINK]:/download/reports/{fallback_path.split('/')[-1]}"
            return

        yield "\n\n✅ Final Report:\n"
        yield f"\n📄 Report:\n\n{temp_report}\n"
        report_path = generate_report_path(self._extract_company_name_from_query(query))
        yield f"[DOWNLOAD_LINK]:/download/reports/{report_path.split('/')[-1]}"

    async def _judge_data(self, new_data: str, base_report: str) -> dict:
        judge_prompt = (
            "You are a judge that evaluates if new research data is relevant to the company described in the base report. "
            "Analyze the information and decide if it is relevant or not. "
            "Respond with a JSON object with exactly two keys:\n"
            '  "decision": a boolean value (true if data is relevant, false otherwise),\n'
            '  "selected_data": if decision is true, include the data that is relevant; '
            '   Be as flexible as possible and include as MUCH DATA AS POSSIBLE. '
            "If decision is false, leave this as an empty string. "
            "Ensure the JSON is valid and nothing else is output."
        )
        input_items = [{"role": "user", "content": f"Base Report:\n{base_report}\n\nNew Data:\n{new_data}\n\n{judge_prompt}"}]
        judge_result = await Runner.run(self.judge_agent, input=input_items)
        judge_text = extract_report_text(judge_result).strip()
        judge_text = re.sub(r"^```(?:json)?\s*", "", judge_text)
        judge_text = re.sub(r"\s*```$", "", judge_text)

        try:
            judge_dict = json.loads(judge_text)
            verdict = judge_dict["decision"]
            judge_selected_data = judge_dict["selected_data"]
        except Exception as e:
            print("❌ Failed to parse judge JSON:", e)
            return {"decision": False, "selected_data": ""}

        return {
            "decision": verdict,
            "selected_data": judge_selected_data if verdict else ""
        }

    async def _update_report(self, collected_data: dict, previous_report: str) -> str:
        template_to_use = self.template if not previous_report else previous_report
        report_input = build_llm_report_input(template_to_use, collected_data)
        print(f"\n🛠️  Report Input Payload:\n{json.dumps(report_input, indent=2)[:1000]}...\n")
        print("\n🧠 Running Report Agent for incremental update...")
        report_result = await Runner.run(self.report_agent, input=report_input)
        updated_report = extract_report_text(report_result)
        return updated_report

    def _save_debug_report(self, report: str, hint: str) -> str:
        debug_filename = f"debug_{hint}"
        debug_path = generate_report_path(debug_filename)
        save_report(report, debug_path)
        return debug_path

    async def _run_agent_streamed(self, agent: Agent, label: str, query: str) -> str:
        print(f"\n🚀 {label} → Query:\n{query}\n")
        input_items = [{"role": "user", "content": query}]
        run_stream = Runner.run_streamed(agent, input=input_items)
        output = ""
        async for event in run_stream.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                delta = event.data.delta
                output += delta
                if not delta.isspace():
                    print(delta, end="", flush=True)
            elif event.type == "agent_updated_stream_event":
                print(f"\n🔄 Handoff to {event.new_agent.name}")
        return output

    async def _run_agent_streamed_yielding(self, agent: Agent, query: str):
        input_items = [{"role": "user", "content": query}]
        run_stream = Runner.run_streamed(agent, input=input_items)
        async for event in run_stream.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                delta = event.data.delta
                if not delta.isspace():
                    yield delta
            elif event.type == "agent_updated_stream_event":
                yield f"\n🔄 Handoff to {event.new_agent.name}\n"

    def _is_invalid(self, data: str) -> bool:
        return (
            not data.strip()
            or "sorry, there was an error processing your request" in data.lower()
        )

    def _extract_company_name_from_query(self, query: str) -> str:
        if "for this company:" in query:
            return query.split("for this company:")[-1].strip()
        return "company"
