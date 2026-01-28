import requests
import sys

API_URL = "http://localhost:8000/api/query"  # Adjust if your server runs elsewhere


def test_query(user_id=1, query_text="Explain quantum entanglement in simple terms. Also, compare it to classical physics and give a real-world analogy.", provider_ids=None):
    import json
    if provider_ids is None:
        provider_ids = ["groq", "gemini", "mistral", "cerebras", "cohere", "huggingface"]
    payload = {
        "user_id": user_id,
        "query_text": query_text,
        "provider_ids": provider_ids
    }
    resp = requests.post(API_URL, json=payload)
    try:
        resp.raise_for_status()
    except Exception as e:
        print(f"HTTP error: {e}\nResponse: {resp.text}")
        return
    data = resp.json()
    print("Final Answer:\n", data.get("final_answer"))
    print("\nPer-Provider Responses:")
    responses = data.get("responses", {})
    if isinstance(responses, dict):
        for r, resp in responses.items():
            print(f"- {r}: {resp.get('response_text')}")
        print("\nErrors:")
        for r, resp in responses.items():
            if resp.get('status') == 'error':
                print(f"- {r}: {resp.get('error_message')}")
    else:
        print("(No responses or unexpected format)")
    print("\nFull JSON Response:")
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Explain quantum entanglement in simple terms. Also, compare it to classical physics and give a real-world analogy."
    test_query(query_text=query)
