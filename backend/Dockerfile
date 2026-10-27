# Imagem do backend do Terra. A mesma imagem roda a API (uvicorn), o worker e o beat (Celery) e a migração
# (alembic): o docker-compose.prod.yml só troca o comando e as credenciais de cada um.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=America/Cuiaba

# tzdata: o Celery e os logs usam o fuso de Cuiabá
RUN apt-get update \
    && apt-get install --no-install-recommends -y tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/terra/backend

# As dependências primeiro, lidas do pyproject: esta camada fica em cache enquanto elas não mudam.
COPY pyproject.toml ./
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']))" \
        > /tmp/dependencias.txt \
    && pip install -r /tmp/dependencias.txt

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
RUN pip install --no-deps .

# Sem root dentro do container.
RUN useradd --create-home --uid 1000 terra
USER terra

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
