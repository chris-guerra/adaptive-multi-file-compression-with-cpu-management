from typing import List
from pydantic import BaseModel

class OperationResponse(BaseModel):
    file_path: str
    original_size: int
    compressed_size: int
    status: str

class FolderOperationResponse(BaseModel):
    files: List[OperationResponse]