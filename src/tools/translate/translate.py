# Compare this snippet from src/tools/translate/translate_tool.py:
from .config import system_prompt
from llm_core import LLMBase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

"""
翻译函数，使用大语言模型将文本从一种语言翻译成另一种语言。

:param llm: 大语言模型实例
:param text: 需要翻译的文本
:param from_lang: 源语言
:param to_lang: 目标语言
:return: 翻译后的文本
:raises ValueError: 如果模型输出为空
"""
# 翻译函数
def translate(llm: LLMBase, text: str, from_lang: str, to_lang: str):
  # partial is used to bind the variables to the prompt template
  prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{text}")
  ]).partial(from_lang=from_lang, to_lang=to_lang)

  #  StrOutputParser 是langchain的输出解析器，用于将LLM的输出转换为字符串
  # 构建链：prompt -> LLM -> 解析器
  llm_chain = prompt_template | llm.llm | StrOutputParser()
  rs =  llm_chain.invoke({"text": text})
  if rs == "":
    raise ValueError(f"Output is empty: {rs}")
  return rs.replace(" ", "").replace("\n", "")

