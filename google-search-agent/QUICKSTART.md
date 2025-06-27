# 🚀 Quick Start Guide - Google Search Agent

Get your Google Search Agent running in **5 minutes**!

## ⚡ Super Quick Setup

### 1. Install ADK (30 seconds)
```bash
pip install google-adk
```

### 2. Set Up API Keys (3 minutes)

#### Get Google AI Studio Key
1. Go to [aistudio.google.com](https://aistudio.google.com/)
2. Sign in → Create API Key
3. Copy the key

#### Get Google Search API
1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create project → Enable "Custom Search JSON API"
3. Create API Key
4. Go to [Custom Search Engine](https://cse.google.com/cse/)
5. Create search engine → Search entire web → Get Engine ID

### 3. Configure Environment (1 minute)
```bash
# Copy the example config
cp env.example .env

# Edit .env with your keys:
GOOGLE_API_KEY=your_ai_studio_key
GOOGLE_SEARCH_API_KEY=your_search_api_key  
GOOGLE_SEARCH_ENGINE_ID=your_engine_id
```

### 4. Test & Run (30 seconds)
```bash
# Test your setup
python test_setup.py

# Run the agent
adk web
```

**Open [localhost:8000](http://localhost:8000) and start searching!** 🎉

---

## 🔥 Try These Searches

- **General**: "Latest developments in AI"
- **News**: "Recent climate change news"  
- **How-to**: "How to learn Python programming"
- **Local**: "Pizza restaurants in New York"
- **Academic**: "Machine learning research papers"

## 🆘 Having Issues?

### Quick Fixes
- **Agent not found**: Make sure you're in the `google-search-agent` directory
- **API errors**: Double-check your keys in `.env` file
- **No search results**: Verify Custom Search Engine is set to "search entire web"

### Get Help
- Run `python test_setup.py` for detailed diagnostics
- Check the full [README.md](README.md) for detailed setup
- Make sure you have Python 3.9+ and internet connection

## 💰 Cost Info
- **Google AI Studio**: Free tier with rate limits
- **Google Search**: 100 free searches/day, then $5/1000 searches

---

**That's it!** You now have an AI-powered search agent. 🔍✨ 