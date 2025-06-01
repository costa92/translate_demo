import pytest
from unittest.mock import patch, MagicMock
from translate_demo.llm import LLMFactory, LLM
from translate_demo.llm.openai import OpenAILLM
from translate_demo.llm.ollama import OllamaLLM
from translate_demo.llm.deepseek import DeepSeekLLM
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_deepseek import ChatDeepSeek


@pytest.fixture
def mock_settings():
    with patch('translate_demo.llm.openai.provider.settings') as mock_settings_openai, \
         patch('translate_demo.llm.ollama.provider.settings') as mock_settings_ollama, \
         patch('translate_demo.llm.deepseek.provider.settings') as mock_settings_deepseek:
        
        # 为所有模块设置相同的mock行为
        for mock_settings in [mock_settings_openai, mock_settings_ollama, mock_settings_deepseek]:
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
        
        yield mock_settings_openai


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