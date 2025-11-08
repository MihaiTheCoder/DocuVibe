"""
Workflow Service

Handles workflow creation, execution, and AI-powered workflow suggestions.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.models.workflow import Workflow, WorkflowExecution
from app.models.task import Task
from app.schemas.workflow import (
    WorkflowCreateFromChatRequest,
    WorkflowUpdateRequest,
    WorkflowExecutionRequest,
    WorkflowSuggestionRequest,
    WorkflowSuggestionResponse,
    WorkflowStep
)


class WorkflowService:
    """Service for managing workflows and AI suggestions"""

    def __init__(self, db: Session, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    def create_workflow_from_chat(
        self,
        request: WorkflowCreateFromChatRequest
    ) -> Workflow:
        """
        Create a workflow from a natural language prompt using AI

        Args:
            request: Chat request containing the prompt and context

        Returns:
            Workflow: Created workflow object
        """
        # TODO: Integrate with actual AI model for workflow generation
        # For now, create a simple workflow based on the prompt

        # Mock AI response - extract intent from prompt
        steps = self._generate_workflow_steps_from_prompt(request.prompt, request.context)

        workflow = Workflow(
            organization_id=uuid.UUID(self.organization_id),
            name=self._extract_workflow_name(request.prompt),
            description=f"AI-generated workflow: {request.prompt}",
            steps=steps,
            triggers={},
            created_by_ai=True,
            ai_prompt=request.prompt
        )

        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    def get_workflows(self) -> List[Workflow]:
        """
        Get all workflows for the organization

        Returns:
            List of workflows
        """
        return self.db.query(Workflow).filter(
            Workflow.organization_id == uuid.UUID(self.organization_id)
        ).all()

    def get_workflow_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get a specific workflow by ID

        Args:
            workflow_id: UUID of the workflow

        Returns:
            Workflow or None if not found
        """
        return self.db.query(Workflow).filter(
            Workflow.id == uuid.UUID(workflow_id),
            Workflow.organization_id == uuid.UUID(self.organization_id)
        ).first()

    def update_workflow(
        self,
        workflow_id: str,
        request: WorkflowUpdateRequest
    ) -> Optional[Workflow]:
        """
        Update a workflow

        Args:
            workflow_id: UUID of the workflow
            request: Update request with new values

        Returns:
            Updated workflow or None if not found
        """
        workflow = self.get_workflow_by_id(workflow_id)
        if not workflow:
            return None

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workflow, field, value)

        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow

        Args:
            workflow_id: UUID of the workflow

        Returns:
            True if deleted, False if not found
        """
        workflow = self.get_workflow_by_id(workflow_id)
        if not workflow:
            return False

        self.db.delete(workflow)
        self.db.commit()

        return True

    def execute_workflow(
        self,
        workflow_id: str,
        request: WorkflowExecutionRequest
    ) -> WorkflowExecution:
        """
        Execute a workflow with given parameters

        Args:
            workflow_id: UUID of the workflow to execute
            request: Execution request with document IDs and parameters

        Returns:
            WorkflowExecution: Created execution object
        """
        workflow = self.get_workflow_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Create execution record
        execution = WorkflowExecution(
            organization_id=uuid.UUID(self.organization_id),
            workflow_id=uuid.UUID(workflow_id),
            status="running",
            started_at=datetime.utcnow(),
            results={}
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        # TODO: Implement actual workflow execution logic
        # For now, create tasks for each step in the workflow
        self._create_workflow_tasks(workflow, execution, request)

        # Update execution status
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        execution.results = {
            "documents_processed": len(request.document_ids),
            "tasks_created": len(workflow.steps)
        }

        self.db.commit()
        self.db.refresh(execution)

        return execution

    def suggest_workflow(
        self,
        request: WorkflowSuggestionRequest
    ) -> WorkflowSuggestionResponse:
        """
        Suggest a workflow based on document type or use case

        Args:
            request: Suggestion request

        Returns:
            WorkflowSuggestionResponse with suggested workflow
        """
        # TODO: Integrate with actual AI model for workflow suggestions
        # For now, return a mock suggestion based on document type

        if request.document_type == "invoice":
            return WorkflowSuggestionResponse(
                suggested_name="Invoice Approval Workflow",
                description="Automated workflow for processing and approving invoices",
                steps=[
                    WorkflowStep(
                        step_type="ocr",
                        name="Extract Invoice Data",
                        description="Extract vendor, amount, date, and line items",
                        config={"extractors": ["invoice"]}
                    ),
                    WorkflowStep(
                        step_type="validation",
                        name="Validate Invoice Data",
                        description="Check for required fields and data consistency",
                        config={"required_fields": ["vendor", "total_amount", "date"]}
                    ),
                    WorkflowStep(
                        step_type="task",
                        name="Manager Review",
                        description="Assign review task to department manager",
                        config={"task_type": "review", "assign_to_role": "admin"}
                    ),
                    WorkflowStep(
                        step_type="approval",
                        name="Approve Invoice",
                        description="Mark invoice as approved and ready for payment",
                        config={"stage": "approved"}
                    )
                ],
                reasoning="This workflow is optimized for Romanian hospital finance departments, ensuring compliance and proper approval chains.",
                similar_workflows=[]
            )
        else:
            return WorkflowSuggestionResponse(
                suggested_name="Document Processing Workflow",
                description="General document processing workflow",
                steps=[
                    WorkflowStep(
                        step_type="ocr",
                        name="Extract Text",
                        description="Extract text content from document",
                        config={}
                    ),
                    WorkflowStep(
                        step_type="classification",
                        name="Classify Document",
                        description="Determine document type and category",
                        config={}
                    ),
                    WorkflowStep(
                        step_type="task",
                        name="Manual Review",
                        description="Assign for manual review if needed",
                        config={"task_type": "review"}
                    )
                ],
                reasoning="A general-purpose workflow suitable for various document types.",
                similar_workflows=[]
            )

    def _generate_workflow_steps_from_prompt(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate workflow steps from a natural language prompt

        Args:
            prompt: Natural language description of the workflow
            context: Additional context

        Returns:
            List of workflow step definitions
        """
        # TODO: Use AI to generate actual steps
        # For now, return a generic workflow

        steps = [
            {
                "step_type": "ocr",
                "name": "Extract Text",
                "order": 1,
                "config": {}
            },
            {
                "step_type": "classification",
                "name": "Classify Document",
                "order": 2,
                "config": {}
            }
        ]

        # Add review step if prompt mentions "approval" or "review"
        if any(word in prompt.lower() for word in ["approval", "review", "approve"]):
            steps.append({
                "step_type": "task",
                "name": "Review and Approve",
                "order": 3,
                "config": {"task_type": "approval"}
            })

        return steps

    def _extract_workflow_name(self, prompt: str) -> str:
        """
        Extract a workflow name from the prompt

        Args:
            prompt: User prompt

        Returns:
            Generated workflow name
        """
        # TODO: Use AI to generate a better name
        # For now, truncate and clean the prompt

        name = prompt.strip()
        if len(name) > 50:
            name = name[:50] + "..."

        return f"Workflow: {name}"

    def _create_workflow_tasks(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        request: WorkflowExecutionRequest
    ) -> None:
        """
        Create tasks for workflow execution

        Args:
            workflow: The workflow being executed
            execution: The execution record
            request: Execution request with parameters
        """
        # Create tasks based on workflow steps
        for i, step in enumerate(workflow.steps):
            if step.get("step_type") == "task":
                task = Task(
                    organization_id=uuid.UUID(self.organization_id),
                    title=step.get("name", f"Step {i+1}"),
                    description=step.get("description", ""),
                    type=step.get("config", {}).get("task_type", "general"),
                    status="pending",
                    workflow_execution_id=execution.id
                )

                # Assign to document if document_ids provided
                if request.document_ids:
                    task.document_id = uuid.UUID(request.document_ids[0])

                self.db.add(task)

        self.db.commit()
