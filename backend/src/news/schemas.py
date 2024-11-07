from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class NewsSumaryRequestSchema(BaseModel):
    content: str