# LLM App with GenUI

A full-stack application combining a Next.js frontend with a FastAPI backend, featuring LangChain multi-agent orchestration and PostgreSQL database integration.

## 📋 Prerequisites

Before setting up the application, ensure you have the following installed:

- **Node.js** (v18 or higher)
- **npm** package manager
- **Python** (3.9 or higher)
- **Poetry** (Python dependency manager)
- **PostgreSQL** (v12 or higher)

## 🚀 Quick Setup Guide

### 1. Clone the Repository

```bash
git clone <repository-url>
cd llm-app-with-genui
```

### 2. Database Setup

#### Create PostgreSQL Database
1. Install PostgreSQL and start the service
2. Create a new database for the application:
```sql
CREATE DATABASE your_database_name;
```

#### Set up Database Schemas
The application uses two schemas:
- `chat_sessions` - for application data
- `langgraph` - for LangChain checkpointing

The schemas will be created automatically when running migrations.

### 3. Server Setup

#### Install Dependencies
```bash
cd server
poetry install
```

#### Environment Configuration
1. Copy the example environment file's content.
2. Change env variables with yours:
```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Database Configuration
PSQL_USERNAME=your_postgres_username
PSQL_PASSWORD=your_postgres_password
PSQL_HOST=localhost
PSQL_PORT=5432
PSQL_DATABASE=your_database_name
PSQL_SSLMODE=disable
```

#### Run Database Migrations
```bash
poetry run alembic upgrade head
```

#### Start the Server
```bash
poetry run start
```

The server will start at `http://localhost:8000`

### 4. Client Setup

#### Install Dependencies
```bash
cd client
npm install
```

#### Environment Configuration
1. Copy the example environment file's content:
2. Create a new `.env` file and paste it:
```bash
BACKEND_URL=http://localhost:8000
```

#### Start the Development Server
```bash
npm run dev
```

The client will start at `http://localhost:3000`

## 🔧 Development Workflow

### Server Commands
```bash
# Install dependencies
poetry install

# Run database migrations
poetry run alembic upgrade head

# Create new migration (after model changes)
poetry run alembic revision --autogenerate -m "description"

# Start development server
poetry run start
```

### Client Commands
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 🏗️ Architecture Overview

### Backend (FastAPI + LangChain)
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM orchestration and multi-agent workflows
- **PostgreSQL** - Database with Alembic migrations
- **Poetry** - Dependency management

### Frontend (Next.js + React)
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **ai-sdk - AI Elements** - Component library

### Key Features
- Multi-agent LLM workflows
- Real-time chat interface
- File handling and processing
- Chart generation and visualization
- Session management

## 🗄️ Database Schema

The application uses two PostgreSQL schemas:

### `chat_sessions` Schema
- `chat_sessions` - Chat session metadata
- `messages` - Chat messages with user/assistant types
- `file_records` - File upload records

### `langgraph` Schema
- Automatically managed by LangChain for checkpointing and state management

## 🔑 API Keys Required

1. **OpenAI API Key** - For LLM functionality
   - Get from: https://platform.openai.com/api-keys
   
2. **Tavily API Key** - For web search capabilities
   - Get from: https://tavily.com/

## 📝 Additional Notes

- The application automatically creates required database schemas
- CORS is configured to allow client-server communication
- File uploads are supported for document processing
- The chat interface supports real-time streaming responses