"""
Utility functions for course-related data mappings
"""

import os
from django.conf import settings

def _exists_in_static(relative_path: str) -> bool:
    # Check in each staticfiles dir (dev) and STATIC_ROOT (prod, if collected)
    candidates = []
    try:
        for d in getattr(settings, 'STATICFILES_DIRS', []) or []:
            candidates.append(os.path.join(d, relative_path.replace('/', os.sep)))
    except Exception:
        pass
    if getattr(settings, 'STATIC_ROOT', None):
        candidates.append(os.path.join(settings.STATIC_ROOT, relative_path.replace('/', os.sep)))
    for p in candidates:
        if os.path.exists(p):
            return True
    return False

def get_course_image_path(course_title):
    """
    Returns the static image path for a course based on its title.
    Returns None if no mapping exists.
    """
    # Normalize course title for matching
    title_lower = course_title.lower().strip()
    
    # Course name to image mapping
    # Map to actual files under staticfiles/img/courses (filenames are cased and often .jpeg)
    course_images = {
        'cybersecurity': 'img/courses/Cybersecurity.jpeg',
        'ds': 'img/courses/DS.jpeg',
        'dsa': 'img/courses/dsa.jpg',
        'digital marketing': 'img/courses/Digital Marketing.jpeg',
        'ai and machine learning': 'img/courses/AI and Machine Learning.jpeg',
        'cloud computing': 'img/courses/Cloud Computing.jpeg',
        'project management': 'img/courses/Project Management.jpeg',
        'microsoft excel': 'img/courses/Microsoft Excel.jpeg',
        'aws': 'img/courses/AWS.jpg',
        'python': 'img/courses/Python.jpeg',
        'java': 'img/courses/Java.jpeg',
        'web design': 'img/courses/Web Design.jpg',
        'web development': 'img/courses/Web Development.jpg',
        'mysql': 'img/courses/MySQL.jpg',
        'ui/ux design': 'img/courses/UIUX Design.jpeg',
        'graphic design': 'img/courses/Graphic design.jpeg',
    }
    
    mapped = course_images.get(title_lower)
    if mapped and _exists_in_static(mapped):
        return mapped

    # Heuristic search: try variants based on title
    base_dir = 'img/courses'
    cleaned_variants = set()
    cleaned_variants.add(title_lower)
    cleaned_variants.add(title_lower.replace('/', ''))   # UI/UX -> UIUX
    cleaned_variants.add(title_lower.replace('/', ' ').strip())

    # Title case variants
    for v in list(cleaned_variants):
        cleaned_variants.add(' '.join(w.capitalize() for w in v.split()))
        cleaned_variants.add(v.upper())

    # Try common extensions
    for name in cleaned_variants:
        for ext in ('.jpeg', '.jpg', '.png'):
            candidate = f"{base_dir}/{name}{ext}"
            if _exists_in_static(candidate):
                return candidate

    return None

def get_course_skills(course_title):
    """
    Returns default skills for a course based on its title.
    Returns empty string if no mapping exists.
    """
    title_lower = course_title.lower().strip()
    
    course_skills = {
        'cybersecurity': 'Network Security, Ethical Hacking, Vulnerability Assessment, Incident Response, Security Best Practices',
        'ds': 'Data Analysis, Python, Statistics, Machine Learning, Data Visualization',
        'dsa': 'Algorithms, Data Structures, Problem Solving, Complexity Analysis, Coding',
        'digital marketing': 'SEO, Social Media Marketing, Content Marketing, Analytics, PPC Advertising',
        'ai and machine learning': 'Machine Learning, Deep Learning, Neural Networks, Python, TensorFlow',
        'cloud computing': 'AWS, Azure, Cloud Architecture, DevOps, Containerization',
        'project management': 'Project Planning, Agile Methodology, Risk Management, Team Leadership',
        'microsoft excel': 'Data Analysis, Formulas, Pivot Tables, VBA, Data Visualization',
        'aws': 'Cloud Computing, EC2, S3, Lambda, Cloud Architecture',
        'python': 'Programming, Data Science, Web Development, Automation, Scripting',
        'java': 'Object-Oriented Programming, Spring Framework, Java EE, Multithreading',
        'web design': 'HTML, CSS, JavaScript, Responsive Design, UI/UX Principles',
        'web development': 'HTML, CSS, JavaScript, React, Node.js, Full Stack Development',
        'mysql': 'Database Design, SQL Queries, Database Administration, Data Modeling',
        'ui/ux design': 'User Interface Design, User Experience, Prototyping, Figma, Design Thinking',
        'graphic design': 'Adobe Photoshop, Illustrator, InDesign, Branding, Visual Communication',
    }
    
    return course_skills.get(title_lower, '')

def get_course_syllabus(course_title):
    """
    Returns default syllabus topics for a course based on its title.
    Returns empty string if no mapping exists.
    """
    title_lower = course_title.lower().strip()
    
    course_syllabi = {
        'cybersecurity': 'Network Security Fundamentals\nEthical Hacking and Penetration Testing\nVulnerability Assessment\nIncident Response and Management\nSecurity Best Practices and Compliance',
        'ds': 'Introduction to Data Science\nData Analysis with Python\nMachine Learning Basics\nData Visualization\nStatistical Methods',
        'dsa': 'Arrays and Linked Lists\nStacks and Queues\nTrees and Graphs\nSorting and Searching Algorithms\nDynamic Programming',
        'digital marketing': 'Introduction to Digital Marketing\nSEO Fundamentals\nSocial Media Marketing\nContent Marketing Strategy\nAnalytics and Measurement',
        'ai and machine learning': 'Introduction to AI and ML\nSupervised Learning\nUnsupervised Learning\nDeep Learning Basics\nModel Evaluation and Deployment',
        'cloud computing': 'Cloud Computing Fundamentals\nAWS Services Overview\nAzure Platform\nContainerization with Docker\nDevOps Practices',
        'project management': 'Project Management Fundamentals\nAgile Methodology\nScrum Framework\nRisk Management\nTeam Leadership',
        'microsoft excel': 'Excel Basics and Navigation\nFormulas and Functions\nData Analysis with Pivot Tables\nCharts and Data Visualization\nAdvanced Excel Techniques',
        'aws': 'AWS Cloud Fundamentals\nEC2 and Compute Services\nS3 and Storage Services\nLambda and Serverless\nCloud Architecture Best Practices',
        'python': 'Python Basics and Syntax\nData Structures in Python\nObject-Oriented Programming\nPython for Data Science\nWeb Development with Python',
        'java': 'Java Fundamentals\nObject-Oriented Programming\nJava Collections Framework\nSpring Framework\nJava EE Development',
        'web design': 'HTML Fundamentals\nCSS Styling and Layout\nJavaScript Basics\nResponsive Design Principles\nUI/UX Design Concepts',
        'web development': 'HTML5 and CSS3\nJavaScript and ES6\nFrontend Frameworks (React)\nBackend Development (Node.js)\nFull Stack Integration',
        'mysql': 'Database Design Principles\nSQL Fundamentals\nAdvanced SQL Queries\nDatabase Administration\nPerformance Optimization',
        'ui/ux design': 'User Interface Design Principles\nUser Experience Research\nPrototyping and Wireframing\nDesign Tools (Figma)\nDesign Systems',
        'graphic design': 'Design Fundamentals\nAdobe Photoshop\nAdobe Illustrator\nBranding and Identity\nPrint and Digital Design',
    }
    
    return course_syllabi.get(title_lower, '')

