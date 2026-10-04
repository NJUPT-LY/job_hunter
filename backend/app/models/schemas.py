from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, Literal, Optional, List
from datetime import datetime

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Job(BaseModel):
    id: NonEmptyText
    title: NonEmptyText
    company: NonEmptyText
    location: NonEmptyText
    salary: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    description: str
    requirements: List[str] = []
    skills: List[str] = []
    source: Optional[str] = None
    crawl_time: Optional[str] = None
    url: Optional[str] = None


class JobPage(BaseModel):
    items: List[Job]
    total: int
    page: int
    page_size: int


class ParsedJD(BaseModel):
    summary: NonEmptyText
    key_responsibilities: List[str]
    required_skills: List[str]
    experience_level: str
    education_requirement: str
    plain_language: NonEmptyText


class AnswerEvaluation(BaseModel):
    score: int = Field(ge=0, le=100)
    feedback: List[str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


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
    phase: NonEmptyText
    title: NonEmptyText
    description: NonEmptyText
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


class AnalyzeJobRequest(BaseModel):
    pass


class SkillGapRequest(BaseModel):
    user_skills: dict[str, List[NonEmptyText]]
    job_id: NonEmptyText


class ParseJDRequest(BaseModel):
    jd_text: NonEmptyText


class ActionPlanRequest(BaseModel):
    job_title: NonEmptyText
    user_profile: dict = {}


class EvaluateResumeRequest(BaseModel):
    resume_content: NonEmptyText
    target_job: NonEmptyText


class OptimizeResumeRequest(BaseModel):
    resume_content: NonEmptyText
    target_job: NonEmptyText


class SimulateInterviewRequest(BaseModel):
    job_title: NonEmptyText
    interview_type: Literal["技术面", "HR面", "行为面"]
    user_answer: Optional[str] = None
    question_index: int = Field(default=0, ge=0)


class EvaluateAnswerRequest(BaseModel):
    question: NonEmptyText
    answer: NonEmptyText
    job_title: NonEmptyText


class CrawlJobsRequest(BaseModel):
    keyword: NonEmptyText


class ImportJobsRequest(BaseModel):
    jobs: List[dict]
