from fastapi import FastAPI, Form, BackgroundTasks
from pydub import AudioSegment
import json
import uuid
import os
import edge_tts
import asyncio
import re
from groq import Groq
from typing import List, Dict
import nest_asyncio
from enum import Enum
from pydantic import BaseModel
import logging
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

nest_asyncio.apply()

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dictionary to store podcast generation requests
requests_db: Dict[str, Dict] = {}

class PodcastStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class PodcastRequest(BaseModel):
    id: str
    status: PodcastStatus
    podcast_path: str = ""
    error: str = ""

class PodcastGenerator:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        logger.debug(f"PodcastGenerator inicializado com api_key: {api_key}")

    async def generate_script(self, prompt: str, language: str) -> str:
        example = """
{
    "topic": "AGI",
    "podcast": [
        {
            "speaker": 2,
            "line": "So, AGI, huh? Seems like everyone's talking about it these days."
        },
        {
            "speaker": 1,
            "line": "Yeah, it's definitely having a moment, isn't it?"
        }
    ]
}
        """

        if language == "Auto Detect":
            language_instruction = "The podcast MUST be in the same language as the user input."
        else:
            language_instruction = f"The podcast MUST be in {language} language."

        system_prompt = f"""
You are a professional podcast generator. Your task is to generate a professional podcast script based on the user input.
- The podcast language MUST be in {language_instruction}
- The podcast should have 2 speakers.
- The podcast should be long.
- Do not use names for the speakers.
- The podcast should be interesting, lively, and engaging, and hook the listener from the start.
- The input text might be disorganized or unformatted, originating from sources like text files. Ignore any formatting inconsistencies or irrelevant details; your task is to distill the essential points, identify key definitions, and highlight intriguing facts that would be suitable for discussion in a podcast.
- The script must be in JSON format without any additional formatting. This means that the content must be in "pure" JSON, that is, without being delimited by code markers such as ```json or other delimiters.
- DO NOT ask for additional input from the user. Generate the complete podcast script directly.
- Ensure the topic closely aligns with the user-provided prompt.
Follow this example structure:
{example}
"""

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]

        logger.debug(f"Gerando script com prompt: {prompt} e language: {language}")

        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model="llama-3.1-70b-versatile"
            )
            logger.debug(f"Resposta da API recebida: {response}")
            if response and response.choices:
                response_text = response.choices[0].message.content
                try:
                    response_json = json.loads(response_text)
                    return json.dumps(response_json, indent=4)
                except json.JSONDecodeError:
                    logger.error("A resposta da API não está em formato JSON válido.")
                    return "A resposta da API não está em formato JSON válido."
            else:
                logger.error("A resposta da API está vazia ou não é válida.")
                return "A resposta da API está vazia ou não é válida."
        except Exception as e:
            logger.error(f"Erro ao gerar script: {e}")
            return f"Falha ao gerar o script do podcast: {e}"

    def clean_text(self, text: str) -> str:
        cleaned_text = re.sub(r'[^\w\s.,!?;:\-()"\']', '', text)
        return cleaned_text

    async def tts_generate(self, text: str, speaker: int, speaker1: str, speaker2: str) -> str:
        voice = speaker1 if speaker == 1 else speaker2
        cleaned_text = self.clean_text(text)
        logger.debug(f"Gerando TTS para o texto: {cleaned_text} com voz: {voice}")
        speech = edge_tts.Communicate(cleaned_text, voice)
        
        temp_filename = f"temp_{uuid.uuid4()}.wav"
        try:
            await speech.save(temp_filename)
            logger.debug(f"Arquivo TTS salvo como: {temp_filename}")
            return temp_filename
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo TTS: {e}")
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            raise e

    async def combine_audio_files(self, audio_files: List[str]) -> str:
        logger.debug(f"Combinando arquivos de áudio: {audio_files}")
        combined_audio = AudioSegment.empty()
        for audio_file in audio_files:
            combined_audio += AudioSegment.from_file(audio_file)
            logger.debug(f"Arquivo de áudio combinado: {audio_file}")
            os.remove(audio_file)

        output_filename = f"output_{uuid.uuid4()}.wav"
        combined_audio.export(f"static/{output_filename}", format="wav")
        logger.debug(f"Arquivo combinado salvo como: static/{output_filename}")
        return output_filename

    async def generate_podcast(self, request_id: str, input_text: str, language: str, speaker1: str, speaker2: str):
        logger.debug(f"Iniciando a geração do podcast com input_text: {input_text}")
        podcast_script = await self.generate_script(input_text, language)
        if not podcast_script:
            requests_db[request_id]["status"] = PodcastStatus.FAILED
            requests_db[request_id]["error"] = "Nenhum script de podcast foi gerado."
            return
        logger.debug(f"Script do podcast gerado: {podcast_script}")
        
        try:
            script_data = json.loads(podcast_script)
            lines = [self.clean_text(entry['line']) for entry in script_data.get('podcast', [])]
        except json.JSONDecodeError:
            requests_db[request_id]["status"] = PodcastStatus.FAILED
            requests_db[request_id]["error"] = "Falha ao analisar o script do podcast."
            return

        audio_files = await asyncio.gather(
            *[self.tts_generate(line, i % 2 + 1, speaker1, speaker2) for i, line in enumerate(lines) if line]
        )
        combined_audio = await self.combine_audio_files(audio_files)
        requests_db[request_id]["status"] = PodcastStatus.COMPLETED
        requests_db[request_id]["podcast_path"] = f"http://127.0.0.1:8000/static/{combined_audio}"

@app.post("/generate_podcast/")
async def create_podcast_request(
    background_tasks: BackgroundTasks,
    api_key: str = Form(...),
    input_text: str = Form(...),
    language: str = Form("Auto Detect"),
    speaker1: str = Form("en-US-AndrewMultilingualNeural"),
    speaker2: str = Form("en-US-BrianMultilingualNeural")
):
    request_id = str(uuid.uuid4())
    requests_db[request_id] = {
        "id": request_id,
        "status": PodcastStatus.PENDING,
        "podcast_path": "",
        "error": ""
    }

    podcast_generator = PodcastGenerator(api_key=api_key)

    background_tasks.add_task(podcast_generator.generate_podcast, request_id, input_text, language, speaker1, speaker2)
    return requests_db[request_id]

@app.get("/podcast_status/{request_id}")
async def get_podcast_status(request_id: str):
    if request_id not in requests_db:
        return {"error": "Invalid request ID"}
    return requests_db[request_id]

@app.get("/static/{filename}")
async def get_audio_file(filename: str):
    file_path = f"static/{filename}"
    if not os.path.exists(file_path):
        return {"error": "Arquivo não encontrado."}
    return FileResponse(file_path)

