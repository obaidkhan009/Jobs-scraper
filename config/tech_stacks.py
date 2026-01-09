# Tech stacks configuration for job matching

# Technologies the user WANTS to see in job descriptions
GOOD_TECH = [
    "Python",
    "Django",
    "machine learning",
    "ML",
    "natural language processing",
    "NLP",
    "large language models",
    "LLM",
    "RAG",
    "AWS",
    "Docker",
    "Kubernetes",
    "RESTful APIs",
    "PostgreSQL",
    "OpenCV",
    "asyncio",
    "Django Channels",
    "Python cryptography",
    "Jenkins",
    "spaCy",
    "Redis",
    "Git",
    "Apache",
    "RabbitMQ",
    "Matplotlib",
    "Selenium",
    "GCP",
    "Tensorflow",
    "Pytorch",
    "GenAI",
    "Generative AI",
    "Elasticsearch",
    "Logstash",
    "Kibana",
    "ELK",
    "EC2",
    "S3",
    "RDS",
    "remote",
    "GitHub Actions",
    "Pandas",
    "Lambda",
    "Microservices",
    "LLMs",
    "ChatGPT",
    "LangChain",
    "AI",
    "Google Cloud Platform",
    "Google Cloud",
    "Linux",
    "SQL",
    "Vertex AI",
    "Vertex",
    "MatLab",
    "RESTful API",
    "Postgres",
    "mlops",
    "data scientist",
    "Data Science",
    "GitHub",
    "scikit-learn",
    "numpy",
]

# Technologies the user does NOT want to work with
BAD_TECH = [
    # JavaScript/TypeScript ecosystem
    "Node.js",
    "Node",
    "nodejs",
    "node.js",
    "NestJS",
    "React",
    "reactjs",
    "react.js",
    "React Native",
    "Redux",
    "angular",
    "Vue.js",
    "Typescript",
    "frontend",
    "front-end",
    "front end",
    
    # Java ecosystem (NOT Python focused)
    "Java",
    "J2EE",
    "Java / J2EE",
    "Spring Boot",
    "Spring Framework",
    "JEE",
    "Jakarta EE",
    
    # Full Stack (user wants backend/ML only)
    "full stack",
    "full-stack",
    "fullstack",
    
    # Other languages/frameworks
    "Ruby on Rails",
    "Ruby",
    "Rails",
    "ROR",
    "Ruby on Rails (ROR)",
    "Go",
    "Golang",
    "Scala",
    ".net",
    "C#",
    "Kotlin",
    "Rust",
    "Web3",
    "crypto",
    
    # BI/Data Viz (not ML)
    "Power BI",
    "Tableau",
    "BI",
    "Boomi",
    "sap",
    "salesforce",
    "Snowflake",
    
    # Other exclusions
    "mobile development",
    "UI/UX",
    "Co-Founder",
    "Staff",
    "R",
    "Secret-level",
    "Hadoop",
    "Azure ADF",
    "Banking Domain",
]

# Maximum number of bad tech matches allowed before filtering out
MAX_BAD_TECH_COUNT = 4

# Job types/keywords to EXCLUDE (entry level, internship, equity, non-US locations)
EXCLUDED_JOB_TYPES = [
    # Entry level / Junior positions
    "entry level",
    "entry-level",
    "junior",
    "associate",
    "graduate",
    "new grad",
    "new graduate",
    "early career",
    
    # Internships
    "intern",
    "internship",
    "trainee",
    "apprentice",
    "co-op",
    
    # Part-time / Freelance / Contract
    "part-time",
    "part time",
    "freelance",
    "freelancer",
    "contractor",
    "temporary",
    "temp position",
    "gig",
    
    # Equity-based / Startup risk
    "equity only",
    "equity-based",
    "unpaid",
    "volunteer",
    "sweat equity",
    "equity compensation only",
    "deferred compensation",
    
    # Non-US locations (sometimes slip through)
    "india",
    "pakistan",
    "philippines",
    "nigeria",
    "uk only",
    "europe only",
    "canada only",
    "australia only",
    "latam",
    "latin america",
    
    # Clearance requirements (ALL types)
    "clearance required",
    "security clearance",
    "top secret",
    "ts/sci",
    "ability to obtain clearance",
    "obtain a government clearance",
    "obtain a clearance",
    "government clearance",
    "secret clearance",
    "public trust",
    
    # Location-restricted "remote" (user is in VA)
    "must reside within",
    "reside within 30 miles",
    "reside within 50 miles",
    "local candidates only",
    "must be located in",
    "must live in",
    "must be based in",
    "candidates must be in",
    "day one onsite",
    "day 1 onsite",
]

# Target job titles to search for
JOB_TITLES = [
    # AI / ML
    'AI Engineer',
    'Artificial Intelligence Engineer',
    'Machine Learning Engineer',
    'ML Engineer',
    'Deep Learning Engineer',
    'Computer Vision Engineer',
    'NLP Engineer',
    'Natural Language Processing Engineer',
    'AI Research Engineer',
    'Research Scientist (AI)',
    'Applied Scientist (ML)',
    'ML Scientist',
    'AI Developer',
    'Generative AI Engineer',
    'LLM Engineer',
    'Prompt Engineer',
    'AI Solutions Engineer',
    'Applied AI Scientist',

    # Data
    'Data Scientist',
    'Senior Data Scientist',
    'Data Analyst',
    'Senior Data Analyst',
    'Business Data Analyst',
    'Data Engineer',
    'Big Data Engineer',
    'Analytics Engineer',
    'Decision Scientist',
    'Quantitative Analyst',
    'BI Developer',

    # Backend / Software
    'Backend Developer',
    'Backend Engineer',
    'Software Engineer',
    'Software Developer',
    'Senior Software Engineer',
    'Python Developer',
    'Python Backend Developer',
    'Django Developer',
    'FastAPI Developer',
    'REST API Developer',
    'API Engineer',
    'Microservices Engineer',
    'Platform Engineer',
    'Systems Engineer',

    # AWS / Cloud / DevOps
    'AWS Engineer',
    'AWS Cloud Engineer',
    'Cloud Engineer',
    'Cloud Solutions Engineer',
    'Cloud Architect',
    'AWS Solutions Architect',
    'DevOps Engineer',
    'Site Reliability Engineer',
    'SRE',
    'Infrastructure Engineer',
    'Cloud DevOps Engineer',
    'Cloud Security Engineer',

    # Hybrid AI + Backend + Cloud
    'AI Backend Engineer',
    'ML Backend Engineer',
    'MLOps Engineer',
    'AI Platform Engineer',
    'Cloud ML Engineer',
    'AI Infrastructure Engineer',
    'Backend Data Engineer',
    'ML Systems Engineer',
    'GenAI Platform Engineer',
]

# Minimum salary requirement (annual)
MIN_SALARY = 120000

# Location filters
LOCATION = "United States"
REMOTE_ONLY = True

# Time filter - jobs posted within this many hours
POSTED_WITHIN_HOURS = 24
