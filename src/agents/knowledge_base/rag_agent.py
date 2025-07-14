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
        Builds the prompt for the LLM.
        """
        context_str = "\n".join(context)
        prompt = f"""
        Given the following context, please answer the query.

        Context:
        {context_str}

        Query: {query}
        """
        return prompt