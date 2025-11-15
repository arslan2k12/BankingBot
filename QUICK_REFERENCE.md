# 🏦 Banking Bot Workshop - Quick Reference Card

## 📋 One-Command Setup

### Mac Users
```bash
./complete_setup_mac.sh
```

### Windows Users
```cmd
complete_setup_windows.bat
```

## 🚀 Start Everything
```bash
# Mac
./start_workshop.sh

# Windows
start_workshop.bat
```

## 🔗 Important URLs
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:2024/docs
- **Health Check:** http://localhost:2024/health

## 🧪 Test Login
- **Username:** `john_doe`
- **Password:** `password123`

## 🎯 Test Questions
- "What's my account balance?"
- "Show me my recent transactions"
- "What are international transfer fees?"

## 🆘 Need Help?
1. Check `health_check.sh` (Mac) or `health_check.bat` (Windows)
2. Look at browser console (F12)
3. Check `BankingBot/logs/banking_bot.log`

## 📂 Directory Structure
```
workshop-files/
├── complete_setup_mac.sh         # One-click setup (Mac)
├── complete_setup_windows.bat    # One-click setup (Windows)
├── start_workshop.sh             # Start both servers (Mac)
├── start_workshop.bat            # Start both servers (Windows)
├── health_check.sh               # Check system health (Mac)
├── health_check.bat              # Check system health (Windows)
├── BankingBot/                   # Python backend
│   ├── setup_mac.sh             # Backend setup (Mac)
│   ├── setup_windows.bat        # Backend setup (Windows)
│   ├── start_banking_bot.sh     # Backend only (Mac)
│   └── start_banking_bot.bat    # Backend only (Windows)
└── banking-bot-ui/               # React frontend
    ├── setup_frontend_mac.sh    # Frontend setup (Mac)
    ├── setup_frontend_windows.bat # Frontend setup (Windows)
    ├── start_frontend.sh        # Frontend only (Mac)
    └── start_frontend.bat       # Frontend only (Windows)
```

---
**Happy Coding! 🚀**
