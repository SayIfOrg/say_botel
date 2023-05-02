FROM python:3.10-slim-buster

# Cache potential requirements
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry

# Set environment variables.
# Force Python stdout and stderr streams to be unbuffered.
# command.
ENV PYTHONUNBUFFERED=1

# Use /project folder as a directory where the source code is stored.
WORKDIR /project

## Install the project requirements ##
# local dependencies are the ones installed with the `-e` flag of pip install
# so install them in entry point where we can bind volumes
# using poetry
RUN pip install poetry
COPY pyproject.toml poetry.lock .
RUN poetry config virtualenvs.create false && poetry install --without local --no-root
# or using pip
# COPY requirements.txt requirements_local.txt .
# RUN pip install -r requirements.txt

# Add user that will be used in the container.
RUN useradd app

# Set this directory to be owned by the "app" user.
RUN chown app:app /project

# Copy the source code of the project into the container.
COPY --chown=app:app . .

# if using pip instead of poetry then replace
# `poetry install --only local` with `pip install -r requirements_local.txt`
# grpc service
# CMD poetry install --only local; python main.py grpc
# telegram polling service
CMD poetry install --only local && python main.py poll
