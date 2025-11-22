# Deploy to Render Free Tier - Step-by-Step Guide

This guide will help you deploy your Agentic AI Research Lab to Render's Free Tier.

## ⚠️ Important Free Tier Limitations

Before you begin, understand these Render Free Tier limitations:

1. **Cold Starts**: Services spin down after 15 minutes of inactivity
   - First request after spin-down takes 30 seconds to 1 minute
   - Subsequent requests are fast

2. **PostgreSQL Free Database**:
   - Only available for **30 days**
   - After 30 days, you'll need to upgrade to paid tier ($6/month minimum)
   - 256 MB RAM, 0.1 CPU

3. **Resources**:
   - 512 MB RAM per service
   - 0.1 CPU per service
   - No persistent disk storage

4. **Best Use Cases**:
   - Demos and testing
   - Personal projects
   - Portfolio projects
   - Not suitable for production with real users

---

## Prerequisites

### 1. GitHub Account & Repository

You need to push your code to a GitHub repository.

**If you don't have a GitHub repo yet:**

```bash
# Navigate to your hosting folder
cd D:\research_agent\agent\hosting

# Initialize git repository
git init

# Create .gitignore to exclude sensitive files
echo ".env" >> .gitignore
echo "*.db" >> .gitignore
echo "**/venv/" >> .gitignore
echo "**/__pycache__/" >> .gitignore
echo "**/node_modules/" >> .gitignore
echo "**/.next/" >> .gitignore

# Add all files
git add .

# Commit
git commit -m "Initial commit for Render deployment"

# Create GitHub repository at https://github.com/new
# Then link it (replace YOUR_USERNAME/YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### 2. Render Account

Sign up for a free Render account at https://render.com

### 3. API Keys

You'll need at least ONE of these LLM provider API keys:
- **OpenAI**: https://platform.openai.com/api-keys
- **Google Gemini**: https://makersuite.google.com/app/apikey
- **OpenRouter**: https://openrouter.ai/keys

Optional but recommended (for web search):
- **Tavily**: https://tavily.com/ (1000 free searches/month)
- **Serper.dev**: https://serper.dev/ (2500 free searches)
- **SerpAPI**: https://serpapi.com/ (100 free searches/month)

---

## Deployment Steps

### Option A: Deploy Using Blueprint (Recommended - Easiest)

The `render.yaml` file is a blueprint that automatically creates all services.

1. **Go to Render Dashboard**
   - Visit https://dashboard.render.com/
   - Click **"New +"** → **"Blueprint"**

2. **Connect GitHub Repository**
   - Click **"Connect a repository"**
   - Authorize Render to access your GitHub
   - Select your repository

3. **Configure Blueprint**
   - Render will detect `render.yaml` automatically
   - Service names will be:
     - `research-agent-backend` (Python FastAPI)
     - `research-agent-frontend` (Next.js)
     - `research-db` (PostgreSQL)

4. **Set Environment Variables**
   - Before clicking "Apply", you'll see a list of environment variables
   - Fill in your **backend** API keys (REQUIRED - at least one LLM provider):
     ```
     OPENAI_API_KEY=sk-...
     TAVILY_API_KEY=tvly-...
     (and other keys you have)
     ```
   - **IMPORTANT**: Leave `NEXT_PUBLIC_API_URL` blank for now (you'll set it in step 7)
   - Leave other optional keys blank if you don't have them

5. **Apply Blueprint**
   - Click **"Apply"**
   - Render will create all 3 services and start deploying
   - **Backend will deploy successfully**
   - **Frontend will deploy but may not work yet** (needs backend URL)
   - Wait 5-10 minutes for deployments

6. **Get Backend URL**
   - Once backend deployment completes, click on **research-agent-backend** service
   - Copy the service URL (e.g., `https://research-agent-backend.onrender.com`)
   - Verify backend is working by visiting: `https://research-agent-backend.onrender.com/health`
   - Should return: `{"status": "healthy", "service": "research-api"}`

7. **Configure Frontend with Backend URL**
   - Click on **research-agent-frontend** service
   - Go to **Environment** tab
   - Find `NEXT_PUBLIC_API_URL` variable
   - Set it to your backend URL: `https://research-agent-backend.onrender.com`
   - **DO NOT include trailing slash**
   - Click **"Save Changes"**
   - Frontend will automatically redeploy (wait 3-5 minutes)

8. **Access Your Application**
   - Once frontend redeployment completes, open the frontend URL
   - Should be: `https://research-agent-frontend.onrender.com`
   - First load will take 30-60 seconds (cold start)
   - Try a simple research query to verify everything works!

---

### Option B: Manual Deployment (If Blueprint Doesn't Work)

If the blueprint method fails, deploy each service manually:

#### Step 1: Deploy PostgreSQL Database

1. In Render Dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `research-db`
   - **Database**: `research_db`
   - **User**: `research_user`
   - **Region**: Oregon (US West)
   - **Plan**: Free
3. Click **"Create Database"**
4. Wait for database to be created
5. Copy the **Internal Database URL** (starts with `postgres://`)

#### Step 2: Deploy Backend Service

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `research-agent-backend`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Environment**: `Python 3`
   - **Build Command**:
     ```bash
     cd backend && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     cd backend && uvicorn app.api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free

4. **Add Environment Variables** (click "Advanced" → "Add Environment Variable"):
   ```
   PYTHON_VERSION=3.11.0
   DATABASE_URL=<paste the Internal Database URL from Step 1>
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly-...
   SERPER_API_KEY=...
   GOOGLE_API_KEY=...
   OPENROUTER_API_KEY=...
   GITHUB_TOKEN=...
   ```

5. Click **"Create Web Service"**
6. Wait 5-10 minutes for deployment
7. Once live, copy your backend URL (e.g., `https://research-agent-backend.onrender.com`)

#### Step 3: Deploy Frontend Service

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository again
3. Configure:
   - **Name**: `research-agent-frontend`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Environment**: `Node`
   - **Build Command**:
     ```bash
     cd frontend && npm install && npm run build
     ```
   - **Start Command**:
     ```bash
     cd frontend && npm start
     ```
   - **Plan**: Free

4. **Add Environment Variables**:
   ```
   NODE_VERSION=18.17.0
   NEXT_PUBLIC_API_URL=<paste your backend URL from Step 2>
   ```
   Example: `NEXT_PUBLIC_API_URL=https://research-agent-backend.onrender.com`

5. Click **"Create Web Service"**
6. Wait 3-5 minutes for deployment
7. Once live, copy your frontend URL

#### Step 4: Update Backend CORS Settings

The backend needs to allow requests from your frontend URL.

1. In your local `hosting/config.yaml`, the CORS is already set to allow all Render URLs:
   ```yaml
   cors_origins:
     - "http://localhost:3000"
     - "http://127.0.0.1:3000"
     - "https://*.onrender.com"
   ```
   This wildcard pattern should work. If not, you may need to add specific URLs.

2. If you need to update CORS, edit `config.yaml` and push to GitHub:
   ```bash
   git add config.yaml
   git commit -m "Update CORS settings"
   git push
   ```
   Render will auto-redeploy.

---

## Verifying Deployment

### 1. Check Backend Health

Open in browser:
```
https://your-backend-url.onrender.com/health
```

You should see:
```json
{
  "status": "healthy",
  "service": "research-api"
}
```

### 2. Check Frontend

Open your frontend URL. You should see the research interface.

### 3. Test Research Query

1. Enter a simple query like "What is machine learning?"
2. Click "Start Research"
3. Wait for the response (may take longer on free tier due to cold starts)

---

## Troubleshooting

### Issue: "Service unavailable" or 502 error

**Cause**: Service is spinning up from cold start
**Solution**: Wait 30-60 seconds and refresh

### Issue: "Database connection failed"

**Cause**: DATABASE_URL not set correctly
**Solution**:
1. Go to Render Dashboard → Backend Service → Environment
2. Verify DATABASE_URL is set to the PostgreSQL Internal URL
3. Should start with `postgresql://` or `postgres://`
4. Change `postgres://` to `postgresql+asyncpg://` if needed

### Issue: Frontend can't connect to backend

**Cause**: NEXT_PUBLIC_API_URL not set
**Solution**:
1. Go to Frontend Service → Environment
2. Add NEXT_PUBLIC_API_URL with your backend URL
3. Must include `https://` and NO trailing slash
4. Example: `https://research-agent-backend.onrender.com`

### Issue: Build fails with "Module not found"

**Cause**: Dependencies not installed
**Solution**:
1. Check your build command includes `pip install -r requirements.txt` or `npm install`
2. Check requirements.txt/package.json are in the correct directory
3. Look at build logs for specific error

### Issue: "No LLM provider configured"

**Cause**: API keys not set
**Solution**:
1. Go to Backend Service → Environment
2. Add at least one of: OPENAI_API_KEY, GOOGLE_API_KEY, or OPENROUTER_API_KEY
3. Redeploy service

### Issue: Research queries time out

**Cause**: Free tier CPU/memory limits
**Solution**:
1. Reduce max_iterations in config.yaml (try 5 instead of 10)
2. Reduce timeout_minutes to 5
3. Keep queries simple on free tier

---

## Monitoring Your Deployment

### View Logs

1. Go to Render Dashboard
2. Click on your service (backend or frontend)
3. Click **"Logs"** tab
4. View real-time logs

### Check Resource Usage

1. In service dashboard, click **"Metrics"** tab
2. View CPU, memory, and request metrics

### Restart Service

If service is stuck:
1. Go to service dashboard
2. Click **"Manual Deploy"** → **"Clear build cache & deploy"**

---

## Cost Considerations

### Free Tier Summary

- **Backend**: $0/month (with cold starts)
- **Frontend**: $0/month (with cold starts)
- **Database**: $0 for first 30 days, then **$6/month**

### After 30 Days

You'll need to upgrade the PostgreSQL database to a paid tier:
- **Basic (256 MB)**: $6/month
- **Standard (1 GB)**: $19/month

Alternatively:
- Export your data before 30 days
- Use an external database service (Supabase, ElephantSQL free tiers)

### LLM API Costs

Render hosting is free, but you'll pay for:
- **OpenAI API**: ~$0.01-0.10 per research query (GPT-4o-mini)
- **Google Gemini**: ~$0.001-0.01 per query (Gemini 2.5 Flash)
- **Tavily Search**: Free for 1000 searches/month
- **Serper**: Free for 2500 searches total

**Estimated total cost for light usage**: $5-15/month (mostly LLM APIs, not Render)

---

## Updating Your Deployment

### Auto-Deploy on Git Push

Render automatically deploys when you push to your main branch:

```bash
# Make changes locally
cd D:\research_agent\agent\hosting

# Commit and push
git add .
git commit -m "Update feature X"
git push

# Render will auto-deploy in 3-5 minutes
```

### Manual Deploy

1. Go to service in Render Dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## Alternative Deployment Options

If Render free tier doesn't meet your needs:

### 1. Railway ($5/month)
- No cold starts
- $5 includes hosting + compute credits
- Better performance
- https://railway.app

### 2. Fly.io (Free tier available)
- 3 free VMs
- No database included in free tier
- https://fly.io

### 3. Heroku ($5-7/month per dyno)
- No free tier anymore
- More mature platform
- https://heroku.com

---

## Security Best Practices

### 1. Never Commit .env File

Already in .gitignore, but double-check:
```bash
git status
# Should NOT show .env file
```

### 2. Rotate API Keys Regularly

Change your API keys every few months:
1. Generate new key from provider
2. Update in Render Dashboard → Environment Variables
3. Delete old key from provider

### 3. Monitor Usage

Check your API provider dashboards weekly to watch for:
- Unexpected high usage
- Unauthorized access
- Cost spikes

---

## Getting Help

### Render Support
- Docs: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

### Application Issues
- Check logs in Render Dashboard
- Review error messages
- Test locally first: `cd hosting && ./start.bat`

### API Provider Issues
- OpenAI Status: https://status.openai.com
- Check API key is valid
- Check billing/quota limits

---

## Next Steps

After successful deployment:

1. **Test all features**
   - Try different research queries
   - Test export to PDF/Word
   - Check history/session management

2. **Share your URL**
   - Frontend URL is public and shareable
   - Example: `https://research-agent-frontend.onrender.com`

3. **Monitor costs**
   - Check LLM API usage dashboards
   - Set up billing alerts

4. **Plan for database expiry**
   - Mark calendar for 30 days from now
   - Export important research before database expires
   - Budget $6/month for database upgrade if needed

---

## Summary Checklist

- [ ] GitHub repository created and code pushed
- [ ] Render account created
- [ ] API keys obtained (at least 1 LLM provider)
- [ ] PostgreSQL database deployed
- [ ] Backend service deployed with environment variables
- [ ] Frontend service deployed with NEXT_PUBLIC_API_URL
- [ ] Backend health check passes (`/health` returns 200)
- [ ] Frontend loads successfully
- [ ] Test research query completes successfully
- [ ] Logs reviewed for errors
- [ ] URLs saved for future reference

---

**Congratulations!** Your Agentic AI Research Lab is now live on the web! 🎉

Users can now access your application at your frontend URL. Remember to monitor usage and costs, especially API usage from your LLM providers.














● Perfect! I've successfully prepared your application for deployment on Render Free Tier. Here's what was done:

  ✅ Changes Made in hosting Folder

  1. Updated backend/app/config/settings.py

  - Added support for ${ENV_VAR:default_value} syntax
  - Allows DATABASE_URL to use PostgreSQL in production, SQLite locally

  2. Updated backend/requirements.txt

  - Added asyncpg>=0.29.0 for PostgreSQL support

  3. Updated render.yaml

  - Fixed frontend environment variable configuration
  - Blueprint ready for one-click deployment

  4. Created DEPLOY_TO_RENDER.md

  - Complete step-by-step deployment guide
  - Troubleshooting section
  - Cost breakdown and monitoring tips

  5. Existing config.yaml (already configured)

  - Database URL with environment variable fallback
  - CORS configured for Render domains

  📋 What You Need to Do Next

  1. Push to GitHub (if not already):
  cd D:\research_agent\agent\hosting
  git init
  git add .
  git commit -m "Ready for Render deployment"
  # Create repo on GitHub, then:
  git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
  git push -u origin main
  2. Follow the deployment guide:
    - Open hosting/DEPLOY_TO_RENDER.md
    - Follow either Option A (Blueprint - easiest) or Option B (Manual)
    - You'll need at least one LLM API key (OpenAI, Gemini, or OpenRouter)

  🎯 Quick Start Path

  Easiest route:
  1. Push code to GitHub
  2. Sign up at https://render.com
  3. Click "New+" → "Blueprint"
  4. Select your GitHub repo
  5. Enter your API keys
  6. Click "Apply"
  7. Wait 5-10 minutes
  8. Done! 🎉

  ⚠️ Important Reminders

  - Free tier has cold starts (30s-1min delay after 15 min inactivity)
  - Database expires after 30 days (need to upgrade to $6/month)
  - Best for demos and testing, not production with real users
  - Your original agent folder is unchanged - local app still works

  Total estimated monthly cost: $0 for hosting, $5-15 for LLM API usage

  The complete deployment guide in hosting/DEPLOY_TO_RENDER.md has all the details!

> on render should i start a new blueprint instance or choose an option from the following:

Static Sites
Static content served over a global CDN. Ideal for frontend, blogs, and content sites.
New Static Site
Web Services
Dynamic web app. Ideal for full-stack apps, API servers, and mobile backends.
New Web Service
Private Services
Web app hosted on a private network, accessible only from your other Render services.
New Private Service
Background Workers
Long-lived services that process async tasks, usually from a job queue.
New Worker
Cron Jobs
Short-lived tasks that run on a periodic schedule.
New Cron Job
Postgres
Relational data storage. Supports point-in-time recovery, read replicas, and high availability.
New Postgres
Key Value
Managed Redis®-compatible storage. Ideal for use as a shared cache, message broker, or job queue.
New Key Value Instance

● Use "Blueprint" - not any of those individual options!

  Here's why and how:

  ✅ Choose Blueprint

  Look for a "Blueprint" or "New Blueprint" option in the Render dashboard. It might be:
  - In the main "New +" dropdown menu
  - Under a "Deploy" section
  - Sometimes labeled as "Infrastructure as Code" or "YAML"

  Blueprint is better because:
  - Creates all 3 services automatically (backend + frontend + database)
  - Uses your render.yaml configuration
  - Ensures services are connected properly
  - One-click deployment

  🔍 Where to Find Blueprint

  1. Go to https://dashboard.render.com/
  2. Look for "New +" button (top right)
  3. Click it and look for one of these:
    - "Blueprint"
    - "From a Blueprint"
    - "YAML/Blueprint"

  If you can't find "Blueprint" option, it might be:
  - Under "Get Started" or "Quick Start"
  - Or look for "Connect a repository" which might lead to Blueprint detection

  📸 What Blueprint Does

  When you select your GitHub repo with render.yaml, Render will:
  1. ✅ Create Web Service for backend (Python)
  2. ✅ Create Web Service for frontend (Next.js)
  3. ✅ Create Postgres database
  4. ✅ Connect them all together

  ⚠️ If You Can't Find Blueprint Option

  Then create services manually in this order:

  Step 1: New Postgres

  - Click "Postgres" → "New Postgres"
  - Name: research-db
  - Plan: Free

  Step 2: New Web Service (Backend)

  - Click "Web Services" → "New Web Service"
  - Follow the manual deployment steps in DEPLOY_TO_RENDER.md

  Step 3: New Web Service (Frontend)

  - Click "Web Services" → "New Web Service" again
  - Follow the manual deployment steps in DEPLOY_TO_RENDER.md