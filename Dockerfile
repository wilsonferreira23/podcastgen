# Dockerfile

# Use a imagem Python
FROM python:3.11-slim

# Instale o ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Defina o diretório de trabalho
WORKDIR /app

# Copie todos os arquivos do diretório atual para o contêiner
COPY . /app

# Crie o diretório /app/static, se não existir
RUN mkdir -p /app/static

# Instale as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta 8000
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]


