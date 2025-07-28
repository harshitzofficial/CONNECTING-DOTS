# Adobe "Connecting the Dots" Hackathon Solution
**Intelligent Document Insight Engine for PDF Processing and Analysis**

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-v3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)

## 🏆 Hackathon Overview

This solution is designed for the **Adobe India Hackathon 2025 "Connecting the Dots"** challenge, which transforms static PDFs into intelligent, interactive experiences through advanced AI-powered processing.

### Challenge Objectives
- **Round 1A**: Extract hierarchical document outlines (Title, H1-H3) with page numbers
- **Round 1B**: Perform persona-aware content ranking across multiple PDFs
- **Performance**: Process 50-page PDFs under 10 seconds (1A) and 60 seconds (1B)
- **Constraints**: CPU-only, offline execution, Docker containerized

<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/381b2aa2-a7e6-409d-8a6c-44aa30fd7a6c" />


## 📁 Project Structure

The project follows a clean, hackathon-compliant structure:

<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/f99e6f4c-2b70-4857-80f1-00a860a1cc85" />


```
connecting-dots/
├── main.py                 # Entry point with runtime guards
├── outline.py              # Round 1A outline extraction
├── ranker.py               # Round 1B persona-aware ranking  
├── utils.py                # Utility functions
├── requirements.txt        # Minimal dependencies (<650MB)
├── Dockerfile              # AMD64 CPU-only container
├── docker-compose.yml      # Optional orchestration
├── README.md              # This documentation
├── input/                 # 📂 Place your PDF files here
└── output/                # 📂 JSON results appear here
```

## 🚀 Quick Start Guide

### Step 1: Prerequisites

Before getting started, ensure you have the following installed:

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/002b8cf9-3a60-43a5-8be2-dd544524fb9f" />


**System Requirements:**
- **Docker Desktop** (Version 20.10+)
- **CPU**: AMD64 architecture, ≥4 cores
- **RAM**: ≥8GB (16GB recommended)
- **Disk Space**: ≥2GB free space
- **OS**: Linux, macOS, or Windows 10/11 with WSL2

**For Windows Users:**
- Enable WSL2 and Hyper-V
- Configure Docker Desktop file sharing
- Use PowerShell or Command Prompt

### Step 2: Project Setup

1. **Download/Clone the Project**
   ```bash
   # Download the project files to your local machine
   # Extract to a folder like: C:\hackathon\connecting-dots\ or ~/hackathon/connecting-dots/
   ```

2. **Navigate to Project Directory**
   ```bash
   cd connecting-dots
   ```

3. **Prepare Input PDFs**
   ```bash
   # Place your PDF files in the input/ directory
   # Each PDF must be ≤50 pages
   # Supported formats: .pdf files only
   ```

### Step 3: Build the Docker Image

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/d21783b6-47d7-4c0a-b6bb-578b48a96192" />


```bash
# Build the optimized hackathon-compliant image
docker build --platform linux/amd64 -t connecting-dots .
```

**Expected Build Time:** 2-3 minutes  
**Final Image Size:** ~650MB

### Step 4: Run the Solution

#### Option A: Process All PDFs (Recommended for Hackathon)
```bash
docker run --rm \
  --network none \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  connecting-dots
```

#### Option B: Round 1A Only (Outline Extraction)
```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  connecting-dots --mode 1A
```

#### Option C: Round 1B Only (Persona Ranking)
```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  connecting-dots --mode 1B --persona "Investment Analyst" --job "Analyze revenue trends"
```

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/44fce126-c553-4e15-88b3-beaf7d014981" />


## 📊 Output Formats

### Round 1A Output (filename.json)

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/c266b62a-ef32-4e2b-ba8f-bb041a9ae8e5" />


```json
{
  "title": "Understanding AI in Healthcare",
  "outline": [
    {
      "level": "H1",
      "text": "Introduction to AI",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "Machine Learning Fundamentals",
      "page": 3
    },
    {
      "level": "H3",
      "text": "Neural Networks Overview",
      "page": 5
    }
  ]
}
```

### Round 1B Output (persona_ranking.json)

```json
{
  "metadata": {
    "documents": ["report1.pdf", "report2.pdf"],
    "persona": "Investment Analyst",
    "job": "Analyze revenue trends",
    "processing_time": 45.2
  },
  "extracted_sections": [
    {
      "document": "report1.pdf",
      "page": 12,
      "section_title": "Quarterly Revenue Analysis",
      "importance_rank": 1,
      "relevance_score": 0.95,
      "subsections": [
        {
          "page": 13,
          "refined_text": "Revenue grew 28% YoY, driven by cloud services..."
        }
      ]
    }
  ]
}
```

## ⚡ Performance Specifications

| Metric | Requirement | Achieved |
|--------|-------------|----------|
| **Round 1A Speed** | ≤10 seconds | ~3-8 seconds |
| **Round 1B Speed** | ≤60 seconds | ~25-55 seconds |
| **Image Size** | ≤1GB | ~650MB |
| **Memory Usage** | ≤16GB | <700MB peak |
| **CPU Architecture** | AMD64 only | ✅ Compatible |
| **Network Access** | Offline only | ✅ No external calls |

## 🛠️ Troubleshooting Guide

### Common Issues and Solutions

#### 1. Docker Build Failures
**Error**: `failed to create task for container`
```bash
# Solution: Ensure Docker Desktop is running
docker --version
docker info
```

#### 2. No PDF Files Found
**Error**: `WARNING - No PDF files found in input directory`
```bash
# Solution: Verify PDF placement
ls input/          # Should show your .pdf files
# Ensure files have .pdf extension (case-sensitive)
```

#### 3. Permission Denied (Windows)
**Error**: `Permission denied` when mounting volumes
```bash
# Solution: Enable Docker Desktop file sharing
# Go to Docker Desktop → Settings → Resources → File Sharing
# Add your project directory
```

#### 4. Processing Timeout
**Error**: `Time limit exceeded`
```bash
# Solution: Check PDF complexity and size
# Ensure PDFs are ≤50 pages
# Try processing smaller batches
```

#### 5. Memory Issues
**Error**: `Killed` or container stops unexpectedly
```bash
# Solution: Increase Docker memory allocation
# Docker Desktop → Settings → Resources → Advanced
# Set memory to at least 8GB
```

### Debug Mode

For troubleshooting, run with verbose logging:

```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -e PYTHONUNBUFFERED=1 \
  connecting-dots --mode 1A
```

### Interactive Shell Access

To inspect the container environment:

```bash
docker run -it --rm \
  -v $(pwd)/input:/app/input \
  --entrypoint sh \
  connecting-dots

# Inside container:
ls /app/input     # Check mounted files
python main.py --help  # View available options
```

## 🔧 Advanced Configuration

### Custom Persona Queries

Create custom persona queries for Round 1B:

```bash
# Example: Financial Analyst
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  connecting-dots --mode 1B \
  --persona "Financial Analyst" \
  --job "Extract key performance indicators and financial metrics"

# Example: Research Scientist  
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  connecting-dots --mode 1B \
  --persona "Research Scientist" \
  --job "Identify methodology and experimental results sections"
```

### Performance Tuning

Adjust worker threads for optimal performance:

```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  connecting-dots --max-workers 4  # Default: 8
```

### Docker Compose Usage

For development and testing:

```bash
# Standard processing
docker-compose up document-processor

# With web interface (if implemented)
docker-compose --profile web up
```

## 📈 Technical Architecture

### Core Components

1. **main.py**: Orchestrates the entire pipeline with runtime guards
2. **outline.py**: Implements font-based heading detection algorithms
3. **ranker.py**: Provides semantic similarity ranking using sentence transformers
4. **utils.py**: Handles PDF validation, text processing, and logging

### Algorithm Overview

**Round 1A Process:**
1. Extract text blocks with PyMuPDF
2. Analyze font sizes and styles
3. Identify title using largest font on first page
4. Classify headings based on font ratios and formatting
5. Generate hierarchical outline with page numbers

**Round 1B Process:**
1. Extract sections using Round 1A results
2. Generate text embeddings using MiniLM-L6-v2
3. Calculate persona-query similarity scores
4. Apply ranking weights for level, content type, and recency
5. Return top-ranked sections with refined excerpts

### Dependencies

```python
# Core dependencies (requirements.txt)
PyMuPDF==1.23.26              # PDF processing
sentence-transformers==2.2.2   # Lightweight embeddings  
scikit-learn==1.3.2           # Similarity calculations
numpy==1.24.3                 # Numerical operations
```

## 🎯 Hackathon Compliance Checklist

- ✅ **Repository Structure**: Correct file organization
- ✅ **Docker Build**: `--platform linux/amd64` specification
- ✅ **Auto-Processing**: No manual intervention required
- ✅ **JSON Schema**: Strict field compliance (`title`, `outline`)
- ✅ **Performance Limits**: Hard 10s/60s enforcement with `sys.exit(1)`
- ✅ **Resource Constraints**: <650MB image, <700MB RAM
- ✅ **Network Isolation**: Compatible with `--network none`
- ✅ **Error Handling**: Graceful failure with proper exit codes

## 📝 Development Notes

### Code Quality
- **Type Hints**: Full typing support for better IDE integration
- **Error Handling**: Comprehensive exception management
- **Logging**: Structured logging for debugging and monitoring
- **Testing**: Built-in validation for PDF processing pipeline

### Extensibility
- **Modular Design**: Easy to add new extraction algorithms
- **Configurable**: Adjustable thresholds and parameters
- **Scalable**: Multi-threaded processing support

## 🤝 Contributing

This solution is optimized for the Adobe India Hackathon 2025. For improvements:

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure hackathon compliance
5. Submit a pull request


## 🏅 Acknowledgments

- **Adobe India Hackathon 2025** for the challenge framework
- **PyMuPDF** for excellent PDF processing capabilities  
- **Sentence Transformers** for lightweight embedding models
- **Docker** for containerization platform
