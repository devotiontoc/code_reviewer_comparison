import os
import json
import requests
from collections import defaultdict

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
PR_NUMBER = os.environ.get("PULL_REQUEST_NUMBER")
print("GITHUB_TOKEN: "+GITHUB_TOKEN)
print("REPO_NAME: "+REPO_NAME)
print("PR_NUMBER: "+PR_NUMBER)

TOOL_IDENTIFIERS = {
    'CodeRabbit': 'coderabbitai[bot]',
    'BitoAI': 'bitoai[bot]'
}
TOOLS = list(TOOL_IDENTIFIERS.keys())

def categorize_comment(comment_text):
    """Assigns a category based on keywords. This is a simple heuristic."""
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
    # 1. Fetch comments from GitHub API
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{REPO_NAME}/pulls/{PR_NUMBER}/comments"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        comments = response.json()
        print(f"Successfully fetched {len(comments)} review comments.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching comments: {e}")
        return

    # 2. Group comments by location (file:line)
    findings_map = defaultdict(list)
    for comment in comments:
        author = comment.get('user', {}).get('login')
        file_path = comment.get('path')
        line = comment.get('line')

        current_tool = next((name for name, id in TOOL_IDENTIFIERS.items() if id == author), None)
        if not all([current_tool, file_path, line]):
            continue

        finding_key = f"{file_path}:{line}"
        findings_map[finding_key].append({
            "tool": current_tool,
            "comment": comment.get('body', '')
        })

    # 3. Process grouped findings into a structured list
    processed_findings = []
    category_counts = defaultdict(int)
    tool_finding_counts = defaultdict(int)

    for location, reviews in findings_map.items():
        # Combine all comments for categorization
        all_comments_text = " ".join([r['comment'] for r in reviews])
        category = categorize_comment(all_comments_text)
        category_counts[category] += 1

        for review in reviews:
            tool_finding_counts[review['tool']] += 1

        processed_findings.append({
            "location": location,
            "category": category,
            "reviews": reviews
        })

    # 4. Assemble the final JSON output
    final_output = {
        "metadata": {
            "repo": REPO_NAME,
            "pr_number": PR_NUMBER,
            "tool_names": TOOLS
        },
        "summary_charts": {
            "findings_by_tool": [tool_finding_counts.get(tool, 0) for tool in TOOLS],
            "findings_by_category": {
                "labels": list(category_counts.keys()),
                "data": list(category_counts.values())
            }
        },
        "findings": processed_findings
    }

    # 5. Save results to a file
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