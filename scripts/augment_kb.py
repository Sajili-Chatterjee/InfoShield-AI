import json
from pathlib import Path

KB_PATH = Path("data/knowledge_base.json")

def build_combined_text(item):
    combined = []

    # Core text
    combined.append(item.get("text", ""))

    # Add structured fields
    combined.extend(item.get("claims", []))
    combined.extend(item.get("keywords", []))
    combined.extend(item.get("related_topics", []))

    # Clean and join
    combined = [str(x).strip() for x in combined if x]
    return " ".join(combined)


def augment_knowledge_base():
    if not KB_PATH.exists():
        print("❌ knowledge_base.json not found")
        return

    with open(KB_PATH, "r", encoding="utf-8") as f:
        kb = json.load(f)

    updated_count = 0

    for item in kb:
        combined_text = build_combined_text(item)
        item["combined_text"] = combined_text
        updated_count += 1

    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)

    print(f"✅ Updated {updated_count} KB entries with combined_text")


if __name__ == "__main__":
    augment_knowledge_base()