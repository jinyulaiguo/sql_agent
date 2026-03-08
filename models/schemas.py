from pydantic import BaseModel
from typing import List, Optional

class ColumnSchema(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    primary_key: bool = False
    foreign_key: Optional[str] = None

class TableSchema(BaseModel):
    name: str
    description: Optional[str] = None
    columns: List[ColumnSchema]
    ddl: Optional[str] = None

    def to_text_representation(self) -> str:
        """Convert schema to a text representation for embedding."""
        text = f"Table: {self.name}\n"
        if self.description:
            text += f"Description: {self.description}\n"
        text += "Columns:\n"
        for col in self.columns:
            desc = f" - {col.description}" if col.description else ""
            pk = " (PK)" if col.primary_key else ""
            fk = f" (FK -> {col.foreign_key})" if col.foreign_key else ""
            text += f"- {col.name} ({col.type}){pk}{fk}{desc}\n"
        return text
