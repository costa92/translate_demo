from llm_core.client import LLMClient

class RAGAgent:
    """
    The RAGAgent is responsible for the "generation" part of Retrieval-Augmented Generation.
    """

    def __init__(self, llm_provider: str = "openai", model: str = None):
        """
        Initializes the RAGAgent.

        Args:
            llm_provider: The LLM provider to use for generation.
            model: The model to use for generation.
        """
        self.llm_client = LLMClient(provider=llm_provider, model=model)

    def generate(self, query: str, context: list[str]) -> str:
        """
        Generates an answer based on the query and retrieved context.

        Args:
            query: The user's query.
            context: A list of context strings retrieved from the knowledge base.

        Returns:
            The generated answer.
        """
        prompt = self._build_prompt(query, context)
        response = self.llm_client.chat([{"role": "user", "content": prompt}])
        return response["content"]

    def _build_prompt(self, query: str, context: list[str]) -> str:
        """
        Builds the prompt for the LLM with improved Chinese support.
        """
        context_str = "\n".join(context)
        
        # Detect if query is in Chinese
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in query)
        
        if is_chinese:
            prompt = f"""请根据以下上下文信息，准确回答用户的问题。请直接给出简洁、准确的答案，不要重复上下文内容。

上下文信息：
{context_str}

用户问题：{query}

请用中文回答，答案要简洁明确："""
        else:
            prompt = f"""Based on the following context information, please provide a precise and concise answer to the user's question. Give a direct answer without repeating the context.

Context:
{context_str}

Question: {query}

Answer:"""
        
        return prompt