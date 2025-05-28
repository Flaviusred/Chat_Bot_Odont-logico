from pydantic import BaseModel
from typing import Optional

class AgendamentoModel(BaseModel):
    usuario: str
    tipo: str
    data: str
    periodo: str
    cadastrado_em: str

class AgendamentoUpdateModel(BaseModel):
    usuario: Optional[str] = None
    tipo: Optional[str] = None
    data: Optional[str] = None
    periodo: Optional[str] = None