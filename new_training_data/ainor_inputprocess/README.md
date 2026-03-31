# PubMed Input Process

这个目录提供一个最小脚本，用来：

1. 用 `phosphoryl*` 检索 PubMed
2. 拉取文章标题和摘要
3. 只保留摘要里命中 `phosphoryl*` 的句子
4. 如果单句超过 `512` token，直接丢弃
4. 默认只保留前 `100` 个输出句子块
5. 同时导出 AIONER 可直接使用的 PubTator `.txt`

## 文件

- `pubmed_search_and_chunk.py`
  主脚本。输出两个 CSV 和一个 AIONER 可直接使用的 txt：
  - `pubmed_raw_articles.csv`
  - `pubmed_phosphoryl_chunks.csv`
  - `pubmed_phosphoryl_pubtator.txt`
- `run_aioner_from_trainingdata.py`
  不改 `NLPv2.4` 里的脚本，直接从 `new_training_data` 调用现成 AIONER 模型。
- `parse_aioner_output.py`
  把 AIONER 的 PubTator 输出整理成 CSV，便于检查和后续做 BioBERT 输入。

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

`pubmed_phosphoryl_pubtator.txt`

- 每条句子会写成 AIONER 可用的 PubTator 结构：

```text
41866640_1|t|It should be noted that our use of the descriptor hyperphosphorylated tau...
41866640_1|a|OBJECTIVE: not even. METHODS: not even. RESULTS: not even. CONCLUSIONS: not even.
```

## 调用 AIONER

先生成输入：

```powershell
cd D:\BTI\newnlp\new_training_data\ainor_inputprocess
python pubmed_search_and_chunk.py
```

再调用 `NLPv2.4` 现成模型：

```powershell
python run_aioner_from_trainingdata.py --python C:\Users\ricky\miniconda3\python.exe
```

如果你的 AIONER 环境不是这个解释器，把 `--python` 换成对应环境里的 Python。

最后把 AIONER 输出转成 CSV：

```powershell
python parse_aioner_output.py
```
