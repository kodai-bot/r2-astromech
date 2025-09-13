# R2 Astromech AI Module

This module provides AI functionality for the R2 astromech droid, including natural language processing, R2-style communication translation, and context-aware responses using the Microsoft Phi-3 model.

## Features

- **Multi-Model Support**: Extensible architecture supporting different AI models
- **Phi-3 Integration**: Microsoft Phi-3 model for natural language understanding
- **R2 Translation**: Bidirectional translation between human language and R2 sounds
- **Context Awareness**: Conversation history and context-sensitive responses
- **Emotion Analysis**: Emotional content analysis for appropriate R2 responses
- **Configurable**: Comprehensive YAML-based configuration system

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test the System

```bash
python test_ai_system.py
```

### 3. Basic Usage

```python
from src.ai import ModelManager, R2Translator

# Initialize the AI system
manager = ModelManager()
translator = R2Translator(manager)

# Load the Phi-3 model (first time will download ~2GB)
manager.load_model('phi-3')

# Translate human text to R2 sounds
r2_response = translator.translate_to_r2("Hello R2, how are you?")
print(f"R2 says: {r2_response}")

# Generate contextual responses
r2_sounds, interpretation = translator.generate_contextual_response("Can you help me?")
print(f"R2: {r2_sounds}")
print(f"Meaning: {interpretation}")
```

## Module Structure

```
src/ai/
├── __init__.py              # Module exports
├── model_manager.py         # AI model management
├── translator.py            # R2 communication translation
├── models/
│   ├── __init__.py         # Model exports
│   ├── base_model.py       # Abstract base model interface
│   └── phi3_model.py       # Phi-3 model implementation
└── README.md               # This file
```

## Configuration

The AI system is configured via `config/ai_config.yaml`. Key settings include:

### Model Configuration
```yaml
models:
  phi-3:
    model_path: "microsoft/Phi-3-mini-4k-instruct"
    device: "auto"  # auto, cuda, or cpu
    max_length: 512
    temperature: 0.7
    personality_mode: "helpful"
```

### Translation Settings
```yaml
translation:
  use_context: true
  context_window: 10
  emotion_analysis: true
  personality:
    base_mood: "curious"
    expressiveness: "medium"
```

## API Reference

### ModelManager

The `ModelManager` class handles loading and managing AI models:

```python
manager = ModelManager()

# Load a model
success = manager.load_model('phi-3')

# Generate responses
response = manager.generate_response("Hello R2")

# Check status
status = manager.get_model_status()

# Switch models
manager.switch_model('another-model')
```

### R2Translator

The `R2Translator` class handles communication translation:

```python
translator = R2Translator(model_manager)

# Human to R2 translation
r2_sounds = translator.translate_to_r2("I'm excited!")
# Output: "excited-chirp-beep!"

# R2 to human translation
meaning = translator.translate_from_r2("confused-warble?")
# Output: "R2 appears confused and is asking for clarification."

# Contextual responses
r2_sounds, interpretation = translator.generate_contextual_response("Thanks!")
```

### BaseAIModel

Abstract interface for implementing new AI models:

```python
class CustomModel(BaseAIModel):
    def load_model(self) -> bool:
        # Load your model
        pass
    
    def generate_response(self, input_text: str, **kwargs) -> str:
        # Generate response
        pass
    
    def translate_to_r2(self, human_text: str) -> str:
        # Translate to R2 sounds
        pass
    
    def translate_from_r2(self, r2_sounds: str) -> str:
        # Interpret R2 sounds
        pass
```

## R2 Sound System

### Available Emotions
- `happy`: chirp-beep, trill-whistle, ascending-whistle
- `excited`: rapid-beeps, triumphant-trill, chirp-chirp-beep!
- `sad`: descending-warble, low-boop, mournful-whistle
- `confused`: questioning-chirp?, warble-beep?, tilted-whistle?
- `angry`: harsh-beep!, angry-buzz!, sharp-warble!
- `thinking`: processing-hum..., contemplative-warble...

### Sound Patterns
- **Basic**: beep, boop, whistle, warble, chirp, trill
- **Complex**: ascending-whistle, descending-warble, rapid-beeps
- **Special**: error-buzz, processing-hum, startup-ascend

## Performance Considerations

### Model Loading
- First-time model loading downloads ~2GB (Phi-3-mini)
- Subsequent loads are faster (cached locally)
- GPU acceleration automatically detected and used

### Memory Usage
- Phi-3-mini: ~4GB GPU memory or ~8GB system RAM
- Conversation history limited to 50 entries
- Models can be unloaded to free memory

### Optimization Options
```yaml
performance:
  enable_quantization: true    # Reduce memory usage
  mixed_precision: true        # Faster inference
  batch_size: 1               # Adjust for throughput
```

## Troubleshooting

### Common Issues

1. **Model won't load**
   - Check internet connection (first download)
   - Verify sufficient memory (4GB+ GPU or 8GB+ RAM)
   - Try CPU device if GPU fails

2. **Slow responses**
   - Enable quantization in config
   - Use GPU if available
   - Reduce max_length parameter

3. **Import errors**
   - Install missing dependencies: `pip install -r requirements.txt`
   - Check Python path includes project root

### Debug Mode
Enable debug mode in configuration:
```yaml
advanced:
  debug_mode: true
```

## Adding New Models

1. Create a new model class inheriting from `BaseAIModel`
2. Implement required methods
3. Register with ModelManager:
   ```python
   manager.register_model('my-model', MyModelClass)
   ```
4. Add configuration to `ai_config.yaml`

## Integration Examples

### With Discovery System
```python
from src.ai import ModelManager, R2Translator
from src.discovery import NetworkScanner

# Initialize components
ai_manager = ModelManager()
translator = R2Translator(ai_manager)
scanner = NetworkScanner()

# Scan for devices and announce findings
devices = scanner.scan_network()
announcement = f"Found {len(devices)} devices on network"
r2_response = translator.translate_to_r2(announcement)
```

### With Personality System
```python
from src.ai import R2Translator
from src.personality import R2Sounds

translator = R2Translator()
sounds = R2Sounds()

# Generate and play R2 response
r2_sounds = translator.translate_to_r2("Mission accomplished!")
sounds.play_sound_sequence(r2_sounds)
```

## License

Part of the R2 Astromech project. See project LICENSE for details.
