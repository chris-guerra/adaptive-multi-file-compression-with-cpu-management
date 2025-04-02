from pydantic import BaseModel
from typing import List

class OperationResponse(BaseModel):
    file_path: str
    original_size: int
    compressed_size: int
    status: str

class MultiFileOperationResponse(BaseModel):
    files: List[OperationResponse]