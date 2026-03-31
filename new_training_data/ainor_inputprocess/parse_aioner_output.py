import argparse
import csv
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "output" / "aioner_output" / "pubmed_phosphoryl_pubtator.txt"
DEFAULT_ENTITY_CSV = SCRIPT_DIR / "output" / "aioner_entities.csv"
DEFAULT_SENTENCE_CSV = SCRIPT_DIR / "output" / "aioner_sentences_with_entities.csv"


def parse_pubtator(path):
    documents = []
    blocks = path.read_text(encoding="utf-8").strip().split("\n\n")
    for block in blocks:
        lines = [line for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        title_line = lines[0]
        abstract_line = lines[1]
        doc_id, title = title_line.split("|t|", 1)
        _, abstract = abstract_line.split("|a|", 1)
        entities = []
        for line in lines[2:]:
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            entities.append(
                {
                    "doc_id": parts[0],
                    "start": int(parts[1]),
                    "end": int(parts[2]),
                    "mention": parts[3],
                    "entity_type": parts[4],
                }
            )
        documents.append(
            {
                "doc_id": doc_id,
                "title": title,
                "abstract": abstract,
                "entities": entities,
            }
        )
    return documents


def write_entities_csv(path, documents):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "doc_id",
                "sentence",
                "start",
                "end",
                "mention",
                "entity_type",
            ],
        )
        writer.writeheader()
        for doc in documents:
            for entity in doc["entities"]:
                writer.writerow(
                    {
                        "doc_id": doc["doc_id"],
                        "sentence": doc["title"],
                        "start": entity["start"],
                        "end": entity["end"],
                        "mention": entity["mention"],
                        "entity_type": entity["entity_type"],
                    }
                )


def write_sentence_csv(path, documents):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "doc_id",
                "sentence",
                "entity_count",
                "entities",
            ],
        )
        writer.writeheader()
        for doc in documents:
            entities = [
                f"{entity['mention']}|{entity['entity_type']}|{entity['start']}|{entity['end']}"
                for entity in doc["entities"]
            ]
            writer.writerow(
                {
                    "doc_id": doc["doc_id"],
                    "sentence": doc["title"],
                    "entity_count": len(doc["entities"]),
                    "entities": " ; ".join(entities),
                }
            )


def main():
    parser = argparse.ArgumentParser(description="Parse AIONER PubTator output into CSV files.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="AIONER PubTator output file.")
    parser.add_argument(
        "--entity-csv",
        default=str(DEFAULT_ENTITY_CSV),
        help="Output CSV with one row per entity.",
    )
    parser.add_argument(
        "--sentence-csv",
        default=str(DEFAULT_SENTENCE_CSV),
        help="Output CSV with one row per sentence and aggregated entities.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    entity_csv = Path(args.entity_csv)
    sentence_csv = Path(args.sentence_csv)

    documents = parse_pubtator(input_path)
    write_entities_csv(entity_csv, documents)
    write_sentence_csv(sentence_csv, documents)

    print(f"Parsed documents: {len(documents)}")
    print(f"Saved entities CSV to: {entity_csv}")
    print(f"Saved sentence CSV to: {sentence_csv}")


if __name__ == "__main__":
    main()
