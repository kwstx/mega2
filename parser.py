import re
import pandas as pd
import pdfplumber
from io import BytesIO
from typing import Dict, Any, List
from datetime import datetime
from schemas import UtilityBill, UsageData, Charges, ParsingResult

class BillParser:
    def __init__(self):
        # Heuristics for field extraction
        self.keywords = {
            "total_consumption": [r"Total (?:Consumption|Usage)", r"Energy Used", r"Total kWh"],
            "peak_usage": [r"Peak", r"On-Peak"],
            "off_peak_usage": [r"Off-Peak", r"Shoulder"],
            "delivery_charges": [r"Delivery (?:Charges|Fee)", r"Service Charge"],
            "taxes": [r"Tax", r"VAT", r"GST"],
            "total_amount": [r"Total Amount Due", r"Amount to Pay", r"Current Charges"]
        }

    def parse_csv(self, file_content: bytes) -> ParsingResult:
        try:
            df = pd.read_csv(BytesIO(file_content))
            # Basic normalization: column names to lowercase
            df.columns = [c.lower() for c in df.columns]
            
            # Simple mapping logic (assuming some common headers)
            data = {}
            # This is a naive implementation; in a real scenario, we'd map columns more robustly
            data['total_consumption'] = df.get('total_usage', df.get('consumption', [0])).iloc[0]
            data['peak_usage'] = df.get('peak', [0]).iloc[0]
            data['off_peak_usage'] = df.get('off_peak', [0]).iloc[0]
            data['delivery_charges'] = df.get('delivery', [0]).iloc[0]
            data['taxes'] = df.get('tax', [0]).iloc[0]
            data['total_amount'] = df.get('total', [0]).iloc[0]
            
            return self._finalize_result(data, provider="CSV_UPLOAD")
        except Exception as e:
            return ParsingResult(success=False, errors=[str(e)])

    def parse_pdf(self, file_content: bytes) -> ParsingResult:
        try:
            text = ""
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            
            extracted = self._extract_from_text(text)
            extracted['raw_text'] = text
            
            return self._finalize_result(extracted, provider="PDF_UPLOAD")
        except Exception as e:
            return ParsingResult(success=False, errors=[str(e)])

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        data = {}
        for field, patterns in self.keywords.items():
            for pattern in patterns:
                # Look for the pattern followed by a number
                match = re.search(f"{pattern}.*?([\d,]+\.?\d*)", text, re.IGNORECASE)
                if match:
                    val = match.group(1).replace(",", "")
                    data[field] = float(val)
                    break
            if field not in data:
                data[field] = 0.0
        return data

    def _finalize_result(self, raw_data: Dict[str, Any], provider: str) -> ParsingResult:
        errors = []
        anomalies = []
        
        # 1. Missing Critical Fields
        critical_fields = ['total_consumption', 'total_amount']
        for field in critical_fields:
            if raw_data.get(field) is None or raw_data.get(field) == 0:
                errors.append(f"Critical field '{field}' is missing or zero.")
        
        # 2. Consumption vs Component Check
        peak = raw_data.get('peak_usage', 0) or 0
        off_peak = raw_data.get('off_peak_usage', 0) or 0
        total_cons = raw_data.get('total_consumption', 0) or 0
        
        if peak > 0 or off_peak > 0:
            if abs((peak + off_peak) - total_cons) > 1.0:
                anomalies.append(f"Usage Discrepancy: Peak ({peak}) + Off-Peak ({off_peak}) = {peak+off_peak}, but Total reported is {total_cons}")

        # 3. Cost Sanity Check (Estimated $0.10 - $0.40 per kWh)
        if total_cons > 0:
            avg_rate = raw_data.get('total_amount', 0) / total_cons
            if avg_rate > 1.0:
                anomalies.append(f"High Unit Cost: Estimated rate ${avg_rate:.2f}/kWh seems unusually high.")
            elif avg_rate < 0.05:
                anomalies.append(f"Low Unit Cost: Estimated rate ${avg_rate:.2f}/kWh seems unusually low.")

        # 4. Outlier Detection (Simple threshold)
        if total_cons > 10000:
            anomalies.append("Extreme Consumption: Usage exceeds 10,000 kWh, verify if this is an industrial bill.")

        if errors:
            return ParsingResult(success=False, errors=errors, anomalies=anomalies)

        try:
            bill = UtilityBill(
                bill_id=f"BILL-{datetime.now().strftime('%Y%m%d%H%M')}-{hash(str(raw_data)) % 10000}",
                provider=provider,
                billing_period_start=datetime.now().date(), # In a real app, extract this from text
                billing_period_end=datetime.now().date(),
                usage=UsageData(
                    peak_usage=peak,
                    off_peak_usage=off_peak,
                    total_consumption=total_cons
                ),
                charges=Charges(
                    delivery_charges=raw_data.get('delivery_charges', 0) or 0,
                    taxes=raw_data.get('taxes', 0) or 0,
                    total_amount=raw_data.get('total_amount', 0) or 0
                ),
                raw_text=raw_data.get('raw_text')
            )
            return ParsingResult(success=True, data=bill, anomalies=anomalies)
        except Exception as e:
            return ParsingResult(success=False, errors=[f"Normalization Error: {str(e)}"])

