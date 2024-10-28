# Podcast Generation API

This API allows users to generate a podcast from a provided text prompt using FastAPI and the GROQ language model. It creates a dialogue between two speakers and then converts the generated text into an audio file (WAV). This project is built using FastAPI, Uvicorn, and Pydub, and is designed for easy deployment to services like Railway.

## Features
- Generate a podcast script based on user-provided text using the GROQ language model.
- Convert the generated script into audio files using Text-to-Speech (TTS).
- Serve the generated audio file through an HTTP endpoint.

## Requirements
To run this API, you need the following dependencies:

- Python 3.8+
- FastAPI
- Uvicorn
- Pydub
- GROQ API
- Edge-TTS
- aiofiles
- nest-asyncio

Install all dependencies using `pip`:

```sh
pip install -r requirements.txt
```

Ensure you have a directory named `static` in the root of your project to store the generated audio files:

```sh
mkdir static
```

## Endpoints

### POST `/generate_podcast/`
Generate a podcast from the provided text prompt.

#### Request Parameters
- `api_key` (str): Your GROQ API key.
- `input_text` (str): The prompt to generate a podcast.
- `language` (str): Language of the podcast (default: "Auto Detect").
- `speaker1` (str): The voice of speaker 1 (default: "en-US-AndrewMultilingualNeural").
- `speaker2` (str): The voice of speaker 2 (default: "en-US-BrianMultilingualNeural").

#### Example Request
```sh
curl -X POST "http://127.0.0.1:8000/generate_podcast/" \
  -F "api_key=YOUR_API_KEY" \
  -F "input_text=The impact of artificial intelligence on modern society" \
  -F "language=English"
```

#### Response
```json
{
  "id": "c5e119c7-7eec-439b-abd7-403ce7273548",
  "status": "pending",
  "podcast_path": "",
  "error": ""
}
```

### GET `/podcast_status/{request_id}`
Get the status of a podcast generation request.

#### Example Request
```sh
curl "http://127.0.0.1:8000/podcast_status/c5e119c7-7eec-439b-abd7-403ce7273548"
```

#### Response
- **`status`**: "pending", "completed", or "failed".
- **`podcast_path`**: URL to the generated audio file if completed.

```json
{
  "id": "c5e119c7-7eec-439b-abd7-403ce7273548",
  "status": "completed",
  "podcast_path": "http://127.0.0.1:8000/static/output_bdf451b2-a649-407a-af4b-1276d3ca7221.wav",
  "error": ""
}
```

## Running Locally
To run the API locally:

1. Install the dependencies using `pip install -r requirements.txt`.
2. Start the server using `uvicorn`:

```sh
uvicorn api:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Deployment to Railway
To deploy this project to Railway, follow these steps:

1. Create a new repository on GitHub and push your project code.
2. Connect your GitHub account to Railway and create a new project from your repository.
3. Set up environment variables, such as `API_KEY`, to provide your GROQ API credentials.
4. Include a `requirements.txt` and a `Procfile` to specify dependencies and commands to run.

### Example `Procfile`
```
web: uvicorn api:app --host 0.0.0.0 --port $PORT
```

## Notes
- Ensure that your `static` directory exists and has proper write permissions to store the generated audio files.
- GROQ API credentials are required to make requests to generate the podcast script.

## License
This project is licensed under the MIT License.

