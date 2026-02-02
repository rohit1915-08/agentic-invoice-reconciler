# Technical Analysis: Invoice Reconciliation System

## 1. Where Extraction Fails & How I Fix It

Even with powerful models like Llama 4, reading "messy" documents is hard. During my testing, I found two main failure points:

- **Blurry or Rotated Text:** If a scan is tilted or low quality, the AI sometimes confuses similar letters (like mistaking a '1' for an 'l' or '8' for 'B').
- **Complex Tables:** If an invoice has a weird table layout without clear lines, the model sometimes merges two columns together.

**How My Agents Fix This:**
I didn't just trust the AI blindly. I built a "self-healing" system to catch these errors:

1.  **Strict Rules (Pydantic):** I force the AI to output data in a specific format. If it tries to return "approx $100" instead of just "100.00", the code rejects it immediately.
2.  **Smart Matching:** If the AI misreads a PO number (e.g., typing "O01" instead of "001"), the exact database search will fail. Instead of crashing, my Matching Agent automatically switches to a "Fuzzy Search." It looks for the Supplier Name and Total Price to find the right record, fixing the typo automatically.

## 2. How to Reach 95% Accuracy

To take this from a prototype to a production system with 95%+ accuracy, I would add these three features:

1.  **Double-Check with Two Models:** Right now, I rely only on Llama 4. To make it bulletproof, I would run a second, cheaper OCR tool (like Tesseract) alongside it. If both models agree, the data is likely correct. If they disagree, the agent would flag it for human review.
2.  **Visual Coordinates:** I would ask the model to return the "bounding box" (x, y coordinates) of the text it finds. This way, if the model pulls a price from the top header instead of the table column, the code can detect that the location is wrong and ignore it.
3.  **Memory:** I would add a "Memory Node" to the graph. If the system constantly fails on invoices from "Supplier X," it should learn that pattern. Over time, it could build custom rules for difficult suppliers so it doesn't make the same mistake twice.

## 3. Scaling to 10,000 Invoices/Day

Processing 10,000 invoices a day is a different challenge. The current version runs one by one, which is too slow for that scale. Here is how I would upgrade it:

- **Run in Parallel:** I would change the architecture to process hundreds of invoices at the same time using cloud functions (like AWS Lambda), instead of a simple loop.
- **Faster Database:** Searching through a JSON file works for 20 POs, but it's too slow for millions. I would switch to a Vector Database (like Pinecone) or SQL. This allows the system to find a matching PO in milliseconds, even with a huge dataset.
- **Cost Control:** Running a big AI model on every single invoice is expensive. I would use a "Router" system: try a cheap, fast OCR first. Only if the invoice is messy or hard to read would the system call the expensive Llama 4 model. This saves money while keeping accuracy high.
