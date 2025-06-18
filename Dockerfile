SHELL ["/bin/bash", "-o", "pipefail", "-c"]

FROM python:3.9-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
      libev-dev python3-dev \
      && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN rm -f config.py && mv config.py.default config.py

# ---- Python deps ----
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir --only-binary=:all: bjoern==3.2.2 \
 && pip install --no-cache-dir -r <(grep -v "^bjoern" requirements.txt)

EXPOSE 5000
CMD ["bjoern", "run:app", "0.0.0.0", "5000"]

