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

                "CRUCIAL INSTRUCTION: The candidate may belong to ANY industry. DO NOT assume they are in IT/Software unless their resume explicitly shows tech skills. Provide strictly industry-specific advice (e.g., for a nurse, provide healthcare advice; for a marketer, marketing advice). If the CV is completely unrelated to IT, your entire response (career_paths, certs, gaps) MUST be exclusively about their specific non-IT industry.\n\n"

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
                "   - 'signals': An array of 2-3 short strings describing the specific resume evidence that led to this inference (e.g. '5 years of B2B sales experience', 'Degree in Nursing but took admin courses', 'Managed cross-functional projects')\n"
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
            "and contextually implied skills (e.g., if they manage ad campaigns, they have Digital Marketing; "
            "if they handled patient triage, they have Clinical Care; if they design UI with React, they have JavaScript). "
            "Categorize each skill as 'technical' (industry-specific hard skills) or 'soft' (interpersonal/general).\n"
            "2. Structured section data:\n"
            "   - 'education': List degrees, schools, and years.\n"
            "   - 'experience': List jobs, companies, dates, and key projects/roles.\n"
            "   - 'certifications': List certifications, courses, or licenses.\n\n"
            "Provide the response in valid JSON format. Do not include any conversational filler, markdown formatting blocks, or surrounding text. "
            "The JSON object must contain exactly two keys:\n"
            "- 'skills': An array of objects, each with 'skill_name' (e.g., 'Python', 'React', 'Problem Solving') and 'skill_type' ('technical' or 'soft').\n"
            "- 'extracted_data': An object with arrays for 'education', 'experience', and 'certifications'.\n\n"
            "CRITICAL: The candidate might be from ANY field (Healthcare, Marketing, Finance, Education, Engineering, etc.). Do NOT assume they are in IT/Software unless explicit tech skills are found. Extract skills relevant to their actual domain.\n\n"
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
            model="claude-haiku-4-5-20251001",
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
            "2. Evaluate which skills the candidate possesses (including contextually implied skills from their resume experience; e.g. SEO implies Digital Marketing, Triage implies Clinical Care, Django implies Python):\n"
            "   - 'matched_essential': Array of essential skills the candidate possesses.\n"
            "   - 'matched_optional': Array of optional skills the candidate possesses.\n"
            "3. Identify gaps:\n"
            "   - 'missing_essential': Array of essential skills they lack.\n"
            "   - 'missing_optional': Array of optional skills they lack.\n"
            "4. Calculate an ESCO-weighted match_percentage (0 to 100) using the formula:\n"
            "   Match % = (0.80 * (len(matched_essential) / len(essential_skills))) + (0.20 * (len(matched_optional) / len(optional_skills))) if optional_skills exists, otherwise 1.0 for optional portion.\n"
            "5. Determine if the role is 'related' to their skillset (true if match percentage is >= 20%).\n\n"
            "CRITICAL INSTRUCTION: The candidate might be from ANY industry (Healthcare, Finance, Marketing, Education, etc.). DO NOT artificially inflate match scores for IT/Software roles if the candidate lacks explicit IT skills. If the CV is non-IT, the IT roles MUST receive very low or 0% match scores. Evaluate all roles strictly based on their specific domain requirements.\n\n"
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
            "      \"id\": \"project_manager\",\n"
            "      \"essential_skills\": [\"Project Management\", \"Agile\", \"Communication\"],\n"
            "      \"optional_skills\": [\"Scrum\", \"Risk Management\"],\n"
            "      \"matched_essential\": [\"Project Management\", \"Communication\"],\n"
            "      \"matched_optional\": [\"Scrum\"],\n"
            "      \"missing_essential\": [\"Agile\"],\n"
            "      \"missing_optional\": [\"Risk Management\"],\n"
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
            model="claude-haiku-4-5-20251001",
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

        if any(s in skill_names for s in ['marketing', 'sales', 'seo', 'management', 'business', 'finance', 'accounting', 'hr', 'human resources']):
            feedback = (
                "### 🌟 Profile Summary\n"
                "Your resume highlights a strong foundation in **Business and Operations**. "
                "With skills in management and business strategy, you are well-positioned for roles in project management, marketing, or business analysis.\n\n"
                "### 🎯 Skill Gap Analysis\n"
                "- **Missing: Data Analytics** — Modern business roles increasingly require data-driven decision making (Excel, Power BI, or basic SQL).\n"
                "- **Missing: Agile/Scrum Methodologies** — Understanding agile workflows is essential for cross-functional management roles.\n"
                "- **Missing: CRM/ERP Systems** — Experience with Salesforce or SAP is often a baseline expectation.\n\n"
                "### 📈 Areas of Improvement\n"
                "- Master advanced Excel functions (Pivot Tables, VLOOKUP) and basic data visualization.\n"
                "- Gain familiarity with project management software like Jira, Asana, or Monday.com.\n"
                "- Rewrite CV bullets to focus on quantifiable business outcomes (e.g., 'Increased sales by X%', 'Reduced costs by Y%').\n\n"
                "### 🗓️ 30/60/90 Day Action Plan\n"
                "**Month 1 (Quick Wins):**\n"
                "- Complete a specialized course in Excel or Power BI.\n"
                "- Update your LinkedIn headline to target specific business domains.\n\n"
                "**Month 2 (Momentum):**\n"
                "- Obtain a foundational project management or agile certification.\n"
                "- Reach out to 3 professionals in your target industry for informational interviews.\n\n"
                "**Month 3 (Launch):**\n"
                "- Apply to 15-20 targeted roles tailoring your resume to the specific job description.\n"
                "- Practice behavioral interviews using the STAR method.\n\n"
                "### 🚀 Strategic Guidance\n"
                "Target roles where your communication and organizational skills can bridge the gap between technical teams and business stakeholders. "
                "Highlight your ability to manage projects and drive results.\n\n"
                "### 💼 LinkedIn Optimization\n"
                "- **Headline:** \"Business Analyst | Project Manager | Operations & Strategy\"\n"
                "- **About opener:** 'Results-driven professional with a passion for optimizing business operations and leading cross-functional teams to success.'\n"
                "- **Featured:** Link a case study, article, or business presentation you've created.\n\n"
                "### 🎤 Interview Prep\n"
                "**Q: 'Describe a time you improved a business process.'**\n"
                "- Situation: The inefficiency you noticed\n"
                "- Task: Your goal to streamline it\n"
                "- Action: The new process or tool you implemented\n"
                "- Result: Time or money saved\n"
            )
            paths = [
                {"title": "Business Analyst", "demand": "High", "salary_range": "$70k-$105k USD", "why_fit": "Your background aligns with analyzing processes and improving operations."},
                {"title": "Project Manager", "demand": "High", "salary_range": "$80k-$120k USD", "why_fit": "Strong organizational skills make you a good fit for leading projects."},
                {"title": "Digital Marketing Specialist", "demand": "Medium", "salary_range": "$60k-$90k USD", "why_fit": "Transferable communication skills are excellent for marketing roles."},
            ]
            certs = [
                {"name": "Project Management Professional (PMP)", "platform": "PMI", "duration": "3-6 months", "priority": "High", "reason": "The gold standard for project managers."},
                {"name": "Google Data Analytics Professional Certificate", "platform": "Coursera", "duration": "3-4 months", "priority": "Medium", "reason": "Adds highly sought-after analytical skills to your business profile."},
                {"name": "Salesforce Administrator", "platform": "Salesforce", "duration": "2 months", "priority": "Medium", "reason": "Validates proficiency with the world's leading CRM platform."},
            ]
            profile_score = 65
            top_skill_gaps = [
                {"skill": "Data Analytics (Excel/SQL)", "urgency": "Critical", "reason": "Essential for making data-driven business decisions."},
                {"skill": "Agile/Scrum", "urgency": "Moderate", "reason": "Many modern business teams operate on Agile frameworks."},
                {"skill": "CRM/ERP Software", "urgency": "Moderate", "reason": "Standard requirement for sales, marketing, and operations roles."},
            ]
            career_aspiration = {
                "target_role": "Business Operations Manager",
                "target_domain": "Business & Management",
                "confidence": "High",
                "signals": ["General business skills", "Management focus"],
                "aspiration_summary": "Looking to transition into a management or analytical business track."
            }
            transition_type = "Growth"
        elif any(s in skill_names for s in ['python', 'scikit-learn', 'pandas', 'numpy', 'machine learning']):
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
            career_aspiration = {
                "target_role": "Machine Learning Engineer",
                "target_domain": "AI & Data Science",
                "confidence": "High",
                "signals": ["Python and data libraries", "ML frameworks"],
                "aspiration_summary": "Aiming to build and deploy ML models."
            }
            transition_type = "Growth"
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
            career_aspiration = {
                "target_role": "Frontend/Full Stack Developer",
                "target_domain": "Software Engineering",
                "confidence": "High",
                "signals": ["React and JS skills", "UI component development"],
                "aspiration_summary": "Focusing on modern web development."
            }
            transition_type = "Growth"
        else:
            feedback = (
                "### 🌟 Profile Summary\n"
                "Your resume shows a versatile professional foundation. "
                "Because your background doesn't strictly align with standard tech profiles, your best path is identifying your core transferable skills (communication, organization, problem-solving) and targeting specific domains like operations, administration, or specialized industry roles.\n\n"
                "### 🎯 Skill Gap Analysis\n"
                "- **Missing: Industry-Specific Tools** — Every field has its standard software (e.g., EHR for Healthcare, AutoCAD for Engineering). Identify and learn yours.\n"
                "- **Missing: Quantifiable Achievements** — Generalist resumes often lack hard numbers. You need to prove impact.\n"
                "- **Missing: Clear Specialization** — Your profile may appear too broad. Employers hire for specific problems.\n\n"
                "### 📈 Areas of Improvement\n"
                "- Pinpoint ONE specific target job title and tailor your entire resume towards it.\n"
                "- Take a short certification course related to that specific job title to show commitment.\n"
                "- Rewrite CV bullets using the STAR format with clear, quantifiable outcomes.\n\n"
                "### 🗓️ 30/60/90 Day Action Plan\n"
                "**Month 1 (Quick Wins):**\n"
                "- Define your target industry and job title.\n"
                "- Update your LinkedIn headline to reflect this target, rather than your current status.\n\n"
                "**Month 2 (Momentum):**\n"
                "- Start a certification or training program highly valued in your target industry.\n"
                "- Connect with 5 professionals in your target field on LinkedIn.\n\n"
                "**Month 3 (Launch):**\n"
                "- Apply to 15-20 entry or mid-level roles in your new target domain.\n"
                "- Conduct mock interviews focusing on how your past experience transfers over.\n\n"
                "### 🚀 Strategic Guidance\n"
                "When your background is non-traditional, networking is more effective than cold applying. "
                "Focus on your adaptability and eagerness to learn. Craft a compelling narrative about *why* you are targeting this specific field.\n\n"
                "### 💼 LinkedIn Optimization\n"
                "- **Headline:** \"[Your Target Role] | Operations & Strategy | Problem Solver\"\n"
                "- **About opener:** 'Adaptable professional with a track record of driving results and streamlining processes. Passionate about transitioning my operational skills into [Target Industry].'\n"
                "- **Featured:** Highlight any major project, presentation, or certification.\n\n"
                "### 🎤 Interview Prep\n"
                "**Q: 'Why are you interested in this role given your different background?'**\n"
                "- Situation: Acknowledge your unique path\n"
                "- Task: Explain your underlying career motivation\n"
                "- Action: Highlight the specific transferable skills you bring\n"
                "- Result: Express how your fresh perspective will benefit their team\n"
            )
            paths = [
                {"title": "Operations Coordinator", "demand": "Medium", "salary_range": "$55k-$80k USD", "why_fit": "Your general professional skills make you highly adaptable for operational support."},
                {"title": "Customer Success Manager", "demand": "High", "salary_range": "$65k-$95k USD", "why_fit": "Communication and problem-solving skills are the core requirements here."},
                {"title": "Administrative Specialist", "demand": "Medium", "salary_range": "$45k-$70k USD", "why_fit": "Organizational skills and reliability are perfectly suited for this role."},
            ]
            certs = [
                {"name": "Microsoft Office Specialist (MOS)", "platform": "Microsoft", "duration": "1 month", "priority": "High", "reason": "Proves baseline professional competency in standard business software."},
                {"name": "Certified Associate in Project Management (CAPM)", "platform": "PMI", "duration": "2-3 months", "priority": "Medium", "reason": "Great entry-level project management certification."},
                {"name": "Google IT Support / Data Analytics", "platform": "Coursera", "duration": "3 months", "priority": "Low", "reason": "Can help bridge your general skills into a more specialized tech-adjacent role."},
            ]
            profile_score = 50
            top_skill_gaps = [
                {"skill": "Industry-Specific Software", "urgency": "Critical", "reason": "You need to know the basic tools used in your newly targeted industry."},
                {"skill": "Quantifiable Metrics", "urgency": "Moderate", "reason": "Generalist resumes often lack the numbers needed to stand out."},
                {"skill": "Domain Specialization", "urgency": "Moderate", "reason": "Employers look for specialists; you must frame your general skills as a specific solution."},
            ]
            career_aspiration = {
                "target_role": "General Professional",
                "target_domain": "Operations / Administration",
                "confidence": "Low",
                "signals": ["Generalist background", "No distinct tech focus"],
                "aspiration_summary": "Looking to leverage versatile skills into a structured operational role."
            }
            transition_type = "Pivot"

        meta_comment = f"\n<!--advisor_meta:{json.dumps({'profile_score': profile_score, 'top_skill_gaps': top_skill_gaps, 'career_aspiration': career_aspiration, 'transition_type': transition_type})}-->"
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

    def generate_cover_letter(self, user_id: str, job_title: str, company_name: str, job_description: str) -> dict:
        """
        Generates a highly tailored cover letter using the candidate's resume and the target job description.
        """
        try:
            resume = self.resume_repo.get_latest_resume(user_id)
            if not resume:
                return {"success": False, "error": "No resume found. Please upload a CV first."}

            resume_text = resume.get('raw_text', '')

            system_prompt = (
                "You are an expert Career Coach and Executive Copywriter. "
                "Your task is to write a premium, compelling, professional, and ATS-friendly cover letter. "
                "Align the candidate's experience directly with the job description and company focus. "
                "Do not invent facts or experiences that are not supported by the resume. "
                "Produce a polished cover letter with a strong opening, value-driven body paragraphs, a company-fit paragraph, and a confident closing. "
                "Write the letter as a one-page document, approximately 250-320 words. "
                "Use precise, executive language, quantify achievements where possible, and keep the final output readable and well-structured. "
                "Format the response as a clean text document with standard cover letter structure: Header, Salutation, Body, Conclusion, Sign-off. "
                "Highlight 2-3 key achievements from the resume that align closely with the target role."
            )

            user_prompt = (
                f"Target Job Title: {job_title}\n"
                f"Target Company: {company_name}\n"
                f"Job Description: {job_description}\n\n"
                f"Candidate's Resume:\n{resume_text[:6000]}\n\n"
                "Please generate the tailored cover letter."
            )

            if self.client:
                response = self.client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1500,
                    temperature=0.4,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return {"success": True, "cover_letter": response.content[0].text}
            else:
                # Mock Cover letter if API is disabled
                return {
                    "success": True,
                    "cover_letter": f"Dear Hiring Manager at {company_name},\n\nI am writing to express my strong interest in the {job_title} position...\n\n[Please enable Anthropic API to generate full AI cover letter]"
                }
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return {"success": False, "error": str(e)}
