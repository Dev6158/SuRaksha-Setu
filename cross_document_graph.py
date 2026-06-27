import re
from typing import Dict, List, Any

AADHAAR_PATTERN = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
PAN_PATTERN = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

NAME_PATTERN = r"Name\s*[:\-]\s*([A-Za-z ]+)"
EMPLOYER_PATTERN = r"Employer\s*[:\-]\s*([A-Za-z0-9 &.,]+)"
INCOME_PATTERN = r"(?:Salary|Income)\s*[:\-]?\s*₹?\s*([0-9,]+)"


class CrossDocumentGraph:

    def __init__(self):
        self.graph = {}

    def mask_aadhaar(self, text: str) -> str:
        def replace(match):
            value = match.group(0)
            digits = re.sub(r"\D", "", value)
            return "XXXX XXXX " + digits[-4:]

        return re.sub(AADHAAR_PATTERN, replace, text)

    def extract_entities(self, text: str) -> Dict[str, Any]:

        entities = {
            "name": None,
            "pan": None,
            "employer": None,
            "income": None
        }

        name_match = re.search(NAME_PATTERN, text)
        if name_match:
            entities["name"] = name_match.group(1).strip()

        pan_match = re.search(PAN_PATTERN, text)
        if pan_match:
            entities["pan"] = pan_match.group(0)

        employer_match = re.search(EMPLOYER_PATTERN, text)
        if employer_match:
            entities["employer"] = employer_match.group(1).strip()

        income_match = re.search(INCOME_PATTERN, text)
        if income_match:
            entities["income"] = int(
                income_match.group(1).replace(",", "")
            )

        return entities

    def build_graph(
        self,
        documents: Dict[str, str]
    ) -> Dict[str, Dict]:

        graph = {}

        for doc_name, content in documents.items():

            safe_text = self.mask_aadhaar(content)

            graph[doc_name] = {
                "entities": self.extract_entities(safe_text)
            }

        self.graph = graph

        return graph

    def detect_contradictions(self) -> List[str]:

        contradictions = []

        employers = set()
        names = set()
        pans = set()

        for node in self.graph.values():

            entities = node["entities"]

            if entities["employer"]:
                employers.add(entities["employer"])

            if entities["name"]:
                names.add(entities["name"])

            if entities["pan"]:
                pans.add(entities["pan"])

        if len(employers) > 1:
            contradictions.append(
                "Employer mismatch across documents"
            )

        if len(names) > 1:
            contradictions.append(
                "Name mismatch across documents"
            )

        if len(pans) > 1:
            contradictions.append(
                "PAN mismatch across documents"
            )

        return contradictions

    def evaluate(
        self,
        documents: Dict[str, str]
    ) -> Dict[str, Any]:

        graph = self.build_graph(documents)

        contradictions = self.detect_contradictions()

        return {
            "graph": graph,
            "contradictions": contradictions,
            "risk": "HIGH" if contradictions else "LOW"
        }

    def analyze(self, text: str) -> Dict[str, Any]:

        entities = self.extract_entities(text)

        contradictions = []

        if entities["name"] is None:
            contradictions.append("NAME_MISSING")

        if entities["pan"] is None:
            contradictions.append("PAN_MISSING")

        if entities["employer"] is None:
            contradictions.append("EMPLOYER_MISSING")

        if entities["income"] is None:
            contradictions.append("INCOME_MISSING")

        score = min(len(contradictions) * 0.25, 1.0)

        return {
            "score": score,
            "contradictions": contradictions,
            "entities": entities
        }


if __name__ == "__main__":

    sample_text = """
    Name: Arnav Vivek
    PAN: ABCDE1234F
    Employer: Yaskawa
    Income: ₹500000
    """

    graph = CrossDocumentGraph()

    print(graph.analyze(sample_text))