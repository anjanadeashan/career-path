import json
import logging
import anthropic
from app.config import Config
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)

class ClaudeService:
    """Service interacting with the Anthropic API to generate intelligent, personalized career feedback."""

    def __init__(self):
        self.api_key = Config.ANTHROPIC_API_KEY
        self.job_repo = JobRepository()
        self.resume_repo = ResumeRepository()
        
        # Initialize Anthropic client if key is set
        if self.api_key and self.api_key != "your-anthropic-claude-api-key-here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Error initializing Anthropic client: {str(e)}")
                self.client = None
        else:
            logger.warning("Anthropic API key not configured. Running ClaudeService in Mock Advisor fallback mode.")
            self.client = None

    def get_career_advice(self, user_id: str) -> dict:
        """
        Gathers user CV data and skills, passes it to Claude API,
        saves the response in the DB, and returns the advice dict.
        """
        try:
            resume = self.resume_repo.get_latest_resume(user_id)
            skills = self.resume_repo.get_skills_by_user(user_id)

            if not resume:
                return {
                    "success": False,
                    "error": "Please upload a resume first before requesting career advice."
                }

            skills_str = ", ".join([s['skill_name'] for s in skills])
            resume_text = resume.get('raw_text', '')

            system_prompt = (
                "You are an expert Senior Career Advisor, Executive Recruiter, and Career Transition Strategist spanning ALL INDUSTRIES (Tech, Finance, Healthcare, Arts, Business, etc.).\n\n"

                "CRUCIAL INSTRUCTION: The candidate may belong to ANY industry. DO NOT assume they are in IT/Software unless their resume explicitly shows tech skills. Provide industry-specific advice (e.g., for a nurse, provide healthcare advice; for a marketer, marketing advice).\n\n"

                "## YOUR FIRST JOB: INFER WHAT THIS PERSON WANTS TO BECOME\n"
                "Before giving any advice, read the resume like a detective. Look for:\n"
                "- The DIRECTION of their career trajectory (what field are they moving toward?)\n"
                "- What they studied vs. what they actually did (a gap signals a pivot desire)\n"
                "- Side projects, personal work, or self-taught skills that reveal passion areas\n"
                "- Technologies or domains they CHOSE to learn beyond their job requirements\n"
                "- Any objective/summary statements, even implied ones\n"
                "- If they are a student/fresh graduate, infer from their study field and projects\n\n"
                "Based on these signals, determine: (a) their inferred target role/domain, "
                "(b) how confident you are in that inference, and (c) what type of move they need — "
                "Growth (advancing in current domain), Pivot (moving to a different domain), or Entry (just starting out).\n\n"

                "## YOUR SECOND JOB: GIVE ADVICE AIMED AT THAT GOAL\n"
                "All sections of your feedback must be oriented around helping them REACH their inferred target, "
                "not just polish their current skills. If they need to cross a domain boundary, say so directly "
                "and give them the specific bridge skills, projects, and strategy to make that leap.\n\n"

                "Provide your full analysis as valid JSON with NO surrounding text or markdown fences.\n\n"
                "The JSON must contain exactly SEVEN keys:\n\n"

                "1. 'career_aspiration': An object describing what this person wants to become:\n"
                "   - 'target_role': The specific role or domain they are aiming for (e.g. 'Financial Analyst', 'Marketing Manager', 'AI/ML Engineer', 'Clinical Researcher', 'Project Manager')\n"
                "   - 'target_domain': The broader field (e.g. 'Finance', 'Healthcare', 'Engineering', 'Marketing & Sales', 'IT & Software')\n"
                "   - 'confidence': 'High', 'Medium', or 'Low' — how clearly the resume signals this direction\n"
                "   - 'signals': An array of 2-3 short strings describing the specific resume evidence that led to this inference (e.g. 'Studied Computer Science with AI electives', 'Built 3 personal ML projects on GitHub', 'Self-taught TensorFlow outside of job scope')\n"
                "   - 'aspiration_summary': One sentence describing what this person is trying to become and why their current background is a useful starting point\n\n"

                "2. 'transition_type': A string — exactly one of: 'Growth', 'Pivot', or 'Entry'\n"
                "   - 'Growth': They are already in the right domain and need to level up\n"
                "   - 'Pivot': They want to move into a clearly different domain from their current role\n"
                "   - 'Entry': They are a student, fresh graduate, or career starter\n\n"

                "3. 'feedback_text': A detailed Markdown document (750-950 words). "
                "Every section must be written with their inferred target role in mind — give advice FOR someone trying to GET INTO or ADVANCE IN that domain:\n"
                "   - '### 🔭 Career Vision': Start here. State what you inferred they want to become, the evidence you found, and whether this is a Growth/Pivot/Entry situation. Be direct and encouraging. Explain what makes their current background a useful launchpad.\n"
                "   - '### 🌟 Current Strengths': 2-3 specific strengths from their profile that are directly transferable to their target domain. Name the exact skills and explain WHY they matter for the target role.\n"
                "   - '### 🎯 Critical Gaps to Close': The top 4-5 skills/experiences they MUST acquire to break into or advance in their target domain. Be brutally specific — not 'learn Python' but 'Learn Python at a level where you can build REST APIs and write unit tests'. Explain what each gap is costing them right now.\n"
                "   - '### 🗓️ 30/60/90 Day Action Plan': Three labeled phases aimed squarely at their target role:\n"
                "       **Month 1 (Foundation):** Skills to start learning now, accounts/profiles to set up, first project idea.\n"
                "       **Month 2 (Build):** Specific project to complete that demonstrates the target domain skills, cert to begin.\n"
                "       **Month 3 (Launch):** How to position themselves for their first role/pivot, who to reach out to, how to stand out.\n"
                "   - '### 🚀 Entry & Positioning Strategy': How to package their EXISTING background as an asset FOR the target role, not baggage from the old one. Which companies to target first (startups vs enterprise vs agencies). Salary expectations for their transition level.\n"
                "   - '### 💼 LinkedIn Optimization': A SPECIFIC ready-to-use LinkedIn headline in quotes that reflects their DESTINATION not just their current status. A 2-sentence About opener that bridges their past to their future. Two featured project ideas that signal domain credibility.\n"
                "   - '### 🎤 Interview Prep': Top 3 questions interviewers ask candidates making this specific type of move (growth/pivot/entry), with a 3-bullet answer framework for each.\n\n"

                "4. 'career_paths': An array of 3-4 objects — paths oriented toward their inferred target domain, including at least one 'stretch' role they can aim for in 12-18 months:\n"
                "   - 'title': Specific modern job title\n"
                "   - 'demand': 'High', 'Medium', or 'Low'\n"
                "   - 'salary_range': Estimated range like '$85k-$130k USD'\n"
                "   - 'readiness': 'Ready Now', '3-6 Months', '6-12 Months', or '12-18 Months' — how long until they can realistically apply\n"
                "   - 'why_fit': One sentence connecting their background specifically to this role\n\n"

                "5. 'recommended_certifications': An array of 3-4 objects — certs that specifically bridge them from their current state to their target domain:\n"
                "   - 'name': Full certification or course name\n"
                "   - 'platform': Provider\n"
                "   - 'duration': Study time\n"
                "   - 'priority': 'High', 'Medium', or 'Low'\n"
                "   - 'reason': One sentence explaining how this cert specifically accelerates their domain transition\n\n"

                "6. 'profile_score': An integer 0-100. Score relative to their TARGET domain readiness, not just raw skill count. "
                "Components: relevant skill coverage for target domain (30%), experience quality/relevance (25%), "
                "portfolio/project signals in target domain (25%), profile visibility & professional presence (20%).\n\n"

                "7. 'top_skill_gaps': An array of 3-4 objects — gaps relative to the TARGET ROLE, not generic industry averages:\n"
                "   - 'skill': The missing skill name\n"
                "   - 'urgency': 'Critical', 'Moderate', or 'Low'\n"
                "   - 'reason': One sentence explaining exactly how this gap blocks entry into or advancement in their target domain\n\n"

                "Return ONLY valid JSON. No markdown code fences, no preamble, no trailing text."
            )

            user_prompt = (
                f"Candidate's Extracted Skills: {skills_str}\n\n"
                f"Candidate's Full Resume:\n{resume_text[:8000]}"
            )

            if self.client:
                response = self.client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=4500,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )

                response_text = response.content[0].text

                try:
                    clean_json = response_text
                    if "```json" in clean_json:
                        clean_json = clean_json.split("```json")[1].split("```")[0]
                    elif "```" in clean_json:
                        clean_json = clean_json.split("```")[1].split("```")[0]

                    parsed_response = json.loads(clean_json.strip())

                    feedback = parsed_response.get('feedback_text', 'No feedback provided.')
                    paths = parsed_response.get('career_paths', [])
                    certs = parsed_response.get('recommended_certifications', [])
                    profile_score = parsed_response.get('profile_score', 0)
                    top_skill_gaps = parsed_response.get('top_skill_gaps', [])
                    career_aspiration = parsed_response.get('career_aspiration', {})
                    transition_type = parsed_response.get('transition_type', 'Growth')

                    meta = {
                        'profile_score': profile_score,
                        'top_skill_gaps': top_skill_gaps,
                        'career_aspiration': career_aspiration,
                        'transition_type': transition_type,
                    }
                    feedback_with_meta = feedback + f"\n<!--advisor_meta:{json.dumps(meta)}-->"

                    self.job_repo.save_career_feedback(user_id, feedback_with_meta, paths, certs)

                    return {
                        "success": True,
                        "feedback_text": feedback,
                        "career_paths": paths,
                        "recommended_certifications": certs,
                        "profile_score": profile_score,
                        "top_skill_gaps": top_skill_gaps,
                        "career_aspiration": career_aspiration,
                        "transition_type": transition_type,
                    }

                except (json.JSONDecodeError, KeyError) as parse_error:
                    logger.error(f"Failed to parse Claude JSON response: {response_text}. Error: {str(parse_error)}")
                    return self._generate_mock_advice(skills, resume_text, user_id)
            else:
                return self._generate_mock_advice(skills, resume_text, user_id)

        except Exception as e:
            logger.error(f"Error in Claude Career Advisor: {str(e)}")
            return {"success": False, "error": str(e)}

    def parse_resume(self, raw_text: str) -> dict:
        """
        Uses Claude API to extract structured layout and complete list of skills
        (both explicit and contextually implied) from the raw resume text.
        
        Returns a dict:
        {
            "skills": [{"skill_name": str, "skill_type": str}, ...],
            "extracted_data": {
                "education": [str, ...],
                "experience": [str, ...],
                "certifications": [str, ...]
            }
        }
        """
        if not self.client:
            raise RuntimeError("Claude client is not initialized or API key is missing.")
            
        system_prompt = (
            "You are an expert ATS (Applicant Tracking System) parser. "
            "Analyze the candidate's resume text and extract:\n"
            "1. A comprehensive list of skills. Crucially, capture both explicitly mentioned skills "
            "and contextually implied skills (e.g., if they build Flask or Django apps, they have Python; "
            "if they build UI components with React, they have JavaScript and CSS; if they design schemas "
            "in PostgreSQL, they have SQL/Database Design). Categorize each skill as 'technical' or 'soft'.\n"
            "2. Structured section data:\n"
            "   - 'education': List degrees, schools, and years.\n"
            "   - 'experience': List jobs, companies, dates, and key projects/roles.\n"
            "   - 'certifications': List certifications, courses, or licenses.\n\n"
            "Provide the response in valid JSON format. Do not include any conversational filler, markdown formatting blocks, or surrounding text. "
            "The JSON object must contain exactly two keys:\n"
            "- 'skills': An array of objects, each with 'skill_name' (e.g., 'Python', 'React', 'Problem Solving') and 'skill_type' ('technical' or 'soft').\n"
            "- 'extracted_data': An object with arrays for 'education', 'experience', and 'certifications'.\n\n"
            "Example JSON response structure:\n"
            "{\n"
            "  \"skills\": [\n"
            "    {\"skill_name\": \"Python\", \"skill_type\": \"technical\"},\n"
            "    {\"skill_name\": \"Communication\", \"skill_type\": \"soft\"}\n"
            "  ],\n"
            "  \"extracted_data\": {\n"
            "    \"education\": [\"B.S. in Computer Science, Stanford University (2022)\"],\n"
            "    \"experience\": [\"Software Engineer at Google (2021-2022) - Built API pipelines...\"],\n"
            "    \"certifications\": [\"AWS Certified Solutions Architect\"]\n"
            "  }\n"
            "}"
        )
        
        user_prompt = f"Candidate Resume Text:\n{raw_text[:8000]}"
        
        # Use claude-3-haiku-20240307 for fast and cost-effective extraction
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            temperature=0.1,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response_text = response.content[0].text
        
        # Clean potential markdown block formatting wrapping the JSON
        clean_json = response_text
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0]
            
        parsed_response = json.loads(clean_json.strip())
        
        # Validation of structure
        if "skills" not in parsed_response or "extracted_data" not in parsed_response:
            raise KeyError("Response JSON is missing required keys 'skills' or 'extracted_data'.")
            
        return parsed_response

    def analyze_job_role_matches(self, resume_text: str, user_skills: list, job_roles_metadata: list) -> list:
        """
        Uses Claude to dynamically match the user's resume and skills to a list of job roles.
        Uses the ESCO taxonomy standard, categorizing required skills into:
        - Essential Skills (80% weight)
        - Optional Skills (20% weight)
        Calculates an ESCO-weighted match percentage.
        """
        if not self.client:
            raise RuntimeError("Claude client is not initialized.")

        # Convert metadata list to a simplified list of roles for prompt efficiency
        roles_input = [
            {
                "id": r["id"],
                "title": r["title"],
                "category": r["category"],
                "description": r["description"]
            }
            for r in job_roles_metadata
        ]

        system_prompt = (
            "You are a recruitment and talent matching AI engine aligned with the ESCO (European Skills, Competences, Qualifications and Occupations) classification standard.\n"
            "Your task is to analyze a candidate's resume and skills profile, and evaluate their fit for a set of standard job roles.\n"
            "For each job role, you must:\n"
            "1. Define the top modern standard skills required for this role today (2026/2027) and categorize them into:\n"
            "   - 'essential_skills': 4 to 6 core skills that are absolutely mandatory for the role.\n"
            "   - 'optional_skills': 2 to 4 supplementary, specialized, or transverse skills that are useful but not strictly mandatory.\n"
            "2. Evaluate which skills the candidate possesses (including contextually implied skills from their resume experience; e.g. Django implies Python, React implies JavaScript):\n"
            "   - 'matched_essential': Array of essential skills the candidate possesses.\n"
            "   - 'matched_optional': Array of optional skills the candidate possesses.\n"
            "3. Identify gaps:\n"
            "   - 'missing_essential': Array of essential skills they lack.\n"
            "   - 'missing_optional': Array of optional skills they lack.\n"
            "4. Calculate an ESCO-weighted match_percentage (0 to 100) using the formula:\n"
            "   Match % = (0.80 * (len(matched_essential) / len(essential_skills))) + (0.20 * (len(matched_optional) / len(optional_skills))) if optional_skills exists, otherwise 1.0 for optional portion.\n"
            "5. Determine if the role is 'related' to their skillset (true if match percentage is >= 20%).\n\n"
            "Provide the response in valid JSON format. The response must be a JSON object containing exactly one key:\n"
            "- 'role_matches': An array of objects, where each object has keys:\n"
            "  - 'id': The role's ID (matching the input ID exactly).\n"
            "  - 'essential_skills': Array of strings.\n"
            "  - 'optional_skills': Array of strings.\n"
            "  - 'matched_essential': Array of strings.\n"
            "  - 'matched_optional': Array of strings.\n"
            "  - 'missing_essential': Array of strings.\n"
            "  - 'missing_optional': Array of strings.\n"
            "  - 'match_percentage': Number (percentage 0-100, rounded to 1 decimal place).\n"
            "  - 'is_related': Boolean.\n\n"
            "Example JSON response structure:\n"
            "{\n"
            "  \"role_matches\": [\n"
            "    {\n"
            "      \"id\": \"software_engineer\",\n"
            "      \"essential_skills\": [\"Python\", \"REST APIs\", \"Docker\", \"Git\"],\n"
            "      \"optional_skills\": [\"AWS\", \"Kubernetes\"],\n"
            "      \"matched_essential\": [\"Python\", \"Git\"],\n"
            "      \"matched_optional\": [\"AWS\"],\n"
            "      \"missing_essential\": [\"REST APIs\", \"Docker\"],\n"
            "      \"missing_optional\": [\"Kubernetes\"],\n"
            "      \"match_percentage\": 60.0,\n"
            "      \"is_related\": true\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Candidate Skills: {', '.join(user_skills)}\n\n"
            f"Candidate Resume Text snippet:\n{resume_text[:6000]}\n\n"
            f"Target Job Roles:\n{json.dumps(roles_input, indent=2)}"
        )

        # Call Claude (fast, cost-effective Haiku model)
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            temperature=0.1,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        response_text = response.content[0].text
        
        # Parse JSON
        clean_json = response_text
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0]

        parsed = json.loads(clean_json.strip())
        return parsed.get("role_matches", [])

    def _generate_mock_advice(self, skills: list, resume_text: str, user_id: str) -> dict:
        """Generates high-quality mock career advice when Anthropic API is disabled."""
        skill_names = [s['skill_name'].lower() for s in skills]

        if any(s in skill_names for s in ['python', 'scikit-learn', 'pandas', 'numpy', 'machine learning']):
            feedback = (
                "### 🌟 Profile Summary\n"
                "Your resume highlights a strong foundation in **Data Science and Machine Learning**. "
                "With Python and analytics libraries (Pandas, NumPy, Scikit-learn), you are well-positioned for data engineering and junior ML roles. "
                "Your quantitative background is a genuine competitive advantage.\n\n"
                "### 🎯 Skill Gap Analysis\n"
                "- **Missing: MLOps / Model Serving** — 80%+ of ML Engineer roles now require experience deploying models via FastAPI, BentoML, or Triton.\n"
                "- **Missing: Cloud Platforms (AWS/GCP)** — Cloud-native ML pipelines (SageMaker, Vertex AI) are expected for any senior role.\n"
                "- **Missing: SQL / Data Warehousing** — Snowflake and BigQuery skills appear in 70% of data-focused job descriptions.\n\n"
                "### 📈 Areas of Improvement\n"
                "- Productionize at least one model end-to-end: training → Docker container → REST API → monitoring.\n"
                "- Add a Kaggle competition or open-source contribution to demonstrate applied ML skills.\n"
                "- Rewrite CV bullets using STAR format: 'Built X using Y, resulting in Z% improvement.'\n\n"
                "### 🗓️ 30/60/90 Day Action Plan\n"
                "**Month 1 (Quick Wins):**\n"
                "- Deploy one existing project as a public REST API on Render or Railway.\n"
                "- Sign up for AWS Free Tier and complete the SageMaker getting-started tutorial.\n"
                "- Update LinkedIn headline and About section.\n\n"
                "**Month 2 (Momentum):**\n"
                "- Build and publish an end-to-end ML project on GitHub with a detailed README.\n"
                "- Start the Google Cloud Professional Data Engineer certification prep.\n\n"
                "**Month 3 (Launch):**\n"
                "- Apply to 15-20 targeted roles with a tailored cover letter.\n"
                "- Reach out to 3 data engineers/scientists on LinkedIn for informational interviews.\n\n"
                "### 🚀 Strategic Guidance\n"
                "Target mid-size companies where a generalist data scientist can have outsized impact. "
                "Emphasize Python fluency and end-to-end ownership in interviews. "
                "Negotiate salary using competing offers — the ML market remains strong for specialists.\n\n"
                "### 💼 LinkedIn Optimization\n"
                "- **Headline:** \"Data Scientist | ML Engineer | Python · Scikit-learn · Cloud Analytics\"\n"
                "- **About opener:** 'I build data pipelines and machine learning systems that turn raw data into business decisions. Focused on end-to-end ownership from model training to production deployment.'\n"
                "- **Featured:** Pin your best deployed project with a live demo link.\n\n"
                "### 🎤 Interview Prep\n"
                "**Q: 'Tell me about a time you improved a model's performance.'**\n"
                "- Situation: Describe the baseline model and metric\n"
                "- Task: What you were asked to improve\n"
                "- Action: Feature engineering / hyperparameter tuning steps\n"
                "- Result: % improvement achieved\n"
            )
            paths = [
                {"title": "Machine Learning Engineer", "demand": "High", "salary_range": "$110k-$160k USD", "why_fit": "Strong Python and ML library foundation matches core requirements."},
                {"title": "Data Scientist (Cloud/MLOps)", "demand": "High", "salary_range": "$95k-$140k USD", "why_fit": "Analytics background translates directly to data science roles at tech companies."},
                {"title": "Business Intelligence Analyst", "demand": "Medium", "salary_range": "$75k-$105k USD", "why_fit": "Python + statistics skills are directly applicable to BI and analytics engineering."},
            ]
            certs = [
                {"name": "AWS Certified Machine Learning – Specialty", "platform": "AWS", "duration": "3-4 months", "priority": "High", "reason": "Most in-demand cloud ML cert; opens doors to senior ML Engineer roles."},
                {"name": "Google Cloud Professional Data Engineer", "platform": "Google Cloud", "duration": "2-3 months", "priority": "High", "reason": "GCP BigQuery and Dataflow skills are heavily requested in data pipelines roles."},
                {"name": "TensorFlow Developer Certificate", "platform": "Google / Coursera", "duration": "2 months", "priority": "Medium", "reason": "Validates deep learning skills and signals commitment to the ML specialization."},
            ]
            profile_score = 58
            top_skill_gaps = [
                {"skill": "MLOps / Model Deployment", "urgency": "Critical", "reason": "Required to move from junior data science to mid-level ML engineering roles."},
                {"skill": "Cloud Platforms (AWS or GCP)", "urgency": "Critical", "reason": "Cloud-native pipelines are expected for 85%+ of senior data/ML roles in 2026."},
                {"skill": "SQL & Data Warehousing", "urgency": "Moderate", "reason": "Snowflake/BigQuery appear in 70% of data-focused job descriptions."},
            ]
        elif any(s in skill_names for s in ['javascript', 'typescript', 'react', 'html', 'css', 'node.js']):
            feedback = (
                "### 🌟 Profile Summary\n"
                "You demonstrate strong capability in **Modern Web Development**. "
                "React/JavaScript skills with UI architecture experience match well with full-stack and frontend pathways. "
                "Your component-building experience is a genuine market asset.\n\n"
                "### 🎯 Skill Gap Analysis\n"
                "- **Missing: TypeScript** — TypeScript is now required in 80% of frontend roles at companies above 50 engineers.\n"
                "- **Missing: Testing (Jest / Cypress)** — Automated testing is a hiring bar for senior frontend positions.\n"
                "- **Missing: CI/CD Pipelines** — GitHub Actions or CircleCI experience signals production engineering maturity.\n\n"
                "### 📈 Areas of Improvement\n"
                "- Migrate an existing React project to TypeScript with strict mode enabled.\n"
                "- Add Jest unit tests and a Cypress E2E test suite to your portfolio project.\n"
                "- Add CI/CD pipeline configuration to your GitHub repos (build + test on PR).\n\n"
                "### 🗓️ 30/60/90 Day Action Plan\n"
                "**Month 1 (Quick Wins):**\n"
                "- Convert one React project to TypeScript.\n"
                "- Update LinkedIn headline and optimize featured section.\n"
                "- Write 5 Jest unit tests for an existing component.\n\n"
                "**Month 2 (Momentum):**\n"
                "- Build a full-stack project (React + Node.js + PostgreSQL) and deploy it.\n"
                "- Add GitHub Actions CI pipeline to your main portfolio repo.\n\n"
                "**Month 3 (Launch):**\n"
                "- Apply to 20 targeted frontend/full-stack roles.\n"
                "- Do 3 mock technical interviews on Pramp or interviewing.io.\n\n"
                "### 🚀 Strategic Guidance\n"
                "Target product companies over agencies for better comp and growth. "
                "Frame yourself as performance-focused: mention Core Web Vitals and accessibility in interviews. "
                "Salary negotiation tip: full-stack ability (even basic backend) commands a 15-20% premium over pure frontend.\n\n"
                "### 💼 LinkedIn Optimization\n"
                "- **Headline:** \"Frontend Engineer | React · TypeScript · Node.js | Building Fast, Accessible UIs\"\n"
                "- **About opener:** 'I craft high-performance web experiences using React and TypeScript, with a focus on component architecture, accessibility, and measurable Core Web Vitals improvements.'\n"
                "- **Featured:** Pin your best deployed app with screenshots and a GitHub link.\n\n"
                "### 🎤 Interview Prep\n"
                "**Q: 'How do you optimize React performance?'**\n"
                "- Mention: React.memo, useMemo, useCallback for unnecessary re-renders\n"
                "- Mention: Code splitting with React.lazy and dynamic imports\n"
                "- Mention: Profiler API to identify bottlenecks\n"
                "- Result: 'Reduced initial load time by 40% on a previous project'\n"
            )
            paths = [
                {"title": "Senior Frontend Engineer", "demand": "High", "salary_range": "$100k-$155k USD", "why_fit": "React and component architecture skills directly match senior frontend requirements."},
                {"title": "Full Stack Web Developer (MERN)", "demand": "High", "salary_range": "$90k-$135k USD", "why_fit": "JavaScript breadth enables full-stack roles with a minimal Node.js ramp-up."},
                {"title": "UX/UI Design Technologist", "demand": "Medium", "salary_range": "$80k-$115k USD", "why_fit": "Frontend skills combined with design sensibility open hybrid design-engineer roles."},
            ]
            certs = [
                {"name": "Meta Front-End Developer Professional Certificate", "platform": "Coursera", "duration": "7 months", "priority": "High", "reason": "Industry-recognized credential that validates React and modern frontend practices."},
                {"name": "AWS Certified Developer – Associate", "platform": "AWS", "duration": "2-3 months", "priority": "Medium", "reason": "Adds cloud deployment skills that command a 20% salary premium for frontend engineers."},
                {"name": "Certified ScrumMaster (CSM)", "platform": "Scrum Alliance", "duration": "1-2 weeks", "priority": "Low", "reason": "Agile certification valued at product companies hiring senior engineers."},
            ]
            profile_score = 62
            top_skill_gaps = [
                {"skill": "TypeScript", "urgency": "Critical", "reason": "Required in 80% of frontend roles at established tech companies in 2026."},
                {"skill": "Automated Testing (Jest/Cypress)", "urgency": "Critical", "reason": "Hard requirement for senior frontend positions at most product companies."},
                {"skill": "CI/CD Pipelines", "urgency": "Moderate", "reason": "Signals production maturity; commonly assessed in senior-level technical screens."},
            ]
        else:
            feedback = (
                "### 🌟 Profile Summary\n"
                "Your resume shows a versatile technical foundation. "
                "To maximize career trajectory, narrow your target to backend software engineering or cloud consulting where generalist skills translate to quick impact.\n\n"
                "### 🎯 Skill Gap Analysis\n"
                "- **Missing: REST API Development** — Flask/FastAPI or Express are baseline expectations for any backend role.\n"
                "- **Missing: Docker / Containerization** — Container skills appear in 75% of backend and DevOps job descriptions.\n"
                "- **Missing: Database Proficiency (SQL/NoSQL)** — PostgreSQL or MongoDB experience is expected for full-stack and backend roles.\n\n"
                "### 📈 Areas of Improvement\n"
                "- Build and deploy a REST API project — even a simple CRUD app shows real engineering discipline.\n"
                "- Add a Dockerfile and docker-compose.yml to your main GitHub project.\n"
                "- Rewrite CV bullets using STAR format with quantifiable outcomes.\n\n"
                "### 🗓️ 30/60/90 Day Action Plan\n"
                "**Month 1 (Quick Wins):**\n"
                "- Build a Flask or FastAPI REST API and deploy it to Render (free tier).\n"
                "- Update GitHub profile with a pinned repo showcase and filled-out README.\n"
                "- Update LinkedIn headline.\n\n"
                "**Month 2 (Momentum):**\n"
                "- Add Docker containerization to your project and push to Docker Hub.\n"
                "- Complete the Google IT Support or CompTIA A+ cert prep.\n\n"
                "**Month 3 (Launch):**\n"
                "- Apply to 20 junior backend or cloud support roles.\n"
                "- Attend one tech meetup or virtual networking event.\n\n"
                "### 🚀 Strategic Guidance\n"
                "Start by targeting companies that value versatility over deep specialization: startups, consultancies, and mid-size SaaS companies. "
                "Use your breadth as a selling point in interviews — you can contribute across the stack from day one.\n\n"
                "### 💼 LinkedIn Optimization\n"
                "- **Headline:** \"Software Developer | Backend APIs · Python · Cloud Infrastructure\"\n"
                "- **About opener:** 'I build backend systems and APIs that are reliable, testable, and easy to maintain. Comfortable working across the stack and contributing from day one in fast-moving teams.'\n"
                "- **Featured:** Pin your best GitHub project with a live link and clear README.\n\n"
                "### 🎤 Interview Prep\n"
                "**Q: 'Tell me about a challenging technical problem you solved.'**\n"
                "- Situation: Describe a real project obstacle\n"
                "- Task: What you were responsible for\n"
                "- Action: Specific debugging/design steps you took\n"
                "- Result: The outcome and what you learned\n"
            )
            paths = [
                {"title": "Backend Software Engineer", "demand": "High", "salary_range": "$85k-$125k USD", "why_fit": "General programming skills are foundational; Python/API experience accelerates backend ramp-up."},
                {"title": "Cloud Systems Administrator", "demand": "Medium", "salary_range": "$75k-$110k USD", "why_fit": "Technical breadth suits cloud ops and infrastructure support roles well."},
                {"title": "Technical Solutions Consultant", "demand": "Medium", "salary_range": "$80k-$120k USD", "why_fit": "Versatile technical profile matches consulting roles that bridge code and client communication."},
            ]
            certs = [
                {"name": "CompTIA Security+", "platform": "CompTIA", "duration": "2-3 months", "priority": "High", "reason": "Widely recognized cert that opens doors to cloud, IT, and security-adjacent roles."},
                {"name": "Google IT Support Professional Certificate", "platform": "Coursera", "duration": "3-4 months", "priority": "High", "reason": "Entry-level credential that demonstrates systems and networking fundamentals to employers."},
                {"name": "Python Institute PCEP Certification", "platform": "Python Institute", "duration": "1-2 months", "priority": "Medium", "reason": "Validates Python fundamentals for roles that list Python as a requirement."},
            ]
            profile_score = 42
            top_skill_gaps = [
                {"skill": "REST API Development", "urgency": "Critical", "reason": "Baseline expectation for any backend or full-stack engineering role."},
                {"skill": "Docker / Containerization", "urgency": "Critical", "reason": "Appears in 75% of backend job descriptions; required for most DevOps-adjacent roles."},
                {"skill": "SQL / Database Design", "urgency": "Moderate", "reason": "Database skills are expected for virtually all application-layer engineering roles."},
            ]

        meta_comment = f"\n<!--advisor_meta:{json.dumps({'profile_score': profile_score, 'top_skill_gaps': top_skill_gaps})}-->"
        self.job_repo.save_career_feedback(user_id, feedback + meta_comment, paths, certs)

        return {
            "success": True,
            "feedback_text": feedback,
            "career_paths": paths,
            "recommended_certifications": certs,
            "profile_score": profile_score,
            "top_skill_gaps": top_skill_gaps,
            "is_mock": True
        }
