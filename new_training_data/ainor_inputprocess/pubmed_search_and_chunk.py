import argparse
import csv
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_QUERY = "phosphoryl*"
DEFAULT_DB = "pubmed"
DEFAULT_RETMAX = 100
DEFAULT_MAX_TOKENS = 512
DEFAULT_BATCH_SIZE = 100
DEFAULT_MAX_SENTENCES = 100
USER_AGENT = "ainor-inputprocess/1.0"


def split_sentences(text):
    text = normalize_whitespace(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9@\(])", text)
    return [part.strip() for part in parts if part.strip()]


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text or "").strip()


class BasicTokenizer:
    def encode(self, text):
        return re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)


def build_tokenizer():
    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            "dmis-lab/biobert-base-cased-v1.1",
            use_fast=True,
        )
        return tokenizer, "biobert"
    except Exception:
        return BasicTokenizer(), "basic"


def count_tokens(tokenizer, text):
    if hasattr(tokenizer, "encode"):
        if tokenizer.__class__.__name__ == "BasicTokenizer":
            return len(tokenizer.encode(text))
        return len(tokenizer.encode(text, add_special_tokens=False))
    raise TypeError("Tokenizer must provide an encode method.")


def split_long_sentence(sentence, tokenizer, max_tokens):
    words = sentence.split()
    if not words:
        return []

    chunks = []
    current = []
    for word in words:
        candidate = " ".join(current + [word]).strip()
        if current and count_tokens(tokenizer, candidate) > max_tokens:
            chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        chunks.append(" ".join(current))

    final_chunks = []
    for chunk in chunks:
        if count_tokens(tokenizer, chunk) <= max_tokens:
            final_chunks.append(chunk)
            continue

        chars = list(chunk)
        current_chars = []
        for char in chars:
            candidate = "".join(current_chars + [char]).strip()
            if current_chars and count_tokens(tokenizer, candidate) > max_tokens:
                final_chunks.append("".join(current_chars).strip())
                current_chars = [char]
            else:
                current_chars.append(char)
        if current_chars:
            final_chunks.append("".join(current_chars).strip())

    return [chunk for chunk in final_chunks if chunk]


def chunk_sentences(sentences, tokenizer, max_tokens):
    chunks = []
    current = []

    for sentence in sentences:
        sentence = normalize_whitespace(sentence)
        if not sentence:
            continue

        sentence_tokens = count_tokens(tokenizer, sentence)
        if sentence_tokens > max_tokens:
            oversized_parts = split_long_sentence(sentence, tokenizer, max_tokens)
        else:
            oversized_parts = [sentence]

        for part in oversized_parts:
            candidate = normalize_whitespace(" ".join(current + [part]))
            if current and count_tokens(tokenizer, candidate) > max_tokens:
                chunks.append(normalize_whitespace(" ".join(current)))
                current = [part]
            else:
                current.append(part)

    if current:
        chunks.append(normalize_whitespace(" ".join(current)))

    return [chunk for chunk in chunks if chunk]


def eutils_get(endpoint, params):
    url = f"{EUTILS_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def esearch(query, retmax, email=None, api_key=None):
    params = {
        "db": DEFAULT_DB,
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "sort": "relevance",
    }
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key

    payload = eutils_get("esearch.fcgi", params)
    data = json.loads(payload)
    return data["esearchresult"]["idlist"]


def fetch_pubmed_xml(pmids, email=None, api_key=None):
    if not pmids:
        return ""

    params = {
        "db": DEFAULT_DB,
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key

    return eutils_get("efetch.fcgi", params)


def extract_articles(xml_payload):
    root = ET.fromstring(xml_payload)
    articles = []

    for article in root.findall(".//PubmedArticle"):
        pmid = normalize_whitespace(article.findtext(".//PMID"))
        title = normalize_whitespace(article.findtext(".//ArticleTitle"))

        abstract_texts = []
        for abstract_node in article.findall(".//Abstract/AbstractText"):
            label = abstract_node.attrib.get("Label", "").strip()
            text = normalize_whitespace("".join(abstract_node.itertext()))
            if not text:
                continue
            abstract_texts.append(f"{label}: {text}" if label else text)

        abstract = normalize_whitespace(" ".join(abstract_texts))
        if not abstract:
            continue

        articles.append(
            {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
            }
        )

    return articles


def write_article_csv(path, articles):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["pmid", "title", "abstract"])
        writer.writeheader()
        writer.writerows(articles)


def write_chunks_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["pmid", "title", "chunk_id", "token_count", "text"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Search PubMed and split abstracts into <=512-token chunks."
    )
    parser.add_argument("--query", default=DEFAULT_QUERY, help="PubMed query.")
    parser.add_argument(
        "--retmax",
        type=int,
        default=DEFAULT_RETMAX,
        help="Maximum number of PubMed records to retrieve.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help="Maximum tokens per output chunk.",
    )
    parser.add_argument(
        "--max-sentences",
        type=int,
        default=DEFAULT_MAX_SENTENCES,
        help="Maximum number of output chunks to keep.",
    )
    parser.add_argument(
        "--outdir",
        default="output",
        help="Output directory for raw and chunked CSV files.",
    )
    parser.add_argument("--email", default="", help="NCBI contact email.")
    parser.add_argument("--api-key", default="", help="NCBI API key.")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    tokenizer, tokenizer_name = build_tokenizer()
    print(f"Tokenizer: {tokenizer_name}")

    pmids = esearch(args.query, args.retmax, email=args.email or None, api_key=args.api_key or None)
    print(f"Found {len(pmids)} PubMed IDs.")
    if not pmids:
        return

    all_articles = []
    for index in range(0, len(pmids), DEFAULT_BATCH_SIZE):
        batch = pmids[index:index + DEFAULT_BATCH_SIZE]
        xml_payload = fetch_pubmed_xml(batch, email=args.email or None, api_key=args.api_key or None)
        all_articles.extend(extract_articles(xml_payload))
        if args.api_key:
            time.sleep(0.12)
        else:
            time.sleep(0.34)

    raw_path = outdir / "pubmed_raw_articles.csv"
    write_article_csv(raw_path, all_articles)

    chunk_rows = []
    for article in all_articles:
        text = normalize_whitespace(f"{article['title']}. {article['abstract']}")
        sentences = split_sentences(text)
        chunks = chunk_sentences(sentences, tokenizer, args.max_tokens)
        for idx, chunk in enumerate(chunks, start=1):
            if len(chunk_rows) >= args.max_sentences:
                break
            chunk_rows.append(
                {
                    "pmid": article["pmid"],
                    "title": article["title"],
                    "chunk_id": idx,
                    "token_count": count_tokens(tokenizer, chunk),
                    "text": chunk,
                }
            )
        if len(chunk_rows) >= args.max_sentences:
            break

    chunk_path = outdir / "pubmed_phosphoryl_chunks.csv"
    write_chunks_csv(chunk_path, chunk_rows)

    print(f"Saved articles to: {raw_path}")
    print(f"Saved chunks to: {chunk_path}")
    print(f"Total chunk rows: {len(chunk_rows)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
