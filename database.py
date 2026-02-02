import json
from difflib import SequenceMatcher

class PODatabase:
    def __init__(self, json_path="purchase_orders.json"):
        self.orders = []
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                self.orders = data['purchase_orders']
        except FileNotFoundError:
            print(f"error: {json_path} not found")

    def get_po_by_id(self, po_id):
        # simple lookup by id
        for po in self.orders:
            if po['po_number'] == po_id:
                return po
        return None

    def fuzzy_search(self, supplier_name, total_amount):
        # if po number is missing, try to find by name and price
        best_match = None
        highest_score = 0

        for po in self.orders:
            # 1. check name similarity
            similarity = SequenceMatcher(None, supplier_name.lower(), po['supplier'].lower()).ratio()
            
            # 2. check price (allow 5% difference)
            price_diff = abs(po['total'] - total_amount)
            is_price_close = price_diff <= (po['total'] * 0.05)

            # if name is kinda similar and price is close
            if is_price_close and similarity > 0.6:
                if similarity > highest_score:
                    highest_score = similarity
                    best_match = po

        return best_match