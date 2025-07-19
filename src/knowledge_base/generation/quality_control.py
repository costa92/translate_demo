"""
Quality control mechanisms for generated content.

This module provides utilities for assessing and ensuring the quality of generated content,
including content filtering and answer validation.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

from ..core.config import Config
from ..core.exceptions import GenerationError


class ContentFilterLevel(Enum):
    """Enumeration of content filter levels."""
    NONE = "none"  # No filtering
    LOW = "low"    # Filter only the most harmful content
    MEDIUM = "medium"  # Balance between permissiveness and safety
    HIGH = "high"  # Strict filtering for sensitive contexts


class QualityAssessment:
    """Result of a quality assessment."""
    
    def __init__(
        self,
        score: float,
        issues: List[str] = None,
        filtered: bool = False,
        filter_reason: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize a quality assessment result.
        
        Args:
            score: Quality score between 0.0 and 1.0
            issues: List of identified issues
            filtered: Whether the content was filtered
            filter_reason: Reason for filtering, if applicable
            metadata: Additional metadata about the assessment
        """
        self.score = max(0.0, min(1.0, score))  # Clamp between 0 and 1
        self.issues = issues or []
        self.filtered = filtered
        self.filter_reason = filter_reason
        self.metadata = metadata or {}
    
    @property
    def is_acceptable(self) -> bool:
        """Whether the content meets the minimum quality threshold."""
        return not self.filtered and self.score >= 0.5
    
    def __str__(self) -> str:
        """String representation of the quality assessment."""
        status = "ACCEPTABLE" if self.is_acceptable else "REJECTED"
        if self.filtered:
            reason = f" (FILTERED: {self.filter_reason})"
        else:
            reason = ""
        
        issues_str = f"\nIssues: {', '.join(self.issues)}" if self.issues else ""
        return f"Quality Assessment: {status}{reason} - Score: {self.score:.2f}{issues_str}"


class ContentFilter:
    """Filters inappropriate or harmful content."""
    
    def __init__(self, config: Config):
        """
        Initialize the content filter.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.filter_level = ContentFilterLevel(config.generation.filter_level)
    
    def filter_content(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Filter content for inappropriate or harmful material.
        
        Args:
            content: The content to filter
            
        Returns:
            Tuple of (filtered, reason) where filtered is a boolean indicating
            whether the content should be filtered, and reason is the reason
            for filtering (if applicable)
        """
        # Skip filtering if level is NONE
        if self.filter_level == ContentFilterLevel.NONE:
            return False, None
        
        # Simple keyword-based filtering for demonstration
        # In a real implementation, this would use more sophisticated techniques
        harmful_patterns = self._get_harmful_patterns()
        
        for category, patterns in harmful_patterns.items():
            for pattern in patterns:
                if pattern.lower() in content.lower():
                    return True, f"Content contains harmful material: {category}"
        
        return False, None
    
    def _get_harmful_patterns(self) -> Dict[str, List[str]]:
        """
        Get patterns of harmful content based on the filter level.
        
        Returns:
            Dictionary mapping categories to lists of harmful patterns
        """
        # This is a simplified implementation
        # A real implementation would use more sophisticated techniques
        
        patterns = {
            "harmful_instructions": [
                "how to hack",
                "how to steal",
                "how to ddos",
                "how to create malware",
            ],
            "hate_speech": [
                "hate speech patterns would be defined here",
            ],
            "personal_attacks": [
                "personal attack patterns would be defined here",
            ],
        }
        
        # Adjust patterns based on filter level
        if self.filter_level == ContentFilterLevel.LOW:
            # Only the most harmful patterns
            return {"harmful_instructions": patterns["harmful_instructions"]}
        elif self.filter_level == ContentFilterLevel.MEDIUM:
            # Harmful instructions and hate speech
            return {
                "harmful_instructions": patterns["harmful_instructions"],
                "hate_speech": patterns["hate_speech"],
            }
        elif self.filter_level == ContentFilterLevel.HIGH:
            # All patterns
            return patterns
        
        return {}


class QualityAssessor(ABC):
    """Base class for quality assessment strategies."""
    
    @abstractmethod
    async def assess_quality(self, query: str, answer: str) -> QualityAssessment:
        """
        Assess the quality of a generated answer.
        
        Args:
            query: The original query
            answer: The generated answer
            
        Returns:
            QualityAssessment result
        """
        pass


class SimpleQualityAssessor(QualityAssessor):
    """Simple quality assessment based on heuristics."""
    
    def __init__(self, config: Config):
        """
        Initialize the simple quality assessor.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.content_filter = ContentFilter(config)
        
    async def assess_quality(self, query: str, answer: str) -> QualityAssessment:
        """
        Assess the quality of a generated answer using simple heuristics.
        
        Args:
            query: The original query
            answer: The generated answer
            
        Returns:
            QualityAssessment result
        """
        issues = []
        score = 1.0  # Start with perfect score
        
        # Check for content filtering
        filtered, filter_reason = self.content_filter.filter_content(answer)
        if filtered:
            return QualityAssessment(
                score=0.0,
                filtered=True,
                filter_reason=filter_reason
            )
        
        # Check answer length
        if len(answer) < 10:
            issues.append("Answer too short")
            score -= 0.3
        
        # Check if answer contains "I don't know" or similar phrases
        uncertainty_phrases = ["i don't know", "i am not sure", "i cannot", "i can't"]
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            issues.append("Answer expresses uncertainty")
            score -= 0.2
        
        # Check if answer is relevant to query
        # Simple check: do query keywords appear in the answer?
        query_keywords = set(query.lower().split())
        answer_words = set(answer.lower().split())
        common_words = query_keywords.intersection(answer_words)
        if len(common_words) < min(2, len(query_keywords) / 3):
            issues.append("Answer may not be relevant to query")
            score -= 0.3
        
        return QualityAssessment(
            score=max(0.0, score),
            issues=issues
        )


class LLMQualityAssessor(QualityAssessor):
    """Quality assessment using an LLM to evaluate answers."""
    
    def __init__(self, config: Config):
        """
        Initialize the LLM quality assessor.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.content_filter = ContentFilter(config)
        
        # Import here to avoid circular imports
        from .generator import Generator
        self.generator = Generator(config)
        
    async def assess_quality(self, query: str, answer: str) -> QualityAssessment:
        """
        Assess the quality of a generated answer using an LLM.
        
        Args:
            query: The original query
            answer: The generated answer
            
        Returns:
            QualityAssessment result
        """
        # First check content filtering
        filtered, filter_reason = self.content_filter.filter_content(answer)
        if filtered:
            return QualityAssessment(
                score=0.0,
                filtered=True,
                filter_reason=filter_reason
            )
        
        # Create a prompt for the LLM to evaluate the answer
        evaluation_prompt = f"""
        You are an AI assistant tasked with evaluating the quality of an answer to a user query.
        
        User Query: {query}
        
        Generated Answer: {answer}
        
        Please evaluate the answer on the following criteria:
        1. Relevance: How relevant is the answer to the query?
        2. Accuracy: Does the answer contain factual errors?
        3. Completeness: Does the answer fully address the query?
        4. Clarity: Is the answer clear and well-structured?
        
        For each criterion, provide a score from 0 to 10 and a brief explanation.
        Then provide an overall score from 0 to 10 and a list of any issues with the answer.
        
        Format your response as follows:
        
        Relevance: [score] - [explanation]
        Accuracy: [score] - [explanation]
        Completeness: [score] - [explanation]
        Clarity: [score] - [explanation]
        
        Overall Score: [score]
        
        Issues:
        - [issue 1]
        - [issue 2]
        ...
        """
        
        # Generate evaluation
        evaluation = await self.generator.generate(evaluation_prompt, [])
        
        # Parse evaluation
        try:
            # Extract overall score
            score_line = [line for line in evaluation.split('\n') if "Overall Score:" in line][0]
            score_str = score_line.split("Overall Score:")[1].strip()
            score = float(score_str) / 10.0  # Convert 0-10 score to 0-1
            
            # Extract issues
            issues_section = evaluation.split("Issues:")[1].strip() if "Issues:" in evaluation else ""
            issues = [issue.strip("- ").strip() for issue in issues_section.split("\n") if issue.strip()]
            
            return QualityAssessment(
                score=score,
                issues=issues
            )
        except Exception as e:
            # If parsing fails, return a default assessment
            return QualityAssessment(
                score=0.5,
                issues=["Failed to parse quality assessment"]
            )


class AnswerValidator:
    """Validates generated answers against quality criteria."""
    
    def __init__(self, config: Config):
        """
        Initialize the answer validator.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.assessor = self._create_assessor()
        
    def _create_assessor(self) -> QualityAssessor:
        """
        Create a quality assessor based on configuration.
        
        Returns:
            QualityAssessor instance
        """
        assessor_type = self.config.generation.quality_assessor
        if assessor_type == "llm":
            return LLMQualityAssessor(self.config)
        else:
            return SimpleQualityAssessor(self.config)
    
    async def validate_answer(self, query: str, answer: str) -> Tuple[bool, QualityAssessment]:
        """
        Validate a generated answer.
        
        Args:
            query: The original query
            answer: The generated answer
            
        Returns:
            Tuple of (is_valid, assessment)
        """
        assessment = await self.assessor.assess_quality(query, answer)
        return assessment.is_acceptable, assessment
    
    async def validate_and_improve(self, query: str, answer: str, chunks: List) -> str:
        """
        Validate an answer and improve it if necessary.
        
        Args:
            query: The original query
            answer: The generated answer
            chunks: The context chunks used to generate the answer
            
        Returns:
            Improved answer or original if already acceptable
        """
        is_valid, assessment = await self.validate_answer(query, answer)
        
        if is_valid:
            return answer
        
        # If the answer was filtered, generate a safe alternative
        if assessment.filtered:
            from .generator import Generator
            generator = Generator(self.config)
            
            safe_prompt = f"""
            The user asked: {query}
            
            Please provide a helpful and safe response that addresses the query
            without including any harmful, inappropriate, or offensive content.
            """
            
            return await generator.generate(safe_prompt, chunks)
        
        # If the answer has quality issues, try to improve it
        if assessment.issues:
            from .generator import Generator
            generator = Generator(self.config)
            
            improvement_prompt = f"""
            The user asked: {query}
            
            An initial response was generated, but it has the following issues:
            {', '.join(assessment.issues)}
            
            Initial response: {answer}
            
            Please provide an improved response that addresses these issues while
            answering the original query accurately and completely.
            """
            
            return await generator.generate(improvement_prompt, chunks)
        
        # If we can't improve it, return the original
        return answer