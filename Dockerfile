FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
