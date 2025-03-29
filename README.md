# 📊 Octagon Research Demo

A tool to generate investor-ready research reports using the Octagon Agents API and OpenAI models. This tool can be run either as a command-line interface (CLI) or as a web-based application.

**This repository serves as a demonstration of how to use the [Octagon API](https://docs.octagonagents.com) for creating AI-powered research tools.**

It retrieves structured company and funding data, then synthesizes a professional Markdown report using an LLM and a custom template.

---

## 🚀 Setup

Follow these steps to set up the project:

### 1. Get an API Key

To use the Octagon Agents API, you'll need a free API key:

1. [Sign up for a free Octagon account](https://app.octagonai.co/signup)
2. Go to the Settings page
3. Navigate to the API Keys section
4. Create a new API key

### 2. Set up environment variables
Copy the `.env.example` file to create your own `.env` file:
```bash
cp .env.example .env
```

Then, edit the `.env` file to add your API keys:
- `OPENAI_API_KEY`: Your OpenAI API key
- `OCTAGON_API_KEY`: Your Octagon API key

### 3. Install dependencies
```bash
poetry install
```

---

## 🌐 Web Application

The web application provides a user interface to input company details (name or website) and generate research reports interactively.

**Usage:**
```bash
poetry run web
```

Once started, navigate to `http://127.0.0.1:5000` (or the address provided in the terminal) in your web browser.

---

## 💻 Command-Line Interface (CLI)

The CLI allows you to generate research reports directly from your terminal by providing a CSV file with company names and optional websites.

Your input CSV file must contain at least a `Name` column. A `Website` column is optional but recommended for better results. See [companies.csv](octagon_web_demo/input/companies.csv) for an example.

**Usage:**
```bash
poetry run research --csv /path/to/your/companies.csv
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE)