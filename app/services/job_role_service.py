import logging
from app.services.claude_service import ClaudeService
from app.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)
claude_service = ClaudeService()
resume_repo = ResumeRepository()

JOB_ROLES = [
    # ── IT & Software Development ──────────────────────────────────────────────
    {
        "id": "software_engineer",
        "title": "Software Engineer (Backend)",
        "category": "IT & Software",
        "icon": "fa-server",
        "color": "primary",
        "description": "Develop scalable backend services, APIs, and business logic for software applications.",
        "required_skills": ["Python", "SQL", "REST APIs", "Git", "Docker", "PostgreSQL", "OOP", "Problem Solving"],
        "core_skills": ["Python", "REST APIs", "Git"]
    },
    {
        "id": "full_stack_developer",
        "title": "Full Stack Developer",
        "category": "IT & Software",
        "icon": "fa-layer-group",
        "color": "primary",
        "description": "Build complete web applications handling both frontend UI and backend logic.",
        "required_skills": ["Python", "JavaScript", "HTML", "CSS", "Flask", "SQL", "Git", "Bootstrap", "REST APIs"],
        "core_skills": ["Python", "JavaScript", "HTML"]
    },
    {
        "id": "frontend_developer",
        "title": "Frontend Developer",
        "category": "IT & Software",
        "icon": "fa-desktop",
        "color": "info",
        "description": "Create visually engaging and responsive user interfaces for web applications.",
        "required_skills": ["JavaScript", "HTML", "CSS", "React", "Bootstrap", "Git", "UI/UX", "Responsive Design"],
        "core_skills": ["JavaScript", "HTML", "CSS"]
    },
    {
        "id": "mobile_developer",
        "title": "Mobile App Developer",
        "category": "IT & Software",
        "icon": "fa-mobile-screen",
        "color": "success",
        "description": "Build native or cross-platform mobile applications for iOS and Android.",
        "required_skills": ["Flutter", "Dart", "React Native", "JavaScript", "REST APIs", "Git", "UI/UX"],
        "core_skills": ["Flutter", "React Native", "JavaScript"]
    },
    {
        "id": "qa_engineer",
        "title": "QA / Test Engineer",
        "category": "IT & Software",
        "icon": "fa-bug",
        "color": "warning",
        "description": "Ensure software quality through automated and manual testing strategies.",
        "required_skills": ["Python", "Selenium", "Testing", "Git", "Bug Tracking", "REST APIs", "Communication", "Problem Solving"],
        "core_skills": ["Python", "Selenium", "Testing"]
    },
    {
        "id": "systems_analyst",
        "title": "Systems Analyst",
        "category": "IT & Software",
        "icon": "fa-sitemap",
        "color": "secondary",
        "description": "Analyse and improve IT systems, bridging the gap between business needs and technology.",
        "required_skills": ["System Design", "SQL", "Documentation", "Communication", "Problem Solving", "UML", "Business Analysis"],
        "core_skills": ["System Design", "SQL", "Business Analysis"]
    },
    {
        "id": "it_support",
        "title": "IT Support Specialist",
        "category": "IT & Software",
        "icon": "fa-headset",
        "color": "info",
        "description": "Provide technical support, troubleshoot hardware/software issues, and assist end users.",
        "required_skills": ["Troubleshooting", "Networking", "Windows", "Linux", "Communication", "Hardware", "Ticketing Systems"],
        "core_skills": ["Troubleshooting", "Networking", "Communication"]
    },

    # ── Data & Analytics ──────────────────────────────────────────────────────
    {
        "id": "data_analyst",
        "title": "Data Analyst",
        "category": "Data & Analytics",
        "icon": "fa-chart-bar",
        "color": "primary",
        "description": "Analyse complex datasets to extract insights and support business decisions.",
        "required_skills": ["Python", "SQL", "Excel", "Tableau", "Power BI", "Statistics", "Data Visualization", "Communication"],
        "core_skills": ["Python", "SQL", "Excel"]
    },
    {
        "id": "data_scientist",
        "title": "Data Scientist",
        "category": "Data & Analytics",
        "icon": "fa-flask",
        "color": "info",
        "description": "Build predictive models and apply statistical methods to solve real-world problems.",
        "required_skills": ["Python", "R", "SQL", "Machine Learning", "Statistics", "Data Visualization", "NumPy", "Pandas"],
        "core_skills": ["Python", "Machine Learning", "Statistics"]
    },
    {
        "id": "data_engineer",
        "title": "Data Engineer",
        "category": "Data & Analytics",
        "icon": "fa-database",
        "color": "warning",
        "description": "Design and build data pipelines and infrastructure for large-scale data processing.",
        "required_skills": ["Python", "SQL", "Apache Spark", "ETL", "Docker", "Cloud", "PostgreSQL", "Data Pipeline"],
        "core_skills": ["Python", "SQL", "ETL"]
    },
    {
        "id": "bi_developer",
        "title": "Business Intelligence Developer",
        "category": "Data & Analytics",
        "icon": "fa-chart-pie",
        "color": "success",
        "description": "Build dashboards and reporting systems to transform raw data into actionable insights.",
        "required_skills": ["SQL", "Tableau", "Power BI", "Data Modeling", "Excel", "ETL", "Communication"],
        "core_skills": ["SQL", "Tableau", "Power BI"]
    },
    {
        "id": "database_admin",
        "title": "Database Administrator",
        "category": "Data & Analytics",
        "icon": "fa-hard-drive",
        "color": "secondary",
        "description": "Manage, optimise, and secure relational and non-relational database systems.",
        "required_skills": ["SQL", "PostgreSQL", "MySQL", "Database Design", "Backup/Recovery", "Performance Tuning", "Linux"],
        "core_skills": ["SQL", "PostgreSQL", "Database Design"]
    },

    # ── AI & Machine Learning ─────────────────────────────────────────────────
    {
        "id": "ml_engineer",
        "title": "Machine Learning Engineer",
        "category": "AI & Machine Learning",
        "icon": "fa-brain",
        "color": "danger",
        "description": "Design, train, and deploy machine learning models in production environments.",
        "required_skills": ["Python", "Scikit-learn", "TensorFlow", "PyTorch", "NLP", "SQL", "Statistics", "Linear Algebra", "Git"],
        "core_skills": ["Python", "Scikit-learn", "Machine Learning"]
    },
    {
        "id": "ai_engineer",
        "title": "AI Product Engineer",
        "category": "AI & Machine Learning",
        "icon": "fa-robot",
        "color": "primary",
        "description": "Integrate Large Language Models and AI tools into real-world product features.",
        "required_skills": ["Python", "Claude API", "LLMs", "JSON Parsing", "REST APIs", "Git", "Prompt Engineering", "Docker"],
        "core_skills": ["Python", "LLMs", "REST APIs"]
    },
    {
        "id": "nlp_engineer",
        "title": "NLP Engineer",
        "category": "AI & Machine Learning",
        "icon": "fa-comment-dots",
        "color": "success",
        "description": "Develop natural language processing systems for text classification, extraction, and generation.",
        "required_skills": ["Python", "NLP", "Scikit-learn", "PyTorch", "spaCy", "NLTK", "Machine Learning", "Statistics"],
        "core_skills": ["Python", "NLP", "Machine Learning"]
    },
    {
        "id": "research_engineer",
        "title": "AI Research Engineer",
        "category": "AI & Machine Learning",
        "icon": "fa-microscope",
        "color": "info",
        "description": "Advance the state of the art in AI/ML through original research and experimentation.",
        "required_skills": ["Python", "PyTorch", "TensorFlow", "Research", "Deep Learning", "Mathematics", "NLP", "Academic Writing"],
        "core_skills": ["Python", "Deep Learning", "Research"]
    },

    # ── Infrastructure & Cloud ────────────────────────────────────────────────
    {
        "id": "devops_engineer",
        "title": "DevOps Engineer",
        "category": "Infrastructure & Cloud",
        "icon": "fa-gears",
        "color": "warning",
        "description": "Automate deployment pipelines, manage cloud infrastructure, and ensure system reliability.",
        "required_skills": ["Docker", "Kubernetes", "CI/CD", "Linux", "Git", "Cloud", "Scripting", "Networking"],
        "core_skills": ["Docker", "Linux", "Git"]
    },
    {
        "id": "cloud_engineer",
        "title": "Cloud Engineer",
        "category": "Infrastructure & Cloud",
        "icon": "fa-cloud",
        "color": "info",
        "description": "Design, deploy, and manage cloud-based infrastructure and services.",
        "required_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux", "Networking", "Python", "CI/CD"],
        "core_skills": ["AWS", "Docker", "Linux"]
    },
    {
        "id": "network_engineer",
        "title": "Network Engineer",
        "category": "Infrastructure & Cloud",
        "icon": "fa-network-wired",
        "color": "primary",
        "description": "Design, implement, and maintain computer networks for organisations.",
        "required_skills": ["Networking", "Cisco", "Routing & Switching", "Firewall", "Linux", "TCP/IP", "VPN", "Troubleshooting"],
        "core_skills": ["Networking", "TCP/IP", "Routing & Switching"]
    },

    # ── Cybersecurity ─────────────────────────────────────────────────────────
    {
        "id": "cybersecurity_analyst",
        "title": "Cybersecurity Analyst",
        "category": "Cybersecurity",
        "icon": "fa-shield-halved",
        "color": "danger",
        "description": "Protect systems and networks from cyber threats through monitoring and incident response.",
        "required_skills": ["Networking", "Linux", "Python", "Risk Assessment", "Security Tools", "Incident Response", "SIEM", "Cryptography"],
        "core_skills": ["Networking", "Linux", "Security Tools"]
    },
    {
        "id": "penetration_tester",
        "title": "Penetration Tester",
        "category": "Cybersecurity",
        "icon": "fa-user-secret",
        "color": "danger",
        "description": "Conduct authorised simulated attacks to identify and report security vulnerabilities.",
        "required_skills": ["Ethical Hacking", "Kali Linux", "Python", "Networking", "OWASP", "Burp Suite", "Scripting", "Reporting"],
        "core_skills": ["Ethical Hacking", "Networking", "Python"]
    },

    # ── Finance & Accounting ──────────────────────────────────────────────────
    {
        "id": "financial_analyst",
        "title": "Financial Analyst",
        "category": "Finance & Accounting",
        "icon": "fa-coins",
        "color": "warning",
        "description": "Analyse financial data, build forecasts, and provide investment recommendations.",
        "required_skills": ["Excel", "Financial Modeling", "Accounting", "SQL", "Statistics", "Communication", "Bloomberg", "Risk Analysis"],
        "core_skills": ["Excel", "Financial Modeling", "Accounting"]
    },
    {
        "id": "accountant",
        "title": "Accountant",
        "category": "Finance & Accounting",
        "icon": "fa-calculator",
        "color": "success",
        "description": "Manage financial records, prepare reports, and ensure regulatory compliance.",
        "required_skills": ["Accounting", "Excel", "Bookkeeping", "Tax Compliance", "Financial Reporting", "Auditing", "Communication"],
        "core_skills": ["Accounting", "Excel", "Financial Reporting"]
    },
    {
        "id": "investment_analyst",
        "title": "Investment Analyst",
        "category": "Finance & Accounting",
        "icon": "fa-chart-line",
        "color": "primary",
        "description": "Research and evaluate investment opportunities across equities, bonds, and alternative assets.",
        "required_skills": ["Financial Modeling", "Excel", "Research", "Statistics", "Valuation", "Bloomberg", "Communication", "Risk Analysis"],
        "core_skills": ["Financial Modeling", "Excel", "Valuation"]
    },
    {
        "id": "risk_analyst",
        "title": "Risk Analyst",
        "category": "Finance & Accounting",
        "icon": "fa-triangle-exclamation",
        "color": "danger",
        "description": "Identify, assess, and mitigate financial and operational risks across the organisation.",
        "required_skills": ["Risk Assessment", "Statistics", "Excel", "SQL", "Communication", "Compliance", "Problem Solving"],
        "core_skills": ["Risk Assessment", "Statistics", "Excel"]
    },

    # ── Marketing & Sales ─────────────────────────────────────────────────────
    {
        "id": "digital_marketer",
        "title": "Digital Marketing Specialist",
        "category": "Marketing & Sales",
        "icon": "fa-bullhorn",
        "color": "warning",
        "description": "Plan and execute digital campaigns across SEO, social media, email, and paid ads.",
        "required_skills": ["SEO", "Google Ads", "Social Media Marketing", "Content Writing", "Analytics", "Email Marketing", "Communication"],
        "core_skills": ["SEO", "Social Media Marketing", "Content Writing"]
    },
    {
        "id": "content_marketer",
        "title": "Content Marketing Manager",
        "category": "Marketing & Sales",
        "icon": "fa-pen-nib",
        "color": "info",
        "description": "Develop and manage content strategies to drive brand awareness and lead generation.",
        "required_skills": ["Content Writing", "SEO", "Social Media Marketing", "Analytics", "Editing", "Communication", "Strategy"],
        "core_skills": ["Content Writing", "SEO", "Communication"]
    },
    {
        "id": "sales_executive",
        "title": "Sales Executive",
        "category": "Marketing & Sales",
        "icon": "fa-handshake",
        "color": "success",
        "description": "Drive revenue growth by identifying prospects, building relationships, and closing deals.",
        "required_skills": ["Communication", "Negotiation", "CRM", "Presentation", "Customer Service", "Problem Solving", "Networking"],
        "core_skills": ["Communication", "Negotiation", "CRM"]
    },
    {
        "id": "brand_manager",
        "title": "Brand Manager",
        "category": "Marketing & Sales",
        "icon": "fa-star",
        "color": "primary",
        "description": "Develop brand strategy, manage brand identity, and ensure consistent messaging.",
        "required_skills": ["Brand Strategy", "Marketing", "Communication", "Analytics", "Social Media Marketing", "Creative Thinking", "Research"],
        "core_skills": ["Brand Strategy", "Marketing", "Communication"]
    },

    # ── Human Resources ───────────────────────────────────────────────────────
    {
        "id": "hr_manager",
        "title": "HR Manager",
        "category": "Human Resources",
        "icon": "fa-users",
        "color": "success",
        "description": "Oversee recruitment, employee relations, performance management, and HR policy.",
        "required_skills": ["Recruitment", "HR Policy", "Communication", "Labour Law", "Performance Management", "Conflict Resolution", "Excel"],
        "core_skills": ["Recruitment", "HR Policy", "Communication"]
    },
    {
        "id": "recruiter",
        "title": "Talent Acquisition Specialist",
        "category": "Human Resources",
        "icon": "fa-user-plus",
        "color": "primary",
        "description": "Source, screen, and onboard top talent to meet organisational hiring needs.",
        "required_skills": ["Recruitment", "Communication", "LinkedIn", "Interviewing", "Negotiation", "CRM", "HR Policy"],
        "core_skills": ["Recruitment", "Communication", "Interviewing"]
    },
    {
        "id": "training_specialist",
        "title": "Learning & Development Specialist",
        "category": "Human Resources",
        "icon": "fa-graduation-cap",
        "color": "info",
        "description": "Design and deliver training programmes to upskill employees and boost performance.",
        "required_skills": ["Training", "Instructional Design", "Communication", "Presentation", "LMS", "Curriculum Development", "Assessment"],
        "core_skills": ["Training", "Communication", "Instructional Design"]
    },

    # ── Design & Creative ─────────────────────────────────────────────────────
    {
        "id": "ux_designer",
        "title": "UX/UI Designer",
        "category": "Design & Creative",
        "icon": "fa-pen-ruler",
        "color": "primary",
        "description": "Research user needs and design intuitive, accessible interfaces for digital products.",
        "required_skills": ["Figma", "UI/UX", "Wireframing", "Prototyping", "User Research", "CSS", "Communication", "Adobe XD"],
        "core_skills": ["Figma", "UI/UX", "Wireframing"]
    },
    {
        "id": "graphic_designer",
        "title": "Graphic Designer",
        "category": "Design & Creative",
        "icon": "fa-palette",
        "color": "warning",
        "description": "Create compelling visual content for branding, marketing, and digital platforms.",
        "required_skills": ["Adobe Photoshop", "Adobe Illustrator", "Typography", "Branding", "UI/UX", "Communication", "Creativity"],
        "core_skills": ["Adobe Photoshop", "Adobe Illustrator", "Branding"]
    },
    {
        "id": "video_editor",
        "title": "Video Editor",
        "category": "Design & Creative",
        "icon": "fa-film",
        "color": "danger",
        "description": "Edit and produce video content for social media, marketing campaigns, and corporate use.",
        "required_skills": ["Adobe Premiere Pro", "After Effects", "Colour Grading", "Storytelling", "Audio Editing", "Creativity", "Attention to Detail"],
        "core_skills": ["Adobe Premiere Pro", "After Effects", "Storytelling"]
    },

    # ── Healthcare & Medical ──────────────────────────────────────────────────
    {
        "id": "health_data_analyst",
        "title": "Healthcare Data Analyst",
        "category": "Healthcare",
        "icon": "fa-heart-pulse",
        "color": "danger",
        "description": "Analyse clinical and operational healthcare data to improve patient outcomes.",
        "required_skills": ["SQL", "Python", "Excel", "Statistics", "Healthcare Knowledge", "Data Visualization", "Communication"],
        "core_skills": ["SQL", "Excel", "Healthcare Knowledge"]
    },
    {
        "id": "clinical_researcher",
        "title": "Clinical Research Coordinator",
        "category": "Healthcare",
        "icon": "fa-stethoscope",
        "color": "success",
        "description": "Coordinate clinical trials and research studies, ensuring regulatory compliance and data integrity.",
        "required_skills": ["Research", "Clinical Trials", "Documentation", "Compliance", "Communication", "Data Entry", "Attention to Detail"],
        "core_skills": ["Research", "Clinical Trials", "Documentation"]
    },
    {
        "id": "health_informatics",
        "title": "Health Informatics Specialist",
        "category": "Healthcare",
        "icon": "fa-hospital",
        "color": "primary",
        "description": "Implement and manage health information systems to optimise clinical workflows.",
        "required_skills": ["EHR Systems", "SQL", "Healthcare Knowledge", "System Design", "Communication", "Data Management", "Training"],
        "core_skills": ["EHR Systems", "Healthcare Knowledge", "SQL"]
    },

    # ── Education & Training ──────────────────────────────────────────────────
    {
        "id": "teacher",
        "title": "Secondary School Teacher",
        "category": "Education",
        "icon": "fa-chalkboard-user",
        "color": "success",
        "description": "Educate students across core subjects, design lesson plans, and assess learning outcomes.",
        "required_skills": ["Teaching", "Curriculum Development", "Communication", "Classroom Management", "Assessment", "Subject Knowledge", "Patience"],
        "core_skills": ["Teaching", "Communication", "Subject Knowledge"]
    },
    {
        "id": "elearning_developer",
        "title": "eLearning Developer",
        "category": "Education",
        "icon": "fa-laptop-file",
        "color": "info",
        "description": "Create interactive online courses and learning materials using authoring tools.",
        "required_skills": ["Instructional Design", "Articulate Storyline", "HTML", "CSS", "LMS", "Curriculum Development", "Creativity"],
        "core_skills": ["Instructional Design", "Articulate Storyline", "LMS"]
    },

    # ── Business & Management ─────────────────────────────────────────────────
    {
        "id": "project_manager",
        "title": "Project Manager",
        "category": "Business & Management",
        "icon": "fa-diagram-project",
        "color": "primary",
        "description": "Plan, execute, and close projects on time and within budget across teams.",
        "required_skills": ["Project Management", "Communication", "Risk Management", "Agile", "Scrum", "MS Project", "Stakeholder Management"],
        "core_skills": ["Project Management", "Communication", "Agile"]
    },
    {
        "id": "business_analyst",
        "title": "Business Analyst",
        "category": "Business & Management",
        "icon": "fa-briefcase",
        "color": "warning",
        "description": "Identify business needs, analyse processes, and recommend improvements or technology solutions.",
        "required_skills": ["Business Analysis", "SQL", "Communication", "Documentation", "UML", "Stakeholder Management", "Problem Solving"],
        "core_skills": ["Business Analysis", "Communication", "SQL"]
    },
    {
        "id": "operations_manager",
        "title": "Operations Manager",
        "category": "Business & Management",
        "icon": "fa-sliders",
        "color": "success",
        "description": "Oversee daily operations, optimise processes, and ensure organisational efficiency.",
        "required_skills": ["Operations Management", "Leadership", "Communication", "Problem Solving", "Excel", "Process Improvement", "Team Management"],
        "core_skills": ["Operations Management", "Leadership", "Communication"]
    },
    {
        "id": "product_manager",
        "title": "Product Manager",
        "category": "Business & Management",
        "icon": "fa-boxes-stacked",
        "color": "info",
        "description": "Define product vision, prioritise roadmap features, and align engineering and business teams.",
        "required_skills": ["Product Management", "Agile", "Communication", "User Research", "Data Analysis", "Stakeholder Management", "Roadmapping"],
        "core_skills": ["Product Management", "Agile", "Communication"]
    },

    # ── Legal & Compliance ────────────────────────────────────────────────────
    {
        "id": "compliance_officer",
        "title": "Compliance Officer",
        "category": "Legal & Compliance",
        "icon": "fa-scale-balanced",
        "color": "warning",
        "description": "Ensure the organisation adheres to legal standards, internal policies, and regulations.",
        "required_skills": ["Compliance", "Risk Assessment", "Communication", "Legal Knowledge", "Documentation", "Auditing", "Attention to Detail"],
        "core_skills": ["Compliance", "Risk Assessment", "Legal Knowledge"]
    },
    {
        "id": "legal_analyst",
        "title": "Legal Analyst",
        "category": "Legal & Compliance",
        "icon": "fa-gavel",
        "color": "secondary",
        "description": "Research legal issues, draft documents, and support lawyers with case preparation.",
        "required_skills": ["Legal Research", "Documentation", "Communication", "Attention to Detail", "Legal Writing", "Critical Thinking"],
        "core_skills": ["Legal Research", "Documentation", "Communication"]
    },

    # ── Engineering (Non-IT) ──────────────────────────────────────────────────
    {
        "id": "mechanical_engineer",
        "title": "Mechanical Engineer",
        "category": "Engineering",
        "icon": "fa-cog",
        "color": "warning",
        "description": "Design and analyse mechanical systems, components, and manufacturing processes.",
        "required_skills": ["CAD", "SolidWorks", "Thermodynamics", "Materials Science", "Mathematics", "Problem Solving", "AutoCAD"],
        "core_skills": ["CAD", "SolidWorks", "Mathematics"]
    },
    {
        "id": "civil_engineer",
        "title": "Civil Engineer",
        "category": "Engineering",
        "icon": "fa-building-columns",
        "color": "success",
        "description": "Plan, design, and oversee construction of infrastructure such as roads, bridges, and buildings.",
        "required_skills": ["AutoCAD", "Structural Analysis", "Project Management", "Mathematics", "Problem Solving", "Communication", "STAAD Pro"],
        "core_skills": ["AutoCAD", "Structural Analysis", "Mathematics"]
    },
    {
        "id": "electrical_engineer",
        "title": "Electrical Engineer",
        "category": "Engineering",
        "icon": "fa-bolt",
        "color": "warning",
        "description": "Design, develop, and test electrical systems and components for various industries.",
        "required_skills": ["Circuit Design", "AutoCAD", "MATLAB", "Mathematics", "Problem Solving", "Embedded Systems", "Communication"],
        "core_skills": ["Circuit Design", "MATLAB", "Mathematics"]
    },

    # ── Supply Chain & Logistics ──────────────────────────────────────────────
    {
        "id": "supply_chain_analyst",
        "title": "Supply Chain Analyst",
        "category": "Supply Chain & Logistics",
        "icon": "fa-truck",
        "color": "primary",
        "description": "Analyse and optimise procurement, inventory, and logistics operations.",
        "required_skills": ["Supply Chain Management", "Excel", "SQL", "Data Analysis", "ERP Systems", "Communication", "Problem Solving"],
        "core_skills": ["Supply Chain Management", "Excel", "Data Analysis"]
    },
    {
        "id": "logistics_coordinator",
        "title": "Logistics Coordinator",
        "category": "Supply Chain & Logistics",
        "icon": "fa-boxes-packing",
        "color": "success",
        "description": "Coordinate shipments, manage freight carriers, and ensure on-time delivery.",
        "required_skills": ["Logistics", "Communication", "Excel", "Inventory Management", "Problem Solving", "Attention to Detail", "ERP Systems"],
        "core_skills": ["Logistics", "Excel", "Communication"]
    },
]

# Derive the full set of category names in the order they first appear
CATEGORIES = list(dict.fromkeys(r["category"] for r in JOB_ROLES))


def _normalize(skill: str) -> str:
    return skill.strip().lower()


def _skills_match(user_skill: str, required_skill: str) -> bool:
    u = _normalize(user_skill)
    r = _normalize(required_skill)
    if u == r:
        return True
    if r in u or u in r:
        return True
    aliases = {
        "ml": "machine learning",
        "dl": "deep learning",
        "nlp": "natural language processing",
        "js": "javascript",
        "ts": "typescript",
        "psql": "postgresql",
        "postgres": "postgresql",
        "aws": "amazon web services",
        "gcp": "google cloud",
        "azure": "microsoft azure",
        "scikit": "scikit-learn",
        "sklearn": "scikit-learn",
        "tf": "tensorflow",
        "api": "rest apis",
        "rest api": "rest apis",
    }
    u2 = aliases.get(u, u)
    r2 = aliases.get(r, r)
    if u2 == r2 or u2 in r2 or r2 in u2:
        return True
    return False


def calculate_role_matches_local(user_skills: list) -> list:
    user_skill_names = [s["skill_name"] for s in user_skills if s.get("skill_name")]
    results = []

    for role in JOB_ROLES:
        essential_skills = role["core_skills"]
        optional_skills = [s for s in role["required_skills"] if s not in essential_skills]

        matched_essential = [s for s in essential_skills if any(_skills_match(u, s) for u in user_skill_names)]
        missing_essential = [s for s in essential_skills if s not in matched_essential]

        matched_optional = [s for s in optional_skills if any(_skills_match(u, s) for u in user_skill_names)]
        missing_optional = [s for s in optional_skills if s not in matched_optional]

        # Flat lists for backwards compatibility in templates
        matched_skills = matched_essential + matched_optional
        missing_skills = missing_essential + missing_optional
        required_skills = essential_skills + optional_skills

        # ESCO-weighted match percentage formula: 80% Essential, 20% Optional
        essential_score = (len(matched_essential) / len(essential_skills)) if essential_skills else 1.0
        optional_score = (len(matched_optional) / len(optional_skills)) if optional_skills else 1.0
        pct = round((0.8 * essential_score + 0.2 * optional_score) * 100, 1)

        core_hit = len(matched_essential) > 0

        results.append({
            **role,
            "required_skills": required_skills,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "essential_skills": essential_skills,
            "optional_skills": optional_skills,
            "matched_essential": matched_essential,
            "matched_optional": matched_optional,
            "missing_essential": missing_essential,
            "missing_optional": missing_optional,
            "match_percentage": pct,
            "is_related": core_hit or pct >= 20.0,
            "progress_color": "bg-success" if pct >= 75 else ("bg-warning" if pct >= 45 else "bg-danger"),
            "match_label": "Strong Match" if pct >= 75 else ("Partial Match" if pct >= 45 else "Needs Work"),
            "match_label_class": "match-high" if pct >= 75 else ("match-medium" if pct >= 45 else "match-low"),
        })

    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return results


def calculate_role_matches(user_skills: list, user_id: str = None) -> list:
    """
    Calculate matches.
    If user_id is provided, checks DB cache first.
    If cache misses, queries Claude AI for dynamic modern skill matching,
    saves to DB cache, and returns.
    If anything fails or user_id is missing, falls back to local regex matching.
    """
    user_skill_names = [s["skill_name"] for s in user_skills if s.get("skill_name")]
    if not user_skill_names:
        return []

    # Try AI-Powered Matching with Caching
    if user_id and claude_service.client:
        try:
            resume = resume_repo.get_latest_resume(user_id)
            if resume:
                extracted_data = resume.get("extracted_data") or {}
                cached_matches = extracted_data.get("role_matches")

                # If cache is valid, format with metadata and return
                if cached_matches and isinstance(cached_matches, list):
                    logger.info(f"Loaded cached AI role matches from database for user {user_id}")
                    return _format_ai_matches(cached_matches)

                # Cache miss: Run Claude AI analysis
                raw_text = resume.get("raw_text", "")
                logger.info(f"Cache miss for user {user_id}. Querying Claude for dynamic job matching...")
                ai_matches = claude_service.analyze_job_role_matches(raw_text, user_skill_names, JOB_ROLES)
                
                if ai_matches:
                    # Save to DB cache
                    resume_repo.save_resume_role_matches(user_id, ai_matches)
                    return _format_ai_matches(ai_matches)

        except Exception as err:
            logger.error(f"Failed AI job matching or caching for user {user_id}: {str(err)}. Falling back to local matcher.", exc_info=True)

    # Fallback to local rule-based matching
    logger.info("Using local regex-based job role matcher fallback.")
    return calculate_role_matches_local(user_skills)


def _format_ai_matches(ai_matches: list) -> list:
    """Map AI matched results back to static metadata (icons, colors, categories)."""
    formatted_results = []
    
    # Create a quick map of static role metadata
    role_meta_map = {role["id"]: role for role in JOB_ROLES}
    
    for match in ai_matches:
        role_id = match.get("id")
        meta = role_meta_map.get(role_id)
        if not meta:
            continue
            
        pct = float(match.get("match_percentage", 0.0))
        essential_skills = match.get("essential_skills", [])
        optional_skills = match.get("optional_skills", [])
        matched_essential = match.get("matched_essential", [])
        matched_optional = match.get("matched_optional", [])
        missing_essential = match.get("missing_essential", [])
        missing_optional = match.get("missing_optional", [])

        # Flat lists for backwards compatibility in templates
        required_skills = essential_skills + optional_skills
        matched_skills = matched_essential + matched_optional
        missing_skills = missing_essential + missing_optional
        
        formatted_results.append({
            "id": role_id,
            "title": meta["title"],
            "category": meta["category"],
            "icon": meta["icon"],
            "color": meta["color"],
            "description": meta["description"],
            "required_skills": required_skills,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "essential_skills": essential_skills,
            "optional_skills": optional_skills,
            "matched_essential": matched_essential,
            "matched_optional": matched_optional,
            "missing_essential": missing_essential,
            "missing_optional": missing_optional,
            "match_percentage": pct,
            "is_related": match.get("is_related", False),
            "progress_color": "bg-success" if pct >= 75 else ("bg-warning" if pct >= 45 else "bg-danger"),
            "match_label": "Strong Match" if pct >= 75 else ("Partial Match" if pct >= 45 else "Needs Work"),
            "match_label_class": "match-high" if pct >= 75 else ("match-medium" if pct >= 45 else "match-low")
        })
        
    # Sort by percentage descending
    formatted_results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return formatted_results
