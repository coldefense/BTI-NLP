# PubMed Input Process

这个目录提供一个最小脚本，用来：

1. 用 `phosphoryl*` 检索 PubMed
2. 拉取文章标题和摘要
3. 只保留摘要里命中 `phosphoryl*` 的句子
4. 如果单句超过 `512` token，直接丢弃
4. 默认只保留前 `100` 个输出句子块

## 文件

- `pubmed_search_and_chunk.py`
  主脚本。输出两个 CSV：
  - `pubmed_raw_articles.csv`
  - `pubmed_phosphoryl_chunks.csv`

## 用法

```powershell
cd D:\BTI\newnlp\new_training_data\ainor_inputprocess
python pubmed_search_and_chunk.py --retmax 100 --max-sentences 100
```

如果你有 NCBI API key，可以加上：

```powershell
python pubmed_search_and_chunk.py --retmax 100 --max-sentences 100 --email you@example.com --api-key YOUR_KEY
```

## 说明

- 默认检索词是 `phosphoryl*`
- 默认只保留匹配正则 `\bphosphoryl\w*\b` 的句子
- 默认每段最大 `512` token
- 默认最多输出 `100` 个句子块
- 默认输出目录是 `new_training_data\ainor_inputprocess\output`
- token 计数强制使用 `BioBERT tokenizer`
- 单句超过 `512` token 会直接舍弃，不做二次切分
- 脚本会优先尝试 `BertTokenizerFast`，失败时退回 `BertTokenizer`
- 如果本机没有安装 `transformers`，或无法访问 `dmis-lab/biobert-base-cased-v1.1`，脚本会直接报错退出

如果你要改相关句的判定规则，可以传：

```powershell
python pubmed_search_and_chunk.py --sentence-pattern "\b(phosphoryl\w*|kinase|phosphatase)\b"
```

## 输出字段

`pubmed_raw_articles.csv`

- `pmid`
- `title`
- `abstract`

`pubmed_phosphoryl_chunks.csv`

- `pmid`
- `title`
- `chunk_id`
- `token_count`
- `text`
