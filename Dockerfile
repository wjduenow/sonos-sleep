FROM python:3.6-alpine
COPY . /app
WORKDIR /app
RUN rm -f config.py
RUN mv config.py.default config.py

# Port to expose
EXPOSE 5000

RUN pip install -r requirements.txt
CMD ["python", "run.py", "--host", "0.0.0.0"]

