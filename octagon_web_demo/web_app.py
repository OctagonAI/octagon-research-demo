import os
import asyncio
import tempfile
from flask import send_from_directory
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, redirect, url_for

from octagon_web_demo.pipeline import ResearchPipeline
from octagon_web_demo.utils import load_template, read_companies_from_csv
from octagon_web_demo.agents import deep_research_agent, companies_agent, funding_agent, report_agent

from octagon_web_demo.config import TEMPLATE_PATH, REPORTS_DIR

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

md_template = load_template(str(TEMPLATE_PATH))


# === Routes ===

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return redirect(url_for("process", filepath=filepath))


@app.route("/process")
def process():
    filepath = request.args.get("filepath")
    companies = read_companies_from_csv(filepath)
    print("Companies loaded:", companies)
    return render_template("process.html", companies=companies, filepath=filepath)


@app.route("/run", methods=["POST"])
def run_pipeline():
    filepath = request.form["filepath"]
    companies = read_companies_from_csv(filepath)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run_all():
        pipeline = ResearchPipeline(
            deep_research_agent=deep_research_agent,
            companies_agent=companies_agent,
            funding_agent=funding_agent,
            report_agent=report_agent,
            template=md_template
        )
        paths = []
        for company in companies:
            name = company["name"]
            website = company.get("website")
            prompt = f"Get all available data for this company: {website or name}"
            path = await pipeline.run(prompt)
            paths.append((name, path))
        return paths

    report_paths = loop.run_until_complete(run_all())

    return render_template("results.html", reports=report_paths)


@app.route('/download/reports/<path:filename>')
def download_report(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)


from flask import Response, stream_with_context
import time

@app.route("/stream/<company_name>")
def stream(company_name):
    website = request.args.get("website")
    prompt = f"Get all available data for this company: {website or company_name}"

    def generate():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_stream():
            pipeline = ResearchPipeline(
                deep_research_agent=deep_research_agent,
                companies_agent=companies_agent,
                funding_agent=funding_agent,
                report_agent=report_agent,
                template=md_template
            )
            async for chunk in pipeline.run_streamed(prompt):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        # Use loop.run_until_complete to yield from async gen
        for message in loop.run_until_complete(_collect_streamed_output(run_stream)):
            yield message

    return Response(generate(), content_type='text/event-stream')


async def _collect_streamed_output(async_gen):
    output = []
    async for chunk in async_gen():
        output.append(chunk)
    return output



# === Run App ===
def main():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()
