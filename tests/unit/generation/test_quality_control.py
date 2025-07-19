"""
Unit tests for the quality control mechanisms.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_base.core.config import Config
from src.knowledge_base.generation.quality_control import (
    ContentFilter, ContentFilterLevel, QualityAssessment,
    SimpleQualityAssessor, LLMQualityAssessor, AnswerValidator
)


class TestQualityAssessment:
    """Tests for the QualityAssessment class."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        assessment = QualityAssessment(score=0.7)
        assert assessment.score == 0.7
        assert assessment.issues == []
        assert not assessment.filtered
        assert assessment.filter_reason is None
        assert assessment.metadata == {}
    
    def test_init_with_values(self):
        """Test initialization with provided values."""
        assessment = QualityAssessment(
            score=0.8,
            issues=["Issue 1", "Issue 2"],
            filtered=True,
            filter_reason="Harmful content",
            metadata={"key": "value"}
        )
        assert assessment.score == 0.8
        assert assessment.issues == ["Issue 1", "Issue 2"]
        assert assessment.filtered
        assert assessment.filter_reason == "Harmful content"
        assert assessment.metadata == {"key": "value"}
    
    def test_score_clamping(self):
        """Test that scores are clamped between 0 and 1."""
        assert QualityAssessment(score=-0.5).score == 0.0
        assert QualityAssessment(score=1.5).score == 1.0
        assert QualityAssessment(score=0.5).score == 0.5
    
    def test_is_acceptable(self):
        """Test the is_acceptable property."""
        # Score above threshold, not filtered
        assert QualityAssessment(score=0.7).is_acceptable
        
        # Score below threshold, not filtered
        assert not QualityAssessment(score=0.4).is_acceptable
        
        # Score above threshold, but filtered
        assert not QualityAssessment(score=0.7, filtered=True).is_acceptable
        
        # Score below threshold and filtered
        assert not QualityAssessment(score=0.4, filtered=True).is_acceptable
    
    def test_str_representation(self):
        """Test string representation."""
        # Acceptable
        assessment = QualityAssessment(score=0.7)
        assert "ACCEPTABLE" in str(assessment)
        assert "Score: 0.70" in str(assessment)
        
        # Rejected due to low score
        assessment = QualityAssessment(score=0.4)
        assert "REJECTED" in str(assessment)
        
        # Filtered
        assessment = QualityAssessment(score=0.7, filtered=True, filter_reason="Harmful content")
        assert "REJECTED" in str(assessment)
        assert "FILTERED: Harmful content" in str(assessment)
        
        # With issues
        assessment = QualityAssessment(score=0.7, issues=["Issue 1", "Issue 2"])
        assert "Issues: Issue 1, Issue 2" in str(assessment)


class TestContentFilter:
    """Tests for the ContentFilter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
    
    def test_init(self):
        """Test initialization."""
        self.config.generation.filter_level = "high"
        filter = ContentFilter(self.config)
        assert filter.filter_level == ContentFilterLevel.HIGH
    
    def test_filter_content_none_level(self):
        """Test filtering with NONE level."""
        self.config.generation.filter_level = "none"
        filter = ContentFilter(self.config)
        filtered, reason = filter.filter_content("This contains harmful instructions on how to hack")
        assert not filtered
        assert reason is None
    
    def test_filter_content_low_level(self):
        """Test filtering with LOW level."""
        self.config.generation.filter_level = "low"
        filter = ContentFilter(self.config)
        
        # Should filter harmful instructions
        filtered, reason = filter.filter_content("This contains harmful instructions on how to hack")
        assert filtered
        assert "harmful" in reason.lower()
        
        # Should not filter other content
        filtered, reason = filter.filter_content("This is normal content")
        assert not filtered
        assert reason is None
    
    def test_filter_content_medium_level(self):
        """Test filtering with MEDIUM level."""
        self.config.generation.filter_level = "medium"
        filter = ContentFilter(self.config)
        
        # Should filter harmful instructions
        filtered, reason = filter.filter_content("This contains harmful instructions on how to hack")
        assert filtered
        assert "harmful" in reason.lower()
        
        # Should not filter normal content
        filtered, reason = filter.filter_content("This is normal content")
        assert not filtered
        assert reason is None
    
    def test_filter_content_high_level(self):
        """Test filtering with HIGH level."""
        self.config.generation.filter_level = "high"
        filter = ContentFilter(self.config)
        
        # Should filter harmful instructions
        filtered, reason = filter.filter_content("This contains harmful instructions on how to hack")
        assert filtered
        assert "harmful" in reason.lower()
        
        # Should not filter normal content
        filtered, reason = filter.filter_content("This is normal content")
        assert not filtered
        assert reason is None


class TestSimpleQualityAssessor:
    """Tests for the SimpleQualityAssessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.assessor = SimpleQualityAssessor(self.config)
    
    def test_assess_quality_filtered_content(self):
        """Test assessment of filtered content."""
        # Mock the content filter to always filter
        self.assessor.content_filter.filter_content = MagicMock(return_value=(True, "Harmful content"))
        
        assessment = self.assessor.assess_quality("query", "answer")
        assert assessment.filtered
        assert assessment.filter_reason == "Harmful content"
        assert assessment.score == 0.0
        assert not assessment.is_acceptable
    
    def test_assess_quality_short_answer(self):
        """Test assessment of a short answer."""
        # Mock the content filter to not filter
        self.assessor.content_filter.filter_content = MagicMock(return_value=(False, None))
        
        assessment = self.assessor.assess_quality("query", "short")
        assert not assessment.filtered
        assert "too short" in assessment.issues[0].lower()
        assert assessment.score < 1.0
    
    def test_assess_quality_uncertain_answer(self):
        """Test assessment of an uncertain answer."""
        # Mock the content filter to not filter
        self.assessor.content_filter.filter_content = MagicMock(return_value=(False, None))
        
        assessment = self.assessor.assess_quality("query", "I don't know the answer to that question.")
        assert not assessment.filtered
        assert any("uncertainty" in issue.lower() for issue in assessment.issues)
        assert assessment.score < 1.0
    
    def test_assess_quality_irrelevant_answer(self):
        """Test assessment of an irrelevant answer."""
        # Mock the content filter to not filter
        self.assessor.content_filter.filter_content = MagicMock(return_value=(False, None))
        
        assessment = self.assessor.assess_quality(
            "What is the capital of France?", 
            "The weather is nice today."
        )
        assert not assessment.filtered
        assert any("relevant" in issue.lower() for issue in assessment.issues)
        assert assessment.score < 1.0
    
    def test_assess_quality_good_answer(self):
        """Test assessment of a good answer."""
        # Mock the content filter to not filter
        self.assessor.content_filter.filter_content = MagicMock(return_value=(False, None))
        
        assessment = self.assessor.assess_quality(
            "What is the capital of France?", 
            "The capital of France is Paris. It is known for its iconic landmarks like the Eiffel Tower."
        )
        assert not assessment.filtered
        assert not assessment.issues
        assert assessment.score == 1.0
        assert assessment.is_acceptable


@pytest.mark.asyncio
class TestLLMQualityAssessor:
    """Tests for the LLMQualityAssessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        
        # Create a mock generator
        self.mock_generator = AsyncMock()
        
        # Patch the Generator class
        self.generator_patch = patch("src.knowledge_base.generation.quality_control.Generator", return_value=self.mock_generator)
        self.generator_patch.start()
        
        self.assessor = LLMQualityAssessor(self.config)
    
    def teardown_method(self):
        """Tear down test fixtures."""
        self.generator_patch.stop()
    
    async def test_assess_quality_filtered_content(self):
        """Test assessment of filtered content."""
        # Mock the content filter to always filter
        self.assessor.content_filter.filter_content = MagicMock(return_value=(True, "Harmful content"))
        
        assessment = await self.assessor.assess_quality("query", "answer")
        assert assessment.filtered
        assert assessment.filter_reason == "Harmful content"
        assert assessment.score == 0.0
        assert not assessment.is_acceptable
        
        # Generator should not be called
        self.mock_generator.generate.assert_not_called()
    
    async def test_assess_quality_llm_evaluation(self):
        """Test assessment using LLM evaluation."""
        # Mock the content filter to not filter
        self.assessor.content_filter.filter_content = MagicMock(return_value=(False, None))
        
        # Mock the generator response
        self.mock_generator.generate.return_value = """
        Relevance: 8 - The answer directly addresses the query
        Accuracy: 9 - The information provided is correct
        Completeness: 7 - The answer covers the main points
        Clarity: 8 - The answer is well-structured
        
        Overall Score: 8
        
        Issues:
        - Could provide more historical context
        - Missing some specific details
        """
        
        assessment = await self.assessor.assess_quality("What is Paris?", "Paris is the capital of France.")
        assert not assessment.filtered
        assert assessment.score == 0.8
        assert len(assessment.issues) == 2
        assert assessment.is_acceptable
        
        # Generator should be called
        self.mock_generator.generate.assert_called_once()
    
    async def test_assess_quality_parsing_error(self):
        """Test handling of parsing errors in LLM evaluation."""
        # Mock the content filter to not filter
        self.assessor.content_filter.filter_content = MagicMock(return_value=(False, None))
        
        # Mock the generator with invalid response format
        self.mock_generator.generate.return_value = "This is not a properly formatted evaluation"
        
        assessment = await self.assessor.assess_quality("query", "answer")
        assert not assessment.filtered
        assert assessment.score == 0.5  # Default score
        assert len(assessment.issues) == 1
        assert "Failed to parse" in assessment.issues[0]
        assert assessment.is_acceptable  # Default score is acceptable


@pytest.mark.asyncio
class TestAnswerValidator:
    """Tests for the AnswerValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        
        # Create mock assessors
        self.mock_simple_assessor = AsyncMock()
        self.mock_llm_assessor = AsyncMock()
        
        # Patch the assessor classes
        self.simple_patch = patch(
            "src.knowledge_base.generation.quality_control.SimpleQualityAssessor",
            return_value=self.mock_simple_assessor
        )
        self.llm_patch = patch(
            "src.knowledge_base.generation.quality_control.LLMQualityAssessor",
            return_value=self.mock_llm_assessor
        )
        self.simple_patch.start()
        self.llm_patch.start()
    
    def teardown_method(self):
        """Tear down test fixtures."""
        self.simple_patch.stop()
        self.llm_patch.stop()
    
    def test_create_assessor_simple(self):
        """Test creation of simple assessor."""
        self.config.generation.quality_assessor = "simple"
        validator = AnswerValidator(self.config)
        assert validator.assessor == self.mock_simple_assessor
    
    def test_create_assessor_llm(self):
        """Test creation of LLM assessor."""
        self.config.generation.quality_assessor = "llm"
        validator = AnswerValidator(self.config)
        assert validator.assessor == self.mock_llm_assessor
    
    def test_create_assessor_default(self):
        """Test creation of default assessor."""
        self.config.generation.quality_assessor = "unknown"
        validator = AnswerValidator(self.config)
        assert validator.assessor == self.mock_simple_assessor
    
    async def test_validate_answer_acceptable(self):
        """Test validation of an acceptable answer."""
        validator = AnswerValidator(self.config)
        
        # Mock the assessor to return an acceptable assessment
        assessment = QualityAssessment(score=0.8)
        validator.assessor.assess_quality = AsyncMock(return_value=assessment)
        
        is_valid, result_assessment = await validator.validate_answer("query", "answer")
        assert is_valid
        assert result_assessment == assessment
    
    async def test_validate_answer_unacceptable(self):
        """Test validation of an unacceptable answer."""
        validator = AnswerValidator(self.config)
        
        # Mock the assessor to return an unacceptable assessment
        assessment = QualityAssessment(score=0.3)
        validator.assessor.assess_quality = AsyncMock(return_value=assessment)
        
        is_valid, result_assessment = await validator.validate_answer("query", "answer")
        assert not is_valid
        assert result_assessment == assessment
    
    async def test_validate_and_improve_acceptable(self):
        """Test that acceptable answers are not improved."""
        validator = AnswerValidator(self.config)
        
        # Mock the assessor to return an acceptable assessment
        assessment = QualityAssessment(score=0.8)
        validator.assessor.assess_quality = AsyncMock(return_value=assessment)
        
        result = await validator.validate_and_improve("query", "good answer", [])
        assert result == "good answer"
    
    async def test_validate_and_improve_filtered(self):
        """Test improvement of filtered answers."""
        validator = AnswerValidator(self.config)
        
        # Mock the assessor to return a filtered assessment
        assessment = QualityAssessment(score=0.0, filtered=True, filter_reason="Harmful content")
        validator.assessor.assess_quality = AsyncMock(return_value=assessment)
        
        # Mock the generator
        mock_generator = AsyncMock()
        mock_generator.generate.return_value = "safe answer"
        
        with patch("src.knowledge_base.generation.quality_control.Generator", return_value=mock_generator):
            result = await validator.validate_and_improve("query", "harmful answer", [])
            assert result == "safe answer"
            
            # Generator should be called with a safe prompt
            call_args = mock_generator.generate.call_args[0]
            assert "safe" in call_args[0].lower()
    
    async def test_validate_and_improve_low_quality(self):
        """Test improvement of low quality answers."""
        validator = AnswerValidator(self.config)
        
        # Mock the assessor to return a low quality assessment
        assessment = QualityAssessment(score=0.3, issues=["Answer too short"])
        validator.assessor.assess_quality = AsyncMock(return_value=assessment)
        
        # Mock the generator
        mock_generator = AsyncMock()
        mock_generator.generate.return_value = "improved answer"
        
        with patch("src.knowledge_base.generation.quality_control.Generator", return_value=mock_generator):
            result = await validator.validate_and_improve("query", "short answer", [])
            assert result == "improved answer"
            
            # Generator should be called with an improvement prompt
            call_args = mock_generator.generate.call_args[0]
            assert "improved" in call_args[0].lower()
            assert "issues" in call_args[0].lower()