"""
CampusFlow — Seed Comprehensive Preparation Hub Roadmaps, Roles, Topics, and Materials.

Includes:
- System Design & Distributed Systems (HLD, LLD, Caching, Sharding, Message Queues, Case Studies)
- Software Engineer (SDE Core)
- AI & Machine Learning Engineer
- Generative AI & LLM Engineer
- DevOps & Cloud Platform Engineer
- Data Platform & Analytics Engineer
- Fullstack Web Engineer
- QA & Automation Test Engineer
"""
import asyncio
from uuid import uuid4
from sqlalchemy import select, delete, update
from app.db.session import get_session_factory
from app.models.preparation import (
    PreparationCategory,
    PreparationRole,
    PreparationTopic,
    PreparationRoleTopic,
    PreparationMaterial,
)


async def seed():
    async with get_session_factory()() as session:
        print("[1/5] Cleaning up legacy and duplicate roles...")
        # Clean up legacy duplicate role codes
        legacy_roles = ["AIML_ENGINEER", "CLOUD_DEVOPS"]
        for leg_code in legacy_roles:
            leg_r = (await session.execute(select(PreparationRole).where(PreparationRole.code == leg_code))).scalar_one_or_none()
            if leg_r:
                target_code = "AI_ML_ENGINEER" if leg_code == "AIML_ENGINEER" else "DEVOPS_ENGINEER"
                target_r = (await session.execute(select(PreparationRole).where(PreparationRole.code == target_code))).scalar_one_or_none()
                if target_r:
                    await session.execute(update(PreparationMaterial).where(PreparationMaterial.role_id == leg_r.id).values(role_id=target_r.id))
                await session.execute(delete(PreparationRoleTopic).where(PreparationRoleTopic.role_id == leg_r.id))
                await session.delete(leg_r)

        await session.flush()

        print("[2/5] Upserting canonical preparation roles...")
        roles_data = [
            (
                "SYSTEM_DESIGN",
                "System Design & Distributed Systems",
                "Architecting scalable cloud services, distributed caching, CAP theorem, microservices decomposition, and high-throughput streaming.",
                "server-stack",
            ),
            (
                "SOFTWARE_DEVELOPER",
                "Software Engineer (SDE Core)",
                "Data structures, algorithms, object-oriented design, databases, concurrency, and backend software engineering fundamentals.",
                "code",
            ),
            (
                "AI_ML_ENGINEER",
                "AI & Machine Learning Engineer",
                "Statistical learning, deep neural networks with PyTorch/TensorFlow, model training, feature engineering, and MLOps.",
                "cpu-chip",
            ),
            (
                "GENAI_ENGINEER",
                "Generative AI & LLM Engineer",
                "RAG architectures, vector embeddings, chunking strategies, prompt engineering, fine-tuning with LoRA, and autonomous agents.",
                "sparkles",
            ),
            (
                "DEVOPS_ENGINEER",
                "DevOps & Cloud Platform Engineer",
                "CI/CD automation, Docker containerization, Kubernetes orchestration, Infrastructure as Code (Terraform), and cloud observability.",
                "cloud",
            ),
            (
                "DATA_ENGINEER",
                "Data Platform & Analytics Engineer",
                "Resilient ETL/ELT pipelines, distributed processing with Apache Spark, real-time streaming with Kafka, and analytical data lakehouses.",
                "database",
            ),
            (
                "FULLSTACK_DEVELOPER",
                "Fullstack Web Engineer",
                "Modern frontend React architecture, state management, asynchronous patterns, REST & GraphQL APIs, and web security standards.",
                "globe",
            ),
            (
                "QA_TEST_ENGINEER",
                "QA & Automation Test Engineer",
                "Automated testing frameworks (Playwright, Selenium, PyTest), API testing, load testing, and continuous quality assurance.",
                "check-circle",
            ),
        ]

        seeded_roles: dict[str, PreparationRole] = {}
        for code, name, desc, icon in roles_data:
            stmt = select(PreparationRole).where(PreparationRole.code == code)
            r = (await session.execute(stmt)).scalar_one_or_none()
            if not r:
                r = PreparationRole(
                    id=uuid4(),
                    code=code,
                    name=name,
                    description=desc,
                    icon=icon,
                    is_active=True,
                )
                session.add(r)
                await session.flush()
            else:
                r.name = name
                r.description = desc
                r.icon = icon
                r.is_active = True
                await session.flush()
            seeded_roles[code] = r

        print("[3/5] Upserting preparation categories and topics...")
        # Ensure categories exist
        cats_data = [
            ("TECHNICAL", "Technical Core & System Architecture", "Data structures, algorithms, system design, databases, and core software engineering.", "code", 1),
            ("APTITUDE", "Quantitative & Logical Aptitude", "Mathematical ability, numerical shortcuts, and analytical reasoning for placement screening.", "calculator", 2),
            ("VERBAL", "Verbal Ability & English", "Reading comprehension, sentence correction, and vocabulary.", "book-open", 3),
            ("INTERVIEW", "Interview Preparation & Behavioral", "Technical case studies, system design rounds, and STAR method behavioral defense.", "user-group", 4),
        ]
        seeded_cats: dict[str, PreparationCategory] = {}
        for code, name, desc, icon, seq in cats_data:
            stmt = select(PreparationCategory).where(PreparationCategory.code == code)
            c = (await session.execute(stmt)).scalar_one_or_none()
            if not c:
                c = PreparationCategory(
                    id=uuid4(),
                    code=code,
                    name=name,
                    description=desc,
                    icon=icon,
                    sequence_order=seq,
                )
                session.add(c)
                await session.flush()
            else:
                c.name = name
                c.description = desc
                await session.flush()
            seeded_cats[code] = c

        # Topics definition
        topics_data = [
            # System Design Topics
            ("TECHNICAL", "High-Level System Design (HLD) & Microservices", "high-level-system-design", "Architecting resilient distributed services, microservices decomposition, and load balancing."),
            ("TECHNICAL", "Low-Level Design & Design Patterns (LLD)", "low-level-system-design", "Object-oriented SOLID principles, Factory, Strategy, Observer, and Singleton design patterns."),
            ("TECHNICAL", "Distributed Caching & Database Sharding", "distributed-caching-sharding", "Redis caching hierarchies, cache invalidation strategies, database sharding, and consistent hashing."),
            ("TECHNICAL", "Message Queues & Event Streaming", "message-queues-streaming", "Asynchronous messaging with Apache Kafka and RabbitMQ, pub-sub architectures, and dead letter queues."),
            ("TECHNICAL", "CAP Theorem, Consistency & Scalability", "cap-theorem-consistency", "Partition tolerance, eventual consistency, ACID vs BASE, and high availability design patterns."),
            ("INTERVIEW", "System Design Interview Case Studies", "system-design-case-studies", "Architectural deep dives: designing URL shorteners, rate limiters, notification systems, and ride-sharing dispatch."),
            ("TECHNICAL", "Concurrency, Threads & Deadlocks", "concurrency-multithreading", "Thread safety, race conditions, mutual exclusion locks, semaphores, and non-blocking I/O."),
            
            # Domain Engineering Topics
            ("TECHNICAL", "RAG Architectures & Vector Databases", "rag-architectures", "Dense retrieval pipelines, vector embeddings, semantic search with FAISS/ChromaDB/Pinecone, and reranking."),
            ("TECHNICAL", "Docker & Kubernetes Orchestration", "docker-kubernetes", "Containerization fundamentals, multi-stage builds, pod lifecycles, deployments, and cluster networking."),
            ("TECHNICAL", "Apache Spark & Distributed ETL", "spark-data-pipelines", "Distributed computing with Apache Spark, RDD transformations, DataFrame optimizations, and data lakehouses."),
            ("TECHNICAL", "Web Architecture, React & REST APIs", "web-development", "Modern frontend React rendering, state management, REST and GraphQL APIs, and security standards."),
            
            # Core Foundational Topics
            ("TECHNICAL", "Data Structures & Algorithms", "dsa", "Arrays, Linked Lists, Trees, Graphs, Dynamic Programming, and algorithmic trade-offs."),
            ("TECHNICAL", "SQL & Database Management", "sql-dbms", "RDBMS principles, indexing, normalization, execution plans, and complex analytical queries."),
            ("TECHNICAL", "Python Core & Advanced", "python-programming", "Python data models, generators, OOP, memory management, and asynchronous patterns."),
            ("APTITUDE", "Quantitative Mathematics", "quant-math", "Arithmetic, Algebra, Percentages, Time & Work, and Probability problem sets."),
            ("APTITUDE", "Logical & Analytical Reasoning", "logical-reasoning", "Puzzles, Seating Arrangements, Coding-Decoding, and Syllogisms."),
            ("INTERVIEW", "Behavioral & STAR Method Interview Rounds", "behavioral-hr", "STAR framework, situational judgment, resolving technical conflict, and leadership ethics."),
        ]

        seeded_topics: dict[str, PreparationTopic] = {}
        for cat_code, name, slug, desc in topics_data:
            stmt = select(PreparationTopic).where(PreparationTopic.slug == slug)
            t = (await session.execute(stmt)).scalar_one_or_none()
            if not t:
                t = PreparationTopic(
                    id=uuid4(),
                    category_id=seeded_cats[cat_code].id,
                    name=name,
                    slug=slug,
                    description=desc,
                )
                session.add(t)
                await session.flush()
            else:
                t.name = name
                t.description = desc
                t.category_id = seeded_cats[cat_code].id
                await session.flush()
            seeded_topics[slug] = t

        print("[4/5] Upserting Role-Topic curriculum mappings...")
        role_topic_mappings = [
            # 1. System Design & Distributed Systems
            ("SYSTEM_DESIGN", "high-level-system-design", "CORE"),
            ("SYSTEM_DESIGN", "low-level-system-design", "CORE"),
            ("SYSTEM_DESIGN", "distributed-caching-sharding", "CORE"),
            ("SYSTEM_DESIGN", "cap-theorem-consistency", "CORE"),
            ("SYSTEM_DESIGN", "message-queues-streaming", "CORE"),
            ("SYSTEM_DESIGN", "system-design-case-studies", "CORE"),
            ("SYSTEM_DESIGN", "sql-dbms", "CORE"),
            ("SYSTEM_DESIGN", "concurrency-multithreading", "CORE"),
            ("SYSTEM_DESIGN", "behavioral-hr", "ELECTIVE"),

            # 2. Software Engineer (SDE Core)
            ("SOFTWARE_DEVELOPER", "dsa", "CORE"),
            ("SOFTWARE_DEVELOPER", "python-programming", "CORE"),
            ("SOFTWARE_DEVELOPER", "sql-dbms", "CORE"),
            ("SOFTWARE_DEVELOPER", "concurrency-multithreading", "CORE"),
            ("SOFTWARE_DEVELOPER", "low-level-system-design", "CORE"),
            ("SOFTWARE_DEVELOPER", "high-level-system-design", "ELECTIVE"),
            ("SOFTWARE_DEVELOPER", "distributed-caching-sharding", "ELECTIVE"),
            ("SOFTWARE_DEVELOPER", "quant-math", "CORE"),
            ("SOFTWARE_DEVELOPER", "behavioral-hr", "ELECTIVE"),

            # 3. Generative AI & LLM Engineer
            ("GENAI_ENGINEER", "python-programming", "CORE"),
            ("GENAI_ENGINEER", "rag-architectures", "CORE"),
            ("GENAI_ENGINEER", "high-level-system-design", "CORE"),
            ("GENAI_ENGINEER", "dsa", "CORE"),
            ("GENAI_ENGINEER", "message-queues-streaming", "ELECTIVE"),
            ("GENAI_ENGINEER", "distributed-caching-sharding", "ELECTIVE"),
            ("GENAI_ENGINEER", "behavioral-hr", "ELECTIVE"),

            # 4. DevOps & Cloud Platform Engineer
            ("DEVOPS_ENGINEER", "docker-kubernetes", "CORE"),
            ("DEVOPS_ENGINEER", "high-level-system-design", "CORE"),
            ("DEVOPS_ENGINEER", "python-programming", "CORE"),
            ("DEVOPS_ENGINEER", "concurrency-multithreading", "CORE"),
            ("DEVOPS_ENGINEER", "cap-theorem-consistency", "CORE"),
            ("DEVOPS_ENGINEER", "distributed-caching-sharding", "ELECTIVE"),
            ("DEVOPS_ENGINEER", "message-queues-streaming", "ELECTIVE"),
            ("DEVOPS_ENGINEER", "behavioral-hr", "ELECTIVE"),

            # 5. Data Platform & Analytics Engineer
            ("DATA_ENGINEER", "sql-dbms", "CORE"),
            ("DATA_ENGINEER", "spark-data-pipelines", "CORE"),
            ("DATA_ENGINEER", "python-programming", "CORE"),
            ("DATA_ENGINEER", "message-queues-streaming", "CORE"),
            ("DATA_ENGINEER", "distributed-caching-sharding", "CORE"),
            ("DATA_ENGINEER", "system-design-case-studies", "ELECTIVE"),
            ("DATA_ENGINEER", "quant-math", "CORE"),
            ("DATA_ENGINEER", "behavioral-hr", "ELECTIVE"),

            # 6. Fullstack Web Engineer
            ("FULLSTACK_DEVELOPER", "web-development", "CORE"),
            ("FULLSTACK_DEVELOPER", "dsa", "CORE"),
            ("FULLSTACK_DEVELOPER", "sql-dbms", "CORE"),
            ("FULLSTACK_DEVELOPER", "low-level-system-design", "CORE"),
            ("FULLSTACK_DEVELOPER", "python-programming", "CORE"),
            ("FULLSTACK_DEVELOPER", "distributed-caching-sharding", "ELECTIVE"),
            ("FULLSTACK_DEVELOPER", "behavioral-hr", "ELECTIVE"),

            # 7. AI & Machine Learning Engineer
            ("AI_ML_ENGINEER", "python-programming", "CORE"),
            ("AI_ML_ENGINEER", "dsa", "CORE"),
            ("AI_ML_ENGINEER", "quant-math", "CORE"),
            ("AI_ML_ENGINEER", "sql-dbms", "CORE"),
            ("AI_ML_ENGINEER", "spark-data-pipelines", "ELECTIVE"),
            ("AI_ML_ENGINEER", "rag-architectures", "ELECTIVE"),
            ("AI_ML_ENGINEER", "behavioral-hr", "ELECTIVE"),

            # 8. QA & Automation Test Engineer
            ("QA_TEST_ENGINEER", "python-programming", "CORE"),
            ("QA_TEST_ENGINEER", "dsa", "CORE"),
            ("QA_TEST_ENGINEER", "web-development", "CORE"),
            ("QA_TEST_ENGINEER", "docker-kubernetes", "ELECTIVE"),
            ("QA_TEST_ENGINEER", "sql-dbms", "CORE"),
            ("QA_TEST_ENGINEER", "behavioral-hr", "ELECTIVE"),
        ]

        for role_code, topic_slug, imp in role_topic_mappings:
            r = seeded_roles[role_code]
            t = seeded_topics[topic_slug]
            res = await session.execute(
                select(PreparationRoleTopic).where(
                    PreparationRoleTopic.role_id == r.id,
                    PreparationRoleTopic.topic_id == t.id,
                )
            )
            existing = res.scalar_one_or_none()
            if not existing:
                session.add(PreparationRoleTopic(id=uuid4(), role_id=r.id, topic_id=t.id, importance=imp))
            else:
                existing.importance = imp

        await session.flush()

        print("[5/5] Seeding verified preparation materials for System Design and industry roles...")
        materials_data = [
            # System Design Materials
            (
                "high-level-system-design",
                "SYSTEM_DESIGN",
                "The System Design Primer by Donne Martin (Complete HLD Guide)",
                "https://github.com/donnemartin/system-design-primer",
                "DOCUMENTATION",
                "BEGINNER",
                "GitHub / Donne Martin",
                "Comprehensive open-source guide covering scalability, horizontal scaling, load balancing, reverse proxies, and system architecture fundamentals."
            ),
            (
                "high-level-system-design",
                "SYSTEM_DESIGN",
                "ByteByteGo: High-Level System Architecture Building Blocks",
                "https://bytebytego.com/courses/system-design-interview/scale-from-zero-to-millions-of-users",
                "ARTICLE",
                "INTERMEDIATE",
                "ByteByteGo",
                "Step-by-step walkthrough scaling an application from 1 user to 10+ million users with CDN, multi-region routing, and database decoupling."
            ),
            (
                "low-level-system-design",
                "SYSTEM_DESIGN",
                "Refactoring Guru: SOLID Principles & Design Patterns Mastery",
                "https://refactoring.guru/design-patterns",
                "ARTICLE",
                "INTERMEDIATE",
                "Refactoring Guru",
                "Interactive catalog of Creational, Structural, and Behavioral design patterns (Factory, Observer, Strategy, Singleton) with UML diagrams and code."
            ),
            (
                "distributed-caching-sharding",
                "SYSTEM_DESIGN",
                "Redis In-Depth: Caching Hierarchies & Eviction Strategies",
                "https://redis.io/docs/latest/develop/use/patterns/",
                "DOCUMENTATION",
                "INTERMEDIATE",
                "Redis Official",
                "Master Cache-Aside, Write-Through, Write-Behind, and eviction algorithms (LRU, LFU) with Redis caching architectures."
            ),
            (
                "distributed-caching-sharding",
                "SYSTEM_DESIGN",
                "Database Sharding & Consistent Hashing Explained",
                "https://highscalability.com/consistent-hashing-algorithm/",
                "ARTICLE",
                "ADVANCED",
                "High Scalability",
                "Deep dive into horizontal partitioning, consistent hashing ring, virtual nodes, and mitigating hotspot nodes under uneven traffic."
            ),
            (
                "message-queues-streaming",
                "SYSTEM_DESIGN",
                "Apache Kafka Fundamentals & Event-Driven Architecture",
                "https://kafka.apache.org/intro",
                "DOCUMENTATION",
                "INTERMEDIATE",
                "Apache Kafka",
                "Core concepts of topics, partitions, consumer groups, offset commits, log compaction, and event-driven microservices."
            ),
            (
                "cap-theorem-consistency",
                "SYSTEM_DESIGN",
                "CAP Theorem & Eventual Consistency in Distributed Systems",
                "https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/",
                "ARTICLE",
                "ADVANCED",
                "Eric Brewer / InfoQ",
                "Understand the true trade-offs between Consistency, Availability, and Partition Tolerance, plus PACELC theorem and eventual consistency models."
            ),
            (
                "system-design-case-studies",
                "SYSTEM_DESIGN",
                "Designing a Scalable URL Shortener (TinyURL System Design)",
                "https://github.com/donnemartin/system-design-primer/blob/master/solutions/system_design/pastebin/README.md",
                "PRACTICE_QUESTIONS",
                "INTERMEDIATE",
                "System Design Primer",
                "Step-by-step interview solution: capacity estimation, Base62 token generation, database schema (NoSQL vs SQL), caching, and latency optimization."
            ),
            (
                "system-design-case-studies",
                "SYSTEM_DESIGN",
                "Designing a Distributed Rate Limiter with Redis Token Bucket",
                "https://stripe.com/blog/rate-limiters",
                "ARTICLE",
                "ADVANCED",
                "Stripe Engineering",
                "Production analysis of Token Bucket, Leaky Bucket, and Sliding Window log algorithms for protecting public APIs against denial of service."
            ),

            # SDE & Algorithms Materials
            (
                "dsa",
                "SOFTWARE_DEVELOPER",
                "Blind 75 & NeetCode 150 LeetCode Pattern Roadmap",
                "https://neetcode.io/roadmap",
                "COURSE",
                "INTERMEDIATE",
                "NeetCode",
                "Curated roadmap covering 18 core patterns: Two Pointers, Sliding Window, Tree Traversals, Graphs, Dynamic Programming, and Heaps."
            ),
            (
                "concurrency-multithreading",
                "SOFTWARE_DEVELOPER",
                "Concurrency & Multithreading: Deadlocks, Locks & Mutexes",
                "https://docs.python.org/3/library/asyncio.html",
                "DOCUMENTATION",
                "ADVANCED",
                "Python Docs",
                "Understanding race conditions, deadlocks, thread safety, locks, asyncio event loops, and non-blocking I/O programming."
            ),
            (
                "sql-dbms",
                "SOFTWARE_DEVELOPER",
                "Top 50 SQL Query Interview Questions & Window Functions",
                "https://leetcode.com/studyplan/top-sql-50/",
                "PRACTICE_QUESTIONS",
                "INTERMEDIATE",
                "LeetCode SQL",
                "50 high-yield SQL queries covering JOINs, Window Functions (ROW_NUMBER, RANK, DENSE_RANK), CTEs, and GROUP BY aggregations."
            ),

            # Generative AI Materials
            (
                "rag-architectures",
                "GENAI_ENGINEER",
                "Comprehensive RAG Pipeline Masterclass with LangChain",
                "https://python.langchain.com/docs/tutorials/rag/",
                "ARTICLE",
                "INTERMEDIATE",
                "LangChain Official",
                "End-to-end guide to Retrieval-Augmented Generation: document ingestion, recursive chunking, vector embedding generation, and LLM synthesis."
            ),
            (
                "rag-architectures",
                "GENAI_ENGINEER",
                "Vector Databases & Dense Retrieval: HNSW vs IVF-Flat",
                "https://www.pinecone.io/learn/vector-database/",
                "ARTICLE",
                "ADVANCED",
                "Pinecone Learning Hub",
                "Mathematical intuition and performance trade-offs behind approximate nearest neighbor (ANN) search algorithms like HNSW and inverted file indexing."
            ),

            # DevOps Materials
            (
                "docker-kubernetes",
                "DEVOPS_ENGINEER",
                "Docker Containers & Production Kubernetes Architecture",
                "https://kubernetes.io/docs/concepts/",
                "DOCUMENTATION",
                "INTERMEDIATE",
                "Kubernetes Official",
                "Complete overview of Pods, Deployments, ReplicaSets, Services, ConfigMaps, Ingress controllers, and Horizontal Pod Autoscalers."
            ),

            # Data Engineering Materials
            (
                "spark-data-pipelines",
                "DATA_ENGINEER",
                "Apache Spark Distributed Computing & DataFrame Tuning Guide",
                "https://spark.apache.org/docs/latest/sql-programming-guide.html",
                "DOCUMENTATION",
                "ADVANCED",
                "Apache Spark",
                "Distributed dataset processing, narrow vs wide transformations, shuffle partitions, broadcast joins, and Spark UI performance tuning."
            ),

            # Fullstack Web Materials
            (
                "web-development",
                "FULLSTACK_DEVELOPER",
                "Modern React Architecture, Server Components & Hooks",
                "https://react.dev/learn",
                "DOCUMENTATION",
                "INTERMEDIATE",
                "React Team",
                "Official React deep dive: Component lifecycle, reconciliation, virtual DOM, custom hooks, and state management patterns."
            ),

            # Aptitude & Behavioral Materials
            (
                "quant-math",
                None,
                "Quantitative Aptitude Formulas & Short-Tricks Cheatsheet",
                "https://www.geeksforgeeks.org/quantitative-aptitude-for-placements/",
                "PDF",
                "BEGINNER",
                "GeeksforGeeks",
                "High-speed shortcuts for Speed Math, Percentages, Ratio-Proportion, Profit-Loss, Time-Speed-Distance, and Permutations."
            ),
            (
                "behavioral-hr",
                None,
                "The Complete STAR Method Behavioral Interview Mastery",
                "https://hbr.org/2021/04/how-to-answer-behavioral-interview-questions",
                "ARTICLE",
                "BEGINNER",
                "Harvard Business Review",
                "Framework for answering 'Tell me about a time when...', handling conflicts with teammates, managing tight deadlines, and discussing failures."
            ),
        ]

        for topic_slug, role_code, title, url, mat_type, diff, source, desc in materials_data:
            topic = seeded_topics[topic_slug]
            role = seeded_roles[role_code] if role_code else None
            stmt = select(PreparationMaterial).where(PreparationMaterial.title == title)
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if not existing:
                mat = PreparationMaterial(
                    id=uuid4(),
                    topic_id=topic.id,
                    role_id=role.id if role else None,
                    title=title,
                    url=url,
                    material_type=mat_type,
                    difficulty=diff,
                    source=source,
                    description=desc,
                    status="APPROVED",
                )
                session.add(mat)
            else:
                existing.url = url
                existing.description = desc
                existing.difficulty = diff
                existing.source = source
                existing.role_id = role.id if role else None
                existing.status = "APPROVED"

        await session.commit()
        print("Successfully seeded all Roadmaps, System Design topics, Roles, and verified Materials!")


if __name__ == "__main__":
    asyncio.run(seed())

