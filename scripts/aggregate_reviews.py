import os
import json
import requests
from collections import defaultdict

# --- Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
PR_NUMBER = os.environ.get("PULL_REQUEST_NUMBER")

TOOL_IDENTIFIERS = {
    'CodeRabbit': 'coderabbitai[bot]',
    'BitoAI': 'bito-ai-bot',
    'Codacy': 'codacy-production[bot]',
    'GitHub Copilot': 'github-actions[bot]',
    'devotiontoc': 'devotiontoc'
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

    # 2. Group comments and gather stats in a single loop
    unrecognized_authors = set()
    findings_map = defaultdict(list)
    comment_lengths = defaultdict(list)

    for comment in comments:
        author = comment.get('user', {}).get('login')
        current_tool = next((name for name, id in TOOL_IDENTIFIERS.items() if id == author), None)

        if not current_tool:
            if author and '[bot]' in author and author not in KNOWN_BOT_IDS:
                unrecognized_authors.add(author)
            continue

        file_path = comment.get('path')
        line = comment.get('line')
        comment_body = comment.get('body', '')

        finding_key = ""
        if file_path:
            finding_key = f"{file_path}:{line or 'general'}"
        else:
            finding_key = "General PR Comments"

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

        file_path = location.split(':')[0]
        if file_path != "General PR Comments":
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
            "pr_number": PR_NUMBER,
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
        print("Error: Missing required environment variables.")
        exit(1)
    run_aggregation()