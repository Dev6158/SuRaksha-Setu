import re
from typing import Dict, List, Any, Set, Tuple
from difflib import SequenceMatcher

# ==================== REGEX PATTERNS ====================
# Core identification patterns
AADHAAR_PATTERN = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
PAN_PATTERN = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

# Extended patterns
DOB_PATTERN = r"\b\d{2}[/-]\d{2}[/-]\d{4}\b"
PHONE_PATTERN = r"\b[6-9]\d{9}\b"
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
ADDRESS_PATTERN = r"Address\s*[:\-]\s*(.+)"
IFSC_PATTERN = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
ACCOUNT_PATTERN = r"\b\d{9,18}\b"

# Structured field patterns
NAME_PATTERN = r"Name\s*[:\-]\s*([A-Za-z ]+)"
EMPLOYER_PATTERN = r"Employer\s*[:\-]\s*([A-Za-z0-9 &.,]+)"
INCOME_PATTERN = r"(?:Salary|Income)\s*[:\-]?\s*₹?\s*([0-9,]+)"


class CrossDocumentGraph:
    """
    Enhanced document verification system with:
    - Comprehensive entity extraction (11 fields)
    - Weighted risk scoring across documents
    - Fuzzy matching for name/employer similarity (using stdlib difflib)
    - Graph-based contradiction detection
    - Visualization-ready node/edge structure
    - Zero external dependencies (uses only Python stdlib)
    """

    # Risk weights for each field (higher = more critical)
    FIELD_WEIGHTS = {
        "name": 0.30,
        "dob": 0.30,
        "pan": 0.60,
        "aadhaar": 0.80,
        "phone": 0.10,
        "email": 0.10,
        "address": 0.20,
        "employer": 0.15,
        "income": 0.10
    }

    # Fuzzy matching threshold (0-100)
    FUZZY_THRESHOLD = 85

    def __init__(self):
        self.graph = {}
        self.nodes = []
        self.edges = []

    def mask_aadhaar(self, text: str) -> str:
        """Mask Aadhaar to show only last 4 digits."""
        def replace(match):
            value = match.group(0)
            digits = re.sub(r"\D", "", value)
            return "XXXX XXXX " + digits[-4:]

        return re.sub(AADHAAR_PATTERN, replace, text)

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract all 11 entity types from document text."""
        entities = {
            "name": None,
            "dob": None,
            "pan": None,
            "aadhaar": None,
            "phone": None,
            "email": None,
            "address": None,
            "employer": None,
            "income": None,
            "ifsc": None,
            "account": None
        }

        # Name extraction
        name_match = re.search(NAME_PATTERN, text)
        if name_match:
            entities["name"] = name_match.group(1).strip()

        # Date of birth extraction
        dob_match = re.search(DOB_PATTERN, text)
        if dob_match:
            entities["dob"] = dob_match.group(0)

        # PAN extraction
        pan_match = re.search(PAN_PATTERN, text)
        if pan_match:
            entities["pan"] = pan_match.group(0)

        # Aadhaar extraction (masked)
        aadhaar_match = re.search(AADHAAR_PATTERN, text)
        if aadhaar_match:
            entities["aadhaar"] = aadhaar_match.group(0)

        # Phone extraction
        phone_match = re.search(PHONE_PATTERN, text)
        if phone_match:
            entities["phone"] = phone_match.group(0)

        # Email extraction
        email_match = re.search(EMAIL_PATTERN, text)
        if email_match:
            entities["email"] = email_match.group(0)

        # Address extraction
        address_match = re.search(ADDRESS_PATTERN, text)
        if address_match:
            entities["address"] = address_match.group(1).strip()

        # Employer extraction
        employer_match = re.search(EMPLOYER_PATTERN, text)
        if employer_match:
            entities["employer"] = employer_match.group(1).strip()

        # Income extraction
        income_match = re.search(INCOME_PATTERN, text)
        if income_match:
            entities["income"] = int(
                income_match.group(1).replace(",", "")
            )

        # IFSC extraction
        ifsc_match = re.search(IFSC_PATTERN, text)
        if ifsc_match:
            entities["ifsc"] = ifsc_match.group(0)

        # Account number extraction
        account_match = re.search(ACCOUNT_PATTERN, text)
        if account_match:
            entities["account"] = account_match.group(0)

        return entities

    def build_graph(self, documents: Dict[str, str]) -> Dict[str, Any]:
        """
        Build a cross-document graph with nodes and edges.
        - Nodes: documents and extracted entities
        - Edges: document->entity relationships
        """
        graph = {}
        nodes = []
        edges = []

        # Create document nodes
        for doc_name, content in documents.items():
            safe_text = self.mask_aadhaar(content)
            entities = self.extract_entities(safe_text)

            graph[doc_name] = {
                "type": doc_name.upper(),
                "entities": entities,
                "links": []
            }

            # Add document node
            nodes.append({
                "id": doc_name,
                "type": "document",
                "label": doc_name
            })

            # Create entity nodes and edges
            for field, value in entities.items():
                if value is not None:
                    entity_id = f"{field.upper()}_{str(value)[:10]}"

                    nodes.append({
                        "id": entity_id,
                        "type": field.upper(),
                        "value": value,
                        "label": f"{field}: {value}"
                    })

                    edges.append({
                        "from": doc_name,
                        "to": entity_id,
                        "relation": "contains"
                    })

                    graph[doc_name]["links"].append({
                        "entity": field,
                        "entity_id": entity_id
                    })

        self.graph = graph
        self.nodes = nodes
        self.edges = edges

        return {
            "graph": graph,
            "nodes": nodes,
            "edges": edges
        }

    def detect_contradictions(self) -> Tuple[float, List[str]]:
        """
        Detect contradictions using weighted field matching.
        Returns: (risk_score, reasons_list)
        """
        risk_score = 0.0
        reasons = []

        # Extract all entities by field
        field_values: Dict[str, Set[str]] = {
            field: set() for field in self.FIELD_WEIGHTS.keys()
        }

        for node in self.graph.values():
            entities = node["entities"]
            for field, value in entities.items():
                if value is not None and field in self.FIELD_WEIGHTS:
                    field_values[field].add(str(value))

        # Check each field for contradictions
        for field, values in field_values.items():
            if len(values) > 1:
                weight = self.FIELD_WEIGHTS.get(field, 0.1)

                # Fuzzy matching for text fields (name, employer, address)
                if field in ["name", "employer", "address"]:
                    values_list = list(values)
                    # Use difflib for similarity (0-1 range, multiply by 100 for percentage)
                    similarity = SequenceMatcher(None, values_list[0].lower(), values_list[1].lower()).ratio() * 100

                    if similarity < self.FUZZY_THRESHOLD:
                        risk_score += weight
                        reasons.append(
                            f"{field.upper()} mismatch (similarity: {similarity:.0f}%): "
                            f"{values_list[0]} vs {values_list[1]}"
                        )
                else:
                    # Exact match required for numeric fields
                    risk_score += weight
                    reasons.append(
                        f"{field.upper()} mismatch across documents: {', '.join(values)}"
                    )

        # Normalize risk score to 0-1
        risk_score = min(risk_score, 1.0)

        return risk_score, reasons

    def evaluate(self, documents: Dict[str, str]) -> Dict[str, Any]:
        """
        Comprehensive multi-document evaluation.
        Returns risk score, decision, and visualization data.
        """
        self.build_graph(documents)
        risk_score, reasons = self.detect_contradictions()

        # Decision logic
        if risk_score >= 0.75:
            decision = "HIGH_RISK"
        elif risk_score >= 0.35:
            decision = "MEDIUM_RISK"
        else:
            decision = "LOW_RISK"

        return {
            "graph": self.graph,
            "risk_score": round(risk_score, 3),
            "decision": decision,
            "reasons": reasons,
            "nodes": self.nodes,
            "edges": self.edges,
            "document_count": len(documents)
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Single-document comprehensive validation.
        Validates all 11 fields and assigns risk score.
        """
        entities = self.extract_entities(text)
        score = 0.0
        reasons = []

        # Validate each field
        validation_rules = {
            "name": ("NAME missing", 0.25),
            "dob": ("DOB missing", 0.20),
            "pan": ("PAN missing", 0.40),
            "aadhaar": ("Aadhaar missing", 0.30),
            "phone": ("Phone missing", 0.10),
            "email": ("Email missing", 0.10),
            "address": ("Address missing", 0.15),
            "employer": ("Employer missing", 0.15),
            "income": ("Income missing", 0.15),
            "ifsc": ("IFSC missing", 0.12),
            "account": ("Account number missing", 0.12)
        }

        for field, (reason, weight) in validation_rules.items():
            if entities[field] is None:
                score += weight
                reasons.append(reason)

        # Normalize score
        score = min(score, 1.0)

        # Decision logic
        if score >= 0.75:
            decision = "HIGH_RISK"
        elif score >= 0.35:
            decision = "MEDIUM_RISK"
        else:
            decision = "LOW_RISK"

        return {
            "risk_score": round(score, 3),
            "decision": decision,
            "missing_fields": reasons,
            "entities": entities,
            "completeness": round((1 - score) * 100, 1)
        }


# ==================== EXAMPLE USAGE ====================
if __name__ == "__main__":
    # Single document analysis
    sample_text = """
    Name: Arnav Vivek
    PAN: ABCDE1234F
    Employer: Yaskawa
    Income: ₹500000
    Address: 123 Tech Park, Bangalore
    Phone: 9876543210
    Email: arnav.vivek@yaskawa.com
    DOB: 15-01-1990
    """

    graph = CrossDocumentGraph()

    print("=" * 60)
    print("SINGLE DOCUMENT ANALYSIS")
    print("=" * 60)
    result = graph.analyze(sample_text)
    for key, value in result.items():
        if key != "entities":
            print(f"{key}: {value}")
    print()

    # Multi-document analysis
    documents = {
        "salary_slip_jan.txt": """
            Name: Arnav Vivek
            PAN: ABCDE1234F
            Employer: Yaskawa
            Income: ₹500000
            IFSC: HDFC0001234
            Account: 123456789012345678
        """,
        "bank_statement.txt": """
            Name: Arnav V
            PAN: ABCDE1234F
            Employer: Yaskawa India
            Phone: 9876543210
            Email: arnav.v@yaskawa.com
        """,
        "itax_return.txt": """
            Name: Arnav Vivek
            PAN: ABCDE1234F
            Income: ₹520000
            Employer: Yaskawa
            Address: 123 Tech Park, Bangalore
        """
    }

    print("=" * 60)
    print("MULTI-DOCUMENT CROSS-VERIFICATION")
    print("=" * 60)
    evaluation = graph.evaluate(documents)
    print(f"Risk Score: {evaluation['risk_score']}")
    print(f"Decision: {evaluation['decision']}")
    print(f"Documents Analyzed: {evaluation['document_count']}")
    print(f"\nContradictions Found:")
    for i, reason in enumerate(evaluation['reasons'], 1):
        print(f"  {i}. {reason}")
    print()
    print(f"Total Nodes: {len(evaluation['nodes'])}")
    print(f"Total Edges: {len(evaluation['edges'])}")