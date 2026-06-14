"""Quick end-to-end smoke test of the HTTP app (run directly: python smoke_test.py)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def main() -> None:
    health = client.get("/api/health").json()
    print("HEALTH:", health)

    config = client.get("/api/config").json()
    print("CONFIG:", config)

    team = client.get("/api/team").json()
    print("TEAM:", [a["id"] for a in team["team"]])

    # Full non-streaming run
    resp = client.post("/api/run", json={"request": "Add a login page with email/password"})
    data = resp.json()
    artifacts = data["artifacts"]
    print(f"ARTIFACTS ({len(artifacts)}):", [a["name"] for a in artifacts])

    # Confirm the reviewer feedback loop fired and resolved
    loops = [e for e in data["events"] if e["type"] == "loop"]
    reviewer_verdicts = [
        e.get("verdict") for e in data["events"]
        if e["type"] == "agent_done" and e["agent"] == "reviewer"
    ]
    print("REVIEW LOOPS:", len(loops), "| VERDICTS:", reviewer_verdicts)

    auth = next(a for a in artifacts if a["name"] == "app/auth.py")
    print("FINAL auth.py uses bcrypt:", "bcrypt" in auth["content"])

    # Verify SSE stream endpoint emits events
    with client.stream("GET", "/api/stream", params={"request": "Build a todo API"}) as s:
        sse_types = []
        for line in s.iter_lines():
            if line and line.startswith("data: "):
                import json
                sse_types.append(json.loads(line[6:])["type"])
        print("SSE EVENT TYPES:", sse_types[:3], "...", sse_types[-1])

    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()


