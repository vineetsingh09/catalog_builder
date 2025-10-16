# Catalog Builder

A full-stack template for generating localized product marketing collateral with GPT. Users can submit a product name, keywords, country, and language through a lightweight web UI. The Python backend orchestrates OpenAI's Responses and Images APIs to create:

- A localized marketing description and bullet points.
- A short promotional blurb.
- Synthetic product imagery.
- Suggested shopping links for the selected locale.

The project is designed for deployment on static hosts such as Netlify or Vercel for the frontend, with the FastAPI backend deployable to any container-friendly platform (Railway, Fly.io, Render, etc.).

## Architecture

```
frontend/ (static site)
  index.html
  script.js
  styles.css
backend/ (FastAPI app)
  main.py
  requirements.txt
```

The frontend is framework-agnostic and can be dropped into any static hosting provider. It expects an environment variable called `VITE_API_BASE_URL` (or `window.API_BASE_URL` for plain HTML hosting) that points to the backend URL.

## Prerequisites

- Python 3.10+
- An OpenAI API key with access to the Responses and Images APIs.

## Backend setup

### Providing OpenAI credentials for local testing

The backend reads your OpenAI key from the `OPENAI_API_KEY` environment variable. You can supply it in any of the following ways:

- Export it in your shell before running the app (shown below).
- Create a `.env` file inside `backend/` that contains `OPENAI_API_KEY=sk-...` and use a tool such as [`python-dotenv`](https://pypi.org/project/python-dotenv/) or your process manager to load it.
- Configure it in your hosting provider's dashboard when deploying.

When running locally, the quickest option is to export the variable in your terminal session right before starting Uvicorn:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
uvicorn main:app --reload --port 8000
```

The API exposes two endpoints:

- `GET /health` – simple status check.
- `POST /generate` – accepts a JSON payload with `product_name`, `keywords`, `country`, and `language`.

Example request:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Smart Garden Sensor",
    "keywords": ["solar-powered", "soil moisture", "Bluetooth"],
    "country": "Germany",
    "language": "German"
  }'
```

The response includes localized copy, bullet points, marketing blurb, generated image URLs, and suggested sources.

## Frontend setup

The frontend consists of static assets that can be served locally or deployed to Netlify/Vercel. For local development, you can use any static file server:

```bash
cd frontend
python -m http.server 4173
```

If the backend runs on another origin (e.g. `http://localhost:8000`), create a file named `config.js` next to `index.html` with the following content:

```html
<script>
  window.API_BASE_URL = "http://localhost:8000";
</script>
```

When using a bundler like Vite, define `VITE_API_BASE_URL` in your environment to automatically configure the API endpoint.

### Deploying the frontend to Netlify/Vercel

1. Upload the contents of the `frontend/` directory as your site's build output.
2. Configure the site to inject `window.API_BASE_URL` in a snippet or use a build tool that supports environment variables.
3. Ensure the deployed site can reach the backend API over HTTPS.

## Deploying the backend

- **Railway/Fly.io/Render**: Use the provided `backend/main.py` as the app entry point. Set `OPENAI_API_KEY` as an environment variable. Make sure the port matches the platform's requirement (use the `$PORT` variable when available).
- **Vercel serverless**: Package `backend/main.py` as a serverless function via Vercel's Python runtime, or containerize the FastAPI app and deploy it as a separate service.

## Environment variables

| Variable | Description |
| --- | --- |
| `OPENAI_API_KEY` | Required. OpenAI key with access to Responses and Images APIs. |
| `VITE_API_BASE_URL` | Optional. Frontend build-time variable pointing to the backend. |

## Notes

- The OpenAI endpoints incur usage costs; monitor usage carefully.
- The generated sources are based on LLM reasoning and may require human verification before publishing.
- Extend the schema or prompts in `backend/main.py` to capture more structured attributes (pricing, specifications, etc.).
