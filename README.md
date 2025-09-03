# LexRay: CLDR Date Skeleton Converter

A sophisticated bilingual date format analyzer that converts natural language date expressions to CLDR (Common Locale Data Repository) skeleton patterns. LexRay provides both a web interface and command-line tools for internationalization (i18n) work, allowing developers to create proper date formatting patterns for different locales.

## 🌟 Features

- **Natural Language Processing**: Converts English date expressions to CLDR skeletons
- **Cross-Language Mapping**: Maps English skeletons to target language skeletons
- **Web Interface**: Modern Next.js frontend for easy date format conversion
- **Smart Language Selection**: Typeahead autocomplete for CLDR language selection
- **Skeleton Result Display**: Always shows generated CLDR skeletons as interactive chips, even when errors occur
- **Batch Processing**: Process multiple date pairs from CSV files
- **Interactive CLI**: Command-line tools for advanced users
- **Literal Text Handling**: Preserves non-date words in single quotes
- **Ambiguity Resolution**: Interactive disambiguation for ambiguous date elements
- **Validation System**: Compare generated results against verified ground truth
- **Multi-language Support**: Support for 70+ languages with CLDR data

## 🏗️ Project Structure

This repository is organized as a monorepo with separate frontend and backend projects:

```
LexRay/
├── frontend/                 # Next.js web application
│   ├── app/                 # App router pages
│   │   ├── page.tsx        # Home page
│   │   ├── single/         # Single item processing
│   │   └── batch/          # Batch processing
│   ├── app/api/            # API routes
│   └── public/             # Static assets
└── backend/                 # Python CLDR converter
    ├── src/                # Core Python package
    ├── cldr_data/          # CLDR Excel data files
    ├── tests/              # Test suite
    └── testing/            # Batch testing data
```

## 🚀 Quick Start

### Choose Your Interface

LexRay offers two ways to interact with the system:

1. **🌐 Web Interface** - Modern browser-based UI for easy date conversion
2. **💻 Command Line Interface** - Powerful CLI for advanced users and automation

---

## 🌐 Running the Web Interface (Locally Hosted Website)

### Option A: Full Stack Setup (Recommended)

Run both frontend and backend locally for complete functionality:

#### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add CLDR data files
# Download and place these files in backend/cldr_data/:
# - english_moderate.xlsx (required)
# - {language}_moderate.xlsx (for target languages)
```

#### 2. Start Backend API Server

```bash
# In the backend directory with venv activated
python -m uvicorn api_bridge:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Frontend Setup (New Terminal)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 4. Access the Website

Open your browser and go to: **http://localhost:3000**

### Option B: Frontend Only

If you want to use the web interface without local backend processing:

```bash
cd frontend
npm install
npm run dev
```

Then open **http://localhost:3000** in your browser.

---

## 💻 Running the Command Line Interface

### Quick CLI Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Add CLDR data files to backend/cldr_data/
# - english_moderate.xlsx (required)
# - {language}_moderate.xlsx (for target languages)

# Run the CLI
python cldr_converter.py
```

### CLI Usage Example

```bash
$ python cldr_converter.py

Welcome to LexRay CLDR Date Skeleton Converter!

Enter English date expression: July 27, 2025
Enter target language code: spanish
Enter Spanish translation: 27 de julio de 2025

Results:
- English skeleton: MMMM d, y
- Spanish skeleton: d 'de' MMMM 'de' y
```

### CLI Features

- **Interactive mode**: Enter dates one by one
- **Batch processing**: Process CSV files with multiple date pairs
- **Ambiguity resolution**: Handle ambiguous date elements
- **Validation**: Compare results against verified data
- **Statistics**: Generate analysis reports

---

### Both Interfaces Support:
- Single date expression conversion
- Batch processing from CSV files
- Multiple language support
- CLDR skeleton generation
- Validation and error handling

## 📖 Usage Examples

### Example 1: Single Date Conversion

**Input:**
- English: `"July 27, 2025"`
- Spanish: `"27 de julio de 2025"`

**Output:**
- English skeleton: `"MMMM d, y"`
- Spanish skeleton: `"d 'de' MMMM 'de' y"`

### Example 2: Batch Processing

Upload a CSV file with columns:
- `ENGLISH`: English date expressions
- `TARGET`: Translated date expressions

**Output CSV will include:**
- `ENGLISH_SKELETON`: Generated English CLDR skeleton
- `TARGET_SKELETON`: Generated target language CLDR skeleton  
- `XPATH`: CLDR specification path (automatically generated)

## 🔧 Installation

### Prerequisites

- **Node.js 18+** (for frontend)
- **Python 3.7+** (for backend)
- **npm** or **yarn** (for frontend dependencies)
- **Git** (for cloning the repository)

### Environment Setup

#### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# Frontend API configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=LexRay
```

#### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Backend configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
CLDR_DATA_PATH=./cldr_data
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### CLDR Data Setup

1. Download CLDR data files from [Unicode CLDR Project](https://cldr.unicode.org/)
2. Place files in `backend/cldr_data/`:
   - `english_moderate.xlsx` (required)
   - `{language}_moderate.xlsx` (for each target language)

### Development Dependencies

For development work, install additional dependencies:

```bash
# Backend development dependencies
cd backend
pip install -r requirements-dev.txt  # if available

# Frontend development dependencies
cd frontend
npm install --save-dev
```

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
npm test
```

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

## 🔧 Troubleshooting

### Common Local Development Issues

#### Frontend Issues

**Port 3000 already in use:**
```bash
# Kill process using port 3000
lsof -ti:3000 | xargs kill -9
# Or use a different port
npm run dev -- -p 3001
```

**Module not found errors:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Backend Issues

**Port 8000 already in use:**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9
# Or use a different port
python -m uvicorn api_bridge:app --reload --host 0.0.0.0 --port 8001
```

**CLDR data not found:**
```bash
# Check if files exist
ls backend/cldr_data/
# Ensure english_moderate.xlsx is present
```

**Virtual environment issues:**
```bash
# Recreate virtual environment
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### API Connection Issues

**Frontend can't connect to backend:**
1. Ensure backend is running on port 8000
2. Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`
3. Verify CORS settings in backend API

### Development Tips

- **Hot reload**: Both frontend and backend support hot reloading during development
- **Logs**: Check terminal outputs for both frontend and backend servers
- **Browser dev tools**: Use browser developer tools to debug frontend issues
- **API testing**: Use tools like Postman or curl to test backend endpoints directly

## 🚀 Deployment

### Frontend (Vercel)

The frontend is optimized for Vercel deployment:

```bash
cd frontend
npm run build
```

Set the root directory to `frontend/` when configuring on Vercel.

## 📚 Documentation

- **[Backend Documentation](backend/README.md)**: Detailed CLI usage and API reference
- **[Quick Start Guide](backend/QUICKSTART_GUIDE.md)**: Step-by-step setup instructions
- **[CLDR Data Guide](backend/cldr_data/README.md)**: Data format specifications

## 🔍 Supported Features

- ✅ Month names (wide, abbreviated, narrow)
- ✅ Day names (wide, abbreviated, short, narrow)
- ✅ Numeric dates (1-2 digits, zero-padded)
- ✅ Years (2-digit, 4-digit)
- ✅ Punctuation and separators
- ✅ Literal text elements
- ✅ Multiple date formats per expression
- ✅ Standalone vs formatting contexts
- ✅ Ambiguity resolution
- ✅ Cross-language validation
- ✅ Duplicate element validation (prevents invalid skeletons like yy/M/y)
- ✅ Logical value validation (prevents invalid month/day assignments)

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:

- **Bug reports** and feature requests
- **Code contributions** and pull requests
- **Documentation** improvements
- **Testing** and validation

## 🔗 Links

- **[Unicode CLDR Project](https://cldr.unicode.org/)**: Official CLDR data source


# Trigger Vercel redeploy
