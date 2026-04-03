import re
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model once at module level (cached after first download)
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

SIMILARITY_THRESHOLD = 0.80
MIN_WORDS_FOR_TIMING  = 50
MIN_RESPONSE_SECONDS  = 60   # under 60 s for 50+ words = suspicious


# ── SEMANTIC SIMILARITY CHECK ─────────────────────────────────────────────────
BASELINE_AI_ANSWER = (
    "I have a comprehensive understanding of software engineering principles. "
    "I will delve into my experience with Python, machine learning, and cloud "
    "infrastructure to provide a thorough and detailed overview of my skill set. "
    "I am passionate about leveraging technology to solve real-world problems."
)


def check_ai_similarity(candidate_answer: str) -> dict:
    """
    Encodes the candidate answer and a known AI-generated baseline,
    then computes cosine similarity. Flags if > SIMILARITY_THRESHOLD.
    """
    embeddings = MODEL.encode([candidate_answer, BASELINE_AI_ANSWER])
    similarity = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
    flagged    = similarity > SIMILARITY_THRESHOLD

    return {
        "check":      "ai_similarity",
        "similarity": round(similarity, 4),
        "threshold":  SIMILARITY_THRESHOLD,
        "flagged":    flagged,
        "reason":     (
            f"Answer is {similarity:.1%} similar to known AI-generated baseline "
            f"(threshold: {SIMILARITY_THRESHOLD:.0%})"
            if flagged
            else "Passed — answer appears original"
        ),
    }


# ── TIMING ANALYSIS ───────────────────────────────────────────────────────────
def check_timing(
    answer: str,
    question_sent_at: datetime,
    answer_received_at: datetime,
) -> dict:
    """
    Flags if a response of > MIN_WORDS_FOR_TIMING words was submitted
    in less than MIN_RESPONSE_SECONDS seconds.
    """
    word_count       = len(answer.split())
    elapsed_seconds  = (answer_received_at - question_sent_at).total_seconds()
    flagged          = (word_count > MIN_WORDS_FOR_TIMING and elapsed_seconds < MIN_RESPONSE_SECONDS)

    return {
        "check":           "timing_analysis",
        "word_count":      word_count,
        "elapsed_seconds": round(elapsed_seconds, 1),
        "flagged":         flagged,
        "reason":          (
            f"Impossibly fast: {word_count} words submitted in {elapsed_seconds:.0f}s "
            f"(minimum expected: {MIN_RESPONSE_SECONDS}s)"
            if flagged
            else f"Timing OK: {word_count} words in {elapsed_seconds:.0f}s"
        ),
    }


# ── COMBINED EVALUATION ───────────────────────────────────────────────────────
def evaluate_candidate(
    name: str,
    answer: str,
    question_sent_at: datetime,
    answer_received_at: datetime,
) -> dict:
    similarity_result = check_ai_similarity(answer)
    timing_result     = check_timing(answer, question_sent_at, answer_received_at)
    overall_flagged   = similarity_result["flagged"] or timing_result["flagged"]

    return {
        "candidate":        name,
        "overall_flagged":  overall_flagged,
        "checks":           [similarity_result, timing_result],
    }


def print_report(result: dict):
    status = "🚨 FLAGGED" if result["overall_flagged"] else "✅ CLEAR"
    print(f"\n{'=' * 60}")
    print(f"  Candidate : {result['candidate']}")
    print(f"  Status    : {status}")
    print(f"{'=' * 60}")
    for check in result["checks"]:
        flag_icon = "⚠" if check["flagged"] else "✓"
        print(f"  [{flag_icon}] {check['check'].replace('_', ' ').title()}")
        print(f"       → {check['reason']}")
    print()


# ── DEMO ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    now = datetime.now()

    candidates = [
        {
            "name": "Suspect Sam",
            "answer": (
                "I have a comprehensive understanding of software engineering. "
                "I will delve into my Python and machine learning experience to "
                "provide a thorough overview. I leverage technology to solve problems."
            ),
            "sent":     now - timedelta(seconds=30),
            "received": now,
        },
        {
            "name": "Genuine Gary",
            "answer": (
                "I built a distributed task queue using Redis and Celery to handle "
                "async jobs at scale. I debugged a memory leak by profiling with "
                "py-spy and resolved it by fixing generator exhaustion in a pipeline."
            ),
            "sent":     now - timedelta(minutes=8),
            "received": now,
        },
        {
            "name": "Fast Fiona",
            "answer": (
                "I architected a microservices platform with 12 independent services "
                "communicating over gRPC, implemented circuit breakers using Hystrix, "
                "wrote comprehensive integration tests with pytest-asyncio, and "
                "deployed everything to Kubernetes with Helm charts and ArgoCD."
            ),
            "sent":     now - timedelta(seconds=20),
            "received": now,
        },
    ]

    print("\n🔍 ANTI-CHEAT MODULE — RUNNING EVALUATIONS\n")
    for c in candidates:
        result = evaluate_candidate(c["name"], c["answer"], c["sent"], c["received"])
        print_report(result)