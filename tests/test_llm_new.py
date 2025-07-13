import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import patch, MagicMock
from llm_core.factory import LLMFactory
from llm_core.base import LLMBase as LLM
from llm_core.openai.provider import OpenAILLM
from llm_core.ollama.provider import OllamaLLM
from llm_core.deepseek.provider import DeepSeekLLM
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_deepseek import ChatDeepSeek


@pytest.fixture
def mock_settings():
    with patch('llm_core.config.settings_instance') as mock_settings:
        mock_settings.get.side_effect = lambda key, default=None: {
            'OPENAI_MODEL': 'gpt-4',
            'OPENAI_API_KEY': 'test-key',
            'OPENAI_BASE_URL': 'https://api.openai.com/v1',
            'OLLAMA_MODEL': 'llama2',
            'OLLAMA_BASE_URL': 'http://localhost:11434',
            'DEEPSEEK_MODEL': 'deepseek-test',
            'DEEPSEEK_API_KEY': 'test-key',
            'DEEPSEEK_BASE_URL': 'https://api.deepseek.com'
        }.get(key, default)
        yield mock_settings


def test_openai_llm(mock_settings):
    llm = OpenAILLM()
    assert isinstance(llm.llm, ChatOpenAI)
    assert llm.model == 'gpt-4'
    assert llm.api_key == 'test-key'
    assert llm.base_url == 'https://api.openai.com/v1'


def test_openai_llm_with_custom_params(mock_settings):
    llm = OpenAILLM(model="gpt-3.5-turbo", temperature=0.7)
    assert isinstance(llm.llm, ChatOpenAI)
    assert llm.model == 'gpt-3.5-turbo'
    assert llm.temperature == 0.7


def test_ollama_llm(mock_settings):
    llm = OllamaLLM()
    assert isinstance(llm.llm, ChatOllama)
    assert llm.model == 'llama2'
    assert llm.base_url == 'http://localhost:11434'


def test_ollama_llm_with_custom_params(mock_settings):
    llm = OllamaLLM(model="mistral", temperature=0.5)
    assert isinstance(llm.llm, ChatOllama)
    assert llm.model == 'mistral'
    assert llm.temperature == 0.5


def test_deepseek_llm(mock_settings):
    llm = DeepSeekLLM()
    assert isinstance(llm.llm, ChatDeepSeek)
    assert llm.model == 'deepseek-test'
    assert llm.api_key == 'test-key'
    assert llm.base_url == 'https://api.deepseek.com'


def test_deepseek_llm_with_custom_params(mock_settings):
    llm = DeepSeekLLM(model="deepseek-custom", temperature=0.3)
    assert isinstance(llm.llm, ChatDeepSeek)
    assert llm.model == 'deepseek-custom'
    assert llm.temperature == 0.3


def test_llm_factory_openai(mock_settings):
    llm = LLMFactory.create(provider="openai")
    assert isinstance(llm, OpenAILLM)
    assert isinstance(llm.llm, ChatOpenAI)


def test_llm_factory_ollama(mock_settings):
    llm = LLMFactory.create(provider="ollama")
    assert isinstance(llm, OllamaLLM)
    assert isinstance(llm.llm, ChatOllama)


def test_llm_factory_deepseek(mock_settings):
    llm = LLMFactory.create(provider="deepseek")
    assert isinstance(llm, DeepSeekLLM)
    assert isinstance(llm.llm, ChatDeepSeek)


def test_llm_factory_invalid_provider():
    with pytest.raises(ValueError) as exc_info:
        LLMFactory.create(provider="invalid")
    assert "Unsupported LLM provider" in str(exc_info.value)


def test_llm_factory_with_custom_params(mock_settings):
    llm = LLMFactory.create(provider="openai", model="custom-model", temperature=0.8)
    assert isinstance(llm, OpenAILLM)
    assert isinstance(llm.llm, ChatOpenAI)
    assert llm.model == "custom-model"
    assert llm.temperature == 0.8