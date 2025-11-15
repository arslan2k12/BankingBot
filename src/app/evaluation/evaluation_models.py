"""
Structured output models for LLM-as-a-Judge evaluation
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class EvaluationCriteria(BaseModel):
    """Individual evaluation criterion with score and reasoning"""
    criterion: str = Field(description="Name of the evaluation criterion")
    score: int = Field(description="Score from 1-5 for this criterion", ge=1, le=5)
    reasoning: str = Field(description="Brief explanation for the score")


class ResponseEvaluation(BaseModel):
    """Complete evaluation of a banking assistant response"""
    overall_score: int = Field(description="Overall confidence score from 1-5", ge=1, le=5)
    criteria_scores: List[EvaluationCriteria] = Field(description="Detailed scores for each criterion")
    strengths: List[str] = Field(description="Key strengths of the response")
    weaknesses: List[str] = Field(description="Areas for improvement")
    confidence_level: str = Field(description="High/Medium/Low confidence in the response")
    summary: str = Field(description="Brief summary of the evaluation")
