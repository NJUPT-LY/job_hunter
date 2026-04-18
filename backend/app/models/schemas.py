from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    description: str
    requirements: List[str] = []
    skills: List[str] = []
    source: Optional[str] = None
    crawl_time: Optional[str] = None
    url: Optional[str] = None


class JobAnalysis(BaseModel):
    job_id: str
    real_work_content: List[str] = []
    hard_skills: List[dict] = []
    soft_skills: List[dict] = []
    skill_levels: dict = {}
    career_path: List[str] = []
    summary: str = ""


class SkillGap(BaseModel):
    matched_skills: List[dict] = []
    missing_skills: List[dict] = []
    match_score: float = 0.0
    suggestions: List[str] = []


class ActionItem(BaseModel):
    phase: str
    title: str
    description: str
    tasks: List[str] = []
    resources: List[str] = []
    completed: bool = False


class UserProfile(BaseModel):
    name: Optional[str] = None
    major: Optional[str] = None
    grade: Optional[str] = None
    skills: List[dict] = []
    target_jobs: List[str] = []


class ResumeTemplate(BaseModel):
    id: str
    name: str
    category: str
    content: str


class InterviewQuestion(BaseModel):
    question: str
    category: str
    difficulty: str
    hints: List[str] = []
    evaluation_criteria: List[str] = []
