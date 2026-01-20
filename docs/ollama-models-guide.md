# Ollama Models Guide

## Overview

AgenticBuilder supports all Ollama models installed on your local machine. The system automatically detects and lists available models from your Ollama server.

## How It Works

1. **Automatic Detection**: When you select "Ollama" as the LLM provider, the system automatically fetches all installed models from your Ollama server
2. **Real-time Updates**: Click the "Refresh" button to update the model list after installing new models
3. **No Configuration Needed**: Models are automatically discovered - no manual configuration required

## Installing Ollama Models

### Popular Models

```bash
# Llama 3.3 (Latest, 70B parameters)
ollama pull llama3.3:70b

# Llama 3.1 (8B - Fast, 70B - Powerful)
ollama pull llama3.1:8b
ollama pull llama3.1:70b

# GPS-OSS (20B - Open-source model)
ollama pull gps-oss:20b

# Qwen 2.5 (Multilingual)
ollama pull qwen2.5:72b

# DeepSeek R1 (Advanced reasoning)
ollama pull deepseek-r1:70b

# Mixtral (Mixture of Experts)
ollama pull mixtral:8x7b

# Mistral (Fast and efficient)
ollama pull mistral:7b

# CodeLlama (Code generation)
ollama pull codellama:13b

# Phi-3 (Small but capable)
ollama pull phi3:3.8b
```

### Checking Installed Models

```bash
# List all installed models
ollama list

# Example output:
# NAME                    ID              SIZE    MODIFIED
# llama3.3:70b           abc123def       40 GB   2 hours ago
# llama3.1:8b            def456ghi       4.7 GB  1 day ago
# mistral:7b             ghi789jkl       4.1 GB  3 days ago
```

## Using Models in AgenticBuilder

### 1. In Agent Configuration

1. Open Agent Builder
2. Create or edit an agent
3. Select "Ollama" as the LLM Provider
4. Click "Refresh" to load models
5. Select your desired model from the dropdown

### 2. In Workflow Editor

1. Add an "AI Agent" block to your workflow
2. In the properties panel, select "Ollama" as provider
3. Choose from the list of installed models
4. Configure temperature and other parameters

### 3. In LLM Settings

1. Go to Settings → LLM
2. Enable Ollama
3. Set Ollama Base URL (default: http://localhost:11434)
4. Click "Test Connection" to verify
5. View all available models

## Model Selection Tips

### By Use Case

**General Purpose:**
- `llama3.3:70b` - Best overall performance
- `llama3.1:8b` - Fast responses, good quality
- `gps-oss:20b` - Open-source alternative

**Code Generation:**
- `codellama:13b` - Specialized for code
- `deepseek-r1:70b` - Advanced reasoning for complex code

**Multilingual:**
- `qwen2.5:72b` - Excellent for non-English languages

**Fast & Efficient:**
- `llama3.1:8b` - Small model, quick responses
- `phi3:3.8b` - Very small, very fast
- `mistral:7b` - Good balance of speed and quality

**Complex Reasoning:**
- `deepseek-r1:70b` - Advanced reasoning capabilities
- `mixtral:8x7b` - Mixture of experts architecture

### By Hardware

**High-end GPU (24GB+ VRAM):**
- 70B models (llama3.3:70b, qwen2.5:72b)

**Mid-range GPU (12-16GB VRAM):**
- 20B models (gps-oss:20b)
- 13B models (codellama:13b)
- 8B models (llama3.1:8b, mixtral:8x7b)

**CPU or Low VRAM:**
- 7B models (mistral:7b)
- 3-4B models (phi3:3.8b)

## Troubleshooting

### Models Not Showing Up

1. **Check Ollama is Running:**
   ```bash
   ollama list
   ```

2. **Verify Ollama URL:**
   - Default: http://localhost:11434
   - Check in Settings → LLM → Ollama Base URL

3. **Click Refresh:**
   - In Agent Config, click the "Refresh" button next to Model dropdown

4. **Check Browser Console:**
   - Open Developer Tools (F12)
   - Look for connection errors

### Connection Errors

**Error: "Cannot connect to Ollama"**
- Ensure Ollama is running: `ollama serve`
- Check firewall settings
- Verify URL is correct

**Error: "No models installed"**
- Install at least one model: `ollama pull llama3.1:8b`
- Run `ollama list` to verify installation

### Performance Issues

**Model Loading Slowly:**
- First load takes time (model loads into memory)
- Subsequent requests are faster
- Consider using smaller models for faster responses

**Out of Memory:**
- Use smaller models (8B or 7B instead of 70B)
- Close other applications
- Check available RAM/VRAM

## Advanced Configuration

### Custom Ollama Server

If running Ollama on a different machine or port:

1. Go to Settings → LLM
2. Update "Ollama Base URL"
3. Example: `http://192.168.1.100:11434`
4. Click "Test Connection"

### Model Parameters

When configuring an agent, you can adjust:

- **Temperature** (0.0 - 1.0): Controls randomness
  - 0.0: Deterministic, focused
  - 0.7: Balanced (default)
  - 1.0: Creative, diverse

- **Max Tokens**: Maximum response length
  - 1000: Short responses
  - 2000: Medium responses (default)
  - 4000+: Long, detailed responses

- **System Prompt**: Instructions for the model
  - Define role and behavior
  - Set output format
  - Provide context

## Best Practices

1. **Start Small**: Begin with 8B models, upgrade if needed
2. **Test First**: Use "Test Connection" in LLM Settings
3. **Keep Updated**: Regularly update Ollama and models
4. **Monitor Resources**: Watch RAM/VRAM usage
5. **Use Refresh**: Click refresh after installing new models

## Model Recommendations

### For Development
- `llama3.1:8b` - Fast iteration, good quality

### For Production
- `llama3.3:70b` - Best quality, slower
- `qwen2.5:72b` - Multilingual support

### For Experimentation
- `phi3:3.8b` - Quick tests, low resource
- `mistral:7b` - Good baseline

## Resources

- **Ollama Website**: https://ollama.ai
- **Model Library**: https://ollama.ai/library
- **GitHub**: https://github.com/ollama/ollama
- **Documentation**: https://github.com/ollama/ollama/blob/main/docs/README.md

---

**Last Updated**: 2026-01-20
