"""
Feature Analysis Service
"""

import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import logging

from app.models.github_integration import IssueDifficulty

logger = logging.getLogger(__name__)


@dataclass
class FeatureAnalysis:
    """Analysis result for a feature request"""
    title: str
    description: str
    difficulty: IssueDifficulty
    complexity_score: int  # 1-100
    estimated_hours: int
    components: List[str]  # Affected components
    risks: List[str]
    requirements: List[str]
    labels: List[str]  # GitHub labels to apply


class FeatureAnalyzer:
    """Service for analyzing and classifying feature requests"""

    # Keywords indicating complexity
    COMPLEXITY_INDICATORS = {
        "easy": [
            "simple", "basic", "minor", "small", "typo", "text", "label",
            "color", "style", "css", "rename", "update message", "tooltip"
        ],
        "medium": [
            "add", "new feature", "integrate", "api", "endpoint", "component",
            "validation", "form", "table", "list", "search", "filter"
        ],
        "hard": [
            "complex", "architecture", "refactor", "migration", "security",
            "performance", "real-time", "websocket", "machine learning",
            "ai", "optimization", "scale", "distributed"
        ]
    }

    # Component detection patterns
    COMPONENT_PATTERNS = {
        "frontend": ["ui", "frontend", "react", "component", "page", "view", "style"],
        "backend": ["api", "backend", "server", "database", "endpoint", "service"],
        "database": ["database", "table", "migration", "schema", "model", "query"],
        "authentication": ["auth", "login", "oauth", "permission", "role", "access"],
        "integration": ["integrate", "third-party", "external", "api", "webhook"],
        "testing": ["test", "testing", "unit test", "integration test", "e2e"],
        "documentation": ["docs", "documentation", "readme", "comment", "guide"],
        "deployment": ["deploy", "deployment", "ci/cd", "docker", "kubernetes"]
    }

    def analyze_feature_request(self, message: str) -> FeatureAnalysis:
        """
        Analyze a feature request message

        Args:
            message: User's feature request message

        Returns:
            FeatureAnalysis object with classification
        """
        # Extract title and description
        title, description = self._extract_title_and_description(message)

        # Detect components
        components = self._detect_components(message.lower())

        # Calculate complexity
        complexity_score, difficulty = self._calculate_complexity(
            message.lower(),
            components
        )

        # Estimate hours
        estimated_hours = self._estimate_hours(complexity_score, difficulty)

        # Identify risks
        risks = self._identify_risks(message.lower(), components)

        # Extract requirements
        requirements = self._extract_requirements(message)

        # Generate labels
        labels = self._generate_labels(components, difficulty)

        return FeatureAnalysis(
            title=title,
            description=description,
            difficulty=difficulty,
            complexity_score=complexity_score,
            estimated_hours=estimated_hours,
            components=components,
            risks=risks,
            requirements=requirements,
            labels=labels
        )

    def _extract_title_and_description(self, message: str) -> Tuple[str, str]:
        """
        Extract a title and description from the message

        Args:
            message: User message

        Returns:
            Tuple of (title, description)
        """
        lines = message.strip().split('\n')

        # First line or first sentence as title
        if lines:
            first_line = lines[0].strip()
            # Limit title length
            if len(first_line) > 100:
                # Find first sentence
                sentences = re.split(r'[.!?]', first_line)
                if sentences:
                    title = sentences[0].strip()[:100]
                else:
                    title = first_line[:100]
            else:
                title = first_line

            # Rest as description
            if len(lines) > 1:
                description = '\n'.join(lines[1:]).strip()
            else:
                description = message.strip()
        else:
            title = "Feature Request"
            description = message.strip()

        # Clean up title
        title = re.sub(r'^(I want|I need|Can you|Please|Could you)\s+', '', title, flags=re.IGNORECASE)
        title = title.capitalize()

        return title, description

    def _detect_components(self, message_lower: str) -> List[str]:
        """
        Detect which components are affected

        Args:
            message_lower: Lowercase message

        Returns:
            List of component names
        """
        detected = []

        for component, keywords in self.COMPONENT_PATTERNS.items():
            if any(keyword in message_lower for keyword in keywords):
                detected.append(component)

        # Default to general if nothing detected
        if not detected:
            detected = ["general"]

        return detected

    def _calculate_complexity(
        self,
        message_lower: str,
        components: List[str]
    ) -> Tuple[int, IssueDifficulty]:
        """
        Calculate complexity score and difficulty

        Args:
            message_lower: Lowercase message
            components: Detected components

        Returns:
            Tuple of (complexity_score, difficulty)
        """
        score = 0

        # Check for complexity indicators
        easy_count = sum(1 for word in self.COMPLEXITY_INDICATORS["easy"] if word in message_lower)
        medium_count = sum(1 for word in self.COMPLEXITY_INDICATORS["medium"] if word in message_lower)
        hard_count = sum(1 for word in self.COMPLEXITY_INDICATORS["hard"] if word in message_lower)

        # Base score from indicators
        score += easy_count * 5
        score += medium_count * 15
        score += hard_count * 30

        # Adjust based on component count
        score += len(components) * 10

        # Adjust based on message length (more detailed = more complex)
        word_count = len(message_lower.split())
        if word_count > 100:
            score += 20
        elif word_count > 50:
            score += 10
        elif word_count < 20:
            score -= 10

        # Check for specific patterns
        if "from scratch" in message_lower or "new system" in message_lower:
            score += 30
        if "small change" in message_lower or "quick fix" in message_lower:
            score -= 20

        # Normalize score
        score = max(1, min(100, score))

        # Determine difficulty
        if score <= 30:
            difficulty = IssueDifficulty.EASY
        elif score <= 70:
            difficulty = IssueDifficulty.MEDIUM
        else:
            difficulty = IssueDifficulty.HARD

        return score, difficulty

    def _estimate_hours(self, complexity_score: int, difficulty: IssueDifficulty) -> int:
        """
        Estimate hours based on complexity

        Args:
            complexity_score: Complexity score (1-100)
            difficulty: Difficulty level

        Returns:
            Estimated hours
        """
        if difficulty == IssueDifficulty.EASY:
            return max(1, complexity_score // 10)
        elif difficulty == IssueDifficulty.MEDIUM:
            return max(4, complexity_score // 5)
        else:
            return max(8, complexity_score // 3)

    def _identify_risks(self, message_lower: str, components: List[str]) -> List[str]:
        """
        Identify potential risks

        Args:
            message_lower: Lowercase message
            components: Detected components

        Returns:
            List of risk descriptions
        """
        risks = []

        # Security risks
        if any(word in message_lower for word in ["auth", "security", "permission", "access"]):
            risks.append("Security implications - requires careful review")

        # Performance risks
        if any(word in message_lower for word in ["scale", "performance", "optimize", "real-time"]):
            risks.append("Performance impact - requires load testing")

        # Data risks
        if any(word in message_lower for word in ["migration", "database", "schema"]):
            risks.append("Data migration required - backup recommended")

        # Integration risks
        if "integration" in components or "external" in message_lower:
            risks.append("External dependency - may affect reliability")

        # Breaking changes
        if any(word in message_lower for word in ["refactor", "redesign", "breaking"]):
            risks.append("Potential breaking changes - version planning needed")

        return risks

    def _extract_requirements(self, message: str) -> List[str]:
        """
        Extract specific requirements from message

        Args:
            message: User message

        Returns:
            List of requirements
        """
        requirements = []

        # Look for bullet points or numbered lists
        lines = message.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(r'^[-*•]\s+', line):
                requirement = re.sub(r'^[-*•]\s+', '', line)
                requirements.append(requirement)
            elif re.match(r'^\d+[.)]\s+', line):
                requirement = re.sub(r'^\d+[.)]\s+', '', line)
                requirements.append(requirement)

        # Look for "should" or "must" statements
        should_patterns = re.findall(
            r'(?:should|must|need to|has to)\s+([^.,\n]+)',
            message,
            re.IGNORECASE
        )
        for pattern in should_patterns[:3]:  # Limit to 3
            if pattern not in requirements:
                requirements.append(pattern.strip())

        return requirements

    def _generate_labels(
        self,
        components: List[str],
        difficulty: IssueDifficulty
    ) -> List[str]:
        """
        Generate GitHub labels

        Args:
            components: Detected components
            difficulty: Difficulty level

        Returns:
            List of label names
        """
        labels = ["feature-request", "auto-generated"]

        # Add component labels
        for component in components:
            if component != "general":
                labels.append(f"component:{component}")

        # Note: difficulty label is added separately in GitHub service

        return labels
