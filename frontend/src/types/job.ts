export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  salary?: string | null;
  experience?: string | null;
  education?: string | null;
  description: string;
  requirements: string[];
  skills: string[];
  source?: string | null;
  crawl_time?: string | null;
  url?: string | null;
}

export interface JobPage {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
}

export interface JobStats {
  total: number;
  cities: number;
  companies: number;
  skills: number;
}

export interface JobAnalysis {
  job_id: string;
  real_work_content: string[];
  hard_skills: { name: string; importance: string }[];
  soft_skills: { name: string; importance: string }[];
  skill_levels: Record<string, string>;
  career_path: string[];
  summary: string;
}

export interface ParsedJD {
  summary: string;
  key_responsibilities: string[];
  required_skills: string[];
  experience_level: string;
  education_requirement: string;
  plain_language: string;
  ai_provider: string;
  is_fallback: boolean;
}
