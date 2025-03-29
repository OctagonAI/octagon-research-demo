# 📊 Octagon Research Demo

A tool to generate investor-ready research reports using the Octagon Agents API and OpenAI models. Available both as a CLI and a web-based application.

It retrieves structured company and funding data, then synthesizes a professional Markdown report using an LLM and a custom template.

---

## 🚀 Quickstart


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

### 4. Run web based research
```bash
poetry run web
```


### 5. Run CLI based research
```bash
poetry run research
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.