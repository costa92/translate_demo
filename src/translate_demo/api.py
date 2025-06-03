from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools.translate.translate import translate
from llm_core import LLMFactory, LLMBase
import asyncio
import uvicorn
from translate_demo.config import settings
from llm_core.config import settings_instance

app = FastAPI()

class TranslateRequest(BaseModel):
    text: str
    from_lang: str
    to_lang: str

def get_llm() -> LLMBase:
    settings_instance.update(settings.as_dict())
    return LLMFactory.create(provider="deepseek", model="deepseek-chat", temperature=0)

@app.post("/api/translate")
async def api_translate(req: TranslateRequest):
    llm = get_llm()
    # 获取当前事件循环 asyncio
    loop = asyncio.get_event_loop()
    try:
        # 假如 translate 是同步的，用 run_in_executor 包装
        result = await loop.run_in_executor(None, translate, llm, req.text, req.from_lang, req.to_lang)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    host = settings.API_HOST
    port = settings.API_PORT
    print(f"[INFO] API will start at http://{host}:{port}")
    uvicorn.run("translate_demo.api:app", host=host, port=port, reload=True)
