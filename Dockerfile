FROM python:3.9-slim-bullseye

# Tell every subsequent RUN to use Bash (so <( … ) works)
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN rm -f config.py && mv config.py.default config.py

# ---- Python deps ----
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
#CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "run:app"]

