import click



from translate_demo.log import init_log
from llm_core import LLMFactory, LLM
from tools.translate.translate import translate
from agents.TranslatorAgent import TranslatorAgent

  
# def TranslatorAgent(llm: LLM):
#   tools = [TranslatorTool(llm)]
#   agent = initialize_agent(
#     tools,
#     llm.llm,
#     agent=AgentType.OPENAI_FUNCTIONS,
#     handle_parsing_errors=True,
#     verbose=True
#   )
#   return agent

def use_tool(llm: LLM):
  tool = agents.TranslatorTool(llm)
  result = tool._run(text="I like you, but I don't know you", from_lang="English", to_lang="Chinese")
  print(result)

def use_agent(llm: LLM):
  agent = TranslatorAgent(llm)
  rs = agent.translate("I like you, but I don't know you", "Chinese")
  print(rs)

def get_llm() -> LLM:
  from translate_demo.config import settings
  from llm_core.config import settings_instance
  settings_instance.update(settings.as_dict())
  return LLMFactory.create(provider="openai", model="deepseek-ai/DeepSeek-R1", temperature=0)

@click.command()
def run():
  init_log()
  llm = get_llm()
#   use_tool(llm)
  use_agent(llm)
  # print(rs)
#   print(translate(llm, "i like you, but i don't know you", "en", "zh"))
