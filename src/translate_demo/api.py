from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools.translate.translate import translate
from llm_core import LLMFactory, LLMBase
import asyncio

app = FastAPI()

class TranslateRequest(BaseModel):
    text: str
    from_lang: str
    to_lang: str

def get_llm() -> LLMBase:
    from translate_demo.config import settings
    from llm_core.config import settings_instance
    settings_instance.update(settings.as_dict())
    return LLMFactory.create(provider="deepseek", model="deepseek-chat", temperature=0)

@app.post("/api/translate")
async def api_translate(req: TranslateRequest):
    llm = get_llm()
    loop = asyncio.get_event_loop()
    try:
        # 假如 translate 是同步的，用 run_in_executor 包装
        result = await loop.run_in_executor(None, translate, llm, req.text, req.from_lang, req.to_lang)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    import uvicorn
    uvicorn.run("translate_demo.api:app", host="0.0.0.0", port=8080, reload=True) 