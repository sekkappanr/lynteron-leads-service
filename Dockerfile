FROM python:3.12-slim AS base
WORKDIR /app

# Shared library is provided as a named build context ("shared-lib") because it
# lives in its own nested git repository; BuildKit excludes nested-repo paths
# from a directory build context, so it cannot be COPYed from the main context.
COPY --from=shared-lib src/ /tmp/shared-lib/src/
COPY --from=shared-lib pyproject.toml /tmp/shared-lib/
RUN pip install --no-cache-dir "/tmp/shared-lib[events]" && rm -rf /tmp/shared-lib

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app /app/app
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
