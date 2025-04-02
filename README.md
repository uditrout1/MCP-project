# AI Legacy Application Modernization - README

## Overview

This project is a Proof of Concept (PoC) for an AI-powered legacy application modernization system. It enables users to interact with legacy applications and APIs using natural language, crawl web applications for data extraction and enrichment, and provides a modern interface for these interactions.

## Key Features

- **Natural Language API Access**: Interact with APIs using conversational language
- **Message Control Protocol (MCP)**: Standardized communication between components
- **Flexible API Connectors**: Support for various API types and authentication methods
- **Web Crawling**: Extract and enrich data from web applications
- **Modern Frontend**: User-friendly interface for all interactions

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- venv (Python virtual environment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-legacy-modernization.git
   cd ai-legacy-modernization
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Access the application:
   Open your browser and navigate to `http://localhost:5000`

## Documentation

Comprehensive documentation is available in the `docs` directory:

- [System Documentation](docs/documentation.md): Detailed information about the system architecture, components, and usage
- [Deployment Guide](docs/deployment.md): Instructions for deploying the system in various environments
- [SaaS Expansion Strategy](docs/saas_strategy.md): Strategy for expanding the PoC into a full SaaS product

## Project Structure

```
ai-legacy-modernization/
├── src/
│   ├── mcp/              # Message Control Protocol
│   ├── api/              # API Integration Layer
│   ├── llm/              # LLM Interface
│   ├── crawler/          # Web Crawler
│   └── frontend/         # Frontend Interface
├── tests/                # Test scripts
├── docs/                 # Documentation
├── examples/             # Example scripts
├── app.py                # Main application
├── requirements.txt      # Dependencies
└── README.md             # Project overview
```

## Testing

To run all tests:
```bash
python run_tests.py
```

To run specific tests:
```bash
python tests/unit_test.py
python tests/integration_test.py
python tests/e2e_test.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for providing the LLM capabilities
- Various open-source libraries used in this project
- All contributors who have helped with the development

## Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com).# ai-legacy-modernization
