<img width="939" height="658" alt="Screenshot 2025-10-19 at 5 51 57 AM" src="https://github.com/user-attachments/assets/80e9838c-af8f-4e64-81f0-2a3eee772539" />

# 🧠 FHEVM Docs to LLM

This repository provides a Python utility that **downloads and compiles the Zama FHEVM documentation** into a single Markdown file (`llm.txt`) — perfect for importing into **Cursor**, or any other LLM-based development environment that accepts Markdown as context.

---

## 📘 Source Repository

The documentation is pulled directly from the official **Zama FHEVM** project:

> 🔗 [https://github.com/zama-ai/fhevm/tree/main/docs](https://github.com/zama-ai/fhevm/tree/main/docs)

`fhevm` (Fully Homomorphic Encryption for EVM) enables private smart contract computation using Zama’s homomorphic encryption technology.  
This script helps you integrate that documentation locally for enhanced LLM-assisted coding.

---

## 🧩 Why This Exists

When using **Cursor** (or any AI IDE), it’s useful to provide the LLM with the project’s complete documentation.  
Instead of pasting multiple Markdown files manually, this tool:

- ✅ Downloads the entire FHEVM `docs/` folder automatically  
- ✅ Merges all `.md`, `.mdx`, and `.txt` files into **one** large, structured Markdown file  
- ✅ Adds a **Table of Contents** with anchor links  
- ✅ Outputs a single file — `llm.txt` — that you can **drag & drop into Cursor** (or any AI context window)

---

## 🚀 Quick Start

### 1️⃣ Clone this repo

```bash
git clone https://github.com/<your-username>/fhevm-llm-builder.git
cd fhevm-llm-builder
````

### 2️⃣ Run the builder

By default, it downloads from Zama’s `fhevm` repo and produces `llm.txt`.

```bash
python3 main.py
```

Output example:

```
Downloading 'docs/' from zama-ai/fhevm@main ...
Downloaded docs/ to docs
Wrote /path/to/llm.txt with 42 files combined.
```

### 3️⃣ Import into Cursor

* Open **Cursor**
* Go to your project
* Drag and drop `llm.txt` into your “Knowledge” or “Docs” section
* Cursor will now have full access to the combined FHEVM documentation

---

## ⚙️ Command-line Options

| Flag                    | Description                                       | Default                                           |
| ----------------------- | ------------------------------------------------- | ------------------------------------------------- |
| `--root, -r`            | Root folder to scan/download into                 | `./docs`                                          |
| `--out, -o`             | Output file path                                  | `./llm.txt`                                       |
| `--github`              | GitHub tree URL to fetch docs from                | `https://github.com/zama-ai/fhevm/tree/main/docs` |
| `--ext`                 | Include extra file extensions (e.g. `--ext .rst`) | none                                              |
| `--no-default-excludes` | Include hidden/system folders (not recommended)   | disabled                                          |

Example for another repo:

```bash
python3 main.py \
  --github "https://github.com/facebook/react/tree/main/docs"
```

---

## 📁 Output Example

```markdown
# Combined Documentation
_Source directory:_ `/path/to/docs`

## Table of Contents

- [README.md](#readmemd)
- [usage/getting-started.md](#usagegetting-startedmd)
- [api/reference.txt](#apireferencetxt)

---

## README.md
<a id="readmemd"></a>

> _From `README.md`_

# fhevm
Fully Homomorphic Encryption for EVM-compatible blockchains...
```


## 🧠 Ideal for

* **Cursor AI users** wanting to give their model the full context of FHEVM docs
* **Developers** preparing a single Markdown file for LLM fine-tuning or vector embedding
* **Offline reference** — read all FHEVM docs in one searchable text file

## 🧑‍💻 Contributing

Contributions are welcome — PRs, bug reports, and improvements appreciated!
If you’d like to extend support for other repos or file formats, open an issue.

## 🪪 License

Released under the **MIT License**.

## ❤️ Author

Created by [Romi](https://x.com/romispectrum).
