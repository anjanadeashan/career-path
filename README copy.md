# Smart Job Matching System (AI Career Helper)

A modern, production-ready full-stack web application designed to help students analyze resumes, identify skill gaps, retrieve machine-learned job fits, and obtain custom certification roadmap advice via Claude AI.

---

## Technical Stack
*   **Backend:** Python Flask
*   **Database & Auth:** Supabase (PostgreSQL with Row Level Security)
*   **AI Integration:** Anthropic Claude API (Fallback rules enabled)
*   **NLP Engines:** spaCy (`en_core_web_sm`), NLTK
*   **Machine Learning:** Scikit-learn (TF-IDF & Cosine Similarity ranking)
*   **Document Parsers:** `pypdf`, `python-docx`
*   **Frontend:** HTML5, CSS3 (Custom Glassmorphism), Bootstrap 5, Javascript

---

## Folder Structure
```text
smart_job_matcher/
├── app.py                     # App server entrypoint
├── requirements.txt           # Python dependency specifications
├── setup.sql                  # Database Schema setup SQL
├── .env.example               # Environment variables configuration template
├── README.md                  # Detailed Setup & Deployment guide
└── app/
    ├── __init__.py            # Flask App factory
    ├── config.py              # Configuration & verification manager
    ├── controllers/           # REST Blueprints (Routers)
    │   ├── auth_helper.py     # Decorators (login_required, admin_required)
    │   ├── auth_controller.py
    │   ├── resume_controller.py
    │   ├── job_controller.py
    │   ├── career_controller.py
    │   └── admin_controller.py
    ├── repositories/          # Supabase queries abstraction (Repository Pattern)
    │   ├── base_repository.py
    │   ├── profile_repository.py
    │   ├── job_repository.py
    │   └── resume_repository.py
    ├── services/              # Business Logic (Services)
    │   ├── supabase_client.py
    │   ├── parsing_service.py
    │   ├── nlp_service.py
    │   ├── recommendation_service.py
    │   └── claude_service.py
    ├── static/                # Stylesheets and JS utilities
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       ├── main.js
    │       ├── auth.js
    │       ├── profile.js
    │       └── admin.js
    └── templates/             # Jinja2 Layout Templates
        ├── base.html
        ├── index.html
        ├── login.html
        ├── register.html
        ├── profile.html
        ├── jobs.html
        ├── advisor.html
        └── admin.html
```

---

## Installation & Setup Guide

### 1. Database Setup (Supabase)
1. Go to [Supabase](https://supabase.com) and create a new project.
2. In your Supabase project dashboard, open the **SQL Editor** from the left-hand sidebar.
3. Click **New Query**, paste the contents of `setup.sql` into the editor, and click **Run**.
4. This script initializes all tables (`profiles`, `resumes`, `extracted_skills`, `jobs`, `recommendations`, `skill_gaps`, `career_feedback`), installs triggers to auto-create user profiles upon signup, configures Row Level Security (RLS) policies, and populates the database with five high-quality starter jobs.

### 2. Environment Configurations
1. Copy the `.env.example` file to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in the values:
   *   `SECRET_KEY`: Any secure random string.
   *   `SUPABASE_URL`: Locate under *Settings -> API* in your Supabase project.
   *   `SUPABASE_KEY`: Locate the `anon` public key or `service_role` key under *Settings -> API*. (For absolute backend control, the `service_role` key is recommended as it bypasses standard RLS restrictions).
   *   `ANTHROPIC_API_KEY`: Generate an API key inside the Anthropic Developer Console.
       *   *Note: If no Anthropic key is supplied or left default, the system automatically falls back to a high-quality local rule-based advisor, meaning the program will never crash and can be tested immediately.*

### 3. Local Installation Steps
We recommend creating a virtual environment:

```bash
# 1. Create a virtual environment
python3 -m venv venv

# 2. Activate the virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 3. Install required Python packages
pip install -r requirements.txt

# 4. Download spaCy and NLTK assets
# (The application tries to download these automatically on first startup, but you can trigger it manually)
python -m spacy download en_core_web_sm
```

### 4. Running the Application
Start the Flask development server:
```bash
python app.py
```
Open your browser and navigate to `http://localhost:5001`.

---

## User Evaluation Walkthrough

### Test Case A: The Candidate (Student Flow)
1. Register as a **Student** via `http://localhost:5001/register` (e.g., Jane Doe, `jane@example.com`).
2. Navigate to **Profile**. Upload a sample CV in PDF or DOCX format containing some skills (e.g. Python, SQL, Git).
3. Check the **Skills** layout: you will see technical and soft skills parsed automatically!
4. Go to **Job Matches**: look at the matching scores. Click a job card to expand and review the missing skills gap and click direct Coursera/Udemy links to fix the gap.
5. Go to **AI Career Advisor**: Click **Generate AI Analysis**. Read the detailed profile assessment and recommended LinkedIn career pathways.

### Test Case B: The Administrator (Admin Flow)
1. Register as an **Administrator** (`admin` role selected in the dropdown).
2. Go to **Admin Dashboard** (accessible in the navbar).
3. View global metrics cards tracking total resumes and users.
4. Go to **Jobs Catalog** tab to view postings.
5. Use the **Post New Job** form to submit a new job, specifying title, description, and required skills (e.g. `Python, Docker, React`).
6. Toggle the **Uploaded CVs** tab and click **View Text** on any candidate's card to inspect their parsed resume raw text instantly.

---

## Production Deployment Guide

### Option 1: Deploying to Render
1. Create a new Web Service on [Render](https://render.com) and link your GitHub repository.
2. In the configuration settings, choose **Python** as the Environment.
3. Set the **Build Command**:
   ```bash
   pip install -r requirements.txt && python -m spacy download en_core_web_sm
   ```
4. Set the **Start Command**:
   ```bash
   gunicorn app:app
   ```
5. Go to **Environment Variables** and add all values defined in your local `.env`.
6. Click Deploy. Render will provision the server and host your app.

### Option 2: Deploying to Heroku
1. Create a new application in the [Heroku Dashboard](https://dashboard.heroku.com).
2. Add the official **Python Buildpack** under Settings.
3. Configure your Config Vars (environment variables) in Heroku settings.
4. Create a `Procfile` (already supported via gunicorn):
   ```text
   web: gunicorn app:app
   ```
5. Push your code using Git:
   ```bash
   git push heroku main
   ```
