# AI Invoice Reconciliation Agent

It is a multi-agent system that automates the process of checking supplier invoices.

It uses **LangGraph** to manage the workflow and **Llama 4 Vision (via Groq)** to read the documents. The system reads the invoice, finds the matching Purchase Order (PO) in the database, checks for errors (like price hikes), and decides whether to approve it or flag it for review.

## Project Overview

The system is built with 4 specific agents working together:

1.  **Extraction Agent:** Converts PDF invoices (even scanned/messy ones) into structured JSON data.
2.  **Matching Agent:** Finds the correct PO in the database. If the PO number is missing, it uses a "Fuzzy Search" logic to find it by supplier name and price.
3.  **Discrepancy Agent:** Checks line items one by one. It flags any price increase over 5% or total amount mismatch.
4.  **Resolution Agent:** Makes the final decision (Auto Approve vs. Flag for Review).

## Tech Stack

- **Python 3.10+**
- **LangGraph:** For building the agent workflow.
- **Groq API:**
  - `llama-4-scout-17b`: For vision/OCR (reading the PDFs).
  - `llama-3.3-70b`: For logic and reasoning.
- **PyMuPDF:** To convert PDF pages to images for the AI.
- **Pydantic:** To ensure the AI outputs valid JSON data.

## Setup Instructions

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up keys:**
    Create a `.env` file in the root folder and add your Groq API key:
    ```env
    GROQ_API_KEY=gsk_your_key_here
    ```

## How to Run

You can run the main script and pass the invoice PDF as an argument.

**Test 1: Normal Invoice (Should Auto Approve)**

```bash
python main.py Invoice_1_Baseline.pdf
```

**2. Run the "Price Trap" Test (Invoice 4)**
This invoice has a hidden 10% price increase. The system should detect it and flag it.

```bash
python main.py Invoice_4_Price_Trap.pdf
```
