FROM python:3.12.14-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_DATABASE_URL=sqlite:////workspace/data/app.db

WORKDIR /workspace

COPY environment/repo/requirements.lock.txt /tmp/requirements.lock.txt
RUN pip install --no-cache-dir -r /tmp/requirements.lock.txt \
    && useradd --create-home --uid 10001 agent \
    && mkdir -p /workspace/data /grader

COPY environment/repo/ /workspace/
COPY tests/verifier/ /grader/

RUN chown -R agent:agent /workspace \
    && chown -R root:root /grader \
    && chmod -R a-w /grader \
    && chmod -R a+rX /grader

USER agent

CMD ["python", "/grader/verify.py", "--target", "/workspace"]
