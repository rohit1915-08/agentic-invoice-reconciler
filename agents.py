import base64
import os
import fitz 
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from models import AgentState, ExtractedInvoice, MatchResult, Discrepancy
from database import PODatabase

load_dotenv()

# Setup Groq models
llm_vision = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct", 
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

llm_logic = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

def encode_image(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # convert pdf page to image if needed
    if file_path.lower().endswith(".pdf"):
        doc = fitz.open(file_path)
        page = doc.load_page(0) 
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        return base64.b64encode(img_data).decode("utf-8")
    else:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

def document_intelligence_node(state: AgentState):
    print(f"processing {state.file_path}...")
    
    try:
        image_data = encode_image(state.file_path)
        
        structured_llm = llm_vision.with_structured_output(ExtractedInvoice)
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Extract invoice data into JSON. Set missing PO to null."},
                {
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/png;base64,{image_data}"}
                },
            ]
        )
        
        extraction = structured_llm.invoke([message])
        print(f"extracted invoice: {extraction.invoice_number}")
        
        return {"extracted_data": extraction}

    except Exception as e:
        print(f"extraction failed: {str(e)}")
        return {"logs": state.logs + [f"Error: {str(e)}"]}

def matching_node(state: AgentState):
    print("matching with database...")
    
    extracted = state.extracted_data
    if not extracted:
        return {"match_result": None, "po_data": None}

    db = PODatabase()
    matched_po = None
    method = "none"
    
    # try exact match first
    if extracted.po_reference:
        matched_po = db.get_po_by_id(extracted.po_reference)
        if matched_po: 
            method = "exact"

    # fallback to fuzzy search
    if not matched_po:
        print("exact match failed, trying fuzzy search...")
        matched_po = db.fuzzy_search(extracted.supplier_name, extracted.total_amount)
        if matched_po: 
            method = "fuzzy"

    match_result = MatchResult(
        po_match_confidence=0.99 if method == "exact" else 0.85 if method == "fuzzy" else 0.0,
        matched_po_id=matched_po['po_number'] if matched_po else None,
        match_method=method,
        supplier_match=bool(matched_po),
        line_items_matched=0
    )
    
    po_id = matched_po['po_number'] if matched_po else 'None'
    print(f"found PO: {po_id} (method: {method})")
    
    return {"po_data": matched_po, "match_result": match_result}

def discrepancy_node(state: AgentState):
    print("checking for discrepancies...")
    discrepancies = []
    
    extracted = state.extracted_data
    po = state.po_data
    
    if not extracted:
        return {"discrepancies": []}

    if not po:
        discrepancies.append(Discrepancy(type="missing_po", severity="high", details="No matching PO found."))
    else:
        # check total amount
        diff = abs(extracted.total_amount - po['total'])
        if diff > 5.0 and diff > (po['total'] * 0.01):
            discrepancies.append(Discrepancy(
                type="total_variance", 
                severity="medium", 
                details=f"Total mismatch: {extracted.total_amount} vs {po['total']}"
            ))

        # check line items
        for item in extracted.line_items:
            match = next((p for p in po['line_items'] if item.description.lower() in p['description'].lower() or p['description'].lower() in item.description.lower()), None)
            
            if match:
                price_diff_pct = abs(item.unit_price - match['unit_price']) / match['unit_price'] * 100
                
                if price_diff_pct > 15:
                    discrepancies.append(Discrepancy(
                        type="price_trap", 
                        severity="high", 
                        details=f"Price hike of {price_diff_pct:.1f}% on {item.description}"
                    ))
                elif price_diff_pct > 5:
                    discrepancies.append(Discrepancy(
                        type="price_variance", 
                        severity="medium", 
                        details=f"Price variance {price_diff_pct:.1f}% on {item.description}"
                    ))

    print(f"discrepancies found: {len(discrepancies)}")
    return {"discrepancies": discrepancies}

def resolution_node(state: AgentState):
    discrepancies = state.discrepancies
    match_result = state.match_result
    
    if any(d.severity == "high" for d in discrepancies):
        rec = "escalate_to_human"
        reason = "High severity discrepancies detected."
        
    elif any(d.severity == "medium" for d in discrepancies) or match_result.match_method == "fuzzy":
        rec = "flag_for_review"
        reason = "Minor discrepancies or fuzzy match."
        
    else:
        rec = "auto_approve"
        reason = "Clean match."

    print(f"final verdict: {rec}")
    return {"recommendation": rec, "reasoning": reason}