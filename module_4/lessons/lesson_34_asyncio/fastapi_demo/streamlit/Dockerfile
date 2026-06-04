FROM python:3.12-slim

WORKDIR /app

# requirements.txt знаходиться у streamlit/ всередині build context
COPY streamlit/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# streamlit_demo.py знаходиться у корені build context (fastapi_demo/)
COPY streamlit_demo.py .

EXPOSE 8534

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8534/_stcore/health')" || exit 1

CMD ["streamlit", "run", "streamlit_demo.py", \
     "--server.port=8534", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
