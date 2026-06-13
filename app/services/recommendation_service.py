import logging
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)

# Predefined Course Recommendations mapping for common skills
COURSE_CATALOG = {
    "Python": [
        {"name": "Python for Everybody Specialization", "platform": "Coursera", "url": "https://www.coursera.org/specializations/python"},
        {"name": "Complete Python Bootcamp", "platform": "Udemy", "url": "https://www.udemy.com/course/complete-python-bootcamp/"}
    ],
    "SQL": [
        {"name": "SQL for Data Science", "platform": "Coursera", "url": "https://www.coursera.org/learn/sql-for-data-science"},
        {"name": "The Complete SQL Bootcamp", "platform": "Udemy", "url": "https://www.udemy.com/course/the-complete-sql-bootcamp/"}
    ],
    "Tableau": [
        {"name": "Data Visualization with Tableau", "platform": "Coursera", "url": "https://www.coursera.org/specializations/data-visualization-tableau"},
        {"name": "Tableau 2024 A-Z", "platform": "Udemy", "url": "https://www.udemy.com/course/tableau10/"}
    ],
    "Power BI": [
        {"name": "Microsoft Power BI Data Analyst Professional Certificate", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/microsoft-power-bi-data-analyst"},
        {"name": "Microsoft Power BI - Up & Running With Power BI Desktop", "platform": "Udemy", "url": "https://www.udemy.com/course/power-bi-complete-introduction/"}
    ],
    "Machine Learning": [
        {"name": "Supervised Machine Learning: Regression and Classification", "platform": "Coursera", "url": "https://www.coursera.org/learn/machine-learning"},
        {"name": "Python for Data Science and Machine Learning Bootcamp", "platform": "Udemy", "url": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/"}
    ],
    "Scikit-learn": [
        {"name": "Machine Learning with Python", "platform": "Coursera", "url": "https://www.coursera.org/learn/machine-learning-with-python"},
        {"name": "Hands-On Machine Learning with Scikit-Learn", "platform": "O'Reilly", "url": "https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032631/"}
    ],
    "Docker": [
        {"name": "Docker and Kubernetes: The Complete Guide", "platform": "Udemy", "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/"},
        {"name": "Getting Started with Docker", "platform": "Pluralsight", "url": "https://www.pluralsight.com/courses/docker-getting-started"}
    ],
    "Flask": [
        {"name": "Python and Flask Bootcamp", "platform": "Udemy", "url": "https://www.udemy.com/course/python-and-flask-bootcamp-create-websites-using-flask/"},
        {"name": "REST APIs with Flask and Python", "platform": "Udemy", "url": "https://www.udemy.com/course/rest-api-flask-and-python/"}
    ],
    "PostgreSQL": [
        {"name": "PostgreSQL Boot Camp", "platform": "Udemy", "url": "https://www.udemy.com/course/postgresql-bootcamp/"},
        {"name": "SQL and PostgreSQL: The Complete Developer's Guide", "platform": "Udemy", "url": "https://www.udemy.com/course/coding-with-postgresql/"}
    ],
    "HTML": [
        {"name": "HTML, CSS, and Javascript for Web Developers", "platform": "Coursera", "url": "https://www.coursera.org/learn/html-css-javascript-for-web-developers"}
    ],
    "CSS": [
        {"name": "CSS - The Complete Guide (incl. Flexbox, Grid & Sass)", "platform": "Udemy", "url": "https://www.udemy.com/course/css-the-complete-guide-incl-flexbox-grid-sass/"}
    ],
    "JavaScript": [
        {"name": "The Complete JavaScript Course: From Zero to Expert", "platform": "Udemy", "url": "https://www.udemy.com/course/the-complete-javascript-course-for-beginners/"}
    ],
    "Git": [
        {"name": "Version Control with Git", "platform": "Coursera", "url": "https://www.coursera.org/learn/version-control-with-git"}
    ],
    "Claude API": [
        {"name": "Anthropic Claude API Fundamentals", "platform": "Anthropic Documentation", "url": "https://docs.anthropic.com/en/docs/welcome"},
        {"name": "Prompt Engineering for ChatGPT and LLMs", "platform": "Coursera", "url": "https://www.coursera.org/learn/prompt-engineering"}
    ]
}

SYNONYM_GROUPS = [
    {"react", "react.js", "reactjs", "react native"},
    {"node", "node.js", "nodejs", "express", "express.js"},
    {"next.js", "nextjs", "next"},
    {"vue", "vue.js", "vuejs"},
    {"angular", "angular.js", "angularjs"},
    {"gcp", "google cloud", "google cloud platform"},
    {"aws", "amazon web services", "ec2", "s3", "lambda"},
    {"azure", "microsoft azure", "azure cloud"},
    {"ci/cd", "cicd", "continuous integration", "continuous deployment", "jenkins", "github actions", "gitlab ci"},
    {"nlp", "natural language processing", "text processing", "text analytics"},
    {"ml", "machine learning", "deep learning", "neural networks", "scikit-learn", "pytorch", "tensorflow", "keras"},
    {"ai", "artificial intelligence", "llm", "large language models", "generative ai", "claude api", "openai", "chatgpt"},
    {"postgres", "postgresql"},
    {"mongodb", "mongo", "mongodb"},
    {"api", "apis", "rest api", "rest apis", "restful api", "restful apis", "graphql", "grpc"},
    {"git", "github", "gitlab", "version control"},
    {"css", "css3", "tailwind", "tailwind css", "tailwindcss", "bootstrap", "sass", "scss", "less"},
    {"html", "html5"},
    {"docker", "kubernetes", "k8s", "containers"},
    {"hr", "human resources", "talent acquisition", "recruiting"},
    {"seo", "search engine optimization"},
    {"ux", "ui", "user experience", "user interface", "ui/ux"},
    {"pm", "project management", "project manager"}
]

IMPLICATIONS = {
    "python": ["django", "flask", "fastapi", "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow", "keras", "seaborn", "matplotlib", "jupyter"],
    "sql": ["postgresql", "postgres", "mysql", "sqlite", "oracle", "mariadb", "mssql", "sql server", "pl/sql", "t-sql", "database design", "database administration"],
    "javascript": ["typescript", "react", "react.js", "reactjs", "next.js", "nextjs", "node.js", "nodejs", "express", "vue", "vue.js", "vuejs", "angular", "angularjs", "jquery"],
    "css": ["tailwind", "tailwindcss", "bootstrap", "sass", "scss", "less"],
    "machine learning": ["scikit-learn", "pytorch", "tensorflow", "keras", "deep learning", "nlp", "natural language processing", "computer vision", "reinforcement learning", "data science"],
    "devops": ["docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible", "aws", "gcp", "azure", "kubernetes", "github actions"],
    "marketing": ["seo", "social media", "content writing", "email marketing", "google ads", "digital marketing"],
    "finance": ["accounting", "financial modeling", "excel", "auditing", "tax compliance"],
    "design": ["figma", "adobe photoshop", "adobe illustrator", "ui/ux", "graphic design"],
    "human resources": ["recruitment", "talent acquisition", "employee relations", "onboarding"]
}

class RecommendationService:
    """Service handling ML ranking, cosine similarity calculations, and skill gaps parsing."""

    def __init__(self):
        self.job_repo = JobRepository()
        self.resume_repo = ResumeRepository()

    def _check_skill_match(self, req: str, student_skills: list) -> bool:
        """
        Check if a job requirement is met by any of the candidate's skills.
        Matches using exact match, cleaned string match, substring match,
        synonyms, and hierarchical implications.
        """
        req_lower = req.lower().strip()
        
        # 1. Direct or cleaned string match
        req_clean = re.sub(r'[^a-z0-9\+\#\.]', '', req_lower)
        for skill in student_skills:
            skill_lower = skill.lower().strip()
            skill_clean = re.sub(r'[^a-z0-9\+\#\.]', '', skill_lower)
            if req_clean == skill_clean or req_lower == skill_lower:
                return True
                
            # 2. Substring/Superstring matching for longer skills (avoid matching 'go' or 'r')
            if len(req_clean) >= 3 and len(skill_clean) >= 3:
                if req_clean in skill_clean or skill_clean in req_clean:
                    return True
                    
        # 3. Synonym matching
        for group in SYNONYM_GROUPS:
            if req_lower in group:
                for skill in student_skills:
                    if skill.lower().strip() in group:
                        return True
                        
        # 4. Implication mapping (if req is parent, e.g. Python, and user has child e.g. Django)
        for parent, children in IMPLICATIONS.items():
            if req_lower == parent:
                for skill in student_skills:
                    if skill.lower().strip() in children:
                        return True
                        
        return False

    def generate_recommendations_for_user(self, user_id: str):
        """
        Runs the recommendation pipeline for a user:
        1. Fetch user's latest resume and skills.
        2. Fetch all jobs.
        3. Perform TF-IDF Cosine Similarity on job descriptions vs resume text.
        4. Match skills explicitly to calculate matching percentage.
        5. Combine these metrics to rank job recommendations.
        6. Calculate and save the skill gaps for each job.
        7. Save the recommendations to public.recommendations database.
        """
        try:
            resume = self.resume_repo.get_latest_resume(user_id)
            if not resume:
                logger.warning(f"No resume found for user {user_id}. Cannot run recommendations.")
                return []

            skills_list = self.resume_repo.get_skills_by_user(user_id)
            student_skills = [s['skill_name'].lower() for s in skills_list]
            
            jobs = self.job_repo.get_all_jobs()
            if not jobs:
                logger.info("No jobs found in the database.")
                return []

            # 1. Calculate Cosine Similarity using TF-IDF
            resume_text = resume.get('raw_text', '')
            job_descriptions = [job.get('description', '') + " " + " ".join(str(r) for r in self._get_job_requirements(job)) for job in jobs]
            
            # Combine resume and jobs for fitting Tfidf
            corpus = [resume_text] + job_descriptions
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            # Vector 0 is the resume, vectors 1 to N are the jobs
            resume_vector = tfidf_matrix[0:1]
            jobs_vectors = tfidf_matrix[1:]
            
            cosine_similarities = cosine_similarity(resume_vector, jobs_vectors)[0]

            recommendation_payloads = []
            
            for index, job in enumerate(jobs):
                job_id = job['id']
                job_reqs = self._get_job_requirements(job)
                job_reqs_lower = [req.lower() for req in job_reqs]
                
                # 2. Skill Match calculation
                matched_skills = []
                missing_skills = []
                
                for req in job_reqs:
                    if self._check_skill_match(req, student_skills):
                        matched_skills.append(req)
                    else:
                        missing_skills.append(req)
                        
                skill_match_ratio = len(matched_skills) / len(job_reqs) if job_reqs else 1.0
                
                # 3. Combine TF-IDF Cosine Similarity and Skill Matching
                # Cosine Similarity is normalized 0 to 1
                cos_sim = float(cosine_similarities[index])
                
                # Final score: 60% Skill Match + 40% Text Context Similarity
                final_score = (0.6 * skill_match_ratio) + (0.4 * cos_sim)
                match_percentage = round(final_score * 100, 2)
                
                recommendation_payloads.append({
                    'job_id': job_id,
                    'match_percentage': match_percentage,
                    'missing_skills': missing_skills,
                    'job_title': job['title'],
                    'company': job['company'],
                    'location': job['location'],
                    'job_type': job['job_type']
                })
            
            # Sort recommendations descending by match percentage
            recommendation_payloads.sort(key=lambda x: x['match_percentage'], reverse=True)
            
            # Write to database (public.recommendations and public.skill_gaps)
            db_recommendations = []
            for ranking, rec in enumerate(recommendation_payloads, 1):
                db_recommendations.append({
                    'user_id': user_id,
                    'job_id': rec['job_id'],
                    'match_percentage': rec['match_percentage'],
                    'ranking': ranking
                })
                
                # Generate suggested courses for missing skills
                courses = []
                for missing in rec['missing_skills']:
                    # Look up in local course dictionary. Check matching ignoring case
                    found = False
                    for key, course_list in COURSE_CATALOG.items():
                        if key.lower() == missing.lower():
                            courses.extend(course_list)
                            found = True
                            break
                    if not found:
                        courses.append({
                            "name": f"Mastering {missing} from scratch",
                            "platform": "Coursera / Udemy",
                            "url": f"https://www.google.com/search?q={missing}+online+course"
                        })
                
                # Limit course recommendations to max 5 to avoid overloading
                self.job_repo.save_skill_gap(user_id, rec['job_id'], rec['missing_skills'], courses[:5])
                
            self.job_repo.save_recommendations(user_id, db_recommendations)
            return recommendation_payloads
            
        except Exception as e:
            logger.error(f"Error during recommendation pipeline generation for {user_id}: {str(e)}", exc_info=True)
            raise

    def _get_job_requirements(self, job: dict) -> list:
        """Parse job requirements JSON/array safely."""
        reqs = job.get('requirements', [])
        if isinstance(reqs, str):
            try:
                return json.loads(reqs)
            except Exception:
                return [reqs]
        elif isinstance(reqs, list):
            return reqs
        return []
