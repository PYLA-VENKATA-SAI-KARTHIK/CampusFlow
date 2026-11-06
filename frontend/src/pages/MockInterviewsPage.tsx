import React, { useState, useEffect, useRef } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { mockInterviewService } from '../services/mockInterviewService';
import type {
  MockInterviewEvaluationItem,
  MockInterviewSessionResponse,
} from '../types/mockInterview';

interface InterviewTrack {
  id: string;
  title: string;
  icon: string;
  category: 'TECHNICAL' | 'BEHAVIORAL' | 'SYSTEM_DESIGN' | 'DOMAIN';
  targetRole: string;
  durationMinutes: number;
  questionCount: number;
  badge: string;
  description: string;
  popularTopics: string[];
}

const TRACKS: InterviewTrack[] = [
  {
    id: 'role-swe',
    title: 'Software Engineer (SDE)',
    icon: '💻',
    category: 'TECHNICAL',
    targetRole: 'Software Development Engineer (SDE I/II)',
    durationMinutes: 45,
    questionCount: 5,
    badge: 'Top Choice',
    description: 'Solve core coding challenges, analyze time/space complexity trade-offs, concurrency, and OOP software engineering fundamentals.',
    popularTopics: ['Data Structures & Algorithms', 'Concurrency & Deadlocks', 'Graph Traversals', 'Dynamic Programming'],
  },
  {
    id: 'role-aiml',
    title: 'AI & Machine Learning Engineer',
    icon: '🧠',
    category: 'TECHNICAL',
    targetRole: 'Machine Learning / AI Engineer',
    durationMinutes: 45,
    questionCount: 5,
    badge: 'High Demand',
    description: 'Deep neural networks, PyTorch/TensorFlow, gradient descent, overfitting mitigations, and mathematical feature engineering.',
    popularTopics: ['Deep Learning & PyTorch', 'Overfitting & Regularization', 'Gradient Descent & Loss', 'Feature Engineering'],
  },
  {
    id: 'role-genai',
    title: 'Generative AI & LLM Engineer',
    icon: '✨',
    category: 'DOMAIN',
    targetRole: 'GenAI & LLM Solutions Engineer',
    durationMinutes: 45,
    questionCount: 5,
    badge: 'Cutting Edge',
    description: 'RAG architectures, vector embeddings, chunking strategies, prompt engineering, hallucination mitigation, and autonomous agents.',
    popularTopics: ['RAG Pipelines', 'Vector Databases & Embeddings', 'Hallucination Mitigation', 'Autonomous AI Agents'],
  },
  {
    id: 'role-system-design',
    title: 'System Design & Distributed Systems',
    icon: '🏗️',
    category: 'SYSTEM_DESIGN',
    targetRole: 'Cloud & Distributed Systems Architect',
    durationMinutes: 60,
    questionCount: 5,
    badge: 'Advanced',
    description: 'Architect resilient cloud services, design caching hierarchies, microservices decomposition, CAP theorem, and rate limiters.',
    popularTopics: ['Distributed Caching', 'Horizontal Sharding', 'CAP Theorem', 'Microservices & Message Queues'],
  },
  {
    id: 'role-fullstack',
    title: 'Fullstack & Web Engineer',
    icon: '⚡',
    category: 'DOMAIN',
    targetRole: 'Fullstack Software Engineer',
    durationMinutes: 45,
    questionCount: 5,
    badge: 'Popular',
    description: 'Explore modern React architecture, state management, asynchronous patterns, REST & GraphQL APIs, and web security standards.',
    popularTopics: ['React Rendering & State', 'Optimistic UI Updates', 'REST & GraphQL APIs', 'JWT & Security'],
  },
  {
    id: 'role-devops',
    title: 'DevOps & Cloud Platform Engineer',
    icon: '☁️',
    category: 'DOMAIN',
    targetRole: 'DevOps & Cloud Infrastructure Engineer',
    durationMinutes: 45,
    questionCount: 5,
    badge: 'High Demand',
    description: 'Automate CI/CD pipelines, Docker containerization, Kubernetes orchestration, Infrastructure as Code, and cloud observability.',
    popularTopics: ['Kubernetes Orchestration', 'CI/CD Pipelines', 'Terraform & IaC', 'Monitoring & Observability'],
  },
  {
    id: 'role-data',
    title: 'Data Platform & Analytics Engineer',
    icon: '📊',
    category: 'TECHNICAL',
    targetRole: 'Data Engineer / Analytics Architect',
    durationMinutes: 45,
    questionCount: 5,
    badge: 'Essential',
    description: 'Design resilient ETL/ELT pipelines, distributed processing with Apache Spark, real-time streaming with Kafka, and analytical schemas.',
    popularTopics: ['ETL & ELT Pipelines', 'Apache Spark & Kafka', 'Data Lakehouses', 'SQL Query Tuning'],
  },
  {
    id: 'role-hr',
    title: 'HR & Behavioral Leadership',
    icon: '🤝',
    category: 'BEHAVIORAL',
    targetRole: 'All Engineering & Management Roles',
    durationMinutes: 30,
    questionCount: 5,
    badge: 'Essential',
    description: 'Demonstrate leadership, teamwork, situational judgment, and crisis resolution using the structured STAR framework.',
    popularTopics: ['STAR Framework', 'Conflict Resolution', 'Handling Deadlines', 'Growth Mindset & Ethics'],
  },
];

interface QuestionBankItem {
  id: string;
  trackId: string;
  title: string;
  category: string;
  questionText: string;
  expectedKeywords: string[];
  tips: string;
}

const QUESTION_BANK: QuestionBankItem[] = [
  // ── SDE / Software Engineer ────────────────────────────────────────────────
  {
    id: 'swe-1',
    trackId: 'role-swe',
    title: 'LRU Cache Design & O(1) Operations',
    category: 'Data Structures & Algorithms',
    questionText: 'Explain how you would design and implement a Least Recently Used (LRU) Cache supporting get and put in O(1) time complexity. What data structures do you combine and why?',
    expectedKeywords: ['Doubly Linked List', 'Hash Map', 'O(1)', 'eviction', 'head', 'tail'],
    tips: 'Mention why a hash map provides O(1) key lookups and a doubly linked list allows O(1) node repositioning and tail eviction.',
  },
  {
    id: 'swe-2',
    trackId: 'role-swe',
    title: 'Optimizing Shortest Path: BFS vs Dijkstra',
    category: 'Data Structures & Algorithms',
    questionText: 'When would you select BFS over Dijkstra\'s algorithm for finding the shortest path in a graph, and how does the time complexity change when using a min-heap priority queue?',
    expectedKeywords: ['BFS', 'Dijkstra', 'unweighted', 'weights', 'min-heap', 'O(V + E)', 'O(E log V)'],
    tips: 'Highlight that BFS is optimal for unweighted graphs in O(V + E), whereas Dijkstra handles non-negative weights in O(E log V).',
  },
  {
    id: 'swe-3',
    trackId: 'role-swe',
    title: 'Dynamic Programming vs Greedy Strategy',
    category: 'Algorithms & Optimization',
    questionText: 'How do you determine whether an optimization problem should be solved with a Greedy approach or Dynamic Programming? Walk me through a classic example.',
    expectedKeywords: ['optimal substructure', 'overlapping subproblems', 'greedy choice property', 'memoization', 'knapsack'],
    tips: 'Contrast the Fractional Knapsack problem (greedy works) with the 0/1 Knapsack problem (requires DP due to overlapping subproblems).',
  },
  {
    id: 'swe-4',
    trackId: 'role-swe',
    title: 'Detecting and Preventing Deadlocks in Concurrent Systems',
    category: 'Operating Systems & Concurrency',
    questionText: 'What are the four necessary Coffman conditions for a deadlock to occur, and what techniques do you use in production code to prevent circular wait?',
    expectedKeywords: ['mutual exclusion', 'hold and wait', 'no preemption', 'circular wait', 'lock ordering', 'mutex'],
    tips: 'Detail how strict lock ordering or acquiring locks with timeouts (tryLock) eliminates circular wait.',
  },
  {
    id: 'swe-5',
    trackId: 'role-swe',
    title: 'Self-Balancing Binary Search Trees',
    category: 'Data Structures',
    questionText: 'Compare AVL trees and Red-Black trees. When is an AVL tree preferable over a Red-Black tree, and how do tree rotations maintain logarithmic height?',
    expectedKeywords: ['AVL', 'Red-Black', 'rotation', 'balance factor', 'logarithmic height', 'lookup intensive'],
    tips: 'Explain that AVL trees are more strictly balanced, making them ideal for read-heavy workloads where fast lookups outweigh insertion rotation costs.',
  },
  {
    id: 'swe-6',
    trackId: 'role-swe',
    title: 'Top-K Elements at High Throughput',
    category: 'Algorithms & Complexity',
    questionText: 'Given a stream of 100 million integers, how would you find the top K most frequent elements? Analyze the time and space complexity of your approach.',
    expectedKeywords: ['min-heap', 'hash map', 'Quickselect', 'streaming', 'O(N log K)', 'memory'],
    tips: 'Discuss keeping a min-heap of size K bounded in memory, giving O(N log K) time and O(K) space.',
  },
  {
    id: 'swe-7',
    trackId: 'role-swe',
    title: 'Graph Cycle Detection: Directed vs Undirected',
    category: 'Data Structures & Algorithms',
    questionText: 'How do you detect cycles in a directed graph compared to an undirected graph? Describe an algorithm using DFS and recursion state.',
    expectedKeywords: ['DFS', 'visited', 'recursion stack', 'in-degree', 'topological sort', 'Kahn'],
    tips: 'In directed graphs, an active recursion stack array is required to detect back-edges, or use Kahn’s topological sort.',
  },
  {
    id: 'swe-8',
    trackId: 'role-swe',
    title: 'Sliding Window vs Two-Pointer Optimization',
    category: 'Algorithms',
    questionText: 'Describe how the sliding window technique transforms brute force O(N^2) subarray problems into O(N) linear solutions. Provide a concrete scenario.',
    expectedKeywords: ['sliding window', 'two-pointer', 'linear time', 'O(N)', 'subarray', 'dynamic window'],
    tips: 'Walk through finding the longest substring without repeating characters using a hash set and dynamic window pointers.',
  },

  // ── AI & Machine Learning Engineer ─────────────────────────────────────────
  {
    id: 'aiml-1',
    trackId: 'role-aiml',
    title: 'Preventing Overfitting & Regularization in Deep Learning',
    category: 'Machine Learning Fundamentals',
    questionText: 'Explain the mathematical difference between L1 (Lasso) and L2 (Ridge) regularization. Why does L1 drive weights to exact zero while L2 shrinks them smoothly?',
    expectedKeywords: ['L1', 'L2', 'Lasso', 'Ridge', 'sparsity', 'penalty', 'gradient', 'zero weights'],
    tips: 'Explain the geometric diamond constraint of L1 versus the circular constraint of L2, leading to sparse feature selection.',
  },
  {
    id: 'aiml-2',
    trackId: 'role-aiml',
    title: 'Vanishing & Exploding Gradients in Deep Neural Networks',
    category: 'Deep Learning Architectures',
    questionText: 'What causes the vanishing and exploding gradient problem in deep backpropagation, and how do residual connections (ResNet) and normalization layers mitigate it?',
    expectedKeywords: ['vanishing gradient', 'backpropagation', 'chain rule', 'skip connections', 'ResNet', 'Batch Normalization'],
    tips: 'Show how residual skip connections allow gradients to flow unimpeded via identity mapping during backpropagation.',
  },
  {
    id: 'aiml-3',
    trackId: 'role-aiml',
    title: 'Handling Severely Imbalanced Datasets',
    category: 'Model Training & Evaluation',
    questionText: 'Suppose you are building a fraud detection model where only 0.1% of transactions are fraudulent. Why is accuracy misleading, and how would you optimize the model?',
    expectedKeywords: ['precision', 'recall', 'PR-AUC', 'SMOTE', 'focal loss', 'class weights', 'confusion matrix'],
    tips: 'Advocate for Precision-Recall curves over ROC, and explain cost-sensitive learning or focal loss rather than naive accuracy.',
  },
  {
    id: 'aiml-4',
    trackId: 'role-aiml',
    title: 'Gradient Descent Optimizers: SGD, Momentum, Adam',
    category: 'Optimization Algorithms',
    questionText: 'Compare Stochastic Gradient Descent with Momentum and Adam. What are the advantages of adaptive learning rates, and what risks exist regarding generalization?',
    expectedKeywords: ['SGD', 'Momentum', 'Adam', 'adaptive learning rate', 'first moment', 'second moment', 'generalization'],
    tips: 'Describe how Adam computes exponential moving averages of both gradients and squared gradients to handle sparse parameters.',
  },
  {
    id: 'aiml-5',
    trackId: 'role-aiml',
    title: 'Model Quantization & Pruning for Production',
    category: 'MLOps & Inference',
    questionText: 'How does post-training quantization reduce model inference latency and VRAM footprint? What is the trade-off between FP32, FP16, and INT8 precision?',
    expectedKeywords: ['quantization', 'INT8', 'FP16', 'latency', 'VRAM', 'accuracy degradation', 'calibration'],
    tips: 'Detail mapping 32-bit floating point weights to 8-bit integers using scaling factors and zero points with minimal accuracy loss.',
  },
  {
    id: 'aiml-6',
    trackId: 'role-aiml',
    title: 'Feature Engineering & Data Leakage Prevention',
    category: 'Feature Engineering',
    questionText: 'Describe how data leakage occurs during preprocessing or cross-validation, and how you structure a pipeline to ensure validation integrity.',
    expectedKeywords: ['data leakage', 'preprocessing', 'fit_transform', 'cross-validation', 'pipeline', 'test split'],
    tips: 'Emphasize that scalers and encoders must be fit solely on the training fold, never across the global dataset.',
  },
  {
    id: 'aiml-7',
    trackId: 'role-aiml',
    title: 'Convolutional Networks vs Vision Transformers',
    category: 'Deep Learning',
    questionText: 'Contrast the inductive biases in Convolutional Neural Networks (CNNs) with the global self-attention mechanism in Vision Transformers (ViTs).',
    expectedKeywords: ['inductive bias', 'translation invariance', 'self-attention', 'ViT', 'patches', 'data scale'],
    tips: 'CNNs have built-in spatial locality and translation invariance, whereas ViTs require massive pre-training data to discover spatial patterns.',
  },

  // ── Generative AI & LLM Engineer ──────────────────────────────────────────
  {
    id: 'genai-1',
    trackId: 'role-genai',
    title: 'End-to-End RAG Architecture Design',
    category: 'RAG & Knowledge Retrieval',
    questionText: 'Walk me through an enterprise Retrieval-Augmented Generation (RAG) system from raw PDF ingestion to synthesized LLM answer. How do you handle chunking and re-ranking?',
    expectedKeywords: ['chunking', 'embeddings', 'vector database', 'retrieval', 'cross-encoder', 're-ranking', 'prompt synthesis'],
    tips: 'Detail chunking with semantic overlaps, bi-encoder dense vector retrieval, cross-encoder re-ranking, and grounded context formatting.',
  },
  {
    id: 'genai-2',
    trackId: 'role-genai',
    title: 'Mitigating Hallucinations in Production LLMs',
    category: 'LLM Reliability & Guardrails',
    questionText: 'What techniques do you implement to prevent LLM hallucinations when answering questions about internal enterprise policies?',
    expectedKeywords: ['grounded context', 'temperature', 'guardrails', 'citations', 'Chain-of-Thought', 'hallucination'],
    tips: 'Cite low temperature settings (0.0–0.2), strict system prompt boundaries, quote extraction verification, and guardrail validation.',
  },
  {
    id: 'genai-3',
    trackId: 'role-genai',
    title: 'Vector Indexing: HNSW vs IVF-Flat',
    category: 'Vector Databases',
    questionText: 'How does Hierarchical Navigable Small World (HNSW) indexing compare to Inverted File Flat (IVF-Flat) for approximate nearest neighbor vector search?',
    expectedKeywords: ['HNSW', 'IVF', 'approximate nearest neighbor', 'cosine similarity', 'recall', 'latency', 'memory index'],
    tips: 'Explain that HNSW builds multi-layer skip-graphs offering higher recall and lower search latency at the cost of higher RAM usage.',
  },
  {
    id: 'genai-4',
    trackId: 'role-genai',
    title: 'Fine-Tuning with LoRA vs Full Fine-Tuning',
    category: 'Model Adaptation',
    questionText: 'Explain how Low-Rank Adaptation (LoRA) allows fine-tuning large language models efficiently. What are the rank decomposition matrices, and how do they save GPU memory?',
    expectedKeywords: ['LoRA', 'rank decomposition', 'frozen weights', 'PEFT', 'adapter', 'GPU VRAM', 'matrix multiplication'],
    tips: 'Show that decomposing weight updates into A and B matrices with low rank r reduces trainable parameters by over 99%.',
  },
  {
    id: 'genai-5',
    trackId: 'role-genai',
    title: 'Designing Multi-Step Autonomous AI Agents',
    category: 'Agentic AI Systems',
    questionText: 'How do you structure an autonomous AI agent using the ReAct (Reason + Act) pattern? How do you prevent infinite execution loops and validate tool invocation outputs?',
    expectedKeywords: ['ReAct', 'Thought-Action-Observation', 'tool calling', 'loop termination', 'memory buffer', 'agent'],
    tips: 'Break down the Thought -> Action -> Observation loop, max iterations guard, structured JSON schema parsing, and execution scratchpads.',
  },
  {
    id: 'genai-6',
    trackId: 'role-genai',
    title: 'Context Window Degradation & Needle-in-a-Haystack',
    category: 'LLM Context Dynamics',
    questionText: 'What is the "lost-in-the-middle" phenomenon in long-context LLMs, and how do you structure prompts to ensure critical information is prioritized?',
    expectedKeywords: ['lost-in-the-middle', 'context window', 'attention degradation', 'primacy and recency', 'prompt structuring'],
    tips: 'Highlight that attention mechanisms disproportionately favor information at the beginning and end of long prompts.',
  },
  {
    id: 'genai-7',
    trackId: 'role-genai',
    title: 'Evaluating RAG Pipelines with RAGAS Framework',
    category: 'Evaluation & Benchmarking',
    questionText: 'How do you programmatically evaluate the performance of a RAG pipeline without human annotators? What are Faithfulness and Answer Relevance metrics?',
    expectedKeywords: ['RAGAS', 'faithfulness', 'answer relevance', 'context precision', 'context recall', 'LLM-as-a-judge'],
    tips: 'Explain using LLM-as-a-Judge to measure whether generated claims are strictly grounded in retrieved passages (faithfulness).',
  },

  // ── System Design & Distributed Systems ────────────────────────────────────
  {
    id: 'sd-1',
    trackId: 'role-system-design',
    title: 'Designing a Scalable URL Shortener',
    category: 'Distributed Systems',
    questionText: 'How would you architect a distributed URL shortener service handling 500 million new URLs per month with low-latency redirection and high availability?',
    expectedKeywords: ['Base62', 'Snowflake ID', 'Redis Cache', 'database indexing', 'read replicas', 'collision'],
    tips: 'Discuss unique key generation (Base62 vs Snowflake), caching hot redirects in Redis with TTL, and sharding the persistent store.',
  },
  {
    id: 'sd-2',
    trackId: 'role-system-design',
    title: 'High-Throughput Notification Dispatcher',
    category: 'System Architecture',
    questionText: 'Design a campus-wide multi-channel notification engine (Email, SMS, Web Push) capable of dispatching 100,000 alerts during emergency announcements without dropping messages.',
    expectedKeywords: ['message queue', 'Kafka', 'RabbitMQ', 'worker pool', 'rate limiting', 'idempotency', 'dead-letter queue'],
    tips: 'Explain decoupling with asynchronous message queues, rate limiting third-party API gateways, and dead-letter queues for failed retries.',
  },
  {
    id: 'sd-3',
    trackId: 'role-system-design',
    title: 'Distributed Caching & Cache Invalidation',
    category: 'Distributed Systems',
    questionText: 'What strategies would you employ to maintain cache consistency in a high-read web system, and how would you resolve cache stampede and thundering herd issues?',
    expectedKeywords: ['Cache-Aside', 'Write-Through', 'TTL', 'mutex lock', 'probabilistic early expiration', 'invalidation'],
    tips: 'Detail Cache-Aside pattern, distributed mutex locks on cache misses, and jittered TTLs to prevent simultaneous cache expirations.',
  },
  {
    id: 'sd-4',
    trackId: 'role-system-design',
    title: 'Database Sharding & Consistent Hashing',
    category: 'Database Scalability',
    questionText: 'When vertical scaling is exhausted, how do you shard a relational database horizontally? How does consistent hashing minimize data migration during node scaling?',
    expectedKeywords: ['sharding', 'horizontal partitioning', 'consistent hashing', 'hash ring', 'virtual nodes', 'cross-shard joins'],
    tips: 'Explain virtual nodes on a hash ring to evenly distribute keys, and addressing the trade-off of losing ACID transactions across shard boundaries.',
  },
  {
    id: 'sd-5',
    trackId: 'role-system-design',
    title: 'CAP Theorem & Eventual Consistency',
    category: 'Distributed Systems Theory',
    questionText: 'Explain the CAP theorem trade-offs during a network partition. How does a system choose between Consistency (CP) and Availability (AP)?',
    expectedKeywords: ['CAP theorem', 'network partition', 'consistency', 'availability', 'eventual consistency', 'PACELC'],
    tips: 'Illustrate banking ledgers requiring strict CP versus social media feeds thriving under AP with eventual consistency.',
  },
  {
    id: 'sd-6',
    trackId: 'role-system-design',
    title: 'Architecting an E-Commerce Flash Sale System',
    category: 'High-Concurrency Architecture',
    questionText: 'How do you design an inventory reservation system where 10,000 users attempt to purchase 100 limited items in the same second without overselling?',
    expectedKeywords: ['Redis atomic', 'DECR', 'optimistic locking', 'pessimistic locking', 'message queue', 'idempotency'],
    tips: 'Detail atomic decrement in Redis memory buffers to reject excess traffic before hitting the relational database layer.',
  },
  {
    id: 'sd-7',
    trackId: 'role-system-design',
    title: 'Distributed Saga Pattern for Microservices',
    category: 'Distributed Transactions',
    questionText: 'How do you maintain data consistency across multiple microservices without two-phase commit (2PC)? Compare choreography vs orchestration sagas.',
    expectedKeywords: ['Saga pattern', 'orchestration', 'choreography', 'compensating transaction', 'eventual consistency'],
    tips: 'Explain executing forward transactions followed by automated compensating transactions (rollbacks) upon failure.',
  },

  // ── Fullstack & Web Architecture ───────────────────────────────────────────
  {
    id: 'fs-1',
    trackId: 'role-fullstack',
    title: 'Optimistic vs Pessimistic UI Updates',
    category: 'Frontend Architecture',
    questionText: 'Explain the difference between optimistic UI updates and pessimistic UI updates in single-page applications. When should each pattern be used, and how do you handle rollback?',
    expectedKeywords: ['optimistic', 'pessimistic', 'latency', 'rollback', 'consistency', 'mutation'],
    tips: 'Illustrate how optimistic updates improve perceived speed for low-risk actions like upvoting, with revert on error, while payments require pessimistic waits.',
  },
  {
    id: 'fs-2',
    trackId: 'role-fullstack',
    title: 'Authentication: JWT vs Session Cookies',
    category: 'Web Security',
    questionText: 'How do you secure user authentication across React and a REST backend? Compare storing JWTs in localStorage versus httpOnly cookies regarding XSS and CSRF.',
    expectedKeywords: ['JWT', 'httpOnly', 'cookie', 'localStorage', 'XSS', 'CSRF', 'SameSite', 'refresh token'],
    tips: 'Explain that httpOnly cookies prevent script access during XSS attacks, but require CSRF tokens or SameSite=Strict cookies to guard against CSRF.',
  },
  {
    id: 'fs-3',
    trackId: 'role-fullstack',
    title: 'Database Query Optimization & Indexing',
    category: 'Backend & Databases',
    questionText: 'Suppose an API endpoint fetching student drive applications becomes sluggish under heavy load. How do you profile the query, analyze execution plans, and optimize indexing?',
    expectedKeywords: ['EXPLAIN ANALYZE', 'composite index', 'full table scan', 'N+1 query', 'eager loading', 'latency'],
    tips: 'Walk through using EXPLAIN ANALYZE, eliminating N+1 queries using join or selectin eager loading, and creating B-tree indexes on foreign keys.',
  },
  {
    id: 'fs-4',
    trackId: 'role-fullstack',
    title: 'React Rendering Lifecycle & Performance Tuning',
    category: 'Frontend Performance',
    questionText: 'What triggers a re-render in React? How do useMemo, useCallback, and React.memo prevent unnecessary rendering, and when can premature optimization hurt performance?',
    expectedKeywords: ['re-render', 'Virtual DOM', 'useMemo', 'useCallback', 'React.memo', 'referential equality'],
    tips: 'Focus on referential equality of callbacks passed to memoized children, and memory overhead of hook closures.',
  },
  {
    id: 'fs-5',
    trackId: 'role-fullstack',
    title: 'Designing Idempotent REST and Webhook APIs',
    category: 'API Engineering',
    questionText: 'How do you ensure payment and registration endpoints are idempotent when clients retry network failures? Explain the idempotency key pattern.',
    expectedKeywords: ['idempotency key', 'HTTP POST', 'duplicate request', 'Redis lock', 'retry', 'safe mutation'],
    tips: 'Describe storing idempotency keys in Redis with short expiration to short-circuit duplicate request executions.',
  },
  {
    id: 'fs-6',
    trackId: 'role-fullstack',
    title: 'WebSockets vs Server-Sent Events vs Polling',
    category: 'Real-Time Web Technologies',
    questionText: 'When would you select Server-Sent Events (SSE) over WebSockets for live status updates in a web application? Compare connection overhead and protocol features.',
    expectedKeywords: ['WebSockets', 'Server-Sent Events', 'SSE', 'HTTP/2', 'bidirectional', 'unidirectional', 'reconnection'],
    tips: 'SSE uses standard HTTP/2, supports native automatic reconnection, and is optimal for unidirectional streaming like live notification feeds.',
  },
  {
    id: 'fs-7',
    trackId: 'role-fullstack',
    title: 'Direct S3 / Cloud Storage Upload with Presigned URLs',
    category: 'Cloud File Uploads',
    questionText: 'Why should large file uploads (such as student resume PDFs or videos) bypass the application backend server using presigned URLs? Walk through the workflow.',
    expectedKeywords: ['presigned URL', 'direct upload', 'S3', 'cloud storage', 'backend bottleneck', 'signed token'],
    tips: 'Direct browser-to-cloud upload eliminates server memory starvation and network saturation during concurrent file transfers.',
  },

  // ── DevOps & Cloud Platform Engineer ───────────────────────────────────────
  {
    id: 'devops-1',
    trackId: 'role-devops',
    title: 'Zero-Downtime Deployments: Blue-Green vs Canary',
    category: 'Deployment Strategies',
    questionText: 'Compare Blue-Green deployments with Canary deployments in Kubernetes. How do you monitor error rates to trigger an automated rollback?',
    expectedKeywords: ['Blue-Green', 'Canary', 'traffic shifting', 'rollback', 'ingress', 'health checks', 'zero-downtime'],
    tips: 'Detail gradually routing 5% to 10% of real user traffic to the canary release while monitoring HTTP 5xx error rate thresholds.',
  },
  {
    id: 'devops-2',
    trackId: 'role-devops',
    title: 'Kubernetes Pod Lifecycle & Resource Quotas',
    category: 'Container Orchestration',
    questionText: 'What is the distinction between resource requests and resource limits in a Kubernetes Pod spec? What happens when a container exceeds its memory limit?',
    expectedKeywords: ['requests', 'limits', 'OOMKilled', 'CPU throttling', 'scheduler', 'cgroups', 'QoS tier'],
    tips: 'Explain that requests determine scheduling node placement, while exceeding memory limits leads to immediate kernel OOMKilled eviction.',
  },
  {
    id: 'devops-3',
    trackId: 'role-devops',
    title: 'Infrastructure as Code: Terraform State & Drift',
    category: 'Infrastructure Automation',
    questionText: 'Why is the Terraform state file critical, and how do you manage remote state locking in team environments to prevent concurrent corruption?',
    expectedKeywords: ['Terraform', 'state file', 'remote backend', 'S3', 'DynamoDB', 'state locking', 'drift detection'],
    tips: 'Highlight using cloud object storage (S3/GCS) with distributed locking (DynamoDB) and running periodic terraform plan drift checks.',
  },
  {
    id: 'devops-4',
    trackId: 'role-devops',
    title: 'Continuous Integration & Security Scanning in CI/CD',
    category: 'CI/CD Pipelines',
    questionText: 'How do you architect an enterprise CI pipeline to deliver rapid developer feedback while enforcing static code analysis, SAST, and image vulnerability scans?',
    expectedKeywords: ['CI/CD', 'GitHub Actions', 'SAST', 'vulnerability scanning', 'Docker build cache', 'Trivy', 'SonarQube'],
    tips: 'Describe parallel test matrices, Docker multi-stage caching, and blocking merges when critical CVE vulnerabilities are detected.',
  },
  {
    id: 'devops-5',
    trackId: 'role-devops',
    title: 'Three Pillars of Observability: Metrics, Logs, Traces',
    category: 'Site Reliability Engineering',
    questionText: 'How do metrics, logs, and distributed traces complement each other during a production outage? How does OpenTelemetry tie them together?',
    expectedKeywords: ['metrics', 'logs', 'distributed tracing', 'OpenTelemetry', 'Prometheus', 'trace ID', 'correlation'],
    tips: 'Explain starting from high-level Prometheus alert metrics, pivoting to distributed traces via TraceID, and drilling down into pinpoint error logs.',
  },
  {
    id: 'devops-6',
    trackId: 'role-devops',
    title: 'Disaster Recovery: RTO, RPO & Multi-Region Resilience',
    category: 'Cloud Reliability',
    questionText: 'Define Recovery Time Objective (RTO) and Recovery Point Objective (RPO). How do you architect a database replication topology to achieve near-zero RPO?',
    expectedKeywords: ['RTO', 'RPO', 'replication', 'active-passive', 'multi-region', 'failover', 'point-in-time recovery'],
    tips: 'Explain synchronous replication across availability zones and automated failover DNS routing with health checks.',
  },

  // ── Data Platform & Analytics Engineer ─────────────────────────────────────
  {
    id: 'data-1',
    trackId: 'role-data',
    title: 'Batch vs Stream Processing Architectures',
    category: 'Data Processing Architectures',
    questionText: 'Compare the Lambda architecture and the Kappa architecture for large-scale data systems. When would you choose Apache Flink over Apache Spark for streaming?',
    expectedKeywords: ['Lambda architecture', 'Kappa architecture', 'batch layer', 'speed layer', 'Apache Spark', 'Apache Flink', 'event-driven'],
    tips: 'Highlight that Kappa architecture eliminates duplicate code by processing all data through a single stream engine like Flink.',
  },
  {
    id: 'data-2',
    trackId: 'role-data',
    title: 'Apache Kafka Partitioning & Consumer Groups',
    category: 'Event Streaming',
    questionText: 'How does Kafka achieve horizontal scalability and high throughput? What determines the maximum degree of consumer parallelism in a consumer group?',
    expectedKeywords: ['Kafka', 'partitions', 'consumer group', 'parallelism', 'offset commit', 'rebalance', 'ordering'],
    tips: 'Explain that the number of consumers actively reading in a consumer group cannot exceed the number of partitions on the topic.',
  },
  {
    id: 'data-3',
    trackId: 'role-data',
    title: 'Data Lakehouse ACID Transactions: Delta Lake & Iceberg',
    category: 'Modern Data Storage',
    questionText: 'How do modern table formats like Apache Iceberg and Delta Lake bring ACID transactions to cloud object storage (S3/GCS)?',
    expectedKeywords: ['ACID', 'Delta Lake', 'Apache Iceberg', 'parquet', 'metadata transaction log', 'time travel', 'compaction'],
    tips: 'Detail snapshot isolation using append-only JSON/Avro metadata transaction logs pointing to immutable Parquet data files.',
  },
  {
    id: 'data-4',
    trackId: 'role-data',
    title: 'Distributed SQL Tuning & Data Skew in Apache Spark',
    category: 'Big Data Query Optimization',
    questionText: 'What is data skew in a distributed join in Apache Spark? How do salting and broadcast hash joins resolve sluggish shuffle operations?',
    expectedKeywords: ['data skew', 'shuffle', 'broadcast join', 'salting', 'hash join', 'straggler task', 'partitioning'],
    tips: 'Explain broadcasting small dimension tables to avoid shuffling, and salting skewed join keys with random integers to distribute hot partitions.',
  },
  {
    id: 'data-5',
    trackId: 'role-data',
    title: 'Dimensional Modeling: Star vs Snowflake Schema',
    category: 'Data Warehousing',
    questionText: 'Compare a Star schema with a Snowflake schema in a cloud data warehouse (Snowflake/BigQuery). What are the trade-offs regarding join performance and storage normalization?',
    expectedKeywords: ['Star schema', 'Snowflake schema', 'fact table', 'dimension table', 'normalization', 'join performance', 'denormalization'],
    tips: 'Star schemas denormalize dimensions to reduce query joins and maximize columnar query performance in OLAP engines.',
  },
  {
    id: 'data-6',
    trackId: 'role-data',
    title: 'Change Data Capture (CDC) Architecture',
    category: 'Data Ingestion',
    questionText: 'How does log-based Change Data Capture (CDC) with Debezium capture database mutations without impacting OLTP production database performance?',
    expectedKeywords: ['CDC', 'Debezium', 'Write-Ahead Log', 'WAL', 'Kafka', 'OLTP to OLAP', 'low latency'],
    tips: 'Log-based CDC reads binary transaction logs directly from disk rather than querying tables, avoiding table locks and CPU overhead.',
  },

  // ── HR & Behavioral (STAR Method) ──────────────────────────────────────────
  {
    id: 'hr-1',
    trackId: 'role-hr',
    title: 'Handling Technical Disagreements Constructively',
    category: 'Teamwork & Conflict Resolution',
    questionText: 'Tell me about a time when you strongly disagreed with a teammate on an architectural decision or technical approach. How did you resolve it and what was the outcome?',
    expectedKeywords: ['Situation', 'Task', 'Action', 'Result', 'data-driven', 'consensus', 'compromise'],
    tips: 'Structure your answer with STAR: describe the technical dispute, how you benchmarked or discussed trade-offs constructively, and the positive result.',
  },
  {
    id: 'hr-2',
    trackId: 'role-hr',
    title: 'Navigating an Impending Deadline or Crisis',
    category: 'Resilience & Project Management',
    questionText: 'Describe a situation where a critical software defect or unexpected blocker threatened your project delivery milestone. What steps did you take?',
    expectedKeywords: ['Situation', 'Task', 'Action', 'Result', 'prioritization', 'communication', 'root cause', 'mitigation'],
    tips: 'Highlight proactive communication with stakeholders, triage of non-essential features, and addressing the root cause.',
  },
  {
    id: 'hr-3',
    trackId: 'role-hr',
    title: 'Receiving Critical Feedback & Growth',
    category: 'Growth Mindset & Leadership',
    questionText: 'Can you share an instance where you received constructive or critical feedback on your code or leadership style? How did you respond and adapt?',
    expectedKeywords: ['Situation', 'Task', 'Action', 'Result', 'code review', 'mentorship', 'improvement', 'reflection'],
    tips: 'Demonstrate humility, eagerness to learn, and concrete changes you implemented following the feedback.',
  },
  {
    id: 'hr-4',
    trackId: 'role-hr',
    title: 'Collaborating with Cross-Functional Non-Technical Teams',
    category: 'Stakeholder Communication',
    questionText: 'Describe a time when you had to explain a complex technical limitation or architectural delay to non-technical stakeholders (e.g., product managers or recruiters).',
    expectedKeywords: ['Situation', 'Task', 'Action', 'Result', 'empathy', 'business impact', 'simplification', 'alignment'],
    tips: 'Focus on translating technical debt into business risks and delivering realistic timeline alternatives.',
  },
  {
    id: 'hr-5',
    trackId: 'role-hr',
    title: 'A Critical Project Failure and Lessons Learned',
    category: 'Accountability & Post-Mortem',
    questionText: 'Tell me about a significant mistake or failure in your engineering work. How did you take ownership, and what systemic changes did you put in place to prevent recurrence?',
    expectedKeywords: ['Situation', 'Task', 'Action', 'Result', 'ownership', 'blameless post-mortem', 'testing', 'safeguards'],
    tips: 'Avoid deflecting blame; highlight personal accountability and preventative mechanisms like automated integration tests.',
  },
  {
    id: 'hr-6',
    trackId: 'role-hr',
    title: 'Managing Competing High-Priority Demands',
    category: 'Time Management & Prioritization',
    questionText: 'How do you handle multiple urgent tasks assigned simultaneously during an active sprint? Walk me through a real example from your coursework or internships.',
    expectedKeywords: ['Situation', 'Task', 'Action', 'Result', 'Eisenhower matrix', 'stakeholder communication', 'triage', 'focus'],
    tips: 'Explain aligning with the project lead on impact vs effort, setting realistic delivery expectations, and focusing on high-ROI tasks.',
  },
  {
    id: 'hr-7',
    trackId: 'role-hr',
    title: 'Advocating for Engineering Excellence or Ethics',
    category: 'Ethics & Code Quality',
    questionText: 'Describe an occasion where you advocated for better code quality, security standards, or data privacy when pressured to deliver quickly.',
    expectedKeywords: ['Situation', 'Task', 'Action', 'Result', 'code quality', 'security', 'tech debt', 'long-term maintainability'],
    tips: 'Demonstrate how you framed quality as a protector of velocity that prevents catastrophic production incidents.',
  },
];

// Helper to randomly sample 5 non-repeating questions from track pool
function sampleQuestionsForTrack(trackId: string, count: number = 5, excludeIds: string[] = []): QuestionBankItem[] {
  const pool = QUESTION_BANK.filter((q) => q.trackId === trackId);
  if (pool.length <= count) return pool;

  // Prefer questions not in excludeIds for fresh diversity
  const nonExcluded = pool.filter((q) => !excludeIds.includes(q.id));
  const candidatePool = nonExcluded.length >= count ? nonExcluded : pool;

  const shuffled = [...candidatePool].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

export const MockInterviewsPage: React.FC = () => {
  // Navigation tab
  const [activeTab, setActiveTab] = useState<'simulator' | 'history'>('simulator');

  // Track & Question State
  const [selectedTrackId, setSelectedTrackId] = useState<string>('role-swe');
  const [refreshOffset, setRefreshOffset] = useState<number>(0);
  const [activeQuestions, setActiveQuestions] = useState<QuestionBankItem[]>(() =>
    sampleQuestionsForTrack('role-swe', 5)
  );
  const [activeQuestionIdx, setActiveQuestionIdx] = useState<number>(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [refreshNotification, setRefreshNotification] = useState<string | null>(null);

  // Spoken Answer & Evaluation State
  const [answerText, setAnswerText] = useState<string>('');
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [isFinishing, setIsFinishing] = useState<boolean>(false);
  const [currentEvaluation, setCurrentEvaluation] = useState<MockInterviewEvaluationItem | null>(null);
  const [completedEvaluations, setCompletedEvaluations] = useState<MockInterviewEvaluationItem[]>([]);

  // Performance Report State
  const [performanceReport, setPerformanceReport] = useState<MockInterviewSessionResponse | null>(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);

  // Past Sessions History
  const [pastSessions, setPastSessions] = useState<MockInterviewSessionResponse[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  // Voice Agent Audio & STT State
  const [isAgentSpeaking, setIsAgentSpeaking] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingSeconds, setRecordingSeconds] = useState<number>(0);
  const [autoReadQuestion, setAutoReadQuestion] = useState<boolean>(true);
  const [sttSupported, setSttSupported] = useState<boolean>(true);

  // Refs for audio and timers
  const recognitionRef = useRef<any>(null);
  const timerIntervalRef = useRef<any>(null);
  const audioDurationRef = useRef<number>(0);

  const selectedTrack = TRACKS.find((t) => t.id === selectedTrackId) || TRACKS[0];
  const currentQuestion = activeQuestions[activeQuestionIdx] || activeQuestions[0];

  // Initialize Speech Recognition & Synthesis check
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSttSupported(false);
    }

    return () => {
      stopVoice();
      stopRecording();
    };
  }, []);

  // Fetch past sessions when switching to History tab
  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  const fetchHistory = async () => {
    try {
      setLoadingHistory(true);
      const data = await mockInterviewService.listSessions();
      setPastSessions(data);
    } catch (err) {
      console.error('Failed to load past sessions:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Text-To-Speech Agent Voice
  const speakQuestion = (text: string) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    // Pick an expressive natural English voice if available
    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(
      (v) =>
        v.lang.startsWith('en') &&
        (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Daniel'))
    ) || voices.find((v) => v.lang.startsWith('en'));

    if (naturalVoice) utterance.voice = naturalVoice;

    utterance.onstart = () => setIsAgentSpeaking(true);
    utterance.onend = () => setIsAgentSpeaking(false);
    utterance.onerror = () => setIsAgentSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopVoice = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsAgentSpeaking(false);
    }
  };

  // Speech-To-Text Audio Recording
  const startRecording = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech-to-Text recognition is not supported in this browser. Please type your response directly.');
      return;
    }

    stopVoice();

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsRecording(true);
        setRecordingSeconds(0);
        audioDurationRef.current = 0;
        timerIntervalRef.current = setInterval(() => {
          setRecordingSeconds((prev) => {
            const next = prev + 1;
            audioDurationRef.current = next;
            return next;
          });
        }, 1000);
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        for (let i = 0; i < event.results.length; ++i) {
          finalTranscript += event.results[i][0].transcript;
        }
        setAnswerText(finalTranscript);
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
        stopRecording();
      };

      recognition.onend = () => {
        setIsRecording(false);
        if (timerIntervalRef.current) {
          clearInterval(timerIntervalRef.current);
          timerIntervalRef.current = null;
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error('Failed to initialize speech recognition:', err);
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        // ignore
      }
      recognitionRef.current = null;
    }
    setIsRecording(false);
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
  };

  // Start new mock interview session for a track
  const handleStartTrackSession = async (track: InterviewTrack) => {
    try {
      stopVoice();
      stopRecording();
      setSelectedTrackId(track.id);
      setRefreshOffset(0);

      let sampled = sampleQuestionsForTrack(track.id, 5);
      try {
        const ragDocs = await mockInterviewService.getTrackQuestions(track.id, 5, 0);
        if (ragDocs && ragDocs.length > 0) {
          sampled = ragDocs.map((doc) => ({
            id: doc.id,
            trackId: doc.track_id,
            title: doc.question.length > 55 ? doc.question.slice(0, 55) + '...' : doc.question,
            category: doc.subtopic || doc.category,
            questionText: doc.question,
            expectedKeywords: doc.key_concepts,
            tips: `Verified in ${doc.source_document}. Recommended focus: ${doc.key_concepts.slice(0, 3).join(', ')}.`,
          }));
        }
      } catch (err) {
        console.warn('Using local question pool:', err);
      }

      setActiveQuestions(sampled);
      setActiveQuestionIdx(0);
      setAnswerText('');
      setCurrentEvaluation(null);
      setCompletedEvaluations([]);
      setPerformanceReport(null);
      setRefreshNotification(null);

      const newSession = await mockInterviewService.createSession({
        track_id: track.id,
        track_title: track.title,
        target_role: track.targetRole,
      });

      setSessionId(newSession.id);

      if (sampled[0] && autoReadQuestion) {
        setTimeout(() => {
          speakQuestion(sampled[0].questionText);
        }, 400);
      }

      const el = document.getElementById('interactive-simulator');
      el?.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      console.error('Failed to create mock interview session:', err);
      alert('Could not initialize interview session. Please check your connection.');
    }
  };

  // Refresh Questions: Sample 5 new, non-repeated questions from the RAG knowledge repository
  const handleRefreshQuestions = async () => {
    stopVoice();
    stopRecording();
    const nextOffset = refreshOffset + 5;
    setRefreshOffset(nextOffset);

    try {
      const ragDocs = await mockInterviewService.getTrackQuestions(selectedTrackId, 5, nextOffset);
      if (ragDocs && ragDocs.length > 0) {
        const mappedQuestions: QuestionBankItem[] = ragDocs.map((doc) => ({
          id: doc.id,
          trackId: doc.track_id,
          title: doc.question.length > 55 ? doc.question.slice(0, 55) + '...' : doc.question,
          category: doc.subtopic || doc.category,
          questionText: doc.question,
          expectedKeywords: doc.key_concepts,
          tips: `Verified in ${doc.source_document}. Recommended focus: ${doc.key_concepts.slice(0, 3).join(', ')}.`,
        }));
        setActiveQuestions(mappedQuestions);
        setActiveQuestionIdx(0);
        setAnswerText('');
        setCurrentEvaluation(null);
        setCompletedEvaluations([]);
        setRecordingSeconds(0);
        audioDurationRef.current = 0;

        setRefreshNotification('Loaded 5 new RAG-grounded questions from verified handbooks!');
        setTimeout(() => setRefreshNotification(null), 4000);

        if (mappedQuestions[0] && autoReadQuestion) {
          setTimeout(() => speakQuestion(mappedQuestions[0].questionText), 300);
        }
        return;
      }
    } catch (e) {
      console.warn('Falling back to local question pool', e);
    }

    const currentIds = activeQuestions.map((q) => q.id);
    const newQuestions = sampleQuestionsForTrack(selectedTrackId, 5, currentIds);
    setActiveQuestions(newQuestions);
    setActiveQuestionIdx(0);
    setAnswerText('');
    setCurrentEvaluation(null);
    setCompletedEvaluations([]);
    setRecordingSeconds(0);
    audioDurationRef.current = 0;

    setRefreshNotification('Generated 5 brand new questions for this role! All set for practice.');
    setTimeout(() => setRefreshNotification(null), 4000);

    if (newQuestions[0] && autoReadQuestion) {
      setTimeout(() => speakQuestion(newQuestions[0].questionText), 300);
    }
  };

  // Evaluate candidate answer with the AI Agent
  const handleEvaluateAnswer = async () => {
    if (!answerText.trim()) return;
    stopRecording();
    stopVoice();

    try {
      setIsEvaluating(true);

      // Ensure session exists
      let activeSessionId = sessionId;
      if (!activeSessionId) {
        const created = await mockInterviewService.createSession({
          track_id: selectedTrack.id,
          track_title: selectedTrack.title,
          target_role: selectedTrack.targetRole,
        });
        activeSessionId = created.id;
        setSessionId(activeSessionId);
      }

      const evalResult = await mockInterviewService.evaluateAnswer(activeSessionId, {
        question_index: activeQuestionIdx,
        question_id: currentQuestion.id,
        question_text: currentQuestion.questionText,
        question_category: currentQuestion.category,
        student_answer: answerText,
        expected_keywords: currentQuestion.expectedKeywords,
        coaching_tips: currentQuestion.tips,
        audio_duration_seconds: audioDurationRef.current > 0 ? audioDurationRef.current : undefined,
      });

      setCurrentEvaluation(evalResult);
      setCompletedEvaluations((prev) => {
        const filtered = prev.filter((e) => e.question_index !== activeQuestionIdx);
        return [...filtered, evalResult];
      });
    } catch (err) {
      console.error('Failed to evaluate answer:', err);
      alert('Failed to evaluate response. Please retry.');
    } finally {
      setIsEvaluating(false);
    }
  };

  // Move to next question
  const handleNextQuestion = () => {
    stopVoice();
    stopRecording();
    const nextIdx = activeQuestionIdx + 1;
    if (nextIdx < activeQuestions.length) {
      setActiveQuestionIdx(nextIdx);
      setAnswerText('');
      setCurrentEvaluation(null);
      setRecordingSeconds(0);
      audioDurationRef.current = 0;

      const nextQ = activeQuestions[nextIdx];
      if (nextQ && autoReadQuestion) {
        setTimeout(() => speakQuestion(nextQ.questionText), 300);
      }
    }
  };

  // Complete session and generate Performance Report
  const handleCompleteSession = async () => {
    if (!sessionId) return;
    stopVoice();
    stopRecording();

    try {
      setIsFinishing(true);
      const report = await mockInterviewService.completeSession(sessionId);
      setPerformanceReport(report);
      setIsReportModalOpen(true);
      fetchHistory();
    } catch (err) {
      console.error('Failed to finalize mock interview session:', err);
      alert('Could not complete interview session. Please try again.');
    } finally {
      setIsFinishing(false);
    }
  };

  // Open existing historical session report
  const handleViewHistoricalReport = async (pastSessionId: string) => {
    try {
      const details = await mockInterviewService.getSessionDetails(pastSessionId);
      setPerformanceReport(details);
      setIsReportModalOpen(true);
    } catch (err) {
      console.error('Failed to load session details:', err);
      alert('Could not load report details.');
    }
  };

  const getRatingBadgeVariant = (rating?: string) => {
    switch (rating) {
      case 'EXCEPTIONAL':
        return 'success';
      case 'JOB_READY':
        return 'primary';
      case 'DEVELOPING':
        return 'warning';
      default:
        return 'neutral';
    }
  };

  const formatSeconds = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto pb-20">
      {/* ── Page Header ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="px-3 py-0.5 rounded-full text-[10px] font-black tracking-wider uppercase bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-xs">
              🤖 Agentic AI Voice Engine
            </span>
            <Badge variant="success" size="sm">
              Industry Ready • 5 Questions
            </Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            AI Voice Agent Mock Interviews
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl">
            Simulate realistic corporate placement interviews across SDE, AI/ML, GenAI, System Design, DevOps, and HR roles. Each session features 5 tailored questions with real-time audio evaluation and performance synthesis.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant={activeTab === 'simulator' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('simulator')}
            leftIcon={<span>🎙️</span>}
          >
            Voice Interviewer
          </Button>
          <Button
            variant={activeTab === 'history' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('history')}
            leftIcon={<span>📜</span>}
          >
            Past Reports & History
          </Button>
        </div>
      </div>

      {activeTab === 'simulator' ? (
        <>
          {/* ── Hero Banner ──────────────────────────────────────────────────── */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white p-6 sm:p-8 shadow-2xl border border-indigo-800/40">
            <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />
            <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
              <div className="lg:col-span-2 space-y-3">
                <div className="flex items-center space-x-2">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    Voice-Enabled Corporate Preparation
                  </span>
                  {isAgentSpeaking && (
                    <span className="inline-flex items-center space-x-1 text-xs text-emerald-400 font-semibold animate-pulse">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span>Agent Speaking...</span>
                    </span>
                  )}
                  {isRecording && (
                    <span className="inline-flex items-center space-x-1 text-xs text-rose-400 font-semibold animate-pulse">
                      <span className="w-2 h-2 rounded-full bg-rose-500" />
                      <span>Recording Candidate Voice ({formatSeconds(recordingSeconds)})</span>
                    </span>
                  )}
                </div>

                <h2 className="text-xl sm:text-2xl font-black text-white leading-snug">
                  Practice Spoken Articulation, Technical Depth & STAR Behavioral Precision
                </h2>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-xl">
                  The AI Voice Agent articulates interview questions, listens to your voice responses, detects filler hesitations, and evaluates technical depth, communication clarity, and structural storytelling across 5 tailored questions.
                </p>

                <div className="pt-2 flex flex-wrap gap-2 text-[11px] font-semibold text-indigo-200">
                  <span className="px-3 py-1 rounded-full bg-white/10 border border-white/10">🎙️ Speech-to-Text Analysis</span>
                  <span className="px-3 py-1 rounded-full bg-white/10 border border-white/10">🗣️ Natural Text-to-Speech</span>
                  <span className="px-3 py-1 rounded-full bg-white/10 border border-white/10">🔄 Dynamic Refresh Questions</span>
                  <span className="px-3 py-1 rounded-full bg-white/10 border border-white/10">📊 Deep Performance Report</span>
                </div>
              </div>

              {/* Active Agent Avatar & State Card */}
              <div className="flex flex-col items-center justify-center p-6 bg-white/5 rounded-2xl border border-white/10 text-center backdrop-blur-md">
                <div className="relative mb-3">
                  <div
                    className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl shadow-xl transition-all duration-300 ${
                      isAgentSpeaking
                        ? 'bg-gradient-to-tr from-indigo-500 to-purple-500 ring-8 ring-indigo-400/30 scale-105'
                        : isRecording
                        ? 'bg-gradient-to-tr from-rose-500 to-amber-500 ring-8 ring-rose-500/30 scale-105'
                        : 'bg-gradient-to-tr from-slate-800 to-indigo-900 border border-indigo-500/40'
                    }`}
                  >
                    {isAgentSpeaking ? '🗣️' : isRecording ? '🎙️' : '🤖'}
                  </div>
                  {(isAgentSpeaking || isRecording) && (
                    <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center text-white text-[10px] font-black border-2 border-slate-900 animate-bounce">
                      ●
                    </div>
                  )}
                </div>

                <div className="text-sm font-black text-white">CampusFlow AI Agent</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {isAgentSpeaking
                    ? 'Speaking Question Aloud...'
                    : isRecording
                    ? 'Listening & Transcribing Voice...'
                    : 'Ready for Your Response'}
                </div>

                <div className="mt-4 flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs border-white/20 text-white hover:bg-white/10"
                    onClick={() => speakQuestion(currentQuestion.questionText)}
                  >
                    🔊 Read Question
                  </Button>
                  {isAgentSpeaking && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs border-rose-500/40 text-rose-300 hover:bg-rose-500/10"
                      onClick={stopVoice}
                    >
                      ⏹️ Stop Voice
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* ── Choose Domain Track ─────────────────────────────────────────── */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-extrabold text-slate-900">
                  1. Select Your Target Interview Track
                </h3>
                <p className="text-xs text-slate-500">
                  Select a corporate role to calibrate the AI Voice Agent's interview rubric and questions.
                </p>
              </div>
              <Badge variant="primary" size="sm">
                {TRACKS.length} Specialized Tracks • 5 Questions Each
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {TRACKS.map((track) => {
                const isSelected = selectedTrackId === track.id;
                return (
                  <div
                    key={track.id}
                    onClick={() => handleStartTrackSession(track)}
                    className={`p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between space-y-4 ${
                      isSelected
                        ? 'bg-indigo-50/90 border-indigo-600 ring-2 ring-indigo-300 shadow-md'
                        : 'bg-white border-slate-200/90 hover:border-indigo-300 hover:shadow-xs'
                    }`}
                  >
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-2xl">{track.icon}</span>
                        <span
                          className={`px-2 py-0.5 rounded-md text-[9px] font-black uppercase tracking-wider ${
                            isSelected
                              ? 'bg-indigo-600 text-white'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {track.badge}
                        </span>
                      </div>
                      <h4 className="text-sm font-extrabold text-slate-900 leading-snug">
                        {track.title}
                      </h4>
                      <p className="text-[11px] text-slate-500 leading-relaxed line-clamp-2">
                        {track.description}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-slate-100 space-y-2">
                      <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase">
                        <span>{track.durationMinutes} Mins</span>
                        <span className="text-indigo-600 font-extrabold">5 Questions</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {track.popularTopics.slice(0, 2).map((t, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-[9px] font-semibold"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── Interactive Live Interview Simulator ────────────────────────── */}
          <div id="interactive-simulator" className="space-y-4 scroll-mt-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs">
              <div>
                <h3 className="text-base font-extrabold text-slate-900 flex items-center space-x-2">
                  <span>2. Live Interview Question & Voice Response</span>
                  <Badge variant="primary" size="sm">5 Questions</Badge>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Target Track: <strong className="text-indigo-700">{selectedTrack.title}</strong> • Role: {selectedTrack.targetRole}
                </p>
              </div>

              {/* Controls, Refresh & Finish */}
              <div className="flex flex-wrap items-center gap-2.5">
                {/* Refresh Questions Button */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefreshQuestions}
                  leftIcon={<span>🔄</span>}
                  className="text-xs text-indigo-700 border-indigo-200 hover:bg-indigo-50 font-bold"
                  title="Generate a brand new set of 5 questions from the question bank for this role"
                >
                  Refresh Questions
                </Button>

                <label className="flex items-center space-x-1.5 text-xs text-slate-600 cursor-pointer pl-1">
                  <input
                    type="checkbox"
                    checked={autoReadQuestion}
                    onChange={(e) => setAutoReadQuestion(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Auto-read aloud</span>
                </label>

                {completedEvaluations.length > 0 && (
                  <Button
                    variant="primary"
                    size="sm"
                    isLoading={isFinishing}
                    onClick={handleCompleteSession}
                    leftIcon={<span>📊</span>}
                  >
                    Finish & View Report ({completedEvaluations.length}/5)
                  </Button>
                )}
              </div>
            </div>

            {/* Refresh Notification Toast */}
            {refreshNotification && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 font-bold flex items-center justify-between animate-fade-in">
                <span className="flex items-center space-x-1.5">
                  <span>✨</span>
                  <span>{refreshNotification}</span>
                </span>
                <button
                  onClick={() => setRefreshNotification(null)}
                  className="text-emerald-600 hover:text-emerald-900 text-sm font-black"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Stepper Dots (Q1 to Q5) */}
            <div className="flex items-center space-x-2 bg-slate-100 p-2 rounded-xl border border-slate-200">
              {activeQuestions.map((q, idx) => {
                const isAnswered = completedEvaluations.some((e) => e.question_index === idx);
                const isCurrent = idx === activeQuestionIdx;
                return (
                  <button
                    key={q.id || idx}
                    onClick={() => {
                      stopVoice();
                      stopRecording();
                      setActiveQuestionIdx(idx);
                      const existingEval = completedEvaluations.find((e) => e.question_index === idx);
                      setCurrentEvaluation(existingEval || null);
                      setAnswerText(existingEval ? existingEval.student_answer : '');
                    }}
                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-bold text-center transition ${
                      isCurrent
                        ? 'bg-indigo-600 text-white shadow-xs'
                        : isAnswered
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-white text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    Q{idx + 1} {isAnswered && '✓'}
                  </button>
                );
              })}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Question & Answer Box */}
              <div className="lg:col-span-2 space-y-4">
                <Card variant="default" className="p-6 rounded-3xl border-slate-200 space-y-4 shadow-sm">
                  {/* Category & Status */}
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div className="flex items-center space-x-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        {currentQuestion.category}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs text-indigo-600 hover:bg-indigo-50"
                        onClick={() => speakQuestion(currentQuestion.questionText)}
                        leftIcon={<span>🔊</span>}
                      >
                        Replay Audio
                      </Button>
                      <span className="text-xs font-bold text-slate-400">
                        {activeQuestionIdx + 1} of {activeQuestions.length}
                      </span>
                    </div>
                  </div>

                  {/* Question Content */}
                  <div>
                    <h4 className="text-base sm:text-lg font-black text-slate-900 leading-snug">
                      {currentQuestion.title}
                    </h4>
                    <p className="text-xs sm:text-sm text-slate-800 mt-2 bg-slate-50/80 p-4 rounded-2xl border border-slate-200 leading-relaxed font-medium">
                      "{currentQuestion.questionText}"
                    </p>
                  </div>

                  {/* Coaching Tip */}
                  <div className="p-3 bg-indigo-50/80 border border-indigo-100 rounded-xl text-[11px] text-indigo-900 flex items-start space-x-2">
                    <span className="text-sm shrink-0">💡</span>
                    <p>
                      <strong>Interviewer Focus:</strong> {currentQuestion.tips}
                    </p>
                  </div>

                  {/* Expected Terminology Hints */}
                  <div className="flex flex-wrap items-center gap-1.5 text-xs">
                    <span className="text-[11px] font-bold text-slate-500">Key Concepts to Touch:</span>
                    {currentQuestion.expectedKeywords.map((kw, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[10px] font-semibold border border-slate-200/60"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>

                  {/* Student Response Area */}
                  <div className="space-y-2 pt-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-2">
                        <span>Your Response:</span>
                        {isRecording && (
                          <span className="text-rose-600 text-[11px] font-extrabold flex items-center space-x-1 animate-pulse">
                            <span>● REC</span>
                            <span>{formatSeconds(recordingSeconds)}</span>
                          </span>
                        )}
                      </label>
                      <span className="text-[10px] text-slate-400">
                        {answerText.trim().split(/\s+/).filter(Boolean).length} words
                      </span>
                    </div>

                    <textarea
                      rows={6}
                      value={answerText}
                      onChange={(e) => setAnswerText(e.target.value)}
                      placeholder="Speak your response via microphone, or type your answer here... (Tip: For behavioral, use STAR: Situation -> Task -> Action -> Result. For technical, explain your approach, trade-offs, and complexity)."
                      className={`w-full p-4 rounded-2xl border text-xs sm:text-sm text-slate-800 placeholder:text-slate-400 focus:ring-2 focus:ring-indigo-500 transition leading-relaxed ${
                        isRecording ? 'border-rose-400 bg-rose-50/20' : 'border-slate-200 bg-white'
                      }`}
                    />
                  </div>

                  {/* Microphone & Evaluation Bar */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-100">
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      {isRecording ? (
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={stopRecording}
                          leftIcon={<span>⏹️</span>}
                          className="w-full sm:w-auto animate-pulse"
                        >
                          Stop Speaking ({formatSeconds(recordingSeconds)})
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={startRecording}
                          disabled={!sttSupported}
                          leftIcon={<span>🎙️</span>}
                          className="w-full sm:w-auto text-indigo-700 border-indigo-200 hover:bg-indigo-50"
                        >
                          {sttSupported ? 'Speak Answer (Microphone)' : 'Mic Unavailable (Type Answer)'}
                        </Button>
                      )}

                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs text-slate-500"
                        onClick={() => {
                          // Adaptive exemplar based on current question category
                          if (currentQuestion.category.toLowerCase().includes('behavioral') || currentQuestion.trackId === 'role-hr') {
                            setAnswerText(
                              'Situation: In our pre-final year project, a teammate and I differed on whether to use PostgreSQL or MongoDB for streaming sensor logs. Task: I needed to establish consensus without delaying our sprint milestone. Action: I implemented a benchmark script simulating 10,000 writes/second and compared latency and storage footprints. Result: We reviewed the empirical data together and aligned on PostgreSQL with Timescale, improving query speed by 40%.'
                            );
                          } else if (currentQuestion.trackId === 'role-genai') {
                            setAnswerText(
                              'In my enterprise RAG architecture, document ingestion begins with recursive semantic chunking with a 15% sliding window overlap. We generate dense embeddings using a bi-encoder and persist them in an HNSW-indexed vector database. Upon query arrival, we retrieve the top 20 candidate vectors, apply a cross-encoder re-ranking pass to isolate the top 4 passages, and synthesize the final answer using strict grounded context guardrails.'
                            );
                          } else if (currentQuestion.trackId === 'role-aiml') {
                            setAnswerText(
                              'To mitigate overfitting in our deep neural network, I combined L2 weight decay regularization with a 0.3 dropout rate across fully connected layers. Furthermore, I implemented early stopping based on validation loss patience and used data augmentation to expand our training distribution, reducing generalization error by 18%.'
                            );
                          } else {
                            setAnswerText(
                              'To implement an LRU Cache with O(1) get and put, I combined a Doubly Linked List with a Hash Map. The Hash Map stores keys mapped directly to linked list node pointers for O(1) retrieval. The Doubly Linked List maintains chronological access order: when an item is accessed or inserted, it shifts to the head. When capacity is reached, we evict the tail node in O(1) time.'
                            );
                          }
                        }}
                      >
                        Insert Sample
                      </Button>
                    </div>

                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <Button
                        variant="primary"
                        size="sm"
                        isLoading={isEvaluating}
                        disabled={!answerText.trim() || isEvaluating}
                        onClick={handleEvaluateAnswer}
                        leftIcon={<span>✨</span>}
                      >
                        Evaluate Answer
                      </Button>

                      {currentEvaluation && activeQuestionIdx + 1 < activeQuestions.length && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleNextQuestion}
                          rightIcon={<span>→</span>}
                        >
                          Next Question
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              </div>

              {/* AI Scorecard & Feedback Panel */}
              <div className="space-y-4">
                <Card variant="default" className="p-6 rounded-3xl border-slate-200 space-y-4 shadow-sm h-full flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        Agent Evaluation & Rubric
                      </h4>
                      {currentEvaluation && (
                        <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                          Question {activeQuestionIdx + 1} of 5 Evaluated
                        </span>
                      )}
                    </div>

                    {currentEvaluation ? (
                      <div className="space-y-4 animate-fade-in">
                        {/* Overall Question Score */}
                        <div className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-200 rounded-2xl text-center">
                          <div className="text-3xl font-black text-emerald-700">
                            {currentEvaluation.score}/100
                          </div>
                          <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 mt-0.5">
                            Question Performance Score
                          </div>
                          {currentEvaluation.words_per_minute && (
                            <div className="text-[11px] text-teal-700 font-semibold mt-1">
                              🗣️ Pacing: {currentEvaluation.words_per_minute} WPM (Ideal: 120-160)
                            </div>
                          )}
                        </div>

                        {/* Pillar Scores */}
                        <div className="space-y-2.5 text-xs">
                          <div>
                            <div className="flex justify-between font-bold text-slate-700 mb-1 text-[11px]">
                              <span>Technical Depth (40%)</span>
                              <span>{currentEvaluation.technical_depth_score}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-indigo-600 rounded-full transition-all duration-500"
                                style={{ width: `${currentEvaluation.technical_depth_score}%` }}
                              />
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between font-bold text-slate-700 mb-1 text-[11px]">
                              <span>Communication & Clarity (35%)</span>
                              <span>{currentEvaluation.communication_score}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                                style={{ width: `${currentEvaluation.communication_score}%` }}
                              />
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between font-bold text-slate-700 mb-1 text-[11px]">
                              <span>Structural Flow & STAR (25%)</span>
                              <span>{currentEvaluation.structure_score}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-purple-500 rounded-full transition-all duration-500"
                                style={{ width: `${currentEvaluation.structure_score}%` }}
                              />
                            </div>
                          </div>
                        </div>

                        {/* Filler Words Alert */}
                        {currentEvaluation.filler_words.length > 0 && (
                          <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-800 space-y-1">
                            <span className="font-bold flex items-center space-x-1">
                              <span>⚠️ Filler Words Detected:</span>
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {currentEvaluation.filler_words.map((fw, i) => (
                                <span key={i} className="px-1.5 py-0.5 rounded bg-amber-100 font-bold text-amber-900">
                                  "{fw}"
                                </span>
                              ))}
                            </div>
                            <p className="text-[10px] text-amber-700">
                              Try pausing briefly instead of using verbal filler sounds.
                            </p>
                          </div>
                        )}

                        {/* Strengths */}
                        <div className="space-y-1.5 text-xs">
                          <span className="font-bold text-slate-800 block text-[11px]">
                            Demonstrated Strengths:
                          </span>
                          {currentEvaluation.strengths.map((s, i) => (
                            <div key={i} className="flex items-start space-x-1.5 text-slate-600 text-[11px]">
                              <span className="text-emerald-500 font-bold">✓</span>
                              <span>{s}</span>
                            </div>
                          ))}
                        </div>

                        {/* Growth Focus */}
                        <div className="space-y-1.5 text-xs">
                          <span className="font-bold text-slate-800 block text-[11px]">
                            Recommended Improvements:
                          </span>
                          {currentEvaluation.improvements.map((im, i) => (
                            <div key={i} className="flex items-start space-x-1.5 text-slate-600 text-[11px]">
                              <span className="text-amber-500 font-bold">→</span>
                              <span>{im}</span>
                            </div>
                          ))}
                        </div>

                        {/* Grounded RAG Model Answer & Strategy */}
                        {currentEvaluation.ideal_response && (
                          <div className="p-3.5 bg-indigo-50/70 border border-indigo-200/80 rounded-xl text-[11px] text-indigo-950 space-y-1.5 shadow-sm">
                            <div className="flex items-center justify-between">
                              <span className="font-bold flex items-center gap-1.5 text-indigo-900">
                                <span>📘</span>
                                <span>Verified Handbook Model Answer & Strategy</span>
                              </span>
                              <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-indigo-200/70 text-indigo-800 tracking-wide uppercase">
                                RAG Grounded
                              </span>
                            </div>
                            <p className="text-[11px] leading-relaxed text-indigo-900 whitespace-pre-line">
                              {currentEvaluation.ideal_response}
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="p-8 text-center bg-slate-50/70 rounded-2xl border border-dashed border-slate-200 space-y-3">
                        <span className="text-3xl">🎙️</span>
                        <h5 className="text-xs font-bold text-slate-800">
                          Awaiting Candidate Spoken Response
                        </h5>
                        <p className="text-[11px] text-slate-500 leading-relaxed">
                          Click <strong>Speak Answer</strong> to talk into your microphone, or type your answer and click <strong>Evaluate Answer</strong> to trigger the multi-pillar agent evaluation.
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="pt-4 border-t border-slate-100 text-center">
                    <span className="text-[10px] text-slate-400 block font-medium">
                      Evaluated by CampusFlow Agentic Placement Rubric
                    </span>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </>
      ) : (
        /* ── History & Past Reports View ───────────────────────────────────── */
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-black text-slate-900">
                Mock Interview Performance History
              </h3>
              <p className="text-xs text-slate-500">
                Review your progression across past mock interviews and track score improvements over time.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchHistory}
              isLoading={loadingHistory}
              leftIcon={<span>🔄</span>}
            >
              Refresh
            </Button>
          </div>

          {loadingHistory ? (
            <div className="p-12 text-center text-slate-400 text-sm">
              Loading past interview sessions...
            </div>
          ) : pastSessions.length === 0 ? (
            <Card variant="subtle" className="p-12 text-center space-y-3">
              <span className="text-4xl">📋</span>
              <h4 className="text-sm font-bold text-slate-800">No Mock Interviews Completed Yet</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Select an interview track above and complete your first simulated interview with our AI Voice Agent to generate a detailed report.
              </p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setActiveTab('simulator')}
              >
                Start an Interview Now 🎙️
              </Button>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {pastSessions.map((session) => (
                <Card
                  key={session.id}
                  variant="default"
                  className="p-5 rounded-2xl border-slate-200 flex flex-col justify-between space-y-4 hover:shadow-md transition"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Badge variant={getRatingBadgeVariant(session.performance_rating) as any} size="sm">
                        {session.performance_rating?.replace('_', ' ') || session.status}
                      </Badge>
                      <span className="text-[11px] text-slate-400 font-medium">
                        {new Date(session.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-sm font-extrabold text-slate-900 leading-snug">
                        {session.track_title}
                      </h4>
                      {session.target_role && (
                        <p className="text-xs text-slate-500 mt-0.5 font-medium">
                          Target: {session.target_role}
                        </p>
                      )}
                    </div>

                    {session.overall_score !== null && session.overall_score !== undefined && (
                      <div className="p-3 bg-slate-50 rounded-xl flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-700">Overall Score</span>
                        <span className="text-lg font-black text-indigo-700">
                          {session.overall_score}/100
                        </span>
                      </div>
                    )}

                    {session.evaluations && session.evaluations.length > 0 && (
                      <div className="text-[11px] text-slate-500">
                        {session.evaluations.length} Questions Answered
                      </div>
                    )}
                  </div>

                  <div className="pt-3 border-t border-slate-100">
                    <Button
                      variant="primary"
                      size="sm"
                      className="w-full text-xs"
                      onClick={() => handleViewHistoricalReport(session.id)}
                    >
                      View Comprehensive Report 📊
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Comprehensive Performance Report Modal ──────────────────────────── */}
      {performanceReport && (
        <Modal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          maxWidth="4xl"
          title={
            <div className="flex items-center space-x-2">
              <span className="text-xl">🏆</span>
              <span className="font-black text-slate-900 text-lg">
                Mock Interview Performance Report
              </span>
            </div>
          }
          description={
            <span className="text-xs text-slate-500">
              Track: {performanceReport.track_title} • Role: {performanceReport.target_role || 'General Candidate'} • Generated on {new Date(performanceReport.completed_at || performanceReport.created_at).toLocaleString()}
            </span>
          }
        >
          <div className="space-y-6 pt-2">
            {/* 1. Score Overview Banner */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-gradient-to-br from-slate-900 to-indigo-950 text-white p-6 rounded-2xl border border-indigo-900 shadow-lg">
              <div className="flex flex-col items-center justify-center text-center p-4 bg-white/5 rounded-xl border border-white/10">
                <div className="text-4xl font-black text-emerald-400">
                  {performanceReport.overall_score ?? '--'}/100
                </div>
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-300 mt-1">
                  Overall Readiness Score
                </div>
                <div className="mt-2">
                  <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    {performanceReport.performance_rating?.replace('_', ' ') || 'EVALUATED'}
                  </span>
                </div>
              </div>

              <div className="md:col-span-2 space-y-2 flex flex-col justify-center">
                <h4 className="text-sm font-bold uppercase tracking-wider text-indigo-300">
                  AI Placement Readiness Assessment
                </h4>
                <p className="text-xs text-slate-200 leading-relaxed">
                  {performanceReport.summary_feedback ||
                    'Candidate successfully completed the mock interview questions. Detailed breakdown across technical depth and communication is presented below.'}
                </p>
                <div className="pt-2 flex flex-wrap gap-2 text-[10px] font-semibold text-slate-300">
                  <span>Questions Evaluated: {performanceReport.evaluations.length}</span>
                  <span>•</span>
                  <span>Confidence Metric: {performanceReport.confidence_score ?? 80}%</span>
                </div>
              </div>
            </div>

            {/* 2. Core Pillars Breakdown */}
            <div className="space-y-3">
              <h4 className="text-xs font-black uppercase tracking-wider text-slate-700">
                Core Evaluation Pillars
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex justify-between items-center text-xs font-bold text-slate-700">
                    <span>Technical Depth</span>
                    <span className="text-indigo-700">{performanceReport.technical_score ?? 0}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-600 rounded-full"
                      style={{ width: `${performanceReport.technical_score ?? 0}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-500">
                    Domain concepts, algorithmic complexity, and system trade-offs.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex justify-between items-center text-xs font-bold text-slate-700">
                    <span>Communication & Fluency</span>
                    <span className="text-emerald-700">{performanceReport.communication_score ?? 0}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${performanceReport.communication_score ?? 0}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-500">
                    Verbal clarity, minimal filler hesitation, and conversational pacing.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex justify-between items-center text-xs font-bold text-slate-700">
                    <span>Structural Flow & STAR</span>
                    <span className="text-purple-700">{performanceReport.structure_score ?? 0}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-600 rounded-full"
                      style={{ width: `${performanceReport.structure_score ?? 0}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-500">
                    Logical decomposition, Situation-Task-Action-Result format.
                  </p>
                </div>
              </div>
            </div>

            {/* 3. Topic Mastery Breakdown */}
            {performanceReport.topic_breakdown && Object.keys(performanceReport.topic_breakdown).length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-black uppercase tracking-wider text-slate-700">
                  Topic Mastery Breakdown
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {Object.entries(performanceReport.topic_breakdown).map(([topic, score]) => (
                    <div key={topic} className="p-3 bg-white border border-slate-200 rounded-xl space-y-1.5 shadow-2xs">
                      <div className="flex justify-between text-xs font-bold text-slate-800">
                        <span>{topic}</span>
                        <span className="text-indigo-600">{score}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full"
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. Strengths & Improvements */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-2xl space-y-2">
                <h4 className="text-xs font-extrabold text-emerald-900 uppercase tracking-wider flex items-center space-x-1.5">
                  <span>✓</span>
                  <span>Key Demonstrated Strengths</span>
                </h4>
                <ul className="space-y-1.5 text-xs text-emerald-800">
                  {performanceReport.strengths.map((s, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="font-bold">•</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-2xl space-y-2">
                <h4 className="text-xs font-extrabold text-amber-900 uppercase tracking-wider flex items-center space-x-1.5">
                  <span>→</span>
                  <span>High-Impact Growth Areas</span>
                </h4>
                <ul className="space-y-1.5 text-xs text-amber-800">
                  {performanceReport.improvements.map((im, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="font-bold">•</span>
                      <span>{im}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* 5. Actionable Roadmap */}
            {performanceReport.action_plan && performanceReport.action_plan.length > 0 && (
              <div className="p-5 bg-indigo-50/80 border border-indigo-200 rounded-2xl space-y-3">
                <h4 className="text-xs font-black uppercase tracking-wider text-indigo-900 flex items-center space-x-2">
                  <span>🚀</span>
                  <span>Personalized Growth Roadmap</span>
                </h4>
                <div className="space-y-2">
                  {performanceReport.action_plan.map((step, idx) => (
                    <div key={idx} className="flex items-start space-x-3 text-xs text-indigo-900">
                      <span className="w-5 h-5 rounded-full bg-indigo-600 text-white font-black text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <p className="leading-relaxed font-medium">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 6. Question-by-Question Deep Dive */}
            <div className="space-y-3">
              <h4 className="text-xs font-black uppercase tracking-wider text-slate-700">
                Question-by-Question Deep Dive
              </h4>
              <div className="space-y-3">
                {performanceReport.evaluations.map((ev, i) => (
                  <details
                    key={ev.id || i}
                    className="p-4 rounded-xl border border-slate-200 bg-white group cursor-pointer"
                  >
                    <summary className="flex items-center justify-between font-bold text-xs text-slate-900 list-none">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-black">
                          Q{ev.question_index + 1}
                        </span>
                        <span className="line-clamp-1">{ev.question_text}</span>
                      </div>
                      <div className="flex items-center space-x-3 shrink-0">
                        <span className="font-black text-indigo-600">{ev.score}/100</span>
                        <span className="text-slate-400 group-open:rotate-180 transition-transform">▼</span>
                      </div>
                    </summary>

                    <div className="pt-3 mt-3 border-t border-slate-100 space-y-3 text-xs">
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
                          Candidate Spoken Response:
                        </span>
                        <p className="p-3 bg-slate-50 rounded-xl text-slate-800 leading-relaxed italic border border-slate-100">
                          "{ev.student_answer}"
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-2 text-[11px]">
                        <span className="px-2 py-1 rounded bg-slate-100 text-slate-700 font-semibold">
                          Technical: {ev.technical_depth_score}%
                        </span>
                        <span className="px-2 py-1 rounded bg-slate-100 text-slate-700 font-semibold">
                          Communication: {ev.communication_score}%
                        </span>
                        <span className="px-2 py-1 rounded bg-slate-100 text-slate-700 font-semibold">
                          Structure: {ev.structure_score}%
                        </span>
                        {ev.words_per_minute && (
                          <span className="px-2 py-1 rounded bg-teal-50 text-teal-800 font-semibold">
                            Pacing: {ev.words_per_minute} WPM
                          </span>
                        )}
                        {ev.filler_words.length > 0 && (
                          <span className="px-2 py-1 rounded bg-amber-50 text-amber-800 font-semibold">
                            Fillers: {ev.filler_words.join(', ')}
                          </span>
                        )}
                      </div>

                      <div className="p-3 bg-slate-50 rounded-xl space-y-1">
                        <span className="text-[10px] font-bold text-slate-500 uppercase block">
                          AI Critique:
                        </span>
                        <p className="text-slate-700">{ev.feedback_critique}</p>
                      </div>

                      {ev.ideal_response && (
                        <div className="p-3 bg-indigo-50/70 border border-indigo-200/80 rounded-xl space-y-1.5 text-indigo-950">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold text-indigo-800 uppercase flex items-center gap-1">
                              <span>📘</span> Verified Handbook Model Answer (RAG):
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[8px] font-semibold bg-indigo-200 text-indigo-800">
                              Ground Truth
                            </span>
                          </div>
                          <p className="whitespace-pre-line text-xs leading-relaxed text-indigo-900">{ev.ideal_response}</p>
                        </div>
                      )}
                    </div>
                  </details>
                ))}
              </div>
            </div>

            {/* Modal Footer Controls */}
            <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.print()}
                leftIcon={<span>🖨️</span>}
              >
                Print / Save PDF
              </Button>
              <div className="flex items-center gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsReportModalOpen(false)}
                >
                  Done & Close Report
                </Button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
