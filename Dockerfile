FROM python:3.9-slim

#creat working folder nad install dependencies
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

#copy the application contents
COPY service/ ./service/

#switch to non root user and tranfer ownership of working directory
RUN useradd --uid 1000 theia && chown -R theia /app
USER theia

#Run service
EXPOSE 8000

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]