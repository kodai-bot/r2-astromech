# R2 Astromech Multi-Architecture Deployment Guide

## 🏗️ Architecture Support

| Platform | Architecture | Status | Notes |
|----------|-------------|--------|-------|
| Development PC | x86_64 | ✅ Active | Primary development environment |
| Raspberry Pi 5 | ARM64/aarch64 | 🎯 Target | Production deployment target |

## 📦 Deployment Strategy

### **Option 1: Dual Development (Recommended)**

**Development Machine (x86_64):**
```bash
# Use standard requirements.txt
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Raspberry Pi (ARM64):**
```bash
# Use ARM64-optimized requirements
python3 -m venv venv-rpi
source venv-rpi/bin/activate
pip install -r requirements-rpi.txt
```

### **Option 2: Docker Multi-Architecture**

Create platform-specific Docker images:

```dockerfile
# Dockerfile.x86_64
FROM python:3.12-slim-bullseye
COPY requirements.txt .
RUN pip install -r requirements.txt

# Dockerfile.arm64
FROM python:3.12-slim-bullseye
COPY requirements-rpi.txt .
RUN pip install -r requirements-rpi.txt
```

## 🔧 Raspberry Pi Setup

### **1. System Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Audio support
sudo apt install -y portaudio19-dev python3-pyaudio

# Bluetooth support  
sudo apt install -y bluetooth bluez libbluetooth-dev libglib2.0-dev

# Network tools
sudo apt install -y nmap

# Development tools
sudo apt install -y git build-essential python3-dev
```

### **2. Python Environment**
```bash
# Clone project
git clone <your-repo> r2-astromech
cd r2-astromech

# Create ARM64-specific venv
python3 -m venv venv-rpi
source venv-rpi/bin/activate

# Install ARM64 requirements
pip install --upgrade pip
pip install -r requirements-rpi.txt
```

### **3. Hardware-Specific Setup**
```bash
# Enable GPIO (if needed)
sudo raspi-config
# -> Interface Options -> GPIO -> Enable

# Enable camera (if needed) 
sudo raspi-config
# -> Interface Options -> Camera -> Enable
```

## 🧪 Testing Strategy

### **Cross-Platform Testing:**

1. **Core Functionality**: Test all modules work on both architectures
2. **Performance**: Benchmark AI models on ARM64 vs x86_64
3. **Hardware Integration**: Test GPIO, audio, camera on Raspberry Pi
4. **Network Discovery**: Verify network scanning works on both platforms

### **Test Commands:**
```bash
# Basic functionality test
python src/main.py --status-only

# Network discovery test
python scan_director.py

# AI model test (if using)
python demo_r2_tinyllm_standalone.py
```

## ⚡ Performance Considerations

### **ARM64 Optimizations:**

1. **PyTorch**: Use official ARM64 wheels (much faster than building from source)
2. **Memory**: Raspberry Pi 5 has 4-8GB RAM - monitor usage
3. **CPU**: ARM Cortex-A76 - optimize for quad-core performance
4. **Storage**: Use fast SD card (UHS-I U3) or SSD for better I/O

### **Model Optimization:**
```python
# Example ARM64 optimizations for AI models
import torch

# Use ARM64-optimized settings
if torch.backends.mkldnn.is_available():
    # Enable MKL-DNN for better ARM performance
    torch.backends.mkldnn.enabled = True

# Reduce model precision if needed
model = model.half()  # Use FP16 instead of FP32
```

## 🚀 Deployment Checklist

### **Development (x86_64):**
- [ ] Virtual environment created (`venv`)
- [ ] Dependencies installed (`requirements.txt`)
- [ ] Core functionality tested
- [ ] Code formatted and linted

### **Raspberry Pi (ARM64):**
- [ ] System dependencies installed
- [ ] Virtual environment created (`venv-rpi`) 
- [ ] ARM64 dependencies installed (`requirements-rpi.txt`)
- [ ] Hardware interfaces tested (audio, network, etc.)
- [ ] Performance benchmarked
- [ ] Production deployment verified

## 🔄 Continuous Integration

Consider setting up GitHub Actions for multi-architecture testing:

```yaml
# .github/workflows/multi-arch.yml
name: Multi-Architecture Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest]
        arch: [x86_64, aarch64]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
```

## 📝 Notes

- **Development**: Keep using x86_64 for fast iteration
- **Testing**: Regularly test on actual Raspberry Pi hardware
- **Performance**: ARM64 may be slower for AI workloads - consider model optimization
- **Dependencies**: Some packages may need different versions on ARM64
- **GPIO**: Hardware-specific features only work on Raspberry Pi

## 🆘 Troubleshooting

**Common ARM64 Issues:**
1. **PyTorch installation**: Use `--find-links` for official wheels
2. **Audio issues**: Ensure ALSA/PulseAudio configured correctly
3. **Permission errors**: Add user to audio/gpio groups
4. **Memory issues**: Monitor RAM usage, consider swap file

**Quick fixes:**
```bash
# Add user to groups
sudo usermod -a -G audio,gpio $USER

# Increase swap if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```
