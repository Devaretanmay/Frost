#!/bin/bash
set -e

echo "Installing Harada Execution OS..."

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

if [ "$ARCH" = "x86_64" ]; then
    ARCH="x86_64"
elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    ARCH="arm64"
else
    echo "Unsupported architecture: $ARCH"
    exit 1
fi

if [ "$OS" = "darwin" ]; then
    TARGET="macos-$ARCH"
elif [ "$OS" = "linux" ]; then
    if [ "$ARCH" = "arm64" ]; then
        echo "Linux ARM64 binaries are not yet available via this script. Please build from source."
        exit 1
    fi
    TARGET="linux-$ARCH"
else
    echo "Unsupported OS: $OS"
    exit 1
fi

URL="https://github.com/example/harada/releases/latest/download/harada-$TARGET"

echo "Downloading from $URL..."
curl -sSL "$URL" -o harada
chmod +x harada

echo "Installing to /usr/local/bin (may require sudo)..."
sudo mv harada /usr/local/bin/harada

echo "Harada installed successfully!"
harada --version
