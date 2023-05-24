FROM python:3.10-slim-buster

# Set environment variables.
# Force Python stdout and stderr streams to be unbuffered.
# command.
ENV PYTHONUNBUFFERED=1

# Use /project folder as a directory where the source code is stored.
WORKDIR /project

## Install the project requirements ##
# using poetry
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install poetry
COPY pyproject.toml poetry.lock .
RUN poetry config virtualenvs.create false
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --without local --no-root
# or using pip
# COPY requirements.txt .
# RUN --mount=type=cache,target=/root/.cache/pip \
#      pip install -r requirements.txt

# Add user that will be used in the container.
RUN useradd app

# Set this directory to be owned by the "app" user.
RUN chown app:app /project

# Copy the source code of the project into the container.
COPY --chown=app:app . .

# grpc service
# CMD python main.py grpc
# telegram polling service
CMD ["python", "main.py", "poll"]
