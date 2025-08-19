# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is NAIA v2, a Django REST API backend for an AI assistant system. The project is structured as a modular Django application with multiple specialized apps for different AI functionalities including chat, research, mental health, government services, university guidance, and more.

## Architecture

### Core Structure
- **Django Project**: `naia/` - Main Django project configuration
- **Apps Directory**: `apps/` - Contains modular Django apps for different AI services
- **API Layer**: `api/v1/` - REST API endpoints organized by functionality
- **Services Layer**: `services/` - Shared services including LLM integration and file handling
- **Vector Databases**: `chromadb_*` directories for different knowledge bases

### Key Apps
- `chat` - Core chat functionality and message handling
- `users` - User management and authentication
- `researcher` - Research and document analysis capabilities
- `mental` - Mental health screening and support
- `gobernacion` - Government services integration
- `uniguide` - University guidance system
- `skills` - Skills assessment and development
- `personal` - Personal assistant features
- `recepcionist` - Reception/front-desk automation

### Service Architecture
Each app follows a consistent pattern:
- `models.py` - Data models
- `services.py` - Business logic and external integrations
- `functions.py` - Specialized utility functions
- `repositories.py` - Data access layer (where present)
- `views.py` - API endpoint handlers
- `serializers.py` - Data serialization (where present)

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Load environment variables from .env file
# The project uses python-dotenv for environment management
```

### Django Management
```bash
# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Code Quality
```bash
# Linting (from README.md)
flake8 . --select=F401,E722 --exclude=.git,__pycache__,*/migrations/*,venv,env,deploy_server.py

# Clean requirements.txt
python clean.py
```

### Testing
```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test apps.chat
```

## Key Technologies

- **Framework**: Django 5.1.5 with Django REST Framework
- **Database**: MySQL (using PyMySQL connector)
- **AI/LLM**: OpenAI GPT models via services/llm.py
- **Vector Database**: ChromaDB for different knowledge domains
- **Authentication**: JWT tokens via djangorestframework-simplejwt
- **Documentation**: drf-spectacular for API docs
- **Background Tasks**: Redis integration available
- **Web Scraping**: Selenium and BeautifulSoup4
- **File Processing**: PDF handling, image processing

## Configuration

### Settings Structure
- `naia/settings/base.py` - Base configuration
- `naia/settings/dev.py` - Development settings  
- `naia/settings/prod.py` - Production settings
- Environment determined by `DJANGO_SETTINGS_MODULE_PATH` env var

### Key Environment Variables
- Database connection settings
- OpenAI API key (`open_ai`)
- Email configuration (SMTP)
- Django secret key and debug settings

## LLM Integration

The `services/llm.py` contains the `LLMService` class that handles:
- OpenAI client management with singleton pattern
- Multiple model tiers (nano, mini, standard)
- Message processing with image support
- Tool/function calling capabilities
- Conversation state management

## Vector Databases

ChromaDB instances for different domains:
- `chromadb_recepcionist` - Reception knowledge base
- `chromadb_uniguide` - University guidance content
- `chromadb_user/[user_id]/` - User-specific knowledge bases

## Data Models

Key relationships:
- Users have roles that determine available functionalities
- Chats link users, roles, and message history (JSON field)
- Each specialized app has domain-specific models
- Consistent created_at/updated_at timestamps across models

## API Design

RESTful endpoints under `/api/v1/` with app-specific routing:
- `/api/v1/chat/` - Chat management
- `/api/v1/users/` - User operations  
- `/api/v1/researcher/` - Research functionality
- `/api/v1/mental/` - Mental health features
- And more for each specialized app

## Development Notes

- The project uses function-based and class-based views depending on the app
- JSON fields store complex conversation and configuration data
- Image processing capabilities for chat interactions
- Extensive use of environment variables for configuration
- Custom middleware available in apps/users/middleware.py
- Signal handlers for automated processing in apps/users/signals.py