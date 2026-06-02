FROM python:3.12-slim
WORKDIR /app
COPY streamlit/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY streamlit/app.py .
EXPOSE 8535
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8535/_stcore/health')" || exit 1
CMD ["streamlit", "run", "app.py", "--server.port=8535", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
