from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# schema for invoice line items
class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float
    item_code: Optional[str] = None

# schema for the full invoice extraction
class ExtractedInvoice(BaseModel):
    invoice_number: str
    invoice_date: str
    supplier_name: str
    po_reference: Optional[str] = Field(None, description="PO Number if found")
    currency: str = "GBP"
    line_items: List[LineItem]
    subtotal: float
    total_amount: float

# stores the database match results
class MatchResult(BaseModel):
    po_match_confidence: float
    matched_po_id: Optional[str]
    match_method: Literal["exact", "fuzzy", "none"]
    supplier_match: bool
    line_items_matched: int

# structure for any errors found
class Discrepancy(BaseModel):
    type: str 
    severity: Literal["low", "medium", "high"]
    details: str

# main state passed between langgraph nodes
class AgentState(BaseModel):
    file_path: str
    extracted_data: Optional[ExtractedInvoice] = None
    po_data: Optional[dict] = None
    match_result: Optional[MatchResult] = None
    discrepancies: List[Discrepancy] = []
    recommendation: Literal["auto_approve", "flag_for_review", "escalate_to_human", "pending"] = "pending"
    reasoning: str = ""
    logs: List[str] = []