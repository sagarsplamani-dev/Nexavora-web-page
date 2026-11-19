import logging

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render

from apps.contact.forms import CallbackForm, ContactForm
from apps.contact.models import Enquiry
from apps.contact.services.whatsapp import notify_enquiry


logger = logging.getLogger(__name__)


DATA_SCIENCE_MODULES = [
    ("Python, NumPy & Pandas", "Python foundations, arrays, tabular data, and notebooks."),
    ("SQL & Database Management", "Relational data, queries, joins, and database connectors."),
    ("Machine Learning", "Feature preparation, model selection, and evaluation."),
    ("Natural Language Processing", "Text preparation and language-processing workflows."),
    ("Deep Learning", "Neural-network concepts and practical applications."),
    ("Computer Vision", "Image processing, classification, and detection concepts."),
    ("Generative AI & Agentic AI", "LLMs, retrieval-augmented generation, and agent workflows."),
    ("Git, GitHub & GitLab", "Version control and collaborative project practices."),
]

DATA_SCIENCE_MODULE_DETAILS = [
    {
        "title": "Python, NumPy & Pandas",
        "description": "Use Python to explore, clean, transform and communicate insights from structured data.",
        "topics": [
            "Python for Data Science",
            "NumPy arrays and operations",
            "Pandas Series and DataFrames",
            "Data Cleaning",
            "Data Manipulation",
            "Exploratory Data Analysis (EDA)",
            "Data Preprocessing",
            "Data Visualization",
        ],
        "technologies": ["Python", "NumPy", "Pandas", "Jupyter"],
        "outcome": "Prepare analysis-ready datasets and build a repeatable exploratory analysis workflow.",
    },
    {
        "title": "SQL & Database Management",
        "description": "Learn how SQL is used to retrieve, filter, join, manage, and analyze data held in relational databases.",
        "topics": [
            "Introduction to SQL and Relational Databases",
            "SQL Syntax and Data Types",
            "SELECT Queries",
            "Aggregate Functions",
            "Subqueries",
            "Window Functions",
            "Primary Keys and Foreign Keys",
            "Extracting and Analyzing Data Using SQL",
            "Database Fundamentals",
            "DDL, DML and DQL Commands",
            "WHERE, ORDER BY and GROUP BY",
            "SQL Joins: INNER, LEFT, RIGHT and FULL",
            "Common Table Expressions (CTEs)",
            "INSERT, UPDATE and DELETE",
            "Data Filtering and Sorting",
            "Connecting SQL Databases with Python",
        ],
        "technologies": ["SQL", "Relational databases", "Python database connectors"],
        "outcome": "Query related tables, shape analytical datasets, and connect database results to Python workflows.",
    },
    {
        "title": "Machine Learning",
        "description": "Build a practical understanding of learning algorithms, training workflows, evaluation, and iteration.",
        "topics": [
            "Machine Learning Fundamentals",
            "Supervised Learning",
            "Unsupervised Learning",
            "Classification Algorithms",
            "Regression Algorithms",
            "Clustering Algorithms",
            "Model Training",
            "Model Evaluation",
            "Feature Engineering",
            "Model Optimization",
        ],
        "technologies": ["Scikit-learn (Sklearn)", "Python", "Pandas", "NumPy"],
        "outcome": "Train and evaluate baseline models, select useful features, and explain model behavior.",
    },
    {
        "title": "Natural Language Processing",
        "description": "Prepare text data and introduce common approaches for extracting meaning from language.",
        "topics": [
            "Natural Language Processing (NLP)",
            "Tokenization",
            "Sentiment Analysis",
            "Text Preprocessing",
            "Text Classification",
        ],
        "technologies": ["NLP", "Python", "Text-processing libraries"],
        "outcome": "Build a text-analysis workflow and evaluate a simple text classification task.",
    },
    {
        "title": "Deep Learning",
        "description": "Explore the building blocks of neural-network-based approaches and their common terminology.",
        "topics": [
            "Deep Learning (DL)",
            "Artificial Neural Networks",
            "Neural Networks",
            "Deep Learning Fundamentals",
        ],
        "technologies": ["Deep Learning (DL)", "Neural Networks", "Artificial Neural Networks"],
        "outcome": "Describe a neural network and identify the stages in a basic deep-learning workflow.",
    },
    {
        "title": "Computer Vision",
        "description": "Work with image data and understand foundational computer vision tasks.",
        "topics": [
            "Computer Vision (CV)",
            "Image Classification",
            "Image Processing",
            "Object Detection",
        ],
        "technologies": ["Computer Vision (CV)", "Image processing", "Python"],
        "outcome": "Prepare image data and compare classification and object-detection use cases.",
    },
    {
        "title": "Generative AI & Agentic AI",
        "description": "Understand language-model applications, retrieval grounding, and agent workflow concepts.",
        "topics": [
            "Generative AI (GenAI)",
            "Prompt Engineering",
            "AI Applications",
            "AI Agents",
            "AI Automation",
            "Large Language Models (LLMs)",
            "Retrieval-Augmented Generation (RAG)",
            "Agentic AI",
            "Agent Workflows",
        ],
        "technologies": ["Generative AI (GenAI)", "Large Language Models (LLMs)", "RAG", "AI agents"],
        "outcome": "Prototype a grounded AI application and map the steps in a bounded agent workflow.",
    },
    {
        "title": "Git, GitHub & GitLab",
        "description": "Organize code changes and collaborate with a version-controlled project workflow.",
        "topics": [
            "GitHub",
            "Git",
            "Project Collaboration",
            "GitLab",
            "Version Control",
        ],
        "technologies": ["Git", "GitHub", "GitLab"],
        "outcome": "Track project changes and collaborate using branches, commits, and shared repositories.",
    },
]

DATA_ANALYTICS_CURRICULUM = [
    ("Introduction to Data Analytics", "1 week"),
    ("Excel for Data Analysis", "2 weeks"),
    ("SQL & Database Management", "2 weeks"),
    ("Python Programming", "2 weeks"),
    ("NumPy & Pandas", "2 weeks"),
    ("Data Cleaning & Preparation", "1 week"),
    ("Exploratory Data Analysis", "1 week"),
    ("Statistics & Probability", "2 weeks"),
    ("Data Visualization", "1 week"),
    ("Power BI", "2 weeks"),
    ("Tableau", "1 week"),
    ("Machine Learning Fundamentals", "2 weeks"),
    ("Capstone Projects", "2 weeks"),
    ("Interview Preparation", "1 week"),
]

DATA_SCIENCE_PROJECTS = [
    ("SQL-Based Data Analysis", "Design analytical queries on a sample relational dataset and explain the findings.", "SQL · CTEs · Window Functions · Python"),
    ("Exploratory Data Analysis", "Investigate a sample dataset, document data quality, and communicate patterns.", "Python · Pandas · NumPy · Visualization"),
    ("Sales Prediction Using Machine Learning", "Create a learning exercise for predicting a target from historical sample sales data.", "Python · Pandas · Scikit-learn"),
    ("Customer Churn Prediction", "Explore a sample customer dataset and evaluate a classification approach.", "SQL · Python · Scikit-learn"),
    ("Sentiment Analysis", "Classify sample text and review the effect of text preprocessing.", "Python · NLP · Scikit-learn"),
    ("Image Classification", "Build an introductory image-classification exercise with a labeled sample dataset.", "Python · Deep Learning"),
    ("Object Detection", "Explore detection concepts and evaluate predictions on sample images.", "Python · Computer Vision"),
    ("Generative AI Chatbot", "Prototype a course-domain chatbot and assess its responses against sample questions.", "LLMs · Prompt Engineering"),
    ("Retrieval-Augmented Generation App", "Connect a small document collection to an LLM-based question-answering workflow.", "Python · Embeddings · RAG"),
    ("Agentic AI Automation", "Map a bounded multi-step workflow and add clear human review points.", "Agentic AI · Tool Workflows"),
]

ANALYTICS_PROJECTS = [
    ("Sales Performance Dashboard", "Explore sales trends, category performance, and regional results.", "Excel · SQL · Power BI"),
    ("Customer Segmentation Analysis", "Explore meaningful audience groups in sample customer data.", "Python · Pandas · Tableau"),
    ("E-commerce Data Analysis", "Analyze a sample store dataset across products and order behavior.", "SQL · Python · Power BI"),
    ("Financial Data Visualization", "Present key movements in a sample financial dataset.", "Excel · Tableau"),
    ("Employee Attrition Analysis", "Investigate patterns in a sample workforce dataset.", "Python · Statistics · Power BI"),
    ("Predictive Sales Modeling", "Evaluate a learning exercise using sample sales data.", "Python · Pandas · scikit-learn"),
]

ANALYTICS_SKILLS = [
    ("Big Data Technologies", "Explore data technologies and concepts used in larger-scale data workflows."),
    ("Business Intelligence", "Use reporting and business intelligence concepts to communicate insights."),
    ("Cloud Platforms", "Review cloud platform concepts relevant to data work."),
    ("Communication & Storytelling", "Present analytical findings clearly for different audiences."),
    ("Data Cleaning & Preparation", "Prepare, validate, and transform data for analysis."),
    ("Data Manipulation", "Work with structured datasets using appropriate tools."),
    ("Data Visualization", "Choose clear visual forms to explain patterns and comparisons."),
    ("Machine Learning", "Explore predictive modeling concepts and evaluation."),
    ("Microsoft Excel", "Use spreadsheets for organizing and analyzing data."),
    ("SQL", "Query relational data and combine information from tables."),
    ("Python", "Use Python programming concepts in analytical workflows."),
    ("Power BI", "Build business intelligence reports and visualizations."),
    ("Tableau", "Create visual analyses and dashboards."),
    ("Statistics", "Use statistical methods to interpret data."),
    ("Predictive Modeling", "Build and assess predictive learning exercises."),
    ("Data Modeling", "Organize analytical data for reliable reporting."),
]

DATA_SCIENCE_FAQ = [
    ("What does the Data Science course cover?", "The curriculum is organized into Python data processing, SQL and databases, machine learning, NLP, deep learning, computer vision, Generative AI, Agentic AI, and version control."),
    ("Is SQL a dedicated part of the curriculum?", "Yes. SQL and database management appear as a dedicated learning module."),
    ("Do I need prior programming experience?", "Ask the course team about prerequisites and the level that best fits your experience before enrolling."),
    ("Are practical projects included?", "The page presents illustrative project ideas. Confirm which projects and datasets are part of the current course delivery."),
    ("Is an internship included?", "Internship availability, eligibility, duration, and deliverables are confirmed by Nexavora before enrollment."),
    ("What does certification mean?", "Ask Nexavora to confirm course-completion criteria, the certificate issuer, and any assessment requirements."),
    ("Does the course guarantee a job?", "No job or placement outcome is guaranteed. Career support is educational guidance."),
]

ANALYTICS_FAQ = [
    ("What is Data Analytics?", "The course focuses on data analysis, visualization, and SQL to turn data into business insights."),
    ("Who can enrol in this course?", "Contact the course team to discuss your background, prerequisites, and the available learning options."),
    ("Do I need programming experience?", "Ask an advisor which starting level and prerequisites apply to the current course."),
    ("What tools will I learn?", "The page lists Excel, SQL, Python, Power BI, Tableau, and statistics among the course skills."),
    ("How long does the course take?", "The course catalogue lists Data Analytics as a 16-week course. Confirm the current schedule with Nexavora."),
    ("Is the course available online?", "Confirm current delivery modes and schedules with the course team."),
    ("Will I receive a certificate?", "Certificate criteria and the issuer should be confirmed with Nexavora before enrollment."),
    ("Does the course include placement assistance?", "The page describes career guidance and placement assistance, but does not guarantee employment."),
    ("Can I download the syllabus?", "Use the syllabus download to review the course topics shown on this page."),
    ("How do I book a free demo?", "Submit a callback request or contact Nexavora to ask about available demo times."),
]


def home(request):
    callback_form = CallbackForm()
    popup_callback_form = CallbackForm(auto_id="popup_%s")
    contact_form = ContactForm()
    active_form = None
    open_call_popup = False

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == Enquiry.Kind.CALLBACK:
            open_call_popup = request.POST.get("form_source") == "popup"
            if open_call_popup:
                active_form = popup_callback_form = CallbackForm(
                    request.POST,
                    auto_id="popup_%s",
                )
            else:
                active_form = callback_form = CallbackForm(request.POST)
            return_anchor = "advisor"
        elif form_type == Enquiry.Kind.CONTACT:
            active_form = contact_form = ContactForm(request.POST)
            return_anchor = "contact"
        else:
            return HttpResponse("Unknown form submission.", status=400)

        if active_form.is_valid():
            submission_key = active_form.cleaned_data["submission_key"]
            try:
                with transaction.atomic():
                    enquiry = active_form.save(commit=False)
                    enquiry.kind = form_type
                    enquiry.submission_key = submission_key
                    enquiry.save()
            except IntegrityError:
                if not Enquiry.objects.filter(submission_key=submission_key).exists():
                    raise
                return redirect(f"/?submitted={form_type}#{return_anchor}")

            try:
                notify_enquiry(enquiry)
            except Exception as error:
                logger.error(
                    "Unexpected WhatsApp notification error for enquiry_id=%s error_type=%s",
                    enquiry.pk,
                    type(error).__name__,
                )
                try:
                    Enquiry.objects.filter(pk=enquiry.pk).update(
                        whatsapp_status=Enquiry.WhatsAppStatus.FAILED,
                        whatsapp_error_code="unexpected_error",
                    )
                except Exception as status_error:
                    logger.error(
                        "Could not record WhatsApp notification failure for enquiry_id=%s error_type=%s",
                        enquiry.pk,
                        type(status_error).__name__,
                    )
            return redirect(f"/?submitted={form_type}#{return_anchor}")

    context = {
        "callback_form": callback_form,
        "popup_callback_form": popup_callback_form,
        "contact_form": contact_form,
        "open_call_popup": open_call_popup,
        "callback_submitted": request.GET.get("submitted") == Enquiry.Kind.CALLBACK,
        "contact_submitted": request.GET.get("submitted") == Enquiry.Kind.CONTACT,
        "ds_modules": DATA_SCIENCE_MODULES,
        "ds_module_details": DATA_SCIENCE_MODULE_DETAILS,
        "analytics_curriculum": DATA_ANALYTICS_CURRICULUM,
        "ds_projects": DATA_SCIENCE_PROJECTS,
        "analytics_projects": ANALYTICS_PROJECTS,
        "analytics_skill_items": ANALYTICS_SKILLS,
        "ds_faq": DATA_SCIENCE_FAQ,
        "analytics_faq": ANALYTICS_FAQ,
    }
    return render(request, "core/home.html", context)


def download_syllabus(request):
    lines = [
        "Nexavora Technologies LLP",
        "Data Analytics Course Syllabus",
        "",
    ]
    lines.extend(
        f"{index:02d}. {title} ({duration})"
        for index, (title, duration) in enumerate(DATA_ANALYTICS_CURRICULUM, start=1)
    )
    lines.extend(
        [
            "",
            "Course length shown on the course catalogue: 16 weeks.",
            "Confirm current schedules, prerequisites, and delivery details with Nexavora.",
        ]
    )
    response = HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="nexavora-data-analytics-syllabus.txt"'
    return response
