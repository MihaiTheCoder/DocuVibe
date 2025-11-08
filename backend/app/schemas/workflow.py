"""
Workflow Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class WorkflowBase(BaseModel):
    """Base workflow schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Array of step definitions")
    triggers: Dict[str, Any] = Field(default_factory=dict, description="Event triggers")


class WorkflowCreateFromChatRequest(BaseModel):
    """Schema for creating a workflow from chat prompt"""
    prompt: str = Field(..., min_length=1, description="Natural language prompt describing the workflow")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for workflow creation")


class WorkflowUpdateRequest(BaseModel):
    """Schema for updating a workflow"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    triggers: Optional[Dict[str, Any]] = None


class WorkflowResponse(WorkflowBase):
    """Schema for workflow response"""
    id: str
    organization_id: str
    created_by_ai: bool
    ai_prompt: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowDetailResponse(WorkflowResponse):
    """Schema for detailed workflow response with execution history"""
    execution_count: Optional[int] = 0
    last_executed_at: Optional[datetime] = None


class WorkflowExecutionRequest(BaseModel):
    """Schema for executing a workflow"""
    document_ids: List[str] = Field(default_factory=list, description="Document IDs to process")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")


class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution response"""
    id: str
    workflow_id: str
    organization_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageRequest(BaseModel):
    """Schema for chat message request"""
    message: str = Field(..., min_length=1, description="User message")
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")


class ChatAction(BaseModel):
    """Schema for suggested action in chat response"""
    action_type: str = Field(..., description="Type of action (search, create_workflow, create_task)")
    label: str = Field(..., description="Human-readable action label")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Schema for chat response"""
    message: str = Field(..., description="AI response message")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Search or query results")
    suggested_actions: List[ChatAction] = Field(default_factory=list, description="Suggested follow-up actions")
    conversation_id: Optional[str] = None


class ConversationResponse(BaseModel):
    """Schema for conversation history"""
    id: str
    organization_id: str
    title: Optional[str] = None
    last_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int = 0


class WorkflowSuggestionRequest(BaseModel):
    """Schema for workflow suggestion request"""
    document_type: Optional[str] = Field(None, description="Document type to suggest workflow for")
    use_case: Optional[str] = Field(None, description="Specific use case or scenario")


class WorkflowStep(BaseModel):
    """Schema for a workflow step"""
    step_type: str
    name: str
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowSuggestionResponse(BaseModel):
    """Schema for workflow suggestion response"""
    suggested_name: str
    description: str
    steps: List[WorkflowStep]
    reasoning: str = Field(..., description="Explanation of why this workflow is suggested")
    similar_workflows: List[str] = Field(default_factory=list, description="IDs of similar existing workflows")
