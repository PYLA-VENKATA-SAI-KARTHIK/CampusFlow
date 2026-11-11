"""
CampusFlow — AI Assessment Question Generator.
Generates structured placement assessment MCQs with 4 options, correct answer,
marks, and detailed explanations across technical, aptitude, and domain tracks.
"""
from __future__ import annotations

import random
from decimal import Decimal
from typing import Any

# Comprehensive Question Banks across placement domains
QUESTION_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "dsa": [
        {
            "question": "What is the worst-case time complexity of searching for an element in a balanced Binary Search Tree (AVL or Red-Black Tree)?",
            "options": [
                {"key": "A", "text": "O(1)"},
                {"key": "B", "text": "O(log N)"},
                {"key": "C", "text": "O(N)"},
                {"key": "D", "text": "O(N log N)"},
            ],
            "correct_option": "B",
            "explanation": "Because balanced trees maintain a height bounded strictly by O(log N), search operations traverse from root to leaf in at most O(log N) comparisons.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "Which data structure uses the LIFO (Last In First Out) principle and is used in function call stack management?",
            "options": [
                {"key": "A", "text": "Queue"},
                {"key": "B", "text": "Stack"},
                {"key": "C", "text": "Circular Buffer"},
                {"key": "D", "text": "Priority Queue"},
            ],
            "correct_option": "B",
            "explanation": "A Stack operates on Last-In, First-Out (LIFO), which maps directly to function activation frame stacking and unstacking during recursive calls.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "Which algorithm is commonly used to find the shortest path in an unweighted graph?",
            "options": [
                {"key": "A", "text": "Depth First Search (DFS)"},
                {"key": "B", "text": "Breadth First Search (BFS)"},
                {"key": "C", "text": "Bellman-Ford Algorithm"},
                {"key": "D", "text": "Floyd-Warshall Algorithm"},
            ],
            "correct_option": "B",
            "explanation": "Breadth-First Search (BFS) explores all vertices at the present depth before moving deeper, naturally guaranteeing the shortest path in unweighted graphs.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "In dynamic programming, what are the two core properties a problem must possess to be solvable via DP?",
            "options": [
                {"key": "A", "text": "Optimal substructure and Overlapping subproblems"},
                {"key": "B", "text": "Greedy choice and Memoization"},
                {"key": "C", "text": "Divide and conquer with constant space"},
                {"key": "D", "text": "Topological ordering and DAG structure"},
            ],
            "correct_option": "A",
            "explanation": "Dynamic Programming requires optimal substructure (optimal solution composed of optimal solutions to subproblems) and overlapping subproblems (re-computing identical subproblems).",
            "marks": Decimal("1.00"),
        },
        {
            "question": "What is the average time complexity of insertion into a Hash Table with a good hash function?",
            "options": [
                {"key": "A", "text": "O(N)"},
                {"key": "B", "text": "O(log N)"},
                {"key": "C", "text": "O(1)"},
                {"key": "D", "text": "O(N^2)"},
            ],
            "correct_option": "C",
            "explanation": "Assuming uniform hashing and an appropriate load factor with collision handling, average insertion time in a hash map is O(1).",
            "marks": Decimal("1.00"),
        },
    ],
    "python": [
        {
            "question": "What does Python's Global Interpreter Lock (GIL) prevent in CPython?",
            "options": [
                {"key": "A", "text": "Asynchronous event loops from running"},
                {"key": "B", "text": "Multiple native threads from executing Python bytecode simultaneously"},
                {"key": "C", "text": "Multiprocessing modules from forking child processes"},
                {"key": "D", "text": "Garbage collection of circular references"},
            ],
            "correct_option": "B",
            "explanation": "The CPython GIL is a mutex that prevents multiple native threads from executing Python bytecode in parallel, protecting CPython memory management.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "Which built-in Python function returns an iterator that yields tuples containing an index and the corresponding element?",
            "options": [
                {"key": "A", "text": "zip()"},
                {"key": "B", "text": "map()"},
                {"key": "C", "text": "enumerate()"},
                {"key": "D", "text": "filter()"},
            ],
            "correct_option": "C",
            "explanation": "enumerate(iterable, start=0) returns an enumerate object that yields (index, value) tuples consecutively.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "In Python, which of the following object types is mutable?",
            "options": [
                {"key": "A", "text": "tuple"},
                {"key": "B", "text": "frozenset"},
                {"key": "C", "text": "list"},
                {"key": "D", "text": "str"},
            ],
            "correct_option": "C",
            "explanation": "Lists in Python can be modified in-place (append, pop, slice assignment), whereas tuples, strings, and frozensets are immutable.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "What keyword is used to create a generator function in Python instead of returning a static list?",
            "options": [
                {"key": "A", "text": "generate"},
                {"key": "B", "text": "yield"},
                {"key": "C", "text": "async"},
                {"key": "D", "text": "defer"},
            ],
            "correct_option": "B",
            "explanation": "The 'yield' statement pauses function execution and emits a value to the caller, resuming state on the subsequent next() call.",
            "marks": Decimal("1.00"),
        },
    ],
    "java": [
        {
            "question": "Which Java memory area stores object instances allocated by the 'new' keyword?",
            "options": [
                {"key": "A", "text": "JVM Stack Area"},
                {"key": "B", "text": "Heap Memory"},
                {"key": "C", "text": "Program Counter Register"},
                {"key": "D", "text": "Native Method Stack"},
            ],
            "correct_option": "B",
            "explanation": "All class instances and arrays in Java are dynamically allocated in the Heap memory area and managed by the Garbage Collector.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "In Java OOP, which keyword prevents a class from being inherited/subclassed?",
            "options": [
                {"key": "A", "text": "static"},
                {"key": "B", "text": "const"},
                {"key": "C", "text": "final"},
                {"key": "D", "text": "abstract"},
            ],
            "correct_option": "C",
            "explanation": "Declaring a class with the 'final' keyword marks it non-extendable, preventing any other class from subclassing it.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "Which interface represents a collection that maintains unique elements and forbids duplicates?",
            "options": [
                {"key": "A", "text": "List"},
                {"key": "B", "text": "Queue"},
                {"key": "C", "text": "Set"},
                {"key": "D", "text": "Vector"},
            ],
            "correct_option": "C",
            "explanation": "The java.util.Set interface models the mathematical set abstraction, strictly prohibiting duplicate elements.",
            "marks": Decimal("1.00"),
        },
    ],
    "sql": [
        {
            "question": "Which SQL clause is used to filter records resulting from aggregate functions such as COUNT() or AVG()?",
            "options": [
                {"key": "A", "text": "WHERE"},
                {"key": "B", "text": "HAVING"},
                {"key": "C", "text": "GROUP BY"},
                {"key": "D", "text": "ORDER BY"},
            ],
            "correct_option": "B",
            "explanation": "The HAVING clause applies filtering conditions to summarized/aggregated groups, whereas WHERE filters individual rows before grouping.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "What does the 'A' in ACID properties of relational databases stand for?",
            "options": [
                {"key": "A", "text": "Availability"},
                {"key": "B", "text": "Atomicity"},
                {"key": "C", "text": "Accuracy"},
                {"key": "D", "text": "Authenticity"},
            ],
            "correct_option": "B",
            "explanation": "Atomicity ensures that all operations in a database transaction succeed together or are entirely rolled back (all-or-nothing).",
            "marks": Decimal("1.00"),
        },
        {
            "question": "Which type of database index is most effective for range queries (e.g. BETWEEN 10 AND 50)?",
            "options": [
                {"key": "A", "text": "Hash Index"},
                {"key": "B", "text": "B-Tree Index"},
                {"key": "C", "text": "Bitmap Index"},
                {"key": "D", "text": "Full-text Index"},
            ],
            "correct_option": "B",
            "explanation": "B-Tree and B+Tree indexes store data in sorted sequential order, enabling efficient traversal for range comparison predicates.",
            "marks": Decimal("1.00"),
        },
    ],
    "aptitude": [
        {
            "question": "A train 240 m long passes a pole in 24 seconds. How long will it take to pass a platform 650 m long?",
            "options": [
                {"key": "A", "text": "65 seconds"},
                {"key": "B", "text": "89 seconds"},
                {"key": "C", "text": "100 seconds"},
                {"key": "D", "text": "150 seconds"},
            ],
            "correct_option": "B",
            "explanation": "Speed = 240 / 24 = 10 m/s. Total distance to cross platform = 240 + 650 = 890 m. Time = 890 / 10 = 89 seconds.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "If A can complete a work in 12 days and B in 24 days, in how many days can they complete the work together?",
            "options": [
                {"key": "A", "text": "6 days"},
                {"key": "B", "text": "8 days"},
                {"key": "C", "text": "10 days"},
                {"key": "D", "text": "18 days"},
            ],
            "correct_option": "B",
            "explanation": "A's 1-day work = 1/12, B's 1-day work = 1/24. Together = 1/12 + 1/24 = 3/24 = 1/8. Total time = 8 days.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "A shopkeeper marks an item 20% above cost price and allows a 10% discount. What is his net profit percentage?",
            "options": [
                {"key": "A", "text": "8%"},
                {"key": "B", "text": "10%"},
                {"key": "C", "text": "12%"},
                {"key": "D", "text": "15%"},
            ],
            "correct_option": "A",
            "explanation": "Let CP = 100. Marked Price = 120. SP after 10% discount = 120 - 12 = 108. Net Profit = 108 - 100 = 8%.",
            "marks": Decimal("1.00"),
        },
    ],
    "web": [
        {
            "question": "Which HTTP status code corresponds to '401 Unauthorized' versus '403 Forbidden'?",
            "options": [
                {"key": "A", "text": "401 means unauthenticated (missing credentials); 403 means authenticated but lacking permissions."},
                {"key": "B", "text": "401 means server error; 403 means bad request syntax."},
                {"key": "C", "text": "401 is permanent redirect; 403 is temporary redirect."},
                {"key": "D", "text": "401 and 403 are identical in RFC HTTP specifications."},
            ],
            "correct_option": "A",
            "explanation": "HTTP 401 denotes lack of valid authentication credentials, while 403 indicates authentication succeeded but authorization is refused.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "In modern Web Architecture, what is the primary benefit of JSON Web Tokens (JWT) for stateless authentication?",
            "options": [
                {"key": "A", "text": "Server encrypts all database records automatically"},
                {"key": "B", "text": "Client sessions can be validated cryptographically without checking a centralized server session store on every request"},
                {"key": "C", "text": "Eliminates the need for HTTPS connections"},
                {"key": "D", "text": "Compresses network images on transmission"},
            ],
            "correct_option": "B",
            "explanation": "JWTs carry cryptographically signed claims (HMAC or RSA), allowing distributed backend microservices to verify validity without DB session lookups.",
            "marks": Decimal("1.00"),
        },
    ],
    "cloud": [
        {
            "question": "In Docker containerization, what is the primary advantage of multi-stage builds?",
            "options": [
                {"key": "A", "text": "Allows running multiple OS kernels in one container"},
                {"key": "B", "text": "Dramatically reduces the final production image size by separating build tools from runtime artifacts"},
                {"key": "C", "text": "Eliminates the need for Dockerfiles"},
                {"key": "D", "text": "Increases memory allocation automatically"},
            ],
            "correct_option": "B",
            "explanation": "Multi-stage builds leave heavy compilers, SDKs, and build cache in intermediate stages, copying only minified compiled binaries into the final lightweight runner image.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "In Kubernetes, what is the smallest deployable computing unit that can be created and managed?",
            "options": [
                {"key": "A", "text": "Cluster"},
                {"key": "B", "text": "Node"},
                {"key": "C", "text": "Pod"},
                {"key": "D", "text": "Ingress"},
            ],
            "correct_option": "C",
            "explanation": "A Pod encapsulates one or more co-located containers, shared storage volumes, and network specifications in Kubernetes.",
            "marks": Decimal("1.00"),
        },
    ],
    "ai": [
        {
            "question": "In Large Language Models (LLMs), what is the primary purpose of the Self-Attention mechanism in the Transformer architecture?",
            "options": [
                {"key": "A", "text": "To sequentially process words one by one like an RNN"},
                {"key": "B", "text": "To compute contextual relevance weights between all pairs of tokens in parallel regardless of their position"},
                {"key": "C", "text": "To eliminate the need for GPU parallelization"},
                {"key": "D", "text": "To encrypt prompts before sending to the model"},
            ],
            "correct_option": "B",
            "explanation": "Self-attention computes dynamic attention scores across all tokens concurrently, allowing the model to capture long-range semantic dependencies.",
            "marks": Decimal("1.00"),
        },
        {
            "question": "What is the primary difference between RAG (Retrieval-Augmented Generation) and Model Fine-Tuning?",
            "options": [
                {"key": "A", "text": "RAG updates the underlying model weights; Fine-tuning provides dynamic external context at runtime."},
                {"key": "B", "text": "RAG injects retrieved external documents into the prompt at runtime without altering model weights; Fine-tuning adapts model parameters through gradient updates."},
                {"key": "C", "text": "RAG works only with audio; Fine-tuning works only with images."},
                {"key": "D", "text": "There is no functional difference between RAG and Fine-Tuning."},
            ],
            "correct_option": "B",
            "explanation": "RAG dynamically fetches factual context from a knowledge database into the prompt window, whereas fine-tuning performs gradient descent to adapt model weights.",
            "marks": Decimal("1.00"),
        },
    ]
}


async def generate_assessment_mcqs(topic: str, count: int = 5, difficulty: str = "MEDIUM") -> list[dict[str, Any]]:
    """
    Selects and tailors high-quality MCQs based on the requested placement topic.
    If topic matches specific domains (python, dsa, java, sql, aptitude, cloud, ai),
    curates the relevant questions. Otherwise, blends technical & problem-solving questions.
    """
    topic_lower = topic.lower()
    selected_pool: list[dict[str, Any]] = []

    # Map keywords to question pools
    if any(k in topic_lower for k in ["python", "django", "fastapi"]):
        selected_pool.extend(QUESTION_TEMPLATES["python"])
    if any(k in topic_lower for k in ["dsa", "algorithm", "data structure", "tree", "graph"]):
        selected_pool.extend(QUESTION_TEMPLATES["dsa"])
    if any(k in topic_lower for k in ["java", "spring", "oop", "object"]):
        selected_pool.extend(QUESTION_TEMPLATES["java"])
    if any(k in topic_lower for k in ["sql", "database", "postgres", "rdbms"]):
        selected_pool.extend(QUESTION_TEMPLATES["sql"])
    if any(k in topic_lower for k in ["aptitude", "quantitative", "reasoning", "math"]):
        selected_pool.extend(QUESTION_TEMPLATES["aptitude"])
    if any(k in topic_lower for k in ["web", "api", "rest", "frontend", "backend", "react"]):
        selected_pool.extend(QUESTION_TEMPLATES["web"])
    if any(k in topic_lower for k in ["cloud", "devops", "docker", "kubernetes", "aws"]):
        selected_pool.extend(QUESTION_TEMPLATES["cloud"])
    if any(k in topic_lower for k in ["ai", "machine learning", "ml", "genai", "llm", "data science"]):
        selected_pool.extend(QUESTION_TEMPLATES["ai"])

    # If no specific match or pool is smaller than requested count, draw from general curriculum
    if len(selected_pool) < count:
        all_pools = []
        for cat_questions in QUESTION_TEMPLATES.values():
            all_pools.extend(cat_questions)
        for q in all_pools:
            if q not in selected_pool:
                selected_pool.append(q)

    # Shuffle to provide natural variety
    shuffled = list(selected_pool)
    random.shuffle(shuffled)
    chosen = shuffled[:count]

    # Normalize format for AssessmentQuestion model
    formatted: list[dict[str, Any]] = []
    for item in chosen:
        formatted.append({
            "question_text": item.get("question") or item.get("question_text", ""),
            "options": item["options"],
            "correct_option": item["correct_option"],
            "explanation": item.get("explanation", ""),
            "marks": item.get("marks", Decimal("1.00")),
        })

    return formatted

