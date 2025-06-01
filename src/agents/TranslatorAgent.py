from tools.translate.translate_tool import TranslatorTool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class TranslatorAgent:
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        # 定义提示模板（Prompt）
        # 正确的 prompt（包含 agent_scratchpad）
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a helpful translation assistant."),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),  # ✅ 必须有
        ])


        # 提前初始化工具列表
        self.tools = [TranslatorTool(self.llm)]

       # 创建 Agent
        self.agent = create_openai_functions_agent(
            llm=self.llm.llm,
            tools=self.tools,
            prompt=self.prompt,
        )

        # 创建执行器
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

    def translate(self, text: str, target_language: str):
        # 构造 prompt
        prompt = f"Translate the following text to {target_language}:\n\n{text}"

        # 执行 agent
        result = self.executor.invoke({"input": prompt})

        # 可选：提取输出字段
        return result.get("output", result)  # 视输出结构而定

    

