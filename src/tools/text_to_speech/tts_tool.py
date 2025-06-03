from typing import Optional, ClassVar
from pathlib import Path
import os
import tempfile

from gtts import gTTS
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class TextToSpeechInput(BaseModel):
    """输入参数模型"""
    text: str = Field(..., description="需要转换成语音的文本")
    language: str = Field(default="zh", description="目标语言，例如：'zh' 代表中文，'en' 代表英文")
    output_path: Optional[str] = Field(default=None, description="输出音频文件的路径，如果不指定则使用临时文件")


class TextToSpeechTool(BaseTool):
    """文字转语音工具"""
    name: ClassVar[str] = "text_to_speech"
    description: ClassVar[str] = "将文本转换成语音文件"
    args_schema: ClassVar[type[BaseModel]] = TextToSpeechInput

    def _run(self, text: str, language: str = "zh", output_path: Optional[str] = None) -> str:
        """
        执行文字转语音转换

        Args:
            text: 要转换的文本
            language: 目标语言代码
            output_path: 输出文件路径

        Returns:
            str: 生成的音频文件路径
        """
        try:
            # 创建 gTTS 对象
            tts = gTTS(text=text, lang=language, slow=False)

            # 如果没有指定输出路径，使用临时文件
            if not output_path:
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, f"tts_output_{hash(text)}.mp3")

            # 确保输出目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            # 保存音频文件
            tts.save(output_path)

            return output_path
        except Exception as e:
            raise Exception(f"文字转语音失败: {str(e)}")

    async def _arun(self, text: str, language: str = "zh", output_path: Optional[str] = None) -> str:
        """异步执行文字转语音转换"""
        return self._run(text, language, output_path)
