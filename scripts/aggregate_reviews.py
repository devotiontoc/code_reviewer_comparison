import os
import json
import re
from datetime import datetime, timezone
from collections import defaultdict
from itertools import combinations
import requests

# --- Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
PR_NUMBER = os.environ.get("PULL_REQUEST_NUMBER")

TOOL_IDENTIFIERS = {
    'CodeRabbit': 'coderabbitai[bot]',
    'BitoAI': 'bito-code-review[bot]',
    'Codacy': 'codacy-production[bot]',
    'GitHub Copilot': 'copilot-pull-request-reviewer[bot]',
    'devotiontoc': 'devotiontoc',
    'Copilot' : 'Copilot'

}
TOOLS = list(TOOL_IDENTIFIERS.keys())
KNOWN_BOT_IDS = set(TOOL_IDENTIFIERS.values())

# --- Helper Functions ---
def fetch_github_api(url):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_iso_timestamp(ts_str):
    return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))

def jaccard_similarity(set1, set2):
    """Calculates Jaccard similarity between two sets of words."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)

def get_words(text):
    return set(re.findall(r'\w+', text.lower()))

def categorize_comment(comment_text):
    text = comment_text.lower()
    if any(kw in text for kw in ['security', 'vulnerability', 'cve', 'sql injection', 'xss', 'hardcoded secret']):
        return "Security"
    if any(kw in text for kw in ['performance', 'slow', 'efficient', 'optimize']):
        return "Performance"
    if any(kw in text for kw in ['bug', 'error', 'null pointer', 'exception', 'leak']):
        return "Bug"
    return "Style / Best Practice"

# --- Main Logic ---
def run_aggregation():
    base_api_url = f"https://api.github.com/repos/{REPO_NAME}"

    pr_data = fetch_github_api(f"{base_api_url}/pulls/{PR_NUMBER}")
    if not pr_data:
        print("Failed to fetch PR data. Aborting.")
        return
    pr_created_at = parse_iso_timestamp(pr_data['created_at'])

    review_comments = fetch_github_api(f"{base_api_url}/pulls/{PR_NUMBER}/comments") or []
    review_summaries = fetch_github_api(f"{base_api_url}/pulls/{PR_NUMBER}/reviews") or []
    issue_comments = fetch_github_api(f"{base_api_url}/issues/{PR_NUMBER}/comments") or []
    all_comments = review_comments + review_summaries + issue_comments
    print(f"Successfully fetched a total of {len(all_comments)} comments and review summaries.")

    findings_map = defaultdict(list)
    comment_lengths = defaultdict(list)
    review_times = defaultdict(list)

    for item in all_comments:
        author = item.get('user', {}).get('login')
        current_tool = next((name for name, id in TOOL_IDENTIFIERS.items() if id == author), None)
        if not current_tool:
            continue

        comment_body = item.get('body', '')
        if not comment_body:
            continue

        timestamp_str = item.get('created_at') or item.get('submitted_at')
        if not timestamp_str:
            continue
        comment_created_at = parse_iso_timestamp(timestamp_str)
        time_to_comment = (comment_created_at - pr_created_at).total_seconds()
        review_times[current_tool].append(time_to_comment)

        original_code, suggested_code = None, None
        suggestion_match = re.search(r"```suggestion\r?\n(.*?)\r?\n```", comment_body, re.DOTALL)
        if suggestion_match:
            suggested_code = suggestion_match.group(1)
            if 'diff_hunk' in item:
                original_code_lines = [line[1:] for line in item['diff_hunk'].split('\n') if line.startswith('-') and not line.startswith('---')]
                original_code = '\n'.join(original_code_lines)

        file_path = item.get('path')
        line = item.get('line') or item.get('start_line')
        finding_key = f"{file_path}:{line}" if file_path and line else "General PR Summary"

        findings_map[finding_key].append({
            "tool": current_tool, "comment": comment_body, "original_code": original_code, "suggested_code": suggested_code
        })
        comment_lengths[current_tool].append(len(comment_body))

    processed_findings = []
    category_counts = defaultdict(int)
    tool_finding_counts = defaultdict(int)
    findings_per_file = defaultdict(int)
    overlap_counts = defaultdict(int)

    for location, reviews in findings_map.items():
        review_tools = {review['tool'] for review in reviews}
        if len(review_tools) > 1:
            for r1, r2 in combinations(reviews, 2):
                if r1['tool'] == r2['tool']: continue

                comment1_words = get_words(r1['comment'])
                comment2_words = get_words(r2['comment'])
                if jaccard_similarity(comment1_words, comment2_words) > 0.4:
                    overlap_key = tuple(sorted([r1['tool'], r2['tool']]))
                    overlap_counts[overlap_key] += 1

        all_comments_text = " ".join([r['comment'] for r in reviews])
        category = categorize_comment(all_comments_text)
        category_counts[category] += 1

        if location != "General PR Summary":
            file_path = location.split(':')[0]
            findings_per_file[file_path] += 1

        for review in reviews:
            tool_finding_counts[review['tool']] += 1

        processed_findings.append({
            "location": location, "category": category, "reviews": reviews
        })

    # --- START: FIXED DATA ALIGNMENT ---
    # Helper to calculate average, ensuring alignment with the TOOLS list
    def get_avg(data_dict, key):
        items = data_dict.get(key, [])
        return round(sum(items) / len(items)) if items else 0

    # Build data lists by iterating over the canonical TOOLS list to guarantee order
    avg_comment_lengths = [get_avg(comment_lengths, tool) for tool in TOOLS]
    avg_review_times_seconds = [get_avg(review_times, tool) for tool in TOOLS]
    # --- END: FIXED DATA ALIGNMENT ---

    venn_data = []
    for tools_tuple, count in overlap_counts.items():
        venn_data.append({"sets": list(tools_tuple), "size": count})
    for tool in TOOLS:
        unique_count = tool_finding_counts.get(tool, 0) - sum(c for t, c in overlap_counts.items() if tool in t)
        if unique_count > 0:
            venn_data.append({"sets": [tool], "size": unique_count})

    final_output = {
        "metadata": {"repo": REPO_NAME, "pr_number": int(PR_NUMBER), "tool_names": TOOLS},
        "summary_charts": {
            "findings_by_tool": [tool_finding_counts.get(tool, 0) for tool in TOOLS],
            "findings_by_category": {"labels": list(category_counts.keys()), "data": list(category_counts.values())},
            "comment_verbosity": {"labels": TOOLS, "data": avg_comment_lengths},
            "findings_by_file": {"labels": list(findings_per_file.keys()), "data": list(findings_per_file.values())},
            "review_speed": {"labels": TOOLS, "data": avg_review_times_seconds},
            "suggestion_overlap": venn_data
        },
        "findings": processed_findings
    }

    output_path = 'docs/results.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    print(f"Aggregation complete. Results saved to {output_path}")

if __name__ == "__main__":
    if not all([GITHUB_TOKEN, REPO_NAME, PR_NUMBER]):
        print("Error: Missing required environment variables.")
        exit(1)
    run_aggregation()