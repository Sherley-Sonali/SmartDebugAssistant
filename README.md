# SmartDebug Assistant

SmartDebug Assistant is a tool that transforms standard error messages into actionable, educational solutions. It helps developers learn through their mistakes by providing context-aware solutions, explanations, and learning resources.

## Features

- Error message analysis and classification
- Context-aware solutions based on your code
- Educational explanations of common programming errors
- Syntax-highlighted code examples
- Support for multiple programming languages (currently focused on Python)

## Project Structure

```
smart-debug/
├── backend/                # FastAPI backend
│   ├── main.py             # Main API code
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   └── ErrorAnalyzer.js  # Main React component
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── ...
└── README.md
```

## Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

1. Create the backend directory and files: or simply clone the repo

```bash
mkdir -p smart-debug/backend
cd smart-debug/backend
```

2. Create a requirements.txt file:

```bash
echo "fastapi==0.95.1
uvicorn==0.22.0
pydantic==1.10.7" > requirements.txt
```
Also pip install google-generativeai

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Create the main.py file with the provided FastAPI code

### Frontend Setup

1. Create a new React application:

```bash
npx create-react-app smart-debug/frontend
cd smart-debug/frontend
```

2. Install the required dependencies:

```bash
npm install prismjs @uiw/react-prismjs
```

## Running the Application

### Start the Backend Server

```bash
cd smart-debug/backend
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### Start the Frontend Development Server

```bash
cd smart-debug/frontend
npm start
```

The web application will be available at http://localhost:3000

## Usage

1. Enter an error message in the provided text area
2. Optionally, add the code context where the error occurred
3. Select the programming language
4. Click "Analyze Error"
5. View the analysis results, including:
   - Error type identification
   - Possible solutions with explanations
   - Code examples with syntax highlighting
   - Related programming concepts

## API Endpoints

- `POST /analyze_error` - Analyze an error message
- `GET /supported_languages` - Get a list of supported programming languages
