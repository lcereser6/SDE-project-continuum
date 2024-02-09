FROM python:3.8-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir pipreqs 
RUN python -m  pipreqs.pipreqs . --force
RUN pip install --no-cache-dir -r requirements.txt
RUN ls -la /app  # This will list the contents of /app

CMD ["python", "orchestrator.py"]
