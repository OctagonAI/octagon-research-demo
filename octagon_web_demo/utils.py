# utils.py
import os
import re
import csv
from datetime import datetime
from typing import Dict, List

from octagon_web_demo.config import REPORTS_DIR

def load_template(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def extract_report_text(result) -> str:
    if isinstance(result, str):
        return result
    return getattr(result, "final_output", str(result))


def extract_company_name(report_text: str) -> str:
    match = re.search(r"(?i)Company Name:\s*(.*)", report_text)
    return match.group(1).strip() if match else "company"


def generate_report_path(company_name: str, base_dir: str = REPORTS_DIR) -> str:
    slug = re.sub(r'\W+', '_', company_name.lower()).strip("_")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, f"report_{slug}_{timestamp}.md")


def save_report(content: str, path: str):
    with open(path, "w") as f:
        f.write(content)


def build_llm_report_input(template: str, collected_data: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Format the company and funding data along with the markdown template
    into a prompt suitable for a GPT-style LLM.
    """
    report_summary = "\n\n".join([
        f"=== {key.upper()} DATA ===\n{value}"
        for key, value in collected_data.items()
    ])

    return [
        {
            "role": "system",
            "content": (
                "You are an expert analyst creating investor reports in Markdown format. "
                "Use the following Markdown template to structure your output."
            )
        },
        {
            "role": "user",
            "content": f"""
            You are an expert analyst creating investor reports in Markdown format.
            You are given a template and a summary of company and funding data.
            Your task is to synthesize the data into a complete investor research report.
            Also, for each data entry, include the source of the data in the report and list it as a source.
            Here is the template you must follow when generating the report:

            {template}

            Now, using this format, synthesize the following company and funding data into a complete investor research report:

            {collected_data}
            """
                    }
                ]


def read_companies_from_csv(path: str) -> List[Dict[str, str]]:
    companies = []
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row.get("Name")
            website = row.get("Website")
            if name:
                companies.append({
                    "name": name.strip(),
                    "website": website.strip() if website else None
                })
    return companies
