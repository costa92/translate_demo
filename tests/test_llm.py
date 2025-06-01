import pytest
from unittest.mock import patch, MagicMock
from translate_demo.llm.llm import LLM, get_llm, get_ollama_llm, get_deepseek_llm
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_deepseek import ChatDeepSeek

@pytest.fixture
def mock_settings():
    with patch('translate_demo.llm.llm.settings') as mock_settings:
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

def test_get_llm(mock_settings):
    llm = get_llm()
    assert isinstance(llm, ChatOpenAI)
    assert llm.model == 'gpt-4'
    assert llm.openai_api_key == 'test-key'
    assert llm.base_url == 'https://api.openai.com/v1'

def test_get_llm_with_custom_params(mock_settings):
    llm = get_llm(model="gpt-3.5-turbo", temperature=0.7)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model == 'gpt-3.5-turbo'
    assert llm.temperature == 0.7

def test_get_ollama_llm(mock_settings):
    llm = get_ollama_llm()
    assert isinstance(llm, ChatOllama)
    assert llm.model == 'llama2'
    assert llm.base_url == 'http://localhost:11434'

def test_get_ollama_llm_with_custom_params(mock_settings):
    llm = get_ollama_llm(model="mistral", temperature=0.5)
    assert isinstance(llm, ChatOllama)
    assert llm.model == 'mistral'
    assert llm.temperature == 0.5

def test_get_deepseek_llm(mock_settings):
    llm = get_deepseek_llm()
    assert isinstance(llm, ChatDeepSeek)
    assert llm.model == 'deepseek-test'
    assert llm.api_key == 'test-key'
    assert llm.base_url == 'https://api.deepseek.com'

def test_get_deepseek_llm_with_custom_params(mock_settings):
    llm = get_deepseek_llm(model="deepseek-custom", temperature=0.3)
    assert isinstance(llm, ChatDeepSeek)
    assert llm.model == 'deepseek-custom'
    assert llm.temperature == 0.3

def test_llm_class_openai(mock_settings):
    llm = LLM(llm_type="openai")
    assert isinstance(llm.llm, ChatOpenAI)

def test_llm_class_ollama(mock_settings):
    llm = LLM(llm_type="ollama")
    assert isinstance(llm.llm, ChatOllama)

def test_llm_class_deepseek(mock_settings):
    llm = LLM(llm_type="deepseek")
    assert isinstance(llm.llm, ChatDeepSeek)

def test_llm_class_invalid_type():
    with pytest.raises(ValueError) as exc_info:
        LLM(llm_type="invalid")
    assert "Unsupported LLM type" in str(exc_info.value)

def test_llm_class_with_custom_params(mock_settings):
    llm = LLM(model="custom-model", temperature=0.8, llm_type="openai")
    assert isinstance(llm.llm, ChatOpenAI)
    assert llm.llm.model == "custom-model"
    assert llm.llm.temperature == 0.8 
