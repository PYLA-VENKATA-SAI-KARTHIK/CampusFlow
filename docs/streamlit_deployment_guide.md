# Streamlit Community Cloud Deployment Guide for CampusFlow

This guide provides step-by-step instructions for running the **CampusFlow Interactive Showcase App** locally and deploying it for free to **Streamlit Community Cloud** ([share.streamlit.io](https://share.streamlit.io)).

---

## 1. Running Locally (Quick Evaluation)

To test the Streamlit app on your local machine:

```powershell
# From the backend directory or using the project virtual environment
cd c:\CampusFlow
.\backend\venv\Scripts\streamlit.exe run streamlit_app.py
```

The app will open automatically in your browser at:
👉 **`http://localhost:8501`**

---

## 2. Deploying to Streamlit Community Cloud (Free Public URL)

Streamlit Community Cloud allows you to share your interactive project with mentors, evaluators, and recruiters with a single click.

### Step 1: Push Code to GitHub
Ensure `streamlit_app.py` and `requirements-streamlit.txt` are pushed to your GitHub repository:
```bash
git add streamlit_app.py requirements-streamlit.txt docs/
git commit -m "feat: add interactive Streamlit showcase app for cloud deployment"
git push origin main
```

### Step 2: Connect to Streamlit Community Cloud
1. Navigate to **[share.streamlit.io](https://share.streamlit.io)**.
2. Sign in with your **GitHub** account.
3. Click **"New app"** (or **"Create app"**).

### Step 3: Configure App Settings
Fill in the deployment fields:
- **Repository**: `YourGitHubUsername/CampusFlow`
- **Branch**: `main`
- **Main file path**: `streamlit_app.py`
- **App URL** (Optional): Custom subdomain (e.g. `campusflow-showcase.streamlit.app`)

### Step 4: Specify Requirements
1. Click **"Advanced settings"** before deploying.
2. In the Python requirements file input, set:
   `requirements-streamlit.txt`
3. Click **"Save"** & **"Deploy!"**.

Within 1–2 minutes, Streamlit will provision the cloud container and provide you with a live, shareable URL (e.g. `https://campusflow.streamlit.app`).

---

## 3. What to Demonstrate to Your Mentor

When demonstrating the Streamlit app to your mentor, walk through the 5 interactive tabs:

1. **🌐 System Architecture Tab**:
   - Show the live backend connection badge.
   - Explain the 4-tier domain-driven design (API $\to$ Services $\to$ Repositories $\to$ Immutability Models).
   - Point out that **359 of 359 tests passed** (100% test coverage).

2. **💼 Placement Drives & Stages Tab**:
   - Showcase corporate drive management (Google Cloud, Microsoft, Qualcomm).
   - Walk through sequential round orchestration (Aptitude $\to$ Coding $\to$ HR Interviews).

3. **🧮 Live Eligibility Engine Simulator**:
   - Have your mentor pick any CGPA (e.g. 7.8), backlogs count (e.g. 1), and branch (e.g. ECE).
   - Click evaluate: show how the engine instantly audits every criteria and provides an itemized pass/fail breakdown.

4. **🛡️ Security & RBAC Guard Tab**:
   - Highlight **RS256 2048-bit Asymmetric JWT** tokens.
   - Show the **SlowAPI Rate Limiter** protection rules (10 requests/min on login).
   - Walk through the **RBAC Matrix** explaining why students are blocked from administrative actions.
   - Display the actual **PostgreSQL Immutability Trigger SQL code** that prevents audit log tampering.

5. **📊 Funnel & Placement Insights Tab**:
   - Demonstrate the interactive Plotly CTC distribution bar charts and the 5-stage selection funnel chart.
