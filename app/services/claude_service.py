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
            
            # Format Prompt
            system_prompt = (
                "You are an expert Senior Career Advisor and Full Stack Architect. "
                "Analyze the user's CV and skill profile. "
                "Provide detailed, high-impact career advice in valid JSON format. "
                "The JSON object must contain exactly three keys:\n"
                "1. 'feedback_text': A highly detailed, thorough, and in-depth Markdown document (at least 450-650 words) with bullet points, bold key terms, and the following subheadings:\n"
                "   - '### 🌟 Profile Summary': Provide a comprehensive analysis of their top strengths, hybrid value proposition, and unique competitive advantages.\n"
                "   - '### 📈 Areas of Improvement': Detail critical gaps in their experience, specific frameworks/tools they should master, portfolio projects they should build, and how to improve their CV bullet points.\n"
                "   - '### 🚀 Strategic Guidance': Provide actionable guidance on how to package and position their profile in the current job market, interview preparation advice, and strategic career roadmap details.\n"
                "2. 'career_paths': An array of 3 recommended job/career pathways.\n"
                "3. 'recommended_certifications': An array of 3 professional certifications or courses that will maximize their chances of employment.\n\n"
                "Crucial: Avoid brief summaries. Provide comprehensive, extensive, and actionable paragraphs under each heading, using bolding (**text**) and bullet lists extensively so it renders beautifully.\n\n"
                "Example JSON response structure:\n"
                "{\n"
                "  \"feedback_text\": \"### 🌟 Profile Summary\\nYour profile is...\\n\\n### 📈 Areas of Improvement\\n- **Specialization**: ...\",\n"
                "  \"career_paths\": [\"Role A\", \"Role B\", \"Role C\"],\n"
                "  \"recommended_certifications\": [\"Cert A\", \"Cert B\", \"Cert C\"]\n"
                "}"
            )
            
            user_prompt = (
                f"Candidate Skills: {skills_str}\n\n"
                f"Candidate Resume Text snippet:\n{resume_text[:8000]}"
            )
            
            if self.client:
                # Call Claude API (using claude-3-haiku-20240307 for fast and cost-effective recommendation logic)
                response = self.client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=3000,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                response_text = response.content[0].text
                
                try:
                    # Parse the JSON output from Claude
                    # Sometimes LLMs wrap response in ```json ``` blocks. Clean it up.
                    clean_json = response_text
                    if "```json" in clean_json:
                        clean_json = clean_json.split("```json")[1].split("```")[0]
                    elif "```" in clean_json:
                        clean_json = clean_json.split("```")[1].split("```")[0]
                        
                    parsed_response = json.loads(clean_json.strip())
                    
                    feedback = parsed_response.get('feedback_text', 'No feedback provided.')
                    paths = parsed_response.get('career_paths', [])
                    certs = parsed_response.get('recommended_certifications', [])
                    
                    # Store feedback in database
                    self.job_repo.save_career_feedback(user_id, feedback, paths, certs)
                    
                    return {
                        "success": True,
                        "feedback_text": feedback,
                        "career_paths": paths,
                        "recommended_certifications": certs
                    }
                    
                except (json.JSONDecodeError, KeyError) as parse_error:
                    logger.error(f"Failed to parse Claude JSON response: {response_text}. Error: {str(parse_error)}")
                    # Fallback if JSON parsing fails but we got text
                    return self._generate_mock_advice(skills, resume_text, user_id)
            else:
                # Fallback to local mock generator
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
        
        # Simple heuristic analysis
        if any(s in skill_names for s in ['python', 'scikit-learn', 'pandas', 'numpy', 'machine learning']):
            feedback = (
                "### Profile Assessment\n"
                "Your resume highlights a strong foundation in **Data Science and Machine Learning**. "
                "With python skills and analytics libraries (Pandas, NumPy, Scikit-learn), you are well-positioned for data engineering and junior ML roles.\n\n"
                "### Areas of Improvement\n"
                "To stand out in the current job market, you should expand your depth in cloud architectures (AWS/GCP deployment patterns) "
                "and deep learning packages. Make sure your portfolio projects include productionizing models, not just running Jupyter notebooks."
            )
            paths = ["Data Scientist", "Machine Learning Engineer", "Business Intelligence Analyst"]
            certs = ["AWS Certified Machine Learning - Specialty", "Google Cloud Professional Data Engineer", "TensorFlow Developer Certificate"]
        elif any(s in skill_names for s in ['javascript', 'typescript', 'react', 'html', 'css', 'node.js']):
            feedback = (
                "### Profile Assessment\n"
                "You demonstrate strong capability in **Modern Web Development**. "
                "Your skills with UI design, React/JavaScript, and front-end architectures match well with full-stack and frontend development pathways.\n\n"
                "### Areas of Improvement\n"
                "We recommend mastering state-management patterns (Redux/Zustand) and backend integration with SQL databases. "
                "Adding CI/CD pipeline automation to your github repositories will show hiring managers that you understand engineering lifecycle practices."
            )
            paths = ["Frontend Engineer", "Full Stack Developer", "UX/UI Engineer"]
            certs = ["Meta Front-End Developer Professional Certificate", "AWS Certified Developer", "Certified ScrumMaster (CSM)"]
        else:
            feedback = (
                "### Profile Assessment\n"
                "Your resume shows a versatile academic and technical foundation. "
                "To optimize your career trajectory, we recommend narrowing your target roles to backend software engineering or technology consulting.\n\n"
                "### Areas of Improvement\n"
                "Develop clean API programming skills (Flask/FastAPI) and version control proficiency. "
                "Ensure your CV includes active GitHub links showcasing complete projects with comprehensive README files."
            )
            paths = ["Junior Software Developer", "Systems Administrator", "IT Support Specialist"]
            certs = ["CompTIA Security+", "Google IT Support Professional Certificate", "Python Institute PCEP Certification"]

        # Store feedback in database
        self.job_repo.save_career_feedback(user_id, feedback, paths, certs)

        return {
            "success": True,
            "feedback_text": feedback,
            "career_paths": paths,
            "recommended_certifications": certs,
            "is_mock": True
        }
