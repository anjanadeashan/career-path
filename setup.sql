-- Setup SQL for Smart Job Matching System (AI Career Helper)
-- Run this in the Supabase SQL Editor

-- 1. Create Profiles Table (extends Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'student' CHECK (role IN ('student', 'admin')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create Resumes Table
CREATE TABLE IF NOT EXISTS public.resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    raw_text TEXT NOT NULL,
    extracted_data JSONB, -- stores structured education, experience, certifications
    file_url TEXT, -- public URL to stored PDF/DOCX document
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Create Extracted Skills Table
CREATE TABLE IF NOT EXISTS public.extracted_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL,
    skill_type VARCHAR(50) CHECK (skill_type IN ('technical', 'soft')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_skill UNIQUE (user_id, skill_name)
);

-- 4. Create Jobs Table
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements JSONB NOT NULL, -- array of strings: ["Python", "SQL", "Tableau"]
    location VARCHAR(255),
    job_type VARCHAR(100) DEFAULT 'Full-time',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Create Recommendations Table
CREATE TABLE IF NOT EXISTS public.recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    match_percentage NUMERIC(5,2) NOT NULL,
    ranking INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_job_rec UNIQUE (user_id, job_id)
);

-- 6. Create Skill Gaps Table
CREATE TABLE IF NOT EXISTS public.skill_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    missing_skills JSONB NOT NULL, -- array of strings: ["Power BI", "Tableau"]
    suggested_courses JSONB, -- array of objects: [{"name": "Power BI Course", "platform": "Coursera"}]
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_job_gap UNIQUE (user_id, job_id)
);

-- 7. Create Career Feedback Table (Claude AI Career Suggestions)
CREATE TABLE IF NOT EXISTS public.career_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    feedback_text TEXT NOT NULL,
    career_paths JSONB, -- array of suggested job titles
    recommended_certifications JSONB, -- array of suggested certs
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Trigger to Automatically Create Profile on Signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, role)
    VALUES (
        new.id,
        new.email,
        COALESCE(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
        COALESCE(new.raw_user_meta_data->>'role', 'student')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger execution setup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Enable RLS Policies (Row Level Security) - Bypassable by service role key
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extracted_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skill_gaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.career_feedback ENABLE ROW LEVEL SECURITY;

-- Profiles Policies
CREATE POLICY "Allow public read for profiles" ON public.profiles FOR SELECT USING (true);
CREATE POLICY "Allow user update for profiles" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Resumes Policies
CREATE POLICY "Allow users to read their own resumes" ON public.resumes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Allow users to insert their own resumes" ON public.resumes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Allow users to delete their own resumes" ON public.resumes FOR DELETE USING (auth.uid() = user_id);

-- Extracted Skills Policies
CREATE POLICY "Allow users to read their own skills" ON public.extracted_skills FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Allow users to manage their own skills" ON public.extracted_skills FOR ALL USING (auth.uid() = user_id);

-- Jobs Policies
CREATE POLICY "Allow public read for jobs" ON public.jobs FOR SELECT USING (true);
CREATE POLICY "Allow admin manage jobs" ON public.jobs FOR ALL USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
);

-- Recommendations Policies
CREATE POLICY "Allow users to read their recommendations" ON public.recommendations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Allow system manage recommendations" ON public.recommendations FOR ALL USING (true);

-- Skill Gaps Policies
CREATE POLICY "Allow users to read their skill gaps" ON public.skill_gaps FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Allow system manage skill gaps" ON public.skill_gaps FOR ALL USING (true);

-- Career Feedback Policies
CREATE POLICY "Allow users to read their career feedback" ON public.career_feedback FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Allow system manage career feedback" ON public.career_feedback FOR ALL USING (true);


-- 9. Insert Sample Jobs Data
INSERT INTO public.jobs (title, company, description, requirements, location, job_type)
VALUES
(
    'Data Analyst',
    'FinTech Solutions Ltd',
    'We are looking for a Data Analyst to gather, analyze and interpret complex data to help our organization make business decisions. You will work with SQL, Python, and visualization tools like Tableau or Power BI.',
    '["Python", "SQL", "Tableau", "Power BI", "Data Analysis", "Communication"]',
    'New York, NY (Hybrid)',
    'Full-time'
),
(
    'Software Engineer (Python/Flask)',
    'TechCraft Systems',
    'Join our backend team building high-performance APIs and microservices. You will develop backend logic, manage database migrations, and write clean Python code using Flask and PostgreSQL.',
    '["Python", "Flask", "PostgreSQL", "REST APIs", "Git", "Docker", "Problem Solving"]',
    'Remote',
    'Full-time'
),
(
    'Machine Learning Intern',
    'Cognitive AI',
    'As an ML intern, you will build and evaluate machine learning models for user classification and text extraction. You will work closely with research engineers using scikit-learn, PyTorch, and NLP tools.',
    '["Python", "Scikit-learn", "NLP", "Machine Learning", "Linear Algebra", "Research"]',
    'San Francisco, CA',
    'Internship'
),
(
    'Full Stack Developer',
    'WebSprint Solutions',
    'We are looking for a Full Stack Developer proficient in python backends and modern CSS/HTML. You will build user-friendly dashboard portals, integrate with authentication APIs, and optimize performance.',
    '["Python", "Flask", "HTML", "CSS", "JavaScript", "Bootstrap", "Git", "SQL"]',
    'Chicago, IL (On-site)',
    'Full-time'
),
(
    'AI Product Engineer',
    'Aether Labs',
    'Shape the future of AI-driven tools. You will implement integrations with Large Language Models (LLMs) such as Claude, design smart agent loops, and manage parsing of PDF documents.',
    '["Python", "Claude API", "LLMs", "JSON Parsing", "Node.js", "Git", "Creative Writing"]',
    'Remote',
    'Full-time'
)
ON CONFLICT DO NOTHING;
