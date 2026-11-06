"""
Builds the unified CampusFlow RAG knowledge repository from the 7 uploaded interview question PDFs.
Outputs: backend/app/core/rag/knowledge_data.json
"""
import json
import os
import re
import pypdf

ARTIFACT_DIR = "C:/Users/pylas/.gemini/antigravity/brain/28c5dfba-97e8-424a-8ab3-5762111817bf/.user_uploaded"
OUTPUT_FILE = "backend/app/core/rag/knowledge_data.json"

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_key_concepts(q_text: str, ans_text: str, top_n: int = 7) -> list[str]:
    stopwords = {
        "the", "and", "for", "with", "that", "this", "from", "are", "have",
        "which", "what", "how", "why", "when", "where", "who", "will", "can",
        "they", "their", "your", "you", "also", "into", "used", "using", "between",
        "than", "then", "been", "being", "more", "most", "some", "such", "only",
        "example", "sample", "question", "answer", "page", "follow", "about",
        "makes", "make", "made", "called", "types", "type", "help", "helps",
        "gives", "give", "know", "known", "well", "good", "need", "needs",
        "like", "just", "does", "done", "case", "cases", "each", "both",
        "difference", "differentiate", "explain", "describe", "discuss", "list",
        "please", "tell", "show", "many", "various", "work", "works"
    }
    # 1. Question terms (including 2-char tokens like L1, L2, CI, CD, IP, OS)
    q_tokens = re.findall(r"\b[A-Za-z0-9_-]{2,}\b", q_text)
    concepts = []
    seen = set()
    for tok in q_tokens:
        low = tok.lower()
        if low not in stopwords and not tok.isdigit() and low not in seen:
            seen.add(low)
            concepts.append(tok)

    # 2. Prominent domain terms in answer
    ans_tokens = re.findall(r"\b[A-Z][a-zA-Z0-9_-]{1,}\b|\b[a-zA-Z0-9_-]{4,}\b", ans_text[:400])
    counts = {}
    canonical = {}
    for tok in ans_tokens:
        low = tok.lower()
        if low not in stopwords and not tok.isdigit() and low not in seen:
            counts[low] = counts.get(low, 0) + 1
            if low not in canonical:
                canonical[low] = tok

    sorted_ans = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    for low, _ in sorted_ans:
        concepts.append(canonical[low])
        seen.add(low)
        if len(concepts) >= top_n:
            break

    return concepts[:top_n]


def build_aiml_knowledge() -> list[dict]:
    path = os.path.join(ARTIFACT_DIR, "media_1793984229460_090bbc70.pdf")
    if not os.path.exists(path):
        return []
    reader = pypdf.PdfReader(path)
    full_text = "\n".join([p.extract_text() or "" for p in reader.pages])
    splits = list(re.finditer(r"(?:^|\n)(\d+)\.\s+([^\n\?]+\?)\s*\n", full_text))
    docs = []
    for i in range(len(splits)):
        cur = splits[i]
        q_num = cur.group(1)
        q_text = cur.group(2).strip()
        start = cur.end()
        end = splits[i+1].start() if i+1 < len(splits) else len(full_text)
        ans = clean_text(full_text[start:end])
        if len(ans) < 20:
            continue
        kws = extract_key_concepts(q_text, ans)
        docs.append({
            "id": f"aiml-{q_num}",
            "track_id": "role-aiml",
            "category": "AI & Machine Learning",
            "subtopic": "Machine Learning Fundamentals",
            "question": q_text,
            "answer": ans[:800],
            "key_concepts": kws,
            "difficulty": "INTERMEDIATE" if int(q_num) > 30 else "FOUNDATIONAL",
            "source_document": "100 Machine Learning Interview Questions and Answers",
        })
    return docs

def build_system_design_knowledge() -> list[dict]:
    path = os.path.join(ARTIFACT_DIR, "media_1793984229933_dbbc22f2.pdf")
    if not os.path.exists(path):
        return []
    reader = pypdf.PdfReader(path)
    full_text = "\n".join([p.extract_text() or "" for p in reader.pages])
    cleaned = re.sub(r"Sandhyasahani\s*\|\s*Page\s*\d+\s*of\s*\d+", "", full_text)
    cleaned = re.sub(r"Prepared\s*&\s*watermarked\s*for\s*Sandhyasahani", "", cleaned)
    splits = list(re.finditer(r"(?:^|\n)(\d+)\.\s+([^\n\?]+\??)\s*\n", cleaned))
    docs = []
    for i in range(len(splits)):
        cur = splits[i]
        q_num = cur.group(1)
        q_text = cur.group(2).strip()
        start = cur.end()
        end = splits[i+1].start() if i+1 < len(splits) else len(cleaned)
        ans = clean_text(cleaned[start:end])
        if len(ans) < 20:
            continue
        kws = extract_key_concepts(q_text, ans)
        docs.append({
            "id": f"sd-{q_num}",
            "track_id": "role-system-design",
            "category": "System Design",
            "subtopic": "HLD, LLD & Scalability",
            "question": q_text,
            "answer": ans[:800],
            "key_concepts": kws,
            "difficulty": "ADVANCED" if int(q_num) > 40 else "INTERMEDIATE",
            "source_document": "System Design Interview Questions & Answers Guide",
        })
    return docs

def build_fullstack_knowledge() -> list[dict]:
    path = os.path.join(ARTIFACT_DIR, "media_1793984229918_3f5501a4.pdf")
    if not os.path.exists(path):
        return []
    reader = pypdf.PdfReader(path)
    full_text = "\n".join([p.extract_text() or "" for p in reader.pages])
    splits = list(re.finditer(r"(?:^|\n)(\d+)\.\s+([^\n\?]+\??)\s*\n", full_text))
    docs = []
    for i in range(len(splits)):
        cur = splits[i]
        q_num = cur.group(1)
        q_text = cur.group(2).strip()
        if len(q_text) < 5 or not any(w in q_text.lower() for w in ["what", "why", "how", "diff", "explain", "can", "is", "which", "define"]):
            continue
        start = cur.end()
        end = splits[i+1].start() if i+1 < len(splits) else len(full_text)
        ans = clean_text(full_text[start:end])
        if len(ans) < 20:
            continue
        kws = extract_key_concepts(q_text, ans)
        docs.append({
            "id": f"fs-{q_num}",
            "track_id": "role-fullstack",
            "category": "Full Stack & Web",
            "subtopic": "Frontend, Backend & Runtime",
            "question": q_text,
            "answer": ans[:800],
            "key_concepts": kws,
            "difficulty": "FOUNDATIONAL" if int(q_num) < 25 else "INTERMEDIATE",
            "source_document": "Full Stack Developer Interview Questions & Answers 2025",
        })
    return docs

def build_hr_knowledge() -> list[dict]:
    path = os.path.join(ARTIFACT_DIR, "media_1793984296428_130da495.pdf")
    if not os.path.exists(path):
        return []
    reader = pypdf.PdfReader(path)
    full_text = "\n".join([p.extract_text() or "" for p in reader.pages])
    splits = list(re.finditer(r"(?:^|\n)(\d+)\s+([A-Z][^\n\?]+\??)\s*\n", full_text))
    docs = []
    for i in range(len(splits)):
        cur = splits[i]
        q_num = cur.group(1)
        q_text = cur.group(2).strip()
        if int(q_num) > 100 or len(q_text) < 8:
            continue
        start = cur.end()
        end = splits[i+1].start() if i+1 < len(splits) else len(full_text)
        ans = clean_text(full_text[start:end])
        ans = re.sub(r"HR INTERVIEW:\s*100 QUESTIONS[^\n]*\n?", "", ans)
        ans = re.sub(r"SHIVAM KUMAR[^\n]*\n?", "", ans)
        ans = re.sub(r"SECTION [A-Z]:[^\n]*\n?", "", ans)
        ans = clean_text(ans)
        if len(ans) < 15:
            continue
        kws = extract_key_concepts(q_text, ans)
        docs.append({
            "id": f"hr-{q_num}",
            "track_id": "role-hr",
            "category": "HR & Behavioral",
            "subtopic": "STAR Method & Professional Conduct",
            "question": q_text,
            "answer": ans[:800],
            "key_concepts": kws,
            "difficulty": "BEHAVIORAL",
            "source_document": "HR Interview 100 Questions & Answers Handbook",
        })
    return docs

def build_sdet_knowledge() -> list[dict]:
    path = os.path.join(ARTIFACT_DIR, "media_1793984230012_99689f8e.pdf")
    if not os.path.exists(path):
        return []
    reader = pypdf.PdfReader(path)
    # Read first 80 pages of SDET handbook for high-yield questions
    full_text = "\n".join([reader.pages[p].extract_text() or "" for p in range(4, min(80, len(reader.pages)))])
    splits = list(re.finditer(r"(?:^|\n)(\d+\.\d+)\s*(?:★\s*)?([^\n\?]+\??)\s*\n", full_text))
    docs = []
    for i in range(len(splits)):
        cur = splits[i]
        q_num = cur.group(1)
        q_text = cur.group(2).strip()
        if len(q_text) < 10:
            continue
        start = cur.end()
        end = splits[i+1].start() if i+1 < len(splits) else len(full_text)
        ans = clean_text(full_text[start:end])
        if len(ans) < 25:
            continue
        kws = extract_key_concepts(q_text, ans)
        docs.append({
            "id": f"sde-{q_num.replace('.', '_')}",
            "track_id": "role-swe",
            "category": "Software Engineering & Testing",
            "subtopic": "Framework Design, API Testing & Automation",
            "question": q_text,
            "answer": ans[:800],
            "key_concepts": kws,
            "difficulty": "INTERMEDIATE",
            "source_document": "SDET Interview Handbook 2026 Edition",
        })
    return docs

def build_data_engineer_knowledge() -> list[dict]:
    # Exact 12 deep questions transcribed from the Azure Data Engineer Handbook
    items = [
        {
            "id": "de-1",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Azure Data Factory (ADF)",
            "question": "What are Parameters and Variables in ADF (Azure Data Factory), and how do their mutability and scopes differ?",
            "answer": "Parameters in ADF are external, read-only values passed into pipelines, datasets, or linked services at execution time to make pipelines dynamic and reusable (e.g. passing container file paths). Variables are mutable values defined and used inside the pipeline scope to store temporary state, loop counters in ForEach activities, or status flags, modified via Set Variable or Append Variable activities.",
            "key_concepts": ["Parameters", "Variables", "Read-only", "Mutable", "Pipeline Scope", "ForEach Loop"],
            "difficulty": "INTERMEDIATE",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-2",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Delta Lake & Lakehouse",
            "question": "What is Time Travel in Delta Lake and how is it implemented under the hood?",
            "answer": "Time Travel in Delta Lake allows querying or reverting to previous versions of a Delta table using version numbers (VERSION AS OF 3) or timestamps (TIMESTAMP AS OF '2024-06-01'). It is powered by Delta Lake transaction logs (_delta_log JSON files) that record all ACID transactions (inserts, updates, deletes, merges) with Parquet data snapshots, enabling point-in-time auditing, model reproducibility, and zero-downtime rollbacks via RESTORE TABLE.",
            "key_concepts": ["Time Travel", "Delta Lake", "_delta_log", "Transaction Log", "VERSION AS OF", "RESTORE TABLE", "ACID"],
            "difficulty": "ADVANCED",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-3",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Storage Optimization",
            "question": "Explain the difference between Partitioning and Bucketing in distributed data systems like Spark and Delta Lake.",
            "answer": "Partitioning divides data into distinct subdirectories based on column values (e.g. /year=2025/month=10/), enabling partition pruning during scans. However, high-cardinality partitioning causes the small-file problem. Bucketing applies a hash function on specified columns (hash(key) % N) to distribute data into a fixed number of bucket files within partitions. Bucketing avoids high-cardinality directory explosion and dramatically optimizes joins between large tables by avoiding costly shuffle operations.",
            "key_concepts": ["Partitioning", "Bucketing", "Directory-based", "Hash-based", "Partition Pruning", "Shuffle Optimization", "Small File Problem"],
            "difficulty": "ADVANCED",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-4",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Lakehouse Architecture",
            "question": "Explain the Medallion Architecture (Bronze, Silver, Gold layers) in modern data platforms.",
            "answer": "The Medallion Architecture (Multi-Hop Architecture) organizes data pipelines into three logical layers in Delta Lake: 1. Bronze (Raw Ingestion): Raw, append-only ingested data from sources (Kafka, APIs, CDC, RDBMS) with schema inference and full history for auditing. 2. Silver (Cleaned & Conformed): Refined, deduplicated, validated, and joined enterprise data. 3. Gold (Business-Level Aggregated): Star schemas, KPIs, and aggregated metrics optimized for Power BI, dashboards, and ML models.",
            "key_concepts": ["Medallion Architecture", "Bronze Layer", "Silver Layer", "Gold Layer", "Raw Ingestion", "Deduplication", "Star Schema"],
            "difficulty": "INTERMEDIATE",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-5",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Governance & Metastore",
            "question": "Compare Unity Catalog with traditional Hive Metastore in Databricks.",
            "answer": "Hive Metastore is a legacy, single-workspace catalog storing metadata in external relational databases (MySQL/PostgreSQL) with table-level ACLs and manual audit tracking. Unity Catalog is a modern centralized cross-workspace governance layer across all Databricks assets (tables, volumes, models, functions) providing fine-grained Attribute-Based Access Control (ABAC), native column/row-level security, automatic data lineage tracking, and centralized audit logging.",
            "key_concepts": ["Unity Catalog", "Hive Metastore", "Cross-workspace", "Data Lineage", "ABAC", "Row-Level Security", "Centralized Governance"],
            "difficulty": "ADVANCED",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-6",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Distributed Processing & PySpark",
            "question": "What are the common join strategies in PySpark, and when do you use Broadcast Joins?",
            "answer": "PySpark supports Shuffle Hash Join, Sort-Merge Join, and Broadcast Hash Join. In a standard join, both datasets are partitioned and shuffled across worker nodes, which is expensive for large data. If one table is small (e.g. lookup dimensions under 10MB or configured threshold), a Broadcast Join (broadcast(df_small)) sends the entire small table to every worker node, eliminating the expensive shuffle step entirely and providing O(1) local hash lookups.",
            "key_concepts": ["PySpark Joins", "Broadcast Join", "Sort-Merge Join", "Shuffle Hash", "Shuffle Elimination", "Lookup Tables"],
            "difficulty": "ADVANCED",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-7",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Pipeline Orchestration",
            "question": "How do you implement parallel processing in Azure Data Factory (ADF)?",
            "answer": "Parallel processing in ADF is achieved through three patterns: 1. ForEach Activity with isSequential=false and setting Batch Count (up to 50 concurrent iterations). 2. Independent side-by-side activities inside a single pipeline executed simultaneously without dependencies. 3. Triggering multiple child pipelines via Execute Pipeline activities or event-based triggers, constrained by integration runtime capacity and target sink throughput.",
            "key_concepts": ["ADF Parallelism", "ForEach Batch Count", "isSequential", "Execute Pipeline", "Integration Runtime", "Throughput"],
            "difficulty": "INTERMEDIATE",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-8",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Apache Spark Internals",
            "question": "What is the difference between Narrow and Wide transformations in Apache Spark?",
            "answer": "Narrow transformations (e.g. map, filter, flatMap, union) have a one-to-one or few-to-one partition dependency where each partition of the parent RDD is used by at most one partition of the child RDD without network data movement (no shuffle). Wide transformations (e.g. groupByKey, reduceByKey, join, distinct, repartition) require data from multiple partitions to be redistributed across the cluster (network shuffle), introducing significant latency and disk I/O.",
            "key_concepts": ["Narrow Transformation", "Wide Transformation", "Shuffle", "map/filter", "groupByKey/join", "Data Partitioning"],
            "difficulty": "ADVANCED",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-9",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Data Warehousing",
            "question": "Explain Slowly Changing Dimensions (SCD Type 1, Type 2, and Type 3) in dimensional modeling.",
            "answer": "Slowly Changing Dimensions manage historical changes in dimension tables: 1. SCD1 (Overwrite): The old value is replaced with the new value, maintaining zero historical tracking (used for correcting typos). 2. SCD2 (Row Versioning): A new row is inserted with start_date, end_date, and is_current flag, preserving complete historical timelines (essential for auditing). 3. SCD3 (Column Tracking): A previous_value column is added alongside current_value, keeping limited partial history of the prior state.",
            "key_concepts": ["SCD1", "SCD2", "SCD3", "Slowly Changing Dimensions", "History Tracking", "start_date/end_date", "is_current"],
            "difficulty": "INTERMEDIATE",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-10",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Databricks Infrastructure",
            "question": "What are the cluster options in Databricks and when do you use Job Clusters vs All-Purpose Clusters?",
            "answer": "Databricks provides two primary cluster types: 1. All-Purpose (Interactive) Clusters: Used by multiple data engineers for collaborative ad-hoc analysis, exploratory notebook development, and experiments. They are manually started, persist across runs, and incur higher costs. 2. Job Clusters: Dedicated, ephemeral single-tenant clusters spun up automatically by the Databricks Jobs scheduler for production pipelines, terminating immediately upon job completion for optimal cost-efficiency.",
            "key_concepts": ["Job Clusters", "All-Purpose Clusters", "Ephemeral", "Interactive", "Databricks Jobs", "Cost Optimization"],
            "difficulty": "INTERMEDIATE",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-11",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Lakehouse Storage",
            "question": "What is the difference between Managed and External (Unmanaged) tables in Databricks and Hive?",
            "answer": "Managed Tables: Both metadata and underlying Parquet/Delta data files are managed by Databricks in default warehouse storage; dropping the table (DROP TABLE) deletes BOTH metadata and physical data files. External Tables: Databricks manages only metadata while data files reside in an external storage location (ADLS Gen2, AWS S3); dropping an external table removes only the catalog metadata while leaving raw data files intact.",
            "key_concepts": ["Managed Tables", "External Tables", "DROP TABLE", "ADLS Gen2", "Metadata", "Data Retention"],
            "difficulty": "INTERMEDIATE",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
        {
            "id": "de-12",
            "track_id": "role-data",
            "category": "Data Engineering",
            "subtopic": "Data Modeling",
            "question": "What is a Surrogate Key and why is it preferred over Natural Keys in a data warehouse?",
            "answer": "A Surrogate Key is an artificial, system-generated integer (auto-incrementing ID or hash) uniquely identifying a record in a dimension table. Unlike Natural Keys (e.g. email, SSN), surrogate keys insulate the warehouse from upstream changes, avoid composite multi-column join keys, improve join performance via compact integer indexing, and are required for implementing SCD Type 2 history versioning.",
            "key_concepts": ["Surrogate Key", "Natural Key", "Integer Index", "Join Performance", "SCD2", "Immutability"],
            "difficulty": "INTERMEDIATE",
            "source_document": "Azure Data Engineer Interview Questions Part 1",
        },
    ]
    return items

def build_devops_knowledge() -> list[dict]:
    # 100 questions transcribed directly from the 10-page DevOps Engineer Interview Questions guide
    raw_questions = [
        # Page 1: Fundamentals
        ("1", "What is DevOps?", "DevOps is a culture and set of practices that combines software development and IT operations to shorten the systems development life cycle and deliver software faster and more reliably.", ["culture", "practices", "development", "operations", "continuous delivery"]),
        ("2", "What are the main goals of DevOps?", "The primary goals of DevOps are automation, faster software delivery, improved team collaboration, high system reliability, scalability, and continuous feedback loops.", ["automation", "delivery", "collaboration", "reliability", "scalability", "feedback"]),
        ("3", "What is the DevOps lifecycle?", "The DevOps lifecycle comprises continuous iterative phases: Plan -> Code -> Build -> Test -> Release -> Deploy -> Operate -> Monitor -> and continuous Improve.", ["plan", "code", "build", "test", "release", "deploy", "monitor"]),
        ("4", "What is Continuous Integration (CI)?", "Continuous Integration automatically merges, builds, and tests code changes from multiple developers whenever changes are committed to the version control repository.", ["continuous integration", "automated build", "automated test", "commit", "version control"]),
        ("5", "What is Continuous Delivery (CD)?", "Continuous Delivery ensures software is continuously built, tested, and kept in a deployable state, ready for automated or one-click deployment to production at any time.", ["continuous delivery", "deployable state", "automated testing", "release readiness"]),
        ("6", "What is Continuous Deployment?", "Continuous Deployment extends continuous delivery by automatically deploying every validated code change directly to the production environment without manual intervention.", ["continuous deployment", "automated release", "production", "no manual approval"]),
        ("7", "What is Infrastructure as Code (IaC)?", "Infrastructure as Code manages and provisions computing infrastructure through machine-readable definition and configuration files, rather than physical hardware configuration or interactive configuration tools.", ["infrastructure as code", "IaC", "version control", "declarative", "automation"]),
        ("8", "What is Configuration Management?", "Configuration Management maintains computer systems, servers, and software in a desired, consistent state using automated tools like Ansible, Puppet, or Chef.", ["configuration management", "desired state", "idempotency", "consistency", "Ansible"]),
        ("9", "What is Immutable Infrastructure?", "Immutable infrastructure replaces servers or containers with new versions instead of modifying or patching them in-place after deployment, guaranteeing consistency and eliminating configuration drift.", ["immutable infrastructure", "no in-place patching", "container replacement", "configuration drift"]),
        ("10", "What is Shift-Left Testing?", "Shift-left testing performs automated testing (unit, integration, security, linting) earlier in the software development lifecycle to detect defects as soon as code is written.", ["shift-left", "early testing", "defect detection", "unit test", "lifecycle"]),

        # Page 2: Linux and Networking
        ("11", "How do you check disk usage in Linux?", "Use 'df -h' to check filesystem disk space usage in human-readable units, and 'du -sh *' to inspect directory and file disk consumption.", ["df -h", "du -sh", "disk usage", "filesystem", "Linux"]),
        ("12", "How do you check memory usage in Linux?", "Use 'free -m' or 'free -h' to display total, used, and available RAM, or interactive process viewers like 'top' and 'htop'.", ["free -m", "RAM", "htop", "top", "memory usage"]),
        ("13", "How do you find running processes in Linux?", "Use 'ps aux' or 'ps -ef' piped to grep (ps aux | grep process_name), or interactively monitor resource consumption using 'top' or 'htop'.", ["ps aux", "ps -ef", "top", "htop", "process monitoring"]),
        ("14", "How do you stop a Linux process?", "Send termination signals using 'kill <PID>' for graceful termination (SIGTERM, 15) or 'kill -9 <PID>' (SIGKILL) when graceful shutdown fails.", ["kill", "SIGTERM", "SIGKILL", "PID", "graceful termination"]),
        ("15", "What does the chmod command do?", "chmod changes file and directory access permissions (read, write, execute) for user, group, and others (e.g. chmod 755 script.sh).", ["chmod", "permissions", "read write execute", "755", "octal"]),
        ("16", "What does the chown command do?", "chown changes the user owner and group ownership of files and directories (e.g. chown user:dev file.txt).", ["chown", "ownership", "user", "group", "permissions"]),
        ("17", "What is a symbolic link?", "A symbolic link (symlink) is a special file created with 'ln -s' that points to another file or directory by pathname reference.", ["symbolic link", "symlink", "ln -s", "pointer", "inode"]),
        ("18", "How do you check listening ports in Linux?", "Use 'ss -tulpn' or 'netstat -tulpn' to list all TCP and UDP sockets currently listening, along with their port numbers and associated process IDs.", ["ss -tulpn", "netstat", "listening ports", "TCP", "UDP", "socket"]),
        ("19", "What is DNS and how does it work?", "The Domain Name System (DNS) translates human-readable domain names (e.g. example.com) into machine-routable IP addresses (e.g. 93.184.216.34) through hierarchical resolver lookups.", ["DNS", "domain name", "IP address", "resolver", "nameserver"]),
        ("20", "What is the difference between TCP and UDP?", "TCP is a connection-oriented, reliable protocol that uses a 3-way handshake and guarantees packet ordering and delivery; UDP is connectionless, faster, and does not guarantee delivery or packet order.", ["TCP", "UDP", "handshake", "connection-oriented", "reliable", "low latency"]),

        # Page 3: Git & Version Control
        ("21", "What is Git?", "Git is a distributed version control system (DVCS) used to track source code changes, coordinate concurrent team collaboration, and maintain complete repository history.", ["Git", "distributed", "version control", "commit", "history"]),
        ("22", "What is the difference between Git and GitHub?", "Git is the command-line version control tool installed locally; GitHub is a cloud platform that hosts remote Git repositories and provides collaboration features like pull requests and CI/CD.", ["Git vs GitHub", "tool vs platform", "remote repository", "collaboration"]),
        ("23", "What is a Git branch?", "A Git branch is a lightweight, movable pointer to a specific commit, allowing developers to isolate feature development or bug fixes without affecting main code.", ["Git branch", "commit pointer", "isolation", "feature branch"]),
        ("24", "What is a merge conflict and how do you resolve it?", "A merge conflict occurs when Git cannot automatically combine changes because two branches modified the exact same lines of code. It is resolved by manually editing conflict markers (<<<<<<<, =======, >>>>>>>) and committing the resolution.", ["merge conflict", "conflict markers", "manual resolution", "rebase"]),
        ("25", "What is git rebase?", "Git rebase moves or reapplies commits from one branch on top of another base commit, creating a clean, linear project history without extra merge commits.", ["git rebase", "linear history", "reapply commits", "fast-forward"]),
        ("26", "What is the difference between merge and rebase?", "Git merge preserves full chronological history by creating a two-parent merge commit; Git rebase rewrites commit history to produce a linear commit sequence.", ["merge vs rebase", "merge commit", "linear history", "commit rewriting"]),
        ("27", "What does git stash do?", "Git stash temporarily shelves uncommitted changes (both staged and unstaged) in a local stack, returning the working directory to a clean state.", ["git stash", "stash pop", "uncommitted changes", "clean working tree"]),
        ("28", "What does git cherry-pick do?", "Git cherry-pick applies the specific changes introduced by an individual existing commit from one branch onto the current working HEAD branch.", ["git cherry-pick", "commit SHA", "selective merge", "patch"]),
        ("29", "What is a pull request?", "A pull request (or merge request) is a formal proposal to merge code from a feature branch into a target branch, allowing peer code review, discussions, and automated CI test checks.", ["pull request", "PR", "code review", "CI validation", "collaboration"]),
        ("30", "How do you undo the latest Git commit?", "Use 'git revert <commit>' to create a new safe inverse commit preserving history, or 'git reset --soft HEAD~1' to uncommit while keeping changes staged.", ["git revert", "git reset", "HEAD~1", "undo commit", "history preservation"]),

        # Page 4: CI/CD
        ("31", "What is a CI/CD pipeline?", "A CI/CD pipeline is an automated workflow that executes stages to compile code, run tests, package artifacts, and deploy applications to target environments.", ["CI/CD pipeline", "automation", "build", "test", "deploy", "workflow"]),
        ("32", "What are common CI/CD tools?", "Industry-standard CI/CD tools include Jenkins, GitHub Actions, GitLab CI, Azure DevOps, CircleCI, and Argo CD for GitOps.", ["Jenkins", "GitHub Actions", "GitLab CI", "Azure DevOps", "Argo CD"]),
        ("33", "What is Jenkins?", "Jenkins is an open-source automation server written in Java used to build, test, and deploy applications across distributed agent architectures.", ["Jenkins", "automation server", "controller-agent", "plugins"]),
        ("34", "What is a Jenkinsfile?", "A Jenkinsfile is a text file checked into version control that defines a Jenkins pipeline using declarative or scripted Groovy syntax (Pipeline as Code).", ["Jenkinsfile", "Pipeline as Code", "declarative", "Groovy", "stages"]),
        ("35", "What is a build artifact?", "A build artifact is the deployable binary output produced by a build stage, such as a JAR, ZIP archive, compiled binary, or Docker container image.", ["build artifact", "JAR", "Docker image", "binary", "artifact repository"]),
        ("36", "What is Pipeline as Code?", "Pipeline as Code defines the build, test, and deployment workflows directly inside repository configuration files (e.g. Jenkinsfile, .github/workflows), enabling version control and review.", ["Pipeline as Code", "version controlled", "declarative syntax", "reproducibility"]),
        ("37", "What is a deployment gate?", "A deployment gate is an automated condition, quality threshold, or manual approval requirement that must be satisfied before a release progresses to the next environment.", ["deployment gate", "quality gate", "approval", "automated validation"]),
        ("38", "What is a deployment rollback?", "A rollback restores an application to its previously stable version when a new deployment encounters critical errors, performance regressions, or test failures.", ["rollback", "recovery", "stable version", "incident mitigation"]),
        ("39", "What is a Blue-Green deployment?", "Blue-Green deployment runs two identical production environments (Blue = live, Green = idle). The new release is deployed and validated on Green, after which router/load balancer traffic switches to Green instantly with zero downtime.", ["blue-green", "traffic switch", "zero downtime", "instant rollback", "load balancer"]),
        ("40", "What is a Canary deployment?", "Canary deployment routes a small percentage (e.g. 5-10%) of live user traffic to the newly released version while observing metrics; if healthy, traffic is incrementally shifted to 100%.", ["canary deployment", "incremental rollout", "traffic routing", "telemetry", "risk mitigation"]),

        # Page 5: Docker & Containers
        ("41", "What is Docker?", "Docker is an open-source platform that packages applications and their complete runtime dependencies into lightweight, portable software containers.", ["Docker", "containerization", "runtime", "isolation", "portability"]),
        ("42", "What is a container?", "A container is an isolated user-space process on a host OS that packages application code and dependencies, sharing the host OS kernel via Linux namespaces and cgroups.", ["container", "isolated process", "host kernel", "namespaces", "cgroups"]),
        ("43", "What is a Docker image?", "A Docker image is a read-only, immutable template consisting of stacked filesystem layers used to instantiate Docker containers.", ["Docker image", "read-only", "immutable layers", "UnionFS", "template"]),
        ("44", "What is a Dockerfile?", "A Dockerfile is a text script containing sequential instructions (FROM, RUN, COPY, EXPOSE, CMD) used by the Docker engine to build a container image.", ["Dockerfile", "FROM", "RUN", "COPY", "CMD", "build instructions"]),
        ("45", "What is Docker Compose?", "Docker Compose is a tool for defining and running multi-container Docker applications configured via a single declarative docker-compose.yml file.", ["Docker Compose", "multi-container", "YAML", "services", "networking"]),
        ("46", "What is the difference between a container and a virtual machine?", "Containers share the host operating system kernel and isolate processes via namespaces, making them lightweight (MBs, startup in seconds); VMs include a full guest OS on top of a hypervisor, consuming more memory and CPU.", ["containers vs VMs", "shared kernel", "hypervisor", "guest OS", "lightweight"]),
        ("47", "What is a Docker volume?", "A Docker volume is a persistent storage mechanism managed by Docker outside the container writable layer, allowing data to survive container destruction and be shared across containers.", ["Docker volume", "persistent storage", "data persistence", "host mounting"]),
        ("48", "What is port mapping in Docker?", "Port mapping (-p host_port:container_port) routes incoming network traffic from a specified port on the host machine to a listening port inside the container.", ["port mapping", "-p flag", "host port", "container port", "networking"]),
        ("49", "How do you list running Docker containers?", "Use 'docker ps' to view currently running containers, or 'docker ps -a' to display all containers including stopped ones.", ["docker ps", "docker ps -a", "container inspection", "CLI"]),
        ("50", "How do you reduce Docker image size?", "Reduce Docker image size by using multi-stage builds, minimal base images (Alpine or Distroless), combining RUN commands to reduce layers, and adding unnecessary files to .dockerignore.", ["multi-stage build", "Alpine", "Distroless", ".dockerignore", "layer reduction"]),

        # Page 6: Kubernetes
        ("51", "What is Kubernetes (K8s)?", "Kubernetes is an open-source container orchestration platform designed to automate deploying, scaling, load balancing, and managing containerized applications across clusters.", ["Kubernetes", "orchestration", "scaling", "cluster", "automation"]),
        ("52", "What is a Kubernetes Pod?", "A Pod is the smallest deployable computing unit in Kubernetes, representing a single instance of a running process consisting of one or more tightly coupled containers sharing network and storage.", ["Pod", "deployable unit", "shared network", "localhost", "containers"]),
        ("53", "What is a Kubernetes Deployment?", "A Deployment is a controller that declaratively manages application replicas, providing automated rolling updates, self-healing pod replacements, and zero-downtime rollbacks.", ["Deployment", "replicas", "rolling update", "self-healing", "controller"]),
        ("54", "What is a Kubernetes Service?", "A Service is an abstraction that defines a logical set of Pods and a policy to access them via a stable virtual IP address and DNS name (ClusterIP, NodePort, LoadBalancer).", ["Service", "ClusterIP", "NodePort", "LoadBalancer", "stable IP", "DNS"]),
        ("55", "What is a Kubernetes Namespace?", "A Namespace provides virtual cluster isolation within a physical Kubernetes cluster, separating resources, access controls, and network policies for different environments or teams.", ["Namespace", "multi-tenancy", "isolation", "resource quota"]),
        ("56", "What is a ConfigMap?", "A ConfigMap is an API object used to store non-confidential configuration data as key-value pairs, consumed by Pods as environment variables, command-line arguments, or mounted config files.", ["ConfigMap", "key-value", "environment variables", "configuration decoupling"]),
        ("57", "What is a Kubernetes Secret?", "A Secret stores and manages sensitive information (passwords, tokens, SSH keys) in base64-encoded format, mounting securely to Pods in tmpfs memory volumes.", ["Kubernetes Secret", "sensitive data", "base64", "tmpfs", "encryption at rest"]),
        ("58", "What is an Ingress in Kubernetes?", "An Ingress is an API object that manages external HTTP/HTTPS routing into cluster services, offering URL-based routing, SSL/TLS termination, and virtual host routing.", ["Ingress", "HTTP routing", "TLS termination", "reverse proxy", "Ingress controller"]),
        ("59", "What is a StatefulSet?", "A StatefulSet manages stateful applications requiring unique, persistent network identifiers, ordered deployment and scaling, and dedicated persistent volumes per pod (e.g. databases, Kafka).", ["StatefulSet", "stateful", "persistent identity", "ordered rollout", "PersistentVolume"]),
        ("60", "What is a DaemonSet?", "A DaemonSet ensures that an identical copy of a Pod runs on all (or selected) worker nodes in the cluster, commonly used for log collection (Fluentd) and node monitoring agents (Prometheus Node Exporter).", ["DaemonSet", "node agent", "logging agent", "monitoring", "Fluentd"]),

        # Page 7: Cloud Computing
        ("61", "What is Cloud Computing?", "Cloud computing delivers on-demand computing services (servers, storage, databases, networking, software) over the Internet with pay-as-you-go pricing.", ["cloud computing", "on-demand", "scalability", "pay-as-you-go"]),
        ("62", "What are IaaS, PaaS, and SaaS?", "IaaS (Infrastructure as a Service) provides raw compute and storage (AWS EC2); PaaS (Platform as a Service) provides a managed runtime environment (AWS Elastic Beanstalk, Heroku); SaaS (Software as a Service) delivers end-user applications over the web (Gmail, Slack).", ["IaaS", "PaaS", "SaaS", "cloud service models", "managed services"]),
        ("63", "What is Auto-Scaling?", "Auto-scaling automatically adjusts computing capacity (adding or removing instances or pods) dynamically in response to real-time workload demand and traffic spikes.", ["auto-scaling", "HPA", "elasticity", "workload demand", "scaling policy"]),
        ("64", "What is a Load Balancer?", "A load balancer distributes incoming network traffic across multiple backend servers to maximize throughput, prevent server overload, and ensure high availability.", ["load balancer", "traffic distribution", "high availability", "health checks", "ALB"]),
        ("65", "What is a Cloud Region?", "A cloud region is a distinct geographic area worldwide containing multiple isolated, physically separated data centers connected via low-latency networks.", ["cloud region", "geography", "data centers", "latency", "compliance"]),
        ("66", "What is an Availability Zone (AZ)?", "An Availability Zone is one or more discrete data centers within a cloud region, equipped with independent power, cooling, and networking to provide fault tolerance.", ["Availability Zone", "fault tolerance", "redundancy", "data center"]),
        ("67", "What is a Virtual Private Cloud (VPC)?", "A VPC is a logically isolated virtual network dedicated to your cloud account, where you define subnets, IP CIDR ranges, route tables, and gateways.", ["VPC", "virtual network", "subnets", "CIDR", "isolation"]),
        ("68", "What is a Security Group?", "A Security Group acts as a stateful virtual firewall controlling inbound and outbound network traffic to cloud compute instances based on IP and port rules.", ["security group", "virtual firewall", "stateful", "inbound outbound", "rules"]),
        ("69", "What is Serverless Computing?", "Serverless computing is an execution model (e.g. AWS Lambda) where the cloud provider dynamically manages server provisioning, scaling, and maintenance, charging only for active execution time.", ["serverless", "AWS Lambda", "event-driven", "auto-scaling", "zero server management"]),
        ("70", "What is the Shared Responsibility Model?", "The cloud provider is responsible for security 'of' the cloud (hardware, facilities, hypervisors), while the customer is responsible for security 'in' the cloud (OS patches, data, network config, IAM).", ["shared responsibility", "security of the cloud", "security in the cloud", "IAM", "compliance"]),

        # Page 8: IaC & Automation
        ("71", "What is Terraform?", "Terraform is an open-source declarative Infrastructure as Code tool created by HashiCorp to provision and manage cloud resources using HashiCorp Configuration Language (HCL).", ["Terraform", "HCL", "declarative", "provisioning", "cloud agnostic"]),
        ("72", "What is Terraform State?", "Terraform state (terraform.tfstate) is a file mapping declared configuration resources to real-world cloud infrastructure metadata, tracking resource IDs and dependencies.", ["Terraform state", "tfstate", "state locking", "remote backend", "resource tracking"]),
        ("73", "What does 'terraform plan' do?", "Terraform plan creates an execution plan, comparing existing state against target configuration to preview the exact resources that will be created, updated, or destroyed.", ["terraform plan", "dry run", "preview changes", "execution plan"]),
        ("74", "What does 'terraform apply' do?", "Terraform apply executes the planned actions against cloud APIs to provision, modify, or destroy real infrastructure according to the target configuration.", ["terraform apply", "provisioning", "API calls", "resource creation"]),
        ("75", "What is a Terraform Module?", "A Terraform module is a container for multiple resources configured together, packaged for reuse and standardization across environments (e.g. VPC module, EKS module).", ["Terraform module", "reusability", "encapsulation", "standardization"]),
        ("76", "What is Ansible?", "Ansible is an open-source, agentless automation and configuration management tool that configures systems and deploys software over SSH using YAML playbooks.", ["Ansible", "agentless", "SSH", "automation", "YAML"]),
        ("77", "What is an Ansible Playbook?", "An Ansible Playbook is a YAML file defining a structured series of automated tasks (plays) to be executed sequentially across targeted host inventories.", ["Ansible playbook", "YAML", "tasks", "plays", "automation"]),
        ("78", "What is an Ansible Inventory?", "An Ansible Inventory is an INI or YAML file listing managed servers, IP addresses, and grouping variables targetable by Ansible playbooks.", ["Ansible inventory", "hosts", "groups", "host variables"]),
        ("79", "What is Idempotency in automation?", "Idempotency means that executing an automation task multiple times produces the exact same result without unintended side effects or redundant duplicate changes.", ["idempotency", "repeatable", "consistent state", "no duplicate side-effects"]),
        ("80", "What is a Dynamic Inventory?", "A dynamic inventory automatically queries cloud providers (AWS, Azure, GCP) or APIs at runtime to dynamically discover host IPs and tags instead of hardcoding static server lists.", ["dynamic inventory", "cloud API", "auto-discovery", "tags", "scaling"]),

        # Page 9: Monitoring & Logging
        ("81", "What is Monitoring?", "Monitoring is the continuous collection and analysis of predefined system metrics (CPU, memory, disk, network, error rate) to assess health and detect anomalies.", ["monitoring", "metrics", "health check", "thresholds", "telemetry"]),
        ("82", "What is Observability and its three pillars?", "Observability measures the internal state of a system based on its external outputs, founded on the three pillars: Metrics (numerical aggregates), Logs (timestamped events), and Traces (request journeys).", ["observability", "metrics", "logs", "traces", "telemetry"]),
        ("83", "What is Prometheus?", "Prometheus is an open-source time-series monitoring system and alerting toolkit that pulls metrics via HTTP scraping using a multidimensional data model and PromQL.", ["Prometheus", "time-series", "metrics scraping", "PromQL", "pull model"]),
        ("84", "What is Grafana?", "Grafana is an open-source analytics and interactive visualization web application that queries multiple datasources to generate dynamic real-time dashboards.", ["Grafana", "dashboards", "data visualization", "metrics analysis", "Prometheus datasource"]),
        ("85", "What is the ELK Stack?", "The ELK Stack combines Elasticsearch (distributed search and indexing engine), Logstash (log ingestion and processing pipeline), and Kibana (visualization dashboard) for centralized log management.", ["ELK Stack", "Elasticsearch", "Logstash", "Kibana", "centralized logging"]),
        ("86", "What is an Alert in monitoring?", "An alert is an automated notification triggered when a monitored metric breaches a predefined threshold or alert rule, routing to engineers via PagerDuty, Slack, or email.", ["alert", "alerting rule", "threshold", "PagerDuty", "notification"]),
        ("87", "What is Application Performance Monitoring (APM)?", "APM monitors application code execution, database queries, transaction latencies, and service dependencies to optimize user experience and diagnose bottlenecks.", ["APM", "application performance", "latency", "bottlenecks", "Datadog"]),
        ("88", "What is Distributed Tracing?", "Distributed tracing tracks and profiles end-to-end request flows across microservices by propagating a unique trace ID and span headers to identify latency bottlenecks.", ["distributed tracing", "trace ID", "spans", "microservices latency", "Jaeger", "OpenTelemetry"]),
        ("89", "What is an SLA (Service Level Agreement)?", "An SLA is a formal commitment between a service provider and customer defining expected service availability, performance standards, and penalties for non-compliance.", ["SLA", "service level agreement", "availability commitment", "uptime", "penalties"]),
        ("90", "What are SLI and SLO?", "An SLI (Service Level Indicator) is a direct quantifiable metric of service performance (e.g. 99.8% successful requests); an SLO (Service Level Objective) is the target goal set for that indicator (e.g. 99.9% uptime).", ["SLI", "SLO", "service level indicator", "service level objective", "reliability engineering"]),

        # Page 10: Security & Troubleshooting
        ("91", "What is DevSecOps?", "DevSecOps integrates security practices, automated code analysis (SAST/DAST), dependency auditing, and compliance checks throughout every stage of the DevOps delivery pipeline.", ["DevSecOps", "security automation", "shift-left security", "SAST", "DAST"]),
        ("92", "What is the Principle of Least Privilege (PoLP)?", "The Principle of Least Privilege dictates that users, processes, and service accounts are granted only the minimal permissions necessary to perform their required tasks.", ["least privilege", "PoLP", "IAM", "minimal permissions", "security"]),
        ("93", "How should secrets be managed in cloud applications?", "Secrets should never be hardcoded in source code; they must be encrypted and stored in dedicated secret management vaults (HashiCorp Vault, AWS Secrets Manager) and injected at runtime via environment variables or volume mounts.", ["secret management", "Vault", "AWS Secrets Manager", "encryption at rest", "no hardcoded credentials"]),
        ("94", "What is Vulnerability Scanning?", "Vulnerability scanning is the automated inspection of source code, external dependencies, container base images, and infrastructure configurations to detect known CVEs and security flaws.", ["vulnerability scanning", "CVE", "dependency scan", "Trivy", "Snyk"]),
        ("95", "What is Role-Based Access Control (RBAC)?", "RBAC regulates access to computing and network resources based on the assigned roles of individual users or service accounts rather than individual identities.", ["RBAC", "role-based access", "permissions", "authorization", "roles"]),
        ("96", "How do you troubleshoot a failed deployment in CI/CD?", "Inspect pipeline stage logs, review recent commit diffs, check deployment environment events and health checks, verify container logs and environment variables, and trigger an automated rollback if production is impacted.", ["failed deployment", "pipeline logs", "rollback", "health checks", "troubleshooting"]),
        ("97", "How do you troubleshoot high CPU usage on a Linux server?", "Run 'top' or 'htop' to identify the CPU-consuming process PID, inspect process threads with 'top -H -p <PID>', examine system logs in /var/log/syslog, and profile application stack traces or query workloads.", ["high CPU", "top", "htop", "PID", "profiling", "system logs"]),
        ("98", "How do you troubleshoot a Kubernetes CrashLoopBackOff error?", "Inspect pod failure reasons using 'kubectl describe pod <name>', examine application exit codes and crash logs using 'kubectl logs <name> --previous', and verify container probes, memory limits, and missing configuration secrets.", ["CrashLoopBackOff", "kubectl describe", "kubectl logs", "OOMKilled", "readiness probe"]),
        ("99", "What is Root-Cause Analysis (RCA)?", "Root-cause analysis is a structured problem-solving methodology (e.g. 5 Whys, Ishikawa diagram) used to uncover the fundamental failure point that allowed an incident to occur.", ["RCA", "root cause analysis", "5 Whys", "incident investigation"]),
        ("100", "What is a Post-Incident Review (Postmortem)?", "A post-incident review is a blameless retrospective meeting and documentation process analyzing what happened, impact, what went well, what went wrong, and concrete preventive action items to prevent recurrence.", ["postmortem", "blameless review", "action items", "preventive measures", "continuous improvement"]),
    ]

    docs = []
    for num, q, a, kws in raw_questions:
        docs.append({
            "id": f"devops-{num}",
            "track_id": "role-devops",
            "category": "DevOps & Cloud Platform",
            "subtopic": "Linux, CI/CD, K8s, Cloud & DevSecOps",
            "question": q,
            "answer": a,
            "key_concepts": kws,
            "difficulty": "FOUNDATIONAL" if int(num) <= 30 else ("INTERMEDIATE" if int(num) <= 70 else "ADVANCED"),
            "source_document": "100 DevOps Engineer Interview Questions & Answers",
        })
    return docs

def build_genai_knowledge() -> list[dict]:
    # Rich GenAI & LLM questions to ground the Generative AI track
    items = [
        {
            "id": "genai-1",
            "track_id": "role-genai",
            "category": "Generative AI & LLM",
            "subtopic": "RAG Architectures",
            "question": "What is Retrieval-Augmented Generation (RAG) and how does it prevent LLM hallucination?",
            "answer": "Retrieval-Augmented Generation (RAG) optimizes LLM outputs by retrieving authoritative facts from an external vector database or search index before generating a response. It grounds the model prompt with verified domain context, drastically minimizing hallucination, providing source citations, and avoiding expensive periodic model retraining.",
            "key_concepts": ["RAG", "hallucination mitigation", "vector database", "external knowledge", "embeddings", "grounding"],
            "difficulty": "INTERMEDIATE",
            "source_document": "Generative AI Engineering Handbook",
        },
        {
            "id": "genai-2",
            "track_id": "role-genai",
            "category": "Generative AI & LLM",
            "subtopic": "Chunking & Embeddings",
            "question": "How do you select optimal chunk sizes and overlap strategies for a document ingestion pipeline in RAG?",
            "answer": "Chunk size selection balances semantic completeness against context window limits. Small chunks (128-256 tokens) provide high precision during vector search but may lack context; large chunks (512-1024 tokens) provide rich context but risk diluting vector similarity. A sliding window with 10-20% chunk overlap ensures sentences split across chunk boundaries maintain coherent semantic context.",
            "key_concepts": ["chunk size", "chunk overlap", "semantic completeness", "context window", "precision", "embeddings"],
            "difficulty": "ADVANCED",
            "source_document": "Generative AI Engineering Handbook",
        },
        {
            "id": "genai-3",
            "track_id": "role-genai",
            "category": "Generative AI & LLM",
            "subtopic": "Vector Similarity & Search",
            "question": "Compare Cosine Similarity, Dot Product, and Euclidean Distance for vector search in LLM embeddings.",
            "answer": "Cosine similarity measures the angular distance between vectors regardless of magnitude, ideal when document lengths vary. Dot product accounts for both angle and vector magnitude, and equals cosine similarity when vectors are unit-normalized (providing maximum search performance in GPU indexes like Faiss or HNSW). Euclidean distance measures absolute geometric distance in multidimensional space.",
            "key_concepts": ["cosine similarity", "dot product", "Euclidean distance", "HNSW", "vector embeddings", "normalization"],
            "difficulty": "ADVANCED",
            "source_document": "Generative AI Engineering Handbook",
        },
        {
            "id": "genai-4",
            "track_id": "role-genai",
            "category": "Generative AI & LLM",
            "subtopic": "Fine-Tuning & Adaptation",
            "question": "What is LoRA (Low-Rank Adaptation) and how does Parameter-Efficient Fine-Tuning (PEFT) work?",
            "answer": "LoRA freezes the pre-trained model weights and injects trainable rank decomposition matrices into each Transformer layer. By decomposing large weight update matrices (d x k) into two low-rank matrices (d x r and r x k, where r << min(d, k)), LoRA reduces trainable parameters by over 99% and slashes VRAM requirements while matching full fine-tuning performance.",
            "key_concepts": ["LoRA", "PEFT", "low-rank adaptation", "parameter efficient", "frozen weights", "VRAM reduction"],
            "difficulty": "ADVANCED",
            "source_document": "Generative AI Engineering Handbook",
        },
        {
            "id": "genai-5",
            "track_id": "role-genai",
            "category": "Generative AI & LLM",
            "subtopic": "Agentic AI & Orchestration",
            "question": "Explain the ReAct (Reasoning + Acting) framework for autonomous LLM agents.",
            "answer": "ReAct combines reasoning traces ('Thought') and task-specific actions ('Action' e.g. searching the web, executing code) in an interleaved loop. The model observes tool results ('Observation') and reasons about the next step until reaching an answer, enabling dynamic exception handling, tool usage, and hallucination reduction.",
            "key_concepts": ["ReAct framework", "Thought Action Observation", "autonomous agent", "tool calling", "reasoning trace"],
            "difficulty": "ADVANCED",
            "source_document": "Generative AI Engineering Handbook",
        },
    ]
    return items

def main():
    print("Compiling CampusFlow RAG Knowledge Base...")
    aiml_docs = build_aiml_knowledge()
    print(f"Loaded AIML: {len(aiml_docs)} items")
    sd_docs = build_system_design_knowledge()
    print(f"Loaded System Design: {len(sd_docs)} items")
    fs_docs = build_fullstack_knowledge()
    print(f"Loaded Fullstack: {len(fs_docs)} items")
    hr_docs = build_hr_knowledge()
    print(f"Loaded HR: {len(hr_docs)} items")
    sdet_docs = build_sdet_knowledge()
    print(f"Loaded SDET/SWE: {len(sdet_docs)} items")
    de_docs = build_data_engineer_knowledge()
    print(f"Loaded Data Engineer: {len(de_docs)} items")
    devops_docs = build_devops_knowledge()
    print(f"Loaded DevOps: {len(devops_docs)} items")
    genai_docs = build_genai_knowledge()
    print(f"Loaded GenAI: {len(genai_docs)} items")

    all_docs = (
        aiml_docs +
        sd_docs +
        fs_docs +
        hr_docs +
        sdet_docs +
        de_docs +
        devops_docs +
        genai_docs
    )

    print(f"\nTotal Grounded RAG Documents: {len(all_docs)}")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved knowledge base to {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE)} bytes).")

if __name__ == "__main__":
    main()

