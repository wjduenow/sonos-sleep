FROM python:3.9-slim-bullseye

# Tell every subsequent RUN to use Bash (so <( … ) works)
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libev-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN rm -f config.py && mv config.py.default config.py

# ---- Python deps ----
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
#CMD ["bjoern", "run:app", "0.0.0.0", "5000"]
CMD ["python", "run.py", "--host", "0.0.0.0"]

