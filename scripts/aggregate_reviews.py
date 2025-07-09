import os
import json
import requests
from collections import defaultdict

# --- Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
PR_NUMBER = os.environ.get("PULL_REQUEST_NUMBER")

# Define the login usernames for the AI tools
TOOL_IDENTIFIERS = {
    'CodeRabbit': 'coderabbitai[bot]',
    'BitoAI': 'bito-ai-bot',
    'Codacy': 'codacy-production[bot]',
    'GitHub Copilot': 'github-actions[bot]',
    'devotiontoc': 'devotiontoc',
    'Copilot' : 'Copilot'
}
TOOLS = list(TOOL_IDENTIFIERS.keys())
KNOWN_BOT_IDS = set(TOOL_IDENTIFIERS.values())

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

def fetch_github_api(url):
    """Helper function to fetch data from the GitHub API."""
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

# --- Main Logic ---
def run_aggregation():
    # 1. Fetch all types of comments and reviews
    base_api_url = f"https://api.github.com/repos/{REPO_NAME}"
    review_comments = fetch_github_api(f"{base_api_url}/pulls/{PR_NUMBER}/comments") or []
    review_summaries = fetch_github_api(f"{base_api_url}/pulls/{PR_NUMBER}/reviews") or []
    issue_comments = fetch_github_api(f"{base_api_url}/issues/{PR_NUMBER}/comments") or []

    all_comments = review_comments + review_summaries + issue_comments
    print(f"Successfully fetched a total of {len(all_comments)} comments and review summaries.")

    # 2. Group comments and gather stats in a single loop
    unrecognized_authors = set()
    findings_map = defaultdict(list)
    comment_lengths = defaultdict(list)

    for item in all_comments:
        author = item.get('user', {}).get('login')
        current_tool = next((name for name, id in TOOL_IDENTIFIERS.items() if id == author), None)

        if not current_tool:
            if author and '[bot]' in author and author not in KNOWN_BOT_IDS:
                unrecognized_authors.add(author)
            continue

        comment_body = item.get('body', '')
        # Skip empty review summaries
        if not comment_body:
            continue

        # For inline comments, location is file:line. Otherwise, it's a general comment.
        file_path = item.get('path')
        line = item.get('line') or item.get('start_line')

        if file_path and line:
            finding_key = f"{file_path}:{line}"
        else:
            finding_key = "General PR Summary"

        findings_map[finding_key].append({
            "tool": current_tool,
            "comment": comment_body
        })

        comment_lengths[current_tool].append(len(comment_body))

    # 3. Process grouped findings into a structured list
    processed_findings = []
    category_counts = defaultdict(int)
    tool_finding_counts = defaultdict(int)
    findings_per_file = defaultdict(int)

    for location, reviews in findings_map.items():
        all_comments_text = " ".join([r['comment'] for r in reviews])
        category = categorize_comment(all_comments_text)
        category_counts[category] += 1

        if location != "General PR Summary":
            file_path = location.split(':')[0]
            findings_per_file[file_path] += 1

        for review in reviews:
            tool_finding_counts[review['tool']] += 1

        processed_findings.append({
            "location": location,
            "category": category,
            "reviews": reviews
        })

    # 4. Calculate final stats for charts
    avg_comment_lengths = []
    for tool in TOOLS:
        lengths = comment_lengths.get(tool, [])
        avg = sum(lengths) / len(lengths) if lengths else 0
        avg_comment_lengths.append(round(avg))

    # 5. Assemble the final JSON output
    final_output = {
        "metadata": {
            "repo": REPO_NAME,
            "pr_number": int(PR_NUMBER),
            "tool_names": TOOLS
        },
        "summary_charts": {
            "findings_by_tool": [tool_finding_counts.get(tool, 0) for tool in TOOLS],
            "findings_by_category": {
                "labels": list(category_counts.keys()),
                "data": list(category_counts.values())
            },
            "comment_verbosity": {
                "labels": TOOLS,
                "data": avg_comment_lengths
            },
            "findings_by_file": {
                "labels": list(findings_per_file.keys()),
                "data": list(findings_per_file.values())
            }
        },
        "findings": processed_findings
    }

    if unrecognized_authors:
        print("\n--- Found Unrecognized Bot Authors ---")
        print("Consider adding these to the TOOL_IDENTIFIERS dictionary in your script:")
        for author in unrecognized_authors:
            print(f"- {author}")
        print("-------------------------------------\n")

    # 6. Save results to a file
    output_path = 'docs/results.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    print(f"Aggregation complete. Results saved to {output_path}")

if __name__ == "__main__":
    if not all([GITHUB_TOKEN, REPO_NAME, PR_NUMBER]):
        print("Error: Missing required environment variables: GITHUB_TOKEN, GITHUB_REPOSITORY, PULL_REQUEST_NUMBER.")
        exit(1)
    run_aggregation()