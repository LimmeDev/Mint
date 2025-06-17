# Mint AI Framework

A modern AI assistant framework built with Python, PyTorch, and Transformers.

## Features

- State-of-the-art language model integration
- API server for easy deployment
- Customizable response generation
- Extensible architecture for adding new capabilities

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mint.git
cd mint

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# For development dependencies
pip install -e ".[dev]"
```

## Usage

```python
from mint import Assistant

# Initialize the assistant
assistant = Assistant()

# Generate a response
response = assistant.generate("Tell me about artificial intelligence.")
print(response)
```

## API Server

Start the API server:

```bash
python -m mint.server
```

The API will be available at http://localhost:8000

## Configuration

Create a `.env` file in the root directory with the following variables:

```
MODEL_PATH=path/to/your/model
API_KEY=your_api_key
```

## Development

Run tests:

```bash
pytest
```

Format code:

```bash
black mint tests
isort mint tests
```

## License

MIT 