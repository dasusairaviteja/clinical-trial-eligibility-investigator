FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt \
    && useradd --uid 10001 --create-home triallens \
    && mkdir /data && chown triallens:triallens /data
COPY clinical_trial ./clinical_trial
COPY web ./web
COPY examples/synthetic_sources.json examples/synthetic_request.json ./examples/
COPY gunicorn.conf.py ./
USER 10001:10001
ENV REVIEW_DATABASE=/data/reviews.db
EXPOSE 8000
CMD ["python", "-m", "gunicorn", "-c", "gunicorn.conf.py", "clinical_trial.wsgi:create_app()"]
