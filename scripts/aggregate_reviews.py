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
def fetch_github_api_paginated(url):
    """Fetches all pages for a given GitHub API endpoint."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    results = []
    while url:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            results.extend(response.json())
            # Get the URL for the next page, if it exists
            url = response.links.get('next', {}).get('url')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    return results

def parse_iso_timestamp(ts_str):
    if not ts_str:
        return None
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

    pr_data = fetch_github_api_paginated(f"{base_api_url}/pulls/{PR_NUMBER}")
    if not isinstance(pr_data, dict): # The non-paginated version returns a dict
        _pr_data_single = requests.get(f"{base_api_url}/pulls/{PR_NUMBER}", headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}).json()
        pr_created_at = parse_iso_timestamp(_pr_data_single['created_at'])
    else:
        pr_created_at = parse_iso_timestamp(pr_data['created_at'])

    if not pr_created_at:
        print("Failed to fetch PR creation date. Aborting.")
        return

    # 1. Fetch all top-level review comments (line comments)
    review_comments = fetch_github_api_paginated(f"{base_api_url}/pulls/{PR_NUMBER}/comments") or []

    # 2. Fetch all general issue-level comments
    issue_comments = fetch_github_api_paginated(f"{base_api_url}/issues/{PR_NUMBER}/comments") or []

    # 3. Fetch all review submissions. These are containers for the main review body AND associated comments.
    reviews = fetch_github_api_paginated(f"{base_api_url}/pulls/{PR_NUMBER}/reviews") or []

    # Use a dictionary to store all comments by their unique ID to prevent duplicates
    all_items = {}

    # Add all fetched items to the dictionary
    for item in review_comments + issue_comments:
        all_items[item['id']] = item

    for review in reviews:
        # A) Add the main review body as a "general" comment
        if review.get('body'):
            # This is a review summary, not a line comment. We treat it as a unique item.
            all_items[f"review-summary-{review['id']}"] = review

        # B) Fetch the line comments associated with THIS specific review submission
        # This is a crucial step to get comments posted as part of a single bulk review
        review_specific_comments = fetch_github_api_paginated(f"{base_api_url}/pulls/{PR_NUMBER}/reviews/{review['id']}/comments") or []
        for comment in review_specific_comments:
            all_items[comment['id']] = comment

    final_comments = list(all_items.values())
    print(f"Successfully fetched a total of {len(final_comments)} unique comments and review summaries.")

    findings_map = defaultdict(list)
    comment_lengths = defaultdict(list)
    review_times = defaultdict(list)

    for item in final_comments:
        author = item.get('user', {}).get('login')
        current_tool = next((name for name, id in TOOL_IDENTIFIERS.items() if id == author), None)
        if not current_tool:
            continue

        comment_body = item.get('body', '')
        if not comment_body:
            continue

        timestamp_str = item.get('submitted_at') or item.get('created_at')
        comment_created_at = parse_iso_timestamp(timestamp_str)
        if not comment_created_at:
            continue

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

    for location, reviews_list in findings_map.items():
        review_tools = {review['tool'] for review in reviews_list}
        if len(review_tools) > 1:
            for tool_pair in combinations(sorted(list(review_tools)), 2):
                overlap_counts[tool_pair] += 1

        all_comments_text = " ".join([r['comment'] for r in reviews_list])
        category = categorize_comment(all_comments_text)
        category_counts[category] += 1

        if location != "General PR Summary":
            file_path = location.split(':')[0]
            findings_per_file[file_path] += 1

        for review in reviews_list:
            tool_finding_counts[review['tool']] += 1

        processed_findings.append({
            "location": location, "category": category, "reviews": reviews_list
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