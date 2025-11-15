#!/bin/bash

# Banking Bot Startup Script

echo "🏦 Starting Banking Bot Setup..."

# Check if virtual environment exists
if [ ! -d "venv_bankbot" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv_bankbot
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv_bankbot/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your OpenAI API key!"
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p data/chromadb
mkdir -p logs

# Create sample data
echo "Creating sample banking data..."
cd src
python create_sample_data.py
cd ..

# Ingest sample documents
echo "Ingesting sample documents..."
echo "Starting document ingestion server temporarily..."
cd src/ingestion_app
python ingestion_main.py &
INGESTION_PID=$!
sleep 5

# Upload sample documents
curl -X POST "http://localhost:8001/documents/ingest-directory" \
     -F "directory_path=../../data/sample_documents" \
     -F "document_type=policy"

# Stop ingestion server
kill $INGESTION_PID
cd ../..

echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Start the main API: python src/app/main.py"
echo "3. Start the ingestion API: python src/ingestion_app/ingestion_main.py"
echo "4. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "🧪 Test users created:"
echo "- john_doe (password: password123)"
echo "- jane_smith (password: password123)"  
echo "- mike_johnson (password: password123)"
