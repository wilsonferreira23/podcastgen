import streamlit as st
from pydub import AudioSegment
import json
import uuid
import os
import edge_tts
import asyncio
import aiofiles
import pypdf
from groq import Groq  # Usar a biblioteca Groq
from typing import List

class PodcastGenerator:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # Configurando o cliente Groq

    async def generate_script(self, prompt: str, language: str) -> dict:
        system_prompt = f"""
        You are a professional podcast generator. Your task is to generate a professional podcast script based on the user input.
        - The podcast should have 2 speakers.
        - The podcast should be interesting, lively, and engaging.
        - The script must be in JSON format.
        """

        messages = [{"role": "user", "content": prompt}]

        # Fazendo a requisição para a API do Groq
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model="llama3-8b-8192"  # Exemplo de modelo compatível com Groq
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Falha ao gerar o script do podcast: {e}")
            return {}

    async def tts_generate(self, text: str, speaker: int, speaker1: str, speaker2: str) -> str:
        voice = speaker1 if speaker == 1 else speaker2
        speech = edge_tts.Communicate(text, voice)
        
        temp_filename = f"temp_{uuid.uuid4()}.wav"
        try:
            await speech.save(temp_filename)
            return temp_filename
        except Exception as e:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            raise e

    async def combine_audio_files(self, audio_files: List[str]) -> str:
        combined_audio = AudioSegment.empty()
        for audio_file in audio_files:
            combined_audio += AudioSegment.from_file(audio_file)
            os.remove(audio_file)  # Clean up temporary files

        output_filename = f"output_{uuid.uuid4()}.wav"
        combined_audio.export(output_filename, format="wav")
        return output_filename

    def generate_podcast(self, input_text: str, language: str, speaker1: str, speaker2: str) -> str:
        # Transformar as funções assíncronas em chamadas síncronas
        podcast_json = asyncio.run(self.generate_script(input_text, language))
        audio_files = asyncio.run(asyncio.gather(
            *[self.tts_generate(item['line'], item['speaker'], speaker1, speaker2) for item in podcast_json.get('podcast', [])]
        ))
        combined_audio = asyncio.run(self.combine_audio_files(audio_files))
        return combined_audio

class TextExtractor:
    @staticmethod
    async def extract_from_pdf(file_path: str) -> str:
        async with aiofiles.open(file_path, 'rb') as file:
            content = await file.read()
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))
            return "\n\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())

    @staticmethod
    async def extract_from_txt(file_path: str) -> str:
        async with aiofiles.open(file_path, 'r') as file:
            return await file.read()

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() == '.pdf':
            return asyncio.run(cls.extract_from_pdf(file_path))
        elif file_extension.lower() == '.txt':
            return asyncio.run(cls.extract_from_txt(file_path))
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

# Streamlit Interface
st.title("PodcastGen 🎙️ - Usando Groq com Streamlit")

input_text = st.text_area("Texto de Entrada")
input_file = st.file_uploader("Ou faça o upload de um arquivo PDF ou TXT", type=["pdf", "txt"])
language = st.selectbox("Idioma", ["Auto Detect", "English", "French", "German", "Spanish"])
speaker1 = st.selectbox("Voz do Speaker 1", ["Andrew - English (United States)", "Ava - English (United States)"])
speaker2 = st.selectbox("Voz do Speaker 2", ["Brian - English (United States)", "Emma - English (United States)"])

if st.button("Gerar Podcast"):
    st.write("Iniciando a geração do podcast...")
    podcast_generator = PodcastGenerator()

    if input_file:
        file_path = f"/tmp/{input_file.name}"
        with open(file_path, "wb") as f:
            f.write(input_file.getbuffer())
        input_text = TextExtractor.extract_text(file_path)

    if input_text:
        podcast = podcast_generator.generate_podcast(input_text, language, speaker1, speaker2)
        st.audio(podcast)


