# Use uma imagem base do Python
FROM python:3.11-slim

# Instale o FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Crie um diretório de trabalho
WORKDIR /app

# Copie o conteúdo do projeto para o diretório de trabalho
COPY . /app

# Crie a pasta static para armazenar arquivos (não gere erro se já existir)
RUN mkdir -p /app/static

# Instale as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta em que a API irá rodar
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
