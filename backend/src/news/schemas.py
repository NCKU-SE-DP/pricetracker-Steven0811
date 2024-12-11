from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class NewsSumaryRequestSchema(BaseModel):
    content: str

class NewsSumaryCustomModelSchema(BaseModel):
    content: str
    ai_model: str 