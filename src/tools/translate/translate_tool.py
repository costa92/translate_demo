from typing import Type # For type hinting
from pydantic import BaseModel,Field
from langchain_core.tools import BaseTool
from pydantic import PrivateAttr
from llm_core import LLMBase
from tools.translate.translate import translate

# 翻译输入模型
class TranslationInput(BaseModel):
    text: str = Field(description="The text to translate")
    from_lang: str = Field(description="Source language")
    to_lang: str = Field(description="Target language")

# 翻译工具
class TranslatorTool(BaseTool):
    name: str = "translate"
    description: str = "Translate text from one language to another"
    args_schema: Type[TranslationInput] = TranslationInput

    _llm: LLMBase = PrivateAttr()

    def __init__(self, llm: LLMBase, **kwargs):
        super().__init__(**kwargs)
        self._llm = llm

    def _run(self, text: str, from_lang: str, to_lang: str) -> str:
        return translate(self._llm, text, from_lang, to_lang)
