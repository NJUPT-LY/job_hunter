from fastapi import APIRouter
from typing import List
from app.models.schemas import ActionItem
from app.services.action_generator import ActionPlanGenerator

router = APIRouter()


@router.post("/generate", response_model=List[ActionItem])
async def generate_action_plan(job_title: str, user_profile: dict):
    plan = ActionPlanGenerator.generate(job_title, user_profile)
    return plan


@router.get("/templates")
async def get_plan_templates():
    templates = ActionPlanGenerator.get_templates()
    return templates
