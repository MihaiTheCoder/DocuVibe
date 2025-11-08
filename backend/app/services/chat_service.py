"""
Enhanced Chat Service with GitHub Integration
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import asyncio
from datetime import datetime
import logging

from app.schemas.workflow import (
    ChatMessageRequest,
    ChatResponse,
    ChatAction,
    ConversationResponse
)
from app.models.conversation import Conversation, Message, MessageRole, ConversationStatus
from app.models.github_integration import GitHubIssue, IssueStatus
from app.services.github_service import GitHubService
from app.services.feature_analyzer import FeatureAnalyzer
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedChatService:
    """Enhanced chat service with GitHub integration"""

    def __init__(self, db: Session, organization_id: str, user_id: str):
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id
        self.github_service = GitHubService() if settings.GITHUB_TOKEN else None
        self.feature_analyzer = FeatureAnalyzer()

    async def process_message(
        self,
        request: ChatMessageRequest
    ) -> ChatResponse:
        """
        Process a chat message with feature request detection

        Args:
            request: Chat message request

        Returns:
            ChatResponse with processing results
        """
        # Get or create conversation
        conversation_id = request.context.get("conversation_id")
        conversation = self._get_or_create_conversation(conversation_id, request.message)

        # Save user message
        user_message = self._save_message(
            conversation.id,
            MessageRole.USER,
            request.message,
            meta_data=request.context
        )

        # Analyze message for feature request
        is_feature_request = self._is_feature_request(request.message)

        if is_feature_request and self.github_service:
            # Process as feature request
            response = await self._process_feature_request(
                request.message,
                conversation,
                user_message
            )
        else:
            # Process as general query
            response = await self._process_general_query(
                request.message,
                conversation
            )

        # Save assistant message
        self._save_message(
            conversation.id,
            MessageRole.ASSISTANT,
            response.message,
            meta_data={"results": response.results, "actions": [a.dict() for a in response.suggested_actions]}
        )

        response.conversation_id = str(conversation.id)
        return response

    async def _process_feature_request(
        self,
        message: str,
        conversation: Conversation,
        user_message: Message
    ) -> ChatResponse:
        """
        Process a feature request and create GitHub issue

        Args:
            message: User message
            conversation: Conversation object
            user_message: Message object

        Returns:
            ChatResponse
        """
        # Analyze the feature request
        analysis = self.feature_analyzer.analyze_feature_request(message)

        # Create GitHub issue
        try:
            issue_data = await self.github_service.create_issue(
                title=analysis.title,
                body=analysis.description,
                labels=analysis.labels,
                difficulty=analysis.difficulty
            )

            # Save GitHub issue to database
            github_issue = GitHubIssue(
                organization_id=uuid.UUID(self.organization_id),
                conversation_id=conversation.id,
                message_id=user_message.id,
                issue_number=issue_data["number"],
                issue_url=issue_data["url"],
                issue_title=analysis.title,
                issue_body=analysis.description,
                difficulty=analysis.difficulty,
                labels=analysis.labels,
                status=IssueStatus.CREATED,
                complexity_score=analysis.complexity_score,
                estimated_hours=analysis.estimated_hours,
                auto_merge_enabled=(
                    analysis.difficulty == "easy" and settings.GITHUB_AUTO_MERGE_EASY
                )
            )
            self.db.add(github_issue)
            self.db.commit()

            # Prepare response
            response_message = f"""I've created a GitHub issue for your feature request:

**Issue #{issue_data['number']}**: {analysis.title}
**URL**: {issue_data['url']}
**Difficulty**: {analysis.difficulty.value}
**Estimated Hours**: {analysis.estimated_hours}

{f"**Components**: {', '.join(analysis.components)}" if analysis.components else ""}
{f"**Risks**: {', '.join(analysis.risks)}" if analysis.risks else ""}

The issue has been classified as **{analysis.difficulty.value}** based on complexity analysis.
{"This issue will be automatically merged after successful tests since it's marked as easy." if analysis.difficulty == "easy" else "This issue will require manual review before merging."}

Would you like me to mark this issue as 'ready' for automated implementation?"""

            suggested_actions = [
                ChatAction(
                    action_type="mark_ready",
                    label="Mark issue as ready for implementation",
                    parameters={
                        "issue_id": str(github_issue.id),
                        "issue_number": issue_data["number"]
                    }
                ),
                ChatAction(
                    action_type="view_issue",
                    label="View issue on GitHub",
                    parameters={"url": issue_data["url"]}
                )
            ]

            results = [{
                "type": "github_issue",
                "data": {
                    "id": str(github_issue.id),
                    "number": issue_data["number"],
                    "url": issue_data["url"],
                    "title": analysis.title,
                    "difficulty": analysis.difficulty.value,
                    "estimated_hours": analysis.estimated_hours
                }
            }]

        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            response_message = f"""I understood your feature request but encountered an error creating the GitHub issue:

{str(e)}

Please check that GitHub integration is properly configured."""

            suggested_actions = []
            results = []

        return ChatResponse(
            message=response_message,
            results=results,
            suggested_actions=suggested_actions
        )

    async def _process_general_query(
        self,
        message: str,
        conversation: Conversation
    ) -> ChatResponse:
        """
        Process a general query (non-feature request)

        Args:
            message: User message
            conversation: Conversation object

        Returns:
            ChatResponse
        """
        # Check for status queries
        if "status" in message.lower() and "issue" in message.lower():
            return await self._check_issue_status(message, conversation)

        # Default response
        return ChatResponse(
            message="""I can help you with:
1. Creating feature requests (just describe what you need)
2. Checking issue status (ask about status of issue #X)
3. Document search and management

How can I assist you today?""",
            results=[],
            suggested_actions=[]
        )

    async def _check_issue_status(
        self,
        message: str,
        conversation: Conversation
    ) -> ChatResponse:
        """
        Check status of GitHub issues

        Args:
            message: User message
            conversation: Conversation object

        Returns:
            ChatResponse with status information
        """
        # Extract issue number from message
        import re
        match = re.search(r'#(\d+)', message)

        if match and self.github_service:
            issue_number = int(match.group(1))

            try:
                status = await self.github_service.get_issue_status(issue_number)

                response_message = f"""Issue #{issue_number} Status:
**State**: {status['state']}
**Labels**: {', '.join(status['labels'])}
{f"**Pull Request**: #{status['pr_number']} - {status['pr_url']}" if status['has_pr'] else "**Pull Request**: Not created yet"}
{f"**PR State**: {status['pr_state']}" if status.get('pr_state') else ""}"""

                results = [{"type": "issue_status", "data": status}]

            except Exception as e:
                response_message = f"Failed to check issue status: {str(e)}"
                results = []

        else:
            response_message = "Please specify an issue number (e.g., 'Check status of issue #123')"
            results = []

        return ChatResponse(
            message=response_message,
            results=results,
            suggested_actions=[]
        )

    def get_conversations(self) -> List[ConversationResponse]:
        """
        Get conversation history for the current user and organization

        Returns:
            List of conversations
        """
        conversations = self.db.query(Conversation).filter(
            Conversation.organization_id == uuid.UUID(self.organization_id),
            Conversation.user_id == uuid.UUID(self.user_id),
            Conversation.status != ConversationStatus.ARCHIVED
        ).order_by(Conversation.updated_at.desc()).limit(20).all()

        return [
            ConversationResponse(
                id=str(conv.id),
                organization_id=str(conv.organization_id),
                title=conv.title or f"Conversation {conv.created_at.strftime('%Y-%m-%d')}",
                last_message=self._get_last_message(conv),
                message_count=len(conv.messages),
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]

    async def mark_issue_ready(self, issue_id: str) -> bool:
        """
        Mark a GitHub issue as ready for implementation

        Args:
            issue_id: Database ID of the GitHub issue

        Returns:
            True if successful
        """
        issue = self.db.query(GitHubIssue).filter(
            GitHubIssue.id == uuid.UUID(issue_id),
            GitHubIssue.organization_id == uuid.UUID(self.organization_id)
        ).first()

        if not issue or not self.github_service:
            return False

        try:
            # Add ready label to trigger lazy-bird
            success = await self.github_service.add_ready_label(issue.issue_number)

            if success:
                issue.status = IssueStatus.READY
                issue.ready_at = datetime.utcnow()
                self.db.commit()

                # If easy issue, enable auto-merge on the eventual PR
                if issue.difficulty == "easy" and issue.auto_merge_enabled:
                    # This will be handled by a background job that monitors for PR creation
                    pass

            return success

        except Exception as e:
            logger.error(f"Failed to mark issue ready: {e}")
            return False

    def _get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        first_message: str
    ) -> Conversation:
        """
        Get existing conversation or create new one

        Args:
            conversation_id: Optional existing conversation ID
            first_message: First message for title generation

        Returns:
            Conversation object
        """
        if conversation_id:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == uuid.UUID(conversation_id),
                Conversation.organization_id == uuid.UUID(self.organization_id)
            ).first()

            if conversation:
                return conversation

        # Create new conversation
        title = first_message[:100] if len(first_message) > 100 else first_message
        conversation = Conversation(
            organization_id=uuid.UUID(self.organization_id),
            user_id=uuid.UUID(self.user_id),
            title=title,
            status=ConversationStatus.ACTIVE
        )
        self.db.add(conversation)
        self.db.commit()

        return conversation

    def _save_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        meta_data: Dict[str, Any] = None
    ) -> Message:
        """
        Save a message to the database

        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant/system)
            content: Message content
            meta_data: Optional metadata

        Returns:
            Message object
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            meta_data=meta_data or {}
        )
        self.db.add(message)
        self.db.commit()

        return message

    def _is_feature_request(self, message: str) -> bool:
        """
        Determine if a message is a feature request

        Args:
            message: User message

        Returns:
            True if likely a feature request
        """
        feature_indicators = [
            "add", "create", "implement", "build", "make",
            "feature", "functionality", "ability",
            "i want", "i need", "we need", "can you",
            "it should", "it would be nice"
        ]

        message_lower = message.lower()
        return any(indicator in message_lower for indicator in feature_indicators)

    def _get_last_message(self, conversation: Conversation) -> str:
        """
        Get the last message from a conversation

        Args:
            conversation: Conversation object

        Returns:
            Last message content or empty string
        """
        if conversation.messages:
            last_message = sorted(
                conversation.messages,
                key=lambda m: m.created_at,
                reverse=True
            )[0]
            return last_message.content[:100]

        return ""
