#!/bin/bash
# R2 Astromech - Raspberry Pi ARM64 Setup Script
# Run this script on your Raspberry Pi to set up the environment

set -e  # Exit on any error

echo "🤖 R2 Astromech - Raspberry Pi ARM64 Setup"
echo "=========================================="

# Check if running on ARM64
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" ]]; then
    echo "⚠️  Warning: This script is designed for ARM64 (aarch64) architecture"
    echo "   Current architecture: $ARCH"
    echo "   Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

echo "📋 Detected architecture: $ARCH"
echo ""

# Update system
echo "🔄 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y \
    portaudio19-dev \
    python3-pyaudio \
    bluetooth \
    bluez \
    libbluetooth-dev \
    libglib2.0-dev \
    nmap \
    git \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    alsa-utils \
    pulseaudio

echo "✅ System dependencies installed"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ -d "venv-rpi" ]; then
    echo "📁 Removing existing venv-rpi..."
    rm -rf venv-rpi
fi

python3 -m venv venv-rpi
source venv-rpi/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "🔧 Installing Python dependencies for ARM64..."
if [ -f "requirements-rpi.txt" ]; then
    pip install -r requirements-rpi.txt
else
    echo "❌ requirements-rpi.txt not found"
    echo "   Make sure you're running this from the project root directory"
    exit 1
fi

# Set up user permissions
echo "👤 Setting up user permissions..."
sudo usermod -a -G audio,gpio $USER

# Configure audio (basic setup)
echo "🔊 Configuring audio..."
# Enable audio
sudo systemctl enable alsa-state
sudo systemctl start alsa-state

# Test audio configuration
echo "🧪 Testing audio configuration..."
if command -v speaker-test >/dev/null 2>&1; then
    echo "   Run 'speaker-test -t sine -f 1000 -l 1' to test audio"
else
    echo "   speaker-test not available, install alsa-utils for audio testing"
fi

# Enable services
echo "🔧 Configuring services..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Check if GPIO is available
if [ -d "/sys/class/gpio" ]; then
    echo "✅ GPIO interface available"
else
    echo "⚠️  GPIO interface not found - check if enabled in raspi-config"
fi

# Create activation script
echo "📝 Creating activation script..."
cat > activate_rpi.sh << 'EOF'
#!/bin/bash
# R2 Astromech - Raspberry Pi Environment Activation

echo "🤖 R2 Astromech - Raspberry Pi ARM64 Environment"
echo "==============================================="

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv-rpi" ]; then
    source venv-rpi/bin/activate
    echo "✅ ARM64 virtual environment activated"
    echo "Python: $(python --version)"
    echo "Architecture: $(uname -m)"
    echo "Location: $(which python)"
    echo ""
    echo "🚀 Ready to run R2 systems on Raspberry Pi!"
    echo ""
    echo "Try running:"
    echo "  python src/main.py --status-only"
    echo "  python scan_director.py"
    echo ""
else
    echo "❌ Virtual environment not found. Run setup_rpi.sh first."
    exit 1
fi

# Start a new shell with the venv activated
exec bash
EOF

chmod +x activate_rpi.sh

# Performance check
echo "⚡ Checking system performance..."
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo "CPU: $(nproc) cores"
echo "Storage: $(df -h / | tail -1 | awk '{print $4}') available"

# Final instructions
echo ""
echo "🎉 Raspberry Pi setup complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Reboot to ensure all group permissions take effect:"
echo "   sudo reboot"
echo ""
echo "2. After reboot, activate the environment:"
echo "   ./activate_rpi.sh"
echo ""
echo "3. Test the system:"
echo "   python src/main.py --status-only"
echo ""
echo "4. For audio testing:"
echo "   speaker-test -t sine -f 1000 -l 1"
echo ""
echo "5. For GPIO access (if needed):"
echo "   sudo raspi-config -> Interface Options -> GPIO -> Enable"
echo ""
echo "📚 See docs/RASPBERRY_PI.md for detailed information"

deactivate 2>/dev/null || true
