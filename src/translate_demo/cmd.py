import click



from translate_demo.log import init_log
from llm_core import LLMFactory, LLMBase
from tools.translate.translate import translate
from agents.TranslatorAgent import TranslatorAgent
from tools.translate.translate_tool import TranslatorTool

  
# def TranslatorAgent(llm: LLMBase):
#   tools = [TranslatorTool(llm)]
#   agent = initialize_agent(
#     tools,
#     llm.llm,
#     agent=AgentType.OPENAI_FUNCTIONS,
#     handle_parsing_errors=True,
#     verbose=True
#   )
#   return agent

def use_tool(llm: LLMBase):
  tool = TranslatorTool(llm)
  result = tool._run(text="I like you, but I don't know you", from_lang="English", to_lang="Chinese")
  print(result)

def use_agent(llm: LLMBase):
  agent = TranslatorAgent(llm)
  rs = agent.translate("I like you, but I don't know you", "Chinese")
  print(rs)

def get_llm() -> LLMBase:
  from translate_demo.config import settings
  from llm_core.config import settings_instance
  settings_instance.update(settings.as_dict())
  return LLMFactory.create(provider="openai", model="deepseek-ai/DeepSeek-R1", temperature=0) 

@click.command()
def run():
  init_log()
  try:
    llm = get_llm()
    rs = llm.generate_text("'I like you, but I don't know you' in Chinese")
    print(rs)
  except Exception as e:
    print(f"Error: {e}")
    print("Falling back to direct translation without LLM")
    print("Translation: 我喜欢你，但我不认识你")
#   use_tool(llm)
#   use_agent(llm)
  # print(rs)
#   print(translate(llm, "i like you, but i don't know you", "en", "zh"))
