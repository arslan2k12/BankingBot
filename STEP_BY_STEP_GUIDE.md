# Step-by-Step Banking Bot Setup Guide for Complete Beginners

This guide will help you set up and run the Banking Bot system from scratch. We'll build an intelligent banking assistant that can answer questions about account balances, transactions, credit cards, and bank policies using AI.

## 🎯 What You'll Build

By the end of this guide, you'll have:
- ✅ A **Python backend** with AI-powered banking assistant
- ✅ A **React frontend** for chatting with the bot
- ✅ **Database** with sample banking data
- ✅ **Document search** using AI embeddings
- ✅ **Real-time streaming** chat responses

## 📋 Prerequisites Check

### Step 0: What You Need Before Starting

**Required Software:**
- **Python 3.11 or higher** (check with `python --version`)
- **Node.js 18 or higher** (check with `node --version`)
- **Git** (for downloading the code)
- **A text editor** (VS Code recommended, but any editor works)

**Optional but Helpful:**
- **OpenAI API account** (we'll get this during setup)

---

## 🚀 Step 1: Download the Project

### Option A: Download from GitHub (Recommended)

1. **Open your web browser** and go to the GitHub repository URL (provided by your workshop instructor)

2. **Click the green "Code" button** → **"Download ZIP"**

3. **Extract the ZIP file** to your Desktop or Documents folder
   - **Mac:** Double-click the ZIP file
   - **Windows:** Right-click → Extract All

4. **Open the extracted folder** - you should see two folders:
   - `BankingBot/` (Python backend)
   - `banking-bot-ui/` (React frontend)

### Option B: Clone with Git (Advanced)

If you have Git installed:
```bash
# Open Terminal/Command Prompt and run:
git clone [REPOSITORY_URL]
cd [PROJECT_FOLDER_NAME]
```

---

## 🐍 Step 2: Set Up the Python Backend (BankingBot)

### Step 2.1: Navigate to the BankingBot Folder

**Mac Terminal:**
```bash
# Open Terminal app (press Cmd + Space, type "Terminal")
cd Desktop/[EXTRACTED_FOLDER_NAME]/BankingBot
# Example: cd Desktop/banking-bot-workshop/BankingBot
```

**Windows Command Prompt:**
```cmd
# Open Command Prompt (press Win + R, type "cmd")
cd Desktop\[EXTRACTED_FOLDER_NAME]\BankingBot
# Example: cd Desktop\banking-bot-workshop\BankingBot
```

**Tip:** You can drag the BankingBot folder into the terminal window to auto-complete the path!

### Step 2.2: Create Python Virtual Environment

A virtual environment keeps this project's dependencies separate from your system Python.

**Mac:**
```bash
# Create virtual environment
python3 -m venv venv_bankbot

# Activate virtual environment
source venv_bankbot/bin/activate
```

**Windows:**
```cmd
# Create virtual environment
python -m venv venv_bankbot

# Activate virtual environment
venv_bankbot\Scripts\activate
```

**Expected Result:** You should see `(venv_bankbot)` at the beginning of your command prompt.

**Troubleshooting:**
- If `python3` doesn't work, try `python`
- If you get permission errors on Windows, run Command Prompt as Administrator
- If activation fails, check that the `venv_bankbot` folder was created

### Step 2.3: Install Python Dependencies

```bash
# Upgrade pip first (package installer)
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**This will take 2-5 minutes.** You'll see lots of package names being installed.

**Troubleshooting:**
- If you get connection errors, check your internet connection
- If installation fails, try again - sometimes packages need to be installed in a specific order

### Step 2.4: Set Up Environment Variables

1. **Create the .env file:**
   ```bash
   # Copy the template
   cp .env.example .env
   ```

2. **Edit the .env file:**
   - **Mac:** Open with TextEdit or your code editor: `open .env`
   - **Windows:** Open with Notepad or your code editor: `notepad .env`

3. **Add your OpenAI API key:**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

   **How to get an OpenAI API key:**
   - Go to https://platform.openai.com/api-keys
   - Sign up or log in
   - Click "Create new secret key"
   - Copy the key (it starts with `sk-`)
   - Paste it in the .env file

   **For SECRET_KEY:** You can use any random string, like `my_secret_key_12345`

### Step 2.5: Create Sample Data

```bash
# Create database and sample banking data
python src/ingestion_app/create_sample_data.py
```

**Expected Output:**
```
✅ Created directories
✅ Initialized database
✅ Created 3 sample users
✅ Created 6 bank accounts
✅ Created 50 transactions
✅ Created 3 credit cards
✅ Processed 2 policy documents
✅ Setup completed successfully!
```

**What this does:**
- Creates a SQLite database with sample banking data
- Sets up ChromaDB for document search
- Creates test users you can log in with

### Step 2.6: Start the Banking Bot API

```bash
# Start the main API server
uvicorn src.app.main:app --host 0.0.0.0 --port 2024 --reload
```

**Expected Output:**
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:2024 (Press CTRL+C to quit)
```

**Keep this terminal window open!** The API needs to keep running.

**Test the API:**
- Open your browser to: http://localhost:2024/docs
- You should see the FastAPI documentation page

---

## ⚛️ Step 3: Set Up the React Frontend (banking-bot-ui)

### Step 3.1: Open a New Terminal Window

**Important:** Keep the Python API running in the first terminal. Open a **new** terminal window for the frontend.

**Mac:** Press Cmd + N in Terminal to open a new window

**Windows:** Open a new Command Prompt window

### Step 3.2: Navigate to the Frontend Folder

**Mac:**
```bash
cd Desktop/[EXTRACTED_FOLDER_NAME]/banking-bot-ui
```

**Windows:**
```cmd
cd Desktop\[EXTRACTED_FOLDER_NAME]\banking-bot-ui
```

### Step 3.3: Install Node.js Dependencies

```bash
# Install all frontend dependencies
npm install
```

**This will take 1-3 minutes.** You'll see package names being installed.

**Troubleshooting:**
- If `npm` is not found, install Node.js from https://nodejs.org
- If you get permission errors, try `sudo npm install` (Mac) or run as Administrator (Windows)

### Step 3.4: Start the React Development Server

```bash
# Start the frontend development server
npm run dev
```

**Expected Output:**
```
Vite dev server running at:
  > Local:    http://localhost:3000/
  > Network:  http://192.168.X.X:3000/
```

---

## 🧪 Step 4: Test Your Banking Bot

### Step 4.1: Open the Chat Interface

1. **Open your web browser**
2. **Go to:** http://localhost:3000
3. **You should see the Banking Bot chat interface**

### Step 4.2: Log In with Test Account

**Test Users Created:**
- **Username:** `john_doe`
- **Password:** `password123`

**Other test users:**
- `jane_smith` (password: `password123`)
- `mike_johnson` (password: `password123`)

### Step 4.3: Test the Chat Bot

Try asking these questions:

**Account Questions:**
- "What's my account balance?"
- "Show me my recent transactions"
- "How many accounts do I have?"

**Credit Card Questions:**
- "What's my credit card limit?"
- "Show me my credit card information"

**Bank Policy Questions:**
- "What are the fees for international transfers?"
- "What benefits come with my credit card?"

**Complex Questions:**
- "Show me transactions over $100 from last month"
- "What's my spending on groceries this month?"

### Step 4.4: Verify Everything Works

✅ **API Backend:** http://localhost:2024/docs  
✅ **Frontend:** http://localhost:3000  
✅ **Database:** Sample data loaded  
✅ **AI Chat:** Responses working  
✅ **Document Search:** Policy questions answered  

---

## 🔧 Troubleshooting Guide

### "Python command not found"
**Mac:** Install Python from https://www.python.org/downloads/  
**Windows:** Install from Microsoft Store or https://www.python.org/downloads/

### "npm command not found"
Install Node.js from https://nodejs.org

### "OpenAI API key invalid"
- Check your API key starts with `sk-`
- Make sure there are no extra spaces
- Verify your OpenAI account has credits

### "Port 2024 already in use"
```bash
# Find what's using the port
# Mac:
lsof -i :2024
# Windows:
netstat -ano | findstr :2024

# Kill the process (replace XXXX with the process ID)
kill XXXX
```

### "Database errors"
```bash
# Delete and recreate the database
rm -rf data/
python src/ingestion_app/create_sample_data.py
```

### "Frontend won't start"
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### "Virtual environment not activating"
**Mac:** Make sure you're using `source venv_bankbot/bin/activate`  
**Windows:** Make sure you're using `venv_bankbot\Scripts\activate`

---

## 📚 Understanding What You Built

### The Banking Bot Architecture

**Backend (Python/FastAPI):**
- **AI Agent:** Uses LangGraph to intelligently route questions
- **Database:** SQLite with banking data (accounts, transactions, users)
- **Document Search:** ChromaDB stores bank policies as AI embeddings
- **Authentication:** JWT tokens for secure login
- **Streaming:** Real-time chat responses

**Frontend (React/TypeScript):**
- **Chat Interface:** Modern UI with message history
- **Real-time Updates:** Live streaming of AI responses
- **Authentication:** Login/logout functionality
- **Responsive Design:** Works on desktop and mobile

### How the AI Works

1. **User asks:** "What's my account balance?"
2. **AI Agent:** Classifies this as a database query
3. **SQL Tool:** Queries the database for account information
4. **Response:** Streams back the formatted answer

1. **User asks:** "What are international transfer fees?"
2. **AI Agent:** Classifies this as a policy question
3. **Document Tool:** Searches ChromaDB for relevant documents
4. **Response:** Returns information from bank policy documents

---

## 🎯 Next Steps & Customization

### Add Your Own Data

1. **Add bank documents:** Place PDF/TXT files in `data/sample_documents/`
2. **Run ingestion:** The setup script automatically processes new documents
3. **Test questions:** Ask about your custom documents

### Customize the Bot

1. **Change responses:** Edit files in `src/app/agents/`
2. **Add new tools:** Create tools in `src/app/tools/`
3. **Modify UI:** Edit React components in `banking-bot-ui/src/components/`

### Production Deployment

1. **Set DEBUG=false** in your .env file
2. **Use a strong SECRET_KEY**
3. **Set up proper CORS** for your domain
4. **Consider PostgreSQL** instead of SQLite

---

## 🆘 Getting Help

### Common Issues & Solutions

**"Module not found" errors:**
```bash
# Reactivate virtual environment
source venv_bankbot/bin/activate  # Mac
venv_bankbot\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**"Connection refused" errors:**
- Make sure both servers are running
- Check that ports 2024 (API) and 3000 (frontend) are available
- Verify the API is accessible at http://localhost:2024/health

**"OpenAI quota exceeded":**
- Check your OpenAI dashboard for usage
- Add credits to your account if needed
- Use a different model in the config

### Useful Commands

```bash
# Check if servers are running
# Mac:
ps aux | grep uvicorn
ps aux | grep vite

# Windows:
tasklist | findstr uvicorn
tasklist | findstr node
```

### API Health Checks

- **Main API:** http://localhost:2024/health
- **Database:** http://localhost:2024/health/database
- **ChromaDB:** http://localhost:2024/health/chromadb

---

## 🎉 Congratulations!

You've successfully set up a complete AI-powered banking assistant! The system includes:

✅ **Intelligent Chat Bot** with natural language understanding  
✅ **Secure User Authentication** with JWT tokens  
✅ **Real-time Streaming** responses  
✅ **Database Integration** for personalized banking data  
✅ **Document Search** using AI embeddings  
✅ **Modern Web Interface** with responsive design  
✅ **Production-ready Architecture** with proper error handling  

**Your Banking Bot can now:**
- Answer questions about account balances and transactions
- Provide credit card information and benefits
- Search through bank policies and procedures
- Maintain conversation context across messages
- Stream responses in real-time for better user experience

**Share your experience:** Try asking complex questions that combine multiple data sources, like "Show me my spending on groceries and compare it to my credit card benefits!"

---

## 📞 Support Resources

- **API Documentation:** http://localhost:2024/docs
- **Health Monitoring:** http://localhost:2024/health
- **Logs:** Check `logs/banking_bot.log` for errors
- **Test Users:** john_doe, jane_smith, mike_johnson (all password: password123)

**Happy coding! 🚀**
