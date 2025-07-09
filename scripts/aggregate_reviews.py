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

# Using standard single quotes for all strings
TOOL_IDENTIFIERS = {
    'CodeRabbit': 'coderabbitai[bot]',
    'BitoAI': 'bito-code-review[bot]',
    'Codacy': 'codacy-production[bot]',
    'GitHub Copilot': 'copilot-pull-request-reviewer[bot]',
    'devotiontoc': 'devotiontoc'

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
            for tool_pair in combinations(sorted(list(review_tools)), 2):
                overlap_counts[tool_pair] += 1

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

    def get_avg(data_dict, key):
        items = data_dict.get(key, [])
        return round(sum(items) / len(items)) if items else 0

    avg_comment_lengths = [get_avg(comment_lengths, tool) for tool in TOOLS]
    avg_review_times_seconds = [get_avg(review_times, tool) for tool in TOOLS]

    overlap_data_for_json = [{"sets": list(tools_tuple), "size": count} for tools_tuple, count in overlap_counts.items()]

    final_output = {
        "metadata": {"repo": REPO_NAME, "pr_number": int(PR_NUMBER), "tool_names": TOOLS},
        "summary_charts": {
            "findings_by_tool": [tool_finding_counts.get(tool, 0) for tool in TOOLS],
            "findings_by_category": {"labels": list(category_counts.keys()), "data": list(category_counts.values())},
            "comment_verbosity": {"labels": TOOLS, "data": avg_comment_lengths},
            "findings_by_file": {"labels": list(findings_per_file.keys()), "data": list(findings_per_file.values())},
            "review_speed": {"labels": TOOLS, "data": avg_review_times_seconds},
            "suggestion_overlap": overlap_data_for_json
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