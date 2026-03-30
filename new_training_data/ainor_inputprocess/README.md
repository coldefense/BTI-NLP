# PubMed Input Process

这个目录提供一个最小脚本，用来：

1. 用 `phosphoryl*` 检索 PubMed
2. 拉取文章标题和摘要
3. 按句子切分，并合并成不超过 `512` token 的短文本
4. 默认只保留前 `100` 个输出句子块

## 文件

- `pubmed_search_and_chunk.py`
  主脚本。输出两个 CSV：
  - `pubmed_raw_articles.csv`
  - `pubmed_phosphoryl_chunks.csv`

## 用法

```powershell
cd D:\BTI\newnlp\new_training_data\ainor_inputprocess
python pubmed_search_and_chunk.py --retmax 100 --max-sentences 100 --outdir output
```

如果你有 NCBI API key，可以加上：

```powershell
python pubmed_search_and_chunk.py --retmax 100 --max-sentences 100 --outdir output --email you@example.com --api-key YOUR_KEY
```

## 说明

- 默认检索词是 `phosphoryl*`
- 默认每段最大 `512` token
- 默认最多输出 `100` 个句子块
- token 计数优先使用 `BioBERT tokenizer`
- 如果本机没有安装 `transformers` 或无法下载 tokenizer，会自动退回基础分词

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
