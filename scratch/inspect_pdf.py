from pypdf import PdfReader

def inspect_pdf(path):
    print(f"\n=== Inspecting {path} ===")
    reader = PdfReader(path)
    print("Metadata:", reader.metadata)
    print("Pages:", len(reader.pages))
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        print(f"--- Page {i+1} Text (len={len(text)}) ---")
        print(text[:1000])

inspect_pdf("Aadhar_01.pdf")
inspect_pdf("Aadhar_02.pdf")
