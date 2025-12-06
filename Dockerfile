FROM golang:1.23-bookworm AS builder
WORKDIR /app
COPY go.mod ./
COPY main.go ./
RUN go build -o nfty-say .

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    pulseaudio-utils \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install piper
RUN wget -qO- https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz \
    | tar xz -C /usr/local/bin --strip-components=1

# Download voice model
RUN mkdir -p /models && \
    wget -q -O /models/en_US-amy-medium.onnx \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx" && \
    wget -q -O /models/en_US-amy-medium.onnx.json \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

COPY --from=builder /app/nfty-say /usr/local/bin/
COPY say.sh /usr/local/bin/say.sh
RUN chmod +x /usr/local/bin/say.sh

ENV NFTY_SAY=/usr/local/bin/say.sh
CMD ["nfty-say"]
