# Use an official Python runtime based on Debian 10 "buster" as a parent image.
FROM python:3.10.8-slim-buster

# Set environment variables.
# Force Python stdout and stderr streams to be unbuffered.
# command.
ENV PYTHONUNBUFFERED=1

# Install the project requirements.
COPY requirements.txt /
RUN pip install -r /requirements.txt

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

# Add user that will be used in the container.
RUN useradd app

# Set this directory to be owned by the "app" user.
RUN chown app:app /app

# Copy the source code of the project into the container.
COPY --chown=app:app . .

# Use user "app" to run the build commands below and the server itself.
USER app

# Runtime command that executes when "docker run" is called, it does the
# following:
#   1. Migrate the database.
#   2. Start the application.
# WARNING:
#   Migrating database at the same time as starting the server IS NOT THE BEST
#   PRACTICE. The database should be migrated manually or using the release
#   phase facilities of your hosting platform. This is used only so the
#   instance can be started with a simple "docker run" command.
# grpc service
# CMD set -xe;cd db; alembic upgrade head; cd ..; python main.py grpc
# telegram polling service
CMD set -xe;cd db; alembic upgrade head; cd ..; python main.py poll
