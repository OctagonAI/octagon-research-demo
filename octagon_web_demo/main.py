import asyncio
import argparse
import os

from octagon_web_demo.utils import load_template, read_companies_from_csv
from octagon_web_demo.pipeline import ResearchPipeline
from octagon_web_demo.config import TEMPLATE_PATH, CSV_PATH
from octagon_web_demo.agents import search_agent, deep_research_agent, companies_agent, funding_agent, report_agent, judge_agent

# === Templates & CSV Input ===
md_template = load_template(TEMPLATE_PATH)


# === Entry Point ===
async def async_main(csv_path=None):
    pipeline = ResearchPipeline(
        search_agent=search_agent,
        companies_agent=companies_agent,
        funding_agent=funding_agent,
        deep_research_agent=deep_research_agent,
        report_agent=report_agent,
        judge_agent=judge_agent,
        template=md_template
    )
    # Use provided csv_path or fall back to config CSV_PATH
    path_to_use = csv_path or CSV_PATH
    companies = read_companies_from_csv(path_to_use)
    
    for company in companies:
        try:
            company_name = company["name"]
            website = company.get("website")
            print(f"\nStarting Octagon Private Markets Research for: {company_name}")
            if website:
                prompt = f"Get all available data for this company: {website}"
                filename_hint = website.replace("https://", "").replace("http://", "").split("/")[0]
            else:
                prompt = f"Get all available data for this company: {company_name}"
                filename_hint = company_name
            await pipeline.run(prompt, filename_hint)
        except Exception as e:
            print(f"Failed to process {company_name}: {e}")

def cli():
    """Command line interface entry point"""
    parser = argparse.ArgumentParser(description='Octagon Research Tool')
    parser.add_argument('--csv', '-c', dest='csv_path', 
                        help='Path to the input CSV file containing companies to research')
    args = parser.parse_args()
    
    # Don't set environment variable, just pass the argument directly
    asyncio.run(async_main(args.csv_path))

if __name__ == "__main__":
    cli()
