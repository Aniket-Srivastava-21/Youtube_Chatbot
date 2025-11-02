DEFAULT_PROMPT_TEMPLATE = """You are a helpful assistant.
You are answering people's query regarding content of a youtube video, therefore answer only from the context given below.
If context is insufficient, just say that you don't know.

Context: {context}
Query: {query}"""

class PromptTemplate:
    """
    Minimal PromptTemplate compatible with the notebook usage.

    Usage:
        from prompt import PromptTemplate, DEFAULT_PROMPT_TEMPLATE
        prompt = PromptTemplate(DEFAULT_PROMPT_TEMPLATE, input_variables=['context', 'query'])
        text = prompt.invoke({'context': '...', 'query': '...'})
    """

    def __init__(self, template: str, input_variables=None):
        self.template = template
        self.input_variables = input_variables or []

    def format(self, **kwargs) -> str:
        # Strict formatting: KeyError if required variable missing.
        return self.template.format(**kwargs)

    def invoke(self, inputs):
        """
        Accept either a dict of variables or an object that can be used as 'context'.
        Returns the formatted prompt string.
        """
        if isinstance(inputs, dict):
            # optional: check for missing required inputs
            missing = [v for v in self.input_variables if v not in inputs]
            if missing:
                raise KeyError(f"Missing input variables for prompt: {missing}")
            return self.format(**inputs)
        else:
            # fallback: treat inputs as context if single value provided
            if 'context' in self.input_variables and 'query' not in self.input_variables:
                return self.format(context=inputs)
            raise TypeError("PromptTemplate.invoke expects a dict with input variables")

    def __repr__(self):
        return f"PromptTemplate(template={self.template!r}, input_variables={self.input_variables!r})"


def default_prompt():
    return PromptTemplate(DEFAULT_PROMPT_TEMPLATE, input_variables=['context', 'query'])