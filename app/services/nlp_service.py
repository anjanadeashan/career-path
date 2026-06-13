import os
import re
import logging
import nltk
import spacy
from spacy.matcher import PhraseMatcher

logger = logging.getLogger(__name__)

# Predefined skill sets for dictionary-based extraction
TECHNICAL_SKILLS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "ruby", "go", "golang", "rust", "swift", "kotlin", "php",
    "sql", "nosql", "postgresql", "mysql", "mongodb", "redis", "cassandra", "sqlite", "oracle",
    "html", "css", "sass", "bootstrap", "tailwind", "react", "angular", "vue", "next.js", "node.js",
    "flask", "django", "fastapi", "express", "spring boot", "laravel", "asp.net",
    "scikit-learn", "tensorflow", "pytorch", "keras", "pandas", "numpy", "matplotlib", "seaborn",
    "machine learning", "deep learning", "natural language processing", "nlp", "computer vision",
    "data science", "data analysis", "data engineering", "artificial intelligence", "ai",
    "power bi", "tableau", "excel", "r", "sas", "spss", "matlab",
    "aws", "gcp", "google cloud", "azure", "docker", "kubernetes", "git", "github", "gitlab",
    "ci/cd", "jenkins", "terraform", "ansible", "linux", "unix", "rest apis", "graphql", "grpc",
    "marketing", "seo", "digital marketing", "social media", "content writing", "copywriting", "email marketing", "google ads", "branding", "public relations",
    "sales", "b2b sales", "crm", "salesforce", "negotiation", "account management", "business development",
    "finance", "accounting", "financial modeling", "auditing", "tax compliance", "bookkeeping", "bloomberg", "risk management",
    "human resources", "hr", "recruitment", "talent acquisition", "employee relations", "onboarding", "payroll",
    "healthcare", "nursing", "clinical research", "patient care", "ehr", "medical terminology", "triage",
    "education", "teaching", "curriculum development", "instructional design", "e-learning", "lms",
    "business analysis", "project management", "agile", "scrum", "operations management", "supply chain", "logistics",
    "design", "graphic design", "ui/ux", "figma", "adobe photoshop", "adobe illustrator", "video editing", "autocad", "solidworks"
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "collaboration", "problem solving",
    "critical thinking", "time management", "adaptability", "flexibility",
    "public speaking", "negotiation", "creativity", "conflict resolution",
    "empathy", "active listening", "work ethic", "interpersonal skills",
    "organization", "project management", "decision making"
]

class NlpService:
    """Service utilizing spaCy and NLTK for NLP skill extraction and resume segmentation."""

    def __init__(self):
        self._initialize_resources()
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.info("spaCy model 'en_core_web_sm' not found. Downloading...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._setup_matchers()

    def _initialize_resources(self):
        """Ensure NLTK datasets are downloaded."""
        import ssl
        try:
            _ssl_ctx = ssl.create_default_context()
        except Exception:
            ssl._create_default_https_context = ssl._create_unverified_context

        nltk_dir = '/tmp/nltk_data'
        os.makedirs(nltk_dir, exist_ok=True)
        if nltk_dir not in nltk.data.path:
            nltk.data.path.insert(0, nltk_dir)

        for dataset in ['punkt', 'punkt_tab', 'stopwords']:
            path = (f'tokenizers/{dataset}' if dataset in ('punkt', 'punkt_tab') else f'corpora/{dataset}')
            try:
                nltk.data.find(path)
            except (LookupError, OSError):
                logger.info(f"NLTK dataset '{dataset}' not found. Downloading...")
                try:
                    nltk.download(dataset, quiet=True, download_dir=nltk_dir)
                except Exception:
                    ssl._create_default_https_context = ssl._create_unverified_context
                    nltk.download(dataset, quiet=True, download_dir=nltk_dir)

    def _setup_matchers(self):
        """Create PhraseMatcher rules for skills matching."""
        # Technical skills patterns
        tech_patterns = [self.nlp.make_doc(skill) for skill in TECHNICAL_SKILLS]
        self.phrase_matcher.add("TECH_SKILL", tech_patterns)
        
        # Soft skills patterns
        soft_patterns = [self.nlp.make_doc(skill) for skill in SOFT_SKILLS]
        self.phrase_matcher.add("SOFT_SKILL", soft_patterns)

    def clean_text(self, text: str) -> str:
        """Sanitize text by removing excess whitespace and non-standard characters."""
        text = re.sub(r'\s+', ' ', text) # clean up whitespace
        return text.strip()

    def extract_skills(self, text: str) -> list:
        """
        Extract technical and soft skills from the resume text.
        Returns a list of dicts: [{'skill_name': str, 'skill_type': str}]
        """
        doc = self.nlp(text)
        matches = self.phrase_matcher(doc)
        
        extracted_skills = {}
        for match_id, start, end in matches:
            span = doc[start:end]
            skill_name = span.text.strip().title() # Format nicely
            label = self.nlp.vocab.strings[match_id]
            
            # Map standard label to UI types
            skill_type = 'technical' if label == "TECH_SKILL" else 'soft'
            
            # Use lower-case key to avoid duplicates
            skill_key = skill_name.lower()
            if skill_key not in extracted_skills:
                extracted_skills[skill_key] = {
                    'skill_name': skill_name,
                    'skill_type': skill_type
                }
                
        # Fallback basic keyword matching for skills containing special chars like C++ or C#
        text_lower = text.lower()
        special_cases = {
            "c++": "C++",
            "c#": "C#",
            "next.js": "Next.js",
            "node.js": "Node.js",
            "ci/cd": "CI/CD",
            ".net": ".NET"
        }
        for case, display_name in special_cases.items():
            # Match boundary words or special characters
            if case in text_lower:
                if case not in extracted_skills:
                    # Determine type: all special cases listed are technical
                    extracted_skills[case] = {
                        'skill_name': display_name,
                        'skill_type': 'technical'
                    }
                    
        return list(extracted_skills.values())

    def extract_structured_data(self, text: str) -> dict:
        """
        Segment the resume to extract education, experience, and certifications.
        Uses rule-based heuristics and regex patterns to scan paragraphs.
        """
        cleaned_text = self.clean_text(text)
        
        # Define keywords for sections
        sections = {
            "education": ["education", "academic", "university", "college", "degree", "qualification"],
            "experience": ["experience", "work history", "employment", "professional background", "career", "history"],
            "certifications": ["certification", "certifications", "credential", "credentials", "licenses", "courses"]
        }
        
        lines = text.split('\n')
        extracted = {
            "education": [],
            "experience": [],
            "certifications": []
        }
        
        current_section = None
        
        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                continue
                
            # Check if line indicates a section header
            is_header = False
            for sec_name, keywords in sections.items():
                # Headers are usually short and contain section keywords
                if len(line_strip) < 30 and any(re.search(rf'\b{kw}\b', line_strip.lower()) for kw in keywords):
                    current_section = sec_name
                    is_header = True
                    break
                    
            if is_header:
                continue
                
            # Populate text into active section
            if current_section:
                # Add line to list if it looks substantial
                if len(line_strip) > 5:
                    extracted[current_section].append(line_strip)
                    
        # Fallback regex search for years, universities, and certificates if sections are empty
        if not extracted["education"]:
            edu_patterns = [
                r'.*degree.*', r'.*bachelor.*', r'.*master.*', r'.*phd.*', r'.*university.*', r'.*college.*'
            ]
            for line in lines:
                if any(re.search(pat, line.lower()) for pat in edu_patterns):
                    extracted["education"].append(line.strip())
                    
        if not extracted["certifications"]:
            cert_patterns = [
                r'.*certified.*', r'.*certification.*', r'.*certificate.*', r'.*aws.*', r'.*coursera.*', r'.*udemy.*'
            ]
            for line in lines:
                if any(re.search(pat, line.lower()) for pat in cert_patterns):
                    extracted["certifications"].append(line.strip())

        # Clean duplicates and limit size to keep DB payloads light
        for key in extracted:
            seen = set()
            unique = []
            for x in extracted[key]:
                if x not in seen:
                    seen.add(x)
                    unique.append(x)
            extracted[key] = unique[:15]
            
        return extracted
