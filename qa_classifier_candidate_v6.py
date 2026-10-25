import re
SOFTWARE_GROUPS = {'automation_frameworks': {'selenium': 3, 'playwright': 3, 'tosca': 3, 'qtest': 3, 'cypress': 2, 'pytest': 2, 'appium': 3}, 'api_testing': {'api testing': 3, 'api validation': 2, 'postman': 2, 'api tests': 2}, 'software_testing': {'software testing': 3, 'manual testing': 2, 'automated testing': 2, 'automation testing': 2, 'test automation': 2, 'automated scripts': 2, 'automation test scripts': 2, 'automated test cases': 2, 'manual qa': 2, 'automated qa': 2, 'software quality assurance': 3}, 'functional_testing': {'functional testing': 2, 'regression testing': 2, 'regression tests': 2, 'integration testing': 2, 'integration tests': 2, 'end to end testing': 2, 'end-to-end testing': 2, 'web testing': 2, 'application testing': 2, 'mobile application testing': 2, 'mobile testing': 2, 'functional tests': 2, 'system tests': 2}, 'application_platforms': {'salesforce': 3, 'web applications': 2, 'software applications': 2, 'database applications': 2}, 'test_artifacts': {'test cases': 1, 'test scripts': 1, 'test scenarios': 1, 'test plans': 1}, 'defect_management': {'defect tracking': 1, 'bug tracking': 1, 'defect records': 1, 'software defects': 1, 'report defects': 1}, 'data_validation': {'sql validation': 2, 'database testing': 2, 'sql': 1}, 'uat': {'user acceptance testing': 2, 'uat': 1}, 'test_management': {'test management': 1, 'jira': 1, 'xray': 1}}
MANUFACTURING_GROUPS = {'standards': {'as9100': 3, 'iso 9001': 3, 'iatf 16949': 3, 'iso 13485': 3}, 'engineering': {'engineering drawings': 3, 'machined components': 3, 'technical drawings': 2}, 'inspection': {'inspection plans': 3, 'first article inspection': 3, 'dimensional inspection': 3, 'quality inspection': 1, 'material inspection': 2, 'quality inspections': 2, 'manufacturing quality inspections': 3}, 'production': {'manufacturing operations': 3, 'manufacturing process': 2, 'production line': 2, 'shop floor': 2, 'production lines': 2, 'manufacturing production': 2}, 'materials': {'nonconforming material': 3, 'manufactured parts': 2, 'machined parts': 2}, 'quality_control': {'production defects': 2, 'quality control': 1, 'supplier quality': 2}}
SOFTWARE_TERMS = {term: weight for group in SOFTWARE_GROUPS.values() for (term, weight) in group.items()}
MANUFACTURING_TERMS = {term: weight for group in MANUFACTURING_GROUPS.values() for (term, weight) in group.items()}
NEGATION_PATTERN = re.compile('\\b(?:no|not required|not needed|without|not responsible for)\\b', re.IGNORECASE)
BACKGROUND_PHRASES = ('our company', 'we manufacture', 'company background')

def term_present(text, term):
    pattern = '(?<!\\w)' + re.escape(term).replace('\\ ', '[\\s-]+') + '(?!\\w)'
    return bool(re.search(pattern, text, re.IGNORECASE))

def _grouped_score(description, groups, manufacturing=False):
    if not isinstance(description, str) or not description.strip():
        return (0, [])
    clauses = re.split('(?<=[.!?])\\s+|;|\\bbut\\b|\\bhowever\\b|,\\s+(?=(?:no|without|not responsible for)\\b)', description, flags=re.IGNORECASE)
    matched_terms = set()
    for clause in clauses:
        text = clause.strip().lower()
        if not text or NEGATION_PATTERN.search(text):
            continue
        if manufacturing and any((phrase in text for phrase in BACKGROUND_PHRASES)):
            continue
        for terms in groups.values():
            for term in terms:
                if term_present(text, term):
                    matched_terms.add(term)
    total = 0
    evidence = []
    for (group_name, terms) in groups.items():
        matches = [(term, weight) for (term, weight) in terms.items() if term in matched_terms]
        if not matches:
            continue
        score = max((weight for (_, weight) in matches))
        total += score
        prefix = 'Manufacturing' if manufacturing else 'Software'
        for (term, _) in sorted(matches):
            evidence.append(f'{prefix}: {term}')
    return (total, evidence)

def classify_qa_job(description):
    """
    Classify a job using description evidence only.

    Returns:
        QA_Category
        Classification_Evidence
        Software_Score
        Manufacturing_Score

    Does not modify files or exclude jobs.
    """
    if not isinstance(description, str) or not description.strip():
        return {'QA_Category': 'Needs Verification', 'Classification_Evidence': '', 'Software_Score': 0, 'Manufacturing_Score': 0}
    (software_score, software_evidence) = _grouped_score(description, SOFTWARE_GROUPS)
    (manufacturing_score, manufacturing_evidence) = _grouped_score(description, MANUFACTURING_GROUPS, manufacturing=True)
    if software_score >= 5 and manufacturing_score < 6:
        category = 'Software QA'
    elif manufacturing_score >= 6 and software_score < 3:
        category = 'Manufacturing QA'
    else:
        category = 'Needs Verification'
    return {'QA_Category': category, 'Classification_Evidence': '; '.join(software_evidence + manufacturing_evidence), 'Software_Score': software_score, 'Manufacturing_Score': manufacturing_score}
