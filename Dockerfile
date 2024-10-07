# Build stage
FROM python:3.9-slim-bullseye AS builder

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.4.2

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libtool \
    autoconf \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install "poetry==$POETRY_VERSION"

# Build mp4v2
RUN git clone https://github.com/mp4v2/mp4v2.git ~/mp4v2 && \
    cd ~/mp4v2 && \
    autoreconf -i && \
    ./configure && \
    make CXXFLAGS='-fpermissive -Wno-error=narrowing' && \
    make install

# Set the working directory
WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY README.md poetry.lock pyproject.toml ./

# Install project dependencies
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true

# Copy the project files into the container
COPY . .

# Install the project and its dependencies
RUN poetry install --no-interaction --no-ansi --no-dev

# Activate the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Final stage
FROM python:3.9-slim-bullseye

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    OPENAI_API_KEY="" \
    LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmp3lame0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy built artifacts from builder stage
COPY --from=builder /usr/local/lib/libmp4v2.so* /usr/local/lib/
COPY --from=builder /usr/local/bin/mp4* /usr/local/bin/
COPY --from=builder /app /app

# Run ldconfig to update shared library cache
RUN ldconfig

# Set up the Python environment
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Run the CLI when the container launches
ENTRYPOINT ["/app/.venv/bin/python", "-m", "speedread.speedread_cli"]

# Set the default command to print usage information
CMD ["--help"]
