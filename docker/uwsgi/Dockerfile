ARG PYTHON_VERSION=3.9
############################################################
# JS build
FROM node:14 AS js_build
WORKDIR /app

RUN adduser --home /app --disabled-password --gecos 'webwhois' webwhois

COPY webwhois/static/ /app/webwhois/static/
COPY assets/ /app/assets/
COPY package.json package-lock.json *.js /app/

RUN npm install -g npm@latest
RUN npm clean-install \
    && npm run build

############################################################
# Base image
FROM python:${PYTHON_VERSION}-slim AS base
WORKDIR /app

RUN adduser --home /app --disabled-password --gecos 'webwhois' webwhois

############################################################
# Build image
FROM base AS build
ARG PIP_INDEX_URL=https://pypi.nic.cz/cznic/public
ENV SKIP_NPM=1

# Install build dependencies from debian
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and use virtualenv
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy source code
COPY . /app/src
COPY --from=js_build /app/webwhois/static/ /app/webwhois/static/

# Install application and other dependencies
WORKDIR /app/src
RUN pip install --no-cache-dir \
        . \
        python-environ \
        sentry-sdk \
        # Install uwsgi for the python version in use.
        uwsgi

############################################################
# Uwsgi image
FROM base AS uwsgi

ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="/app/uwsgi"
ENV DJANGO_SETTINGS_MODULE="webwhois_settings"

# Install runtime dependencies
RUN apt-get --yes update \
    && apt-get install --yes --no-install-recommends \
        libomniorb4-2 \
        libxml2 \
    && rm -rf /var/lib/apt/lists/* \
    # Create static directory
    && mkdir -p /var/www/static \
    && chown webwhois:webwhois /var/www/static

# Copy the virtualenv
COPY --from=build /app/venv/ /app/venv/
# Copy the uwsgi configuration
COPY docker/uwsgi /app/uwsgi/

# Switch user
USER webwhois:webwhois

VOLUME /var/www/static
EXPOSE 16000

ENTRYPOINT ["/app/uwsgi/docker-entrypoint.sh"]
CMD ["uwsgi", "--ini", "/app/uwsgi/uwsgi.ini"]
