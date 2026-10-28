# Full-Stack Deployment Guide for CampusFlow (React 19 + FastAPI + PostgreSQL)

This guide shows you how to deploy your **exact custom website and design** online so your mentor, evaluators, and students can access it live with your full React 19 UI, college entrance page, and backend APIs.

---

## Architecture Overview

Your website consists of:
1. **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS (`/frontend`)
2. **Backend**: FastAPI + Python 3.13 (`/backend`)
3. **Database**: PostgreSQL 17

Because Streamlit Cloud is only designed for single-script Python data widgets, deploying on a cloud platform like **Render** or **Railway** will deploy your exact custom design.

---

## Method 1: Deploying on Render (Free & Recommended)

Render provides free hosting for both React static web apps and FastAPI backends connected to your GitHub repository.

### Step 1: Deploy PostgreSQL Database
1. Go to **[render.com](https://render.com)** and log in with your GitHub account.
2. Click **"New +"** $\to$ **"PostgreSQL"**.
3. Name: `campusflow-db`.
4. Click **"Create Database"**.
5. Once created, copy the **Internal Database URL** (or External Database URL).

### Step 2: Deploy the FastAPI Backend
1. On Render, click **"New +"** $\to$ **"Web Service"**.
2. Connect your GitHub repository: `CampusFlow`.
3. Configure the settings:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:
   - `DATABASE_URL`: *(Paste the PostgreSQL URL from Step 1)*
   - `APP_ENV`: `production`
   - `RUN_MIGRATIONS`: `true`
5. Click **"Deploy Web Service"**.
6. Copy your live backend URL (e.g. `https://campusflow-api.onrender.com`).

### Step 3: Deploy Your React Frontend
1. On Render, click **"New +"** $\to$ **"Static Site"**.
2. Connect your GitHub repository: `CampusFlow`.
3. Configure the settings:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. Under **Environment Variables**, add:
   - `VITE_API_URL`: `https://campusflow-api.onrender.com/api/v1` *(Your backend URL from Step 2)*
5. Click **"Create Static Site"**.

Your exact React website is now live online at `https://campusflow.onrender.com`!

---

## Method 2: Deploying via Docker on Railway

Railway deploys full-stack repositories with Docker Compose in a single step:

1. Go to **[railway.app](https://railway.app)** and log in with GitHub.
2. Click **"New Project"** $\to$ **"Deploy from GitHub repo"**.
3. Select `CampusFlow`.
4. Railway will automatically detect your `docker-compose.yml` and spin up your PostgreSQL, FastAPI backend, and React frontend with Nginx together.
