import click
import asyncio


from translate_demo.log import init_log
from llm_core import LLMFactory, LLMBase
from tools.translate.translate import translate_async
from agents.TranslatorAgent import TranslatorAgent
from tools.translate.translate_tool import TranslatorTool
from tools.text_to_speech.tts_tool import TextToSpeechTool


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

def get_llm_openai() -> LLMBase:
  from translate_demo.config import settings
  from llm_core.config import settings_instance
  settings_instance.update(settings.as_dict())
  return LLMFactory.create(provider="openai", model="deepseek-ai/DeepSeek-R1", temperature=0)

def get_llm_ollama() -> LLMBase:
  from translate_demo.config import settings
  from llm_core.config import settings_instance
  settings_instance.update(settings.as_dict())
  return LLMFactory.create(provider="ollama", model="qwen3:8b", temperature=0)

def get_llm_deepseek() -> LLMBase:
  from translate_demo.config import settings
  from llm_core.config import settings_instance
  settings_instance.update(settings.as_dict())
  return LLMFactory.create(provider="deepseek", model="deepseek-chat", temperature=0)

async def async_run():
  init_log()

  text_to_translate = "I like you, but I don't know you"
  target_language = "Chinese"

  print(f"\n🔄 Translating: '{text_to_translate}' to {target_language}\n")

  # Try different providers
  providers = [
    # ("Ollama (local LLM)", get_llm_ollama),
    # ("DeepSeek", get_llm_deepseek),
    ("OpenAI", get_llm_openai),
  ]

  translation = None
  for provider_name, provider_func in providers:
    print(f"\n▶️ Trying {provider_name}...")
    try:
      llm = provider_func()
      translation = await translate_async(llm, text=text_to_translate, from_lang="English", to_lang="Chinese")
      print(f"✅ Success! Translation: {translation}")
      break  # Use the first successful provider
    except Exception as e:
      print(f"❌ Error with {provider_name}: {e}")
  else:
    # Fallback if all providers fail
    translation = "我喜欢你，但我不认识你"
    print("\n⚠️ All providers failed. Using fallback translation:")
    print(f"Translation: {translation}")

  # 将翻译结果转换为语音
  if translation:
    print("\n🔊 Converting translation to speech...")
    try:
      tts_tool = TextToSpeechTool()
      audio_path = tts_tool._run(text=translation, language="zh", output_path="output.mp3")
      print(f"✅ Audio file generated at: {audio_path}")
    except Exception as e:
      print(f"❌ Text-to-speech conversion failed: {e}")

@click.command()
def run():
    """Entry point for the translate command"""
    asyncio.run(async_run())

if __name__ == "__main__":
    run()
