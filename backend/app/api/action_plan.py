from fastapi import APIRouter
from typing import List
from app.models.schemas import ActionItem, ActionPlanRequest
from app.services.action_generator import ActionPlanGenerator

router = APIRouter()


@router.post("/generate", response_model=List[ActionItem])
async def generate_action_plan(request: ActionPlanRequest):
    plan = await ActionPlanGenerator.generate(request.job_title, request.user_profile)
    return plan


@router.get("/templates")
async def get_plan_templates():
    templates = ActionPlanGenerator.get_templates()
    return templates
