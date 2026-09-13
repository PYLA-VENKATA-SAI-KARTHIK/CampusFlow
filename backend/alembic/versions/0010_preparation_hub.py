"""add preparation hub tables and initial taxonomy

Revision ID: 0010_preparation_hub
Revises: 0009_student_personal_email
Create Date: 2026-09-12 23:10:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0010_preparation_hub'
down_revision: Union[str, None] = '0009_student_personal_email'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. preparation_roles
    roles_table = op.create_table(
        'preparation_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_preparation_roles_code', 'preparation_roles', ['code'], unique=True)

    # 2. preparation_categories
    categories_table = op.create_table(
        'preparation_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('sequence_order', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_preparation_categories_code', 'preparation_categories', ['code'], unique=True)

    # 3. preparation_topics
    topics_table = op.create_table(
        'preparation_topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('preparation_categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_preparation_topics_category_id', 'preparation_topics', ['category_id'])
    op.create_index('ix_preparation_topics_slug', 'preparation_topics', ['slug'], unique=True)

    # 4. preparation_role_topics
    role_topics_table = op.create_table(
        'preparation_role_topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('preparation_roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('preparation_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('importance', sa.String(length=20), server_default='CORE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('role_id', 'topic_id', name='uq_role_topic'),
        sa.CheckConstraint("importance IN ('CORE', 'ELECTIVE', 'BONUS')", name='chk_role_topic_importance'),
    )
    op.create_index('ix_preparation_role_topics_role_id', 'preparation_role_topics', ['role_id'])
    op.create_index('ix_preparation_role_topics_topic_id', 'preparation_role_topics', ['topic_id'])

    # 5. preparation_materials
    op.create_table(
        'preparation_materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('preparation_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('preparation_roles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('material_type', sa.String(length=50), server_default='ARTICLE', nullable=False),
        sa.Column('difficulty', sa.String(length=20), server_default='BEGINNER', nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='APPROVED', nullable=False),
        sa.Column('submitted_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("material_type IN ('ARTICLE', 'VIDEO', 'PDF', 'PRACTICE_QUESTIONS', 'DOCUMENTATION', 'COURSE', 'OTHER')", name='chk_material_type'),
        sa.CheckConstraint("difficulty IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')", name='chk_material_difficulty'),
        sa.CheckConstraint("status IN ('PENDING', 'APPROVED', 'REJECTED')", name='chk_material_status'),
    )
    op.create_index('ix_preparation_materials_topic_id', 'preparation_materials', ['topic_id'])
    op.create_index('ix_preparation_materials_role_id', 'preparation_materials', ['role_id'])
    op.create_index('ix_preparation_materials_status', 'preparation_materials', ['status'])
    op.create_index('ix_preparation_materials_submitted_by', 'preparation_materials', ['submitted_by_user_id'])

    # --- SEED INITIAL TAXONOMY ---
    # Categories
    cat_apt_id = uuid.uuid4()
    cat_vbl_id = uuid.uuid4()
    cat_tec_id = uuid.uuid4()
    cat_int_id = uuid.uuid4()

    op.bulk_insert(
        categories_table,
        [
            {'id': cat_apt_id, 'code': 'APTITUDE', 'name': 'Aptitude & Reasoning', 'description': 'Quantitative ability, logical reasoning, and data interpretation.', 'icon': 'Calculator', 'sequence_order': 1},
            {'id': cat_vbl_id, 'code': 'VERBAL', 'name': 'Verbal Ability', 'description': 'Grammar, vocabulary, reading comprehension, and sentence correction.', 'icon': 'BookOpen', 'sequence_order': 2},
            {'id': cat_tec_id, 'code': 'TECHNICAL', 'name': 'Technical Core', 'description': 'Programming languages, databases, computer science core, and AI/ML.', 'icon': 'Code', 'sequence_order': 3},
            {'id': cat_int_id, 'code': 'INTERVIEW', 'name': 'Interview Preparation', 'description': 'HR questions, behavioral, system design, and resume-based prep.', 'icon': 'Users', 'sequence_order': 4},
        ]
    )

    # Core Topics
    t_quant_id = uuid.uuid4()
    t_logic_id = uuid.uuid4()
    t_di_id = uuid.uuid4()
    t_gram_id = uuid.uuid4()
    t_rc_id = uuid.uuid4()
    t_py_id = uuid.uuid4()
    t_java_id = uuid.uuid4()
    t_sql_id = uuid.uuid4()
    t_oop_id = uuid.uuid4()
    t_dbms_id = uuid.uuid4()
    t_cn_id = uuid.uuid4()
    t_os_id = uuid.uuid4()
    t_web_id = uuid.uuid4()
    t_aiml_id = uuid.uuid4()
    t_genai_id = uuid.uuid4()
    t_hr_id = uuid.uuid4()
    t_techint_id = uuid.uuid4()
    t_proj_id = uuid.uuid4()

    op.bulk_insert(
        topics_table,
        [
            {'id': t_quant_id, 'category_id': cat_apt_id, 'name': 'Quantitative Aptitude', 'slug': 'quantitative-aptitude', 'description': 'Percentages, ratios, time & work, algebra, and number systems.'},
            {'id': t_logic_id, 'category_id': cat_apt_id, 'name': 'Logical Reasoning', 'slug': 'logical-reasoning', 'description': 'Deductive reasoning, series completion, coding-decoding, and puzzles.'},
            {'id': t_di_id, 'category_id': cat_apt_id, 'name': 'Data Interpretation', 'slug': 'data-interpretation', 'description': 'Tables, bar graphs, pie charts, and data sufficiency.'},
            {'id': t_gram_id, 'category_id': cat_vbl_id, 'name': 'Grammar & Sentence Correction', 'slug': 'grammar-sentence-correction', 'description': 'Tenses, subject-verb agreement, and error spotting.'},
            {'id': t_rc_id, 'category_id': cat_vbl_id, 'name': 'Reading Comprehension', 'slug': 'reading-comprehension', 'description': 'Passage analysis, critical reasoning, and para jumbles.'},
            {'id': t_py_id, 'category_id': cat_tec_id, 'name': 'Python Programming', 'slug': 'python', 'description': 'Syntax, data structures, functions, decorators, and libraries.'},
            {'id': t_java_id, 'category_id': cat_tec_id, 'name': 'Java Programming', 'slug': 'java', 'description': 'Core Java, collections framework, multithreading, and JVM internals.'},
            {'id': t_sql_id, 'category_id': cat_tec_id, 'name': 'SQL & Database Queries', 'slug': 'sql', 'description': 'SELECT queries, JOINs, subqueries, indexing, and aggregations.'},
            {'id': t_oop_id, 'category_id': cat_tec_id, 'name': 'Object-Oriented Programming (OOP)', 'slug': 'oop', 'description': 'Encapsulation, inheritance, polymorphism, abstraction, and design patterns.'},
            {'id': t_dbms_id, 'category_id': cat_tec_id, 'name': 'Database Management Systems (DBMS)', 'slug': 'dbms', 'description': 'ACID properties, transactions, normalization, and relational schema design.'},
            {'id': t_cn_id, 'category_id': cat_tec_id, 'name': 'Computer Networks', 'slug': 'computer-networks', 'description': 'OSI model, TCP/IP, routing protocols, DNS, and HTTP/HTTPS.'},
            {'id': t_os_id, 'category_id': cat_tec_id, 'name': 'Operating Systems', 'slug': 'operating-systems', 'description': 'Processes, threads, CPU scheduling, deadlocks, and virtual memory.'},
            {'id': t_web_id, 'category_id': cat_tec_id, 'name': 'Web Development (HTML/CSS/JS)', 'slug': 'web-development', 'description': 'DOM manipulation, responsive design, modern JavaScript (ES6+), and REST APIs.'},
            {'id': t_aiml_id, 'category_id': cat_tec_id, 'name': 'AI & Machine Learning', 'slug': 'ai-ml', 'description': 'Supervised/unsupervised learning, model evaluation, and classical ML algorithms.'},
            {'id': t_genai_id, 'category_id': cat_tec_id, 'name': 'Generative AI & LLMs', 'slug': 'generative-ai', 'description': 'Transformers, prompt engineering, RAG, and fine-tuning concepts.'},
            {'id': t_hr_id, 'category_id': cat_int_id, 'name': 'HR & Behavioral Questions', 'slug': 'hr-behavioral', 'description': 'STAR method, strengths/weaknesses, leadership, and conflict resolution.'},
            {'id': t_techint_id, 'category_id': cat_int_id, 'name': 'Technical Interview Practice', 'slug': 'technical-interview', 'description': 'Data structures, algorithm walkthroughs, and live coding explanations.'},
            {'id': t_proj_id, 'category_id': cat_int_id, 'name': 'Project & Resume Defense', 'slug': 'project-defense', 'description': 'Explaining tech stack choices, trade-offs, challenges, and impact.'},
        ]
    )

    # Roles
    r_swe_id = uuid.uuid4()
    r_aiml_id = uuid.uuid4()
    r_da_id = uuid.uuid4()
    r_genai_id = uuid.uuid4()
    r_qa_id = uuid.uuid4()
    r_devops_id = uuid.uuid4()

    op.bulk_insert(
        roles_table,
        [
            {'id': r_swe_id, 'code': 'SOFTWARE_DEVELOPER', 'name': 'Software Developer', 'description': 'Full-stack and backend software engineering across core languages, DSA, and system fundamentals.'},
            {'id': r_aiml_id, 'code': 'AI_ML_ENGINEER', 'name': 'AI/ML Engineer', 'description': 'Machine learning, data preprocessing, mathematical foundations, and AI application engineering.'},
            {'id': r_da_id, 'code': 'DATA_ANALYST', 'name': 'Data Analyst', 'description': 'SQL, statistics, data visualization, and business intelligence.'},
            {'id': r_genai_id, 'code': 'GENAI_ENGINEER', 'name': 'Generative AI Engineer', 'description': 'LLM application development, prompt engineering, RAG architecture, and embeddings.'},
            {'id': r_qa_id, 'code': 'QA_TEST_ENGINEER', 'name': 'QA & Test Automation Engineer', 'description': 'Software testing methodologies, test automation, and API testing.'},
            {'id': r_devops_id, 'code': 'CLOUD_DEVOPS', 'name': 'Cloud & DevOps Engineer', 'description': 'Cloud computing, CI/CD pipelines, containerization, and infrastructure basics.'},
        ]
    )

    # Role Topic Mappings (M2M)
    op.bulk_insert(
        role_topics_table,
        [
            # Software Developer
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_quant_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_logic_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_py_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_java_id, 'importance': 'ELECTIVE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_sql_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_oop_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_dbms_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_os_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_cn_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_techint_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_hr_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_swe_id, 'topic_id': t_proj_id, 'importance': 'CORE'},

            # AI/ML Engineer
            {'id': uuid.uuid4(), 'role_id': r_aiml_id, 'topic_id': t_py_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_aiml_id, 'topic_id': t_sql_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_aiml_id, 'topic_id': t_aiml_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_aiml_id, 'topic_id': t_genai_id, 'importance': 'ELECTIVE'},
            {'id': uuid.uuid4(), 'role_id': r_aiml_id, 'topic_id': t_oop_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_aiml_id, 'topic_id': t_techint_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_aiml_id, 'topic_id': t_hr_id, 'importance': 'CORE'},

            # Data Analyst
            {'id': uuid.uuid4(), 'role_id': r_da_id, 'topic_id': t_quant_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_da_id, 'topic_id': t_di_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_da_id, 'topic_id': t_sql_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_da_id, 'topic_id': t_py_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_da_id, 'topic_id': t_dbms_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_da_id, 'topic_id': t_hr_id, 'importance': 'CORE'},

            # GenAI Engineer
            {'id': uuid.uuid4(), 'role_id': r_genai_id, 'topic_id': t_py_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_genai_id, 'topic_id': t_genai_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_genai_id, 'topic_id': t_aiml_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_genai_id, 'topic_id': t_sql_id, 'importance': 'CORE'},
            {'id': uuid.uuid4(), 'role_id': r_genai_id, 'topic_id': t_proj_id, 'importance': 'CORE'},
        ]
    )


def downgrade() -> None:
    op.drop_table('preparation_materials')
    op.drop_table('preparation_role_topics')
    op.drop_table('preparation_topics')
    op.drop_table('preparation_categories')
    op.drop_table('preparation_roles')
