import pandas as pd
import numpy as np
import re
import sys

# ── CONFIG ──────────────────────────────────────────────────────────────────
AI_BOILERPLATE = [
    "delve into", "comprehensive overview", "leverage synergies",
    "in conclusion", "it is important to note", "as an ai language model",
    "i hope this helps", "please let me know if you have any questions",
    "utilize", "utilize my skills", "passionate about technology",
]

TIER_THRESHOLDS = {
    "Fast-Track": 70,
    "Standard":   45,
    "Review":     25,
}

# ── SCORING ──────────────────────────────────────────────────────────────────
def score_candidate(row: pd.Series) -> tuple[float, list[str]]:
    score = 50.0
    reasons = []

    # Penalize missing GitHub
    github = str(row.get("github", "")).strip()
    if not github or github.lower() in ("nan", "none", ""):
        score -= 20
        reasons.append("PENALTY -20: No GitHub link provided")
    else:
        score += 10
        reasons.append("BONUS +10: GitHub profile present")

    # Penalize AI boilerplate phrases
    answer = str(row.get("answer", "")).lower()
    found_boilerplate = [p for p in AI_BOILERPLATE if p in answer]
    if found_boilerplate:
        deduction = min(len(found_boilerplate) * 8, 30)
        score -= deduction
        reasons.append(
            f"PENALTY -{deduction}: AI boilerplate detected → {found_boilerplate}"
        )

    # Reward code snippets
    code_blocks = re.findall(r"```[\s\S]*?```", str(row.get("answer", "")))
    inline_code = re.findall(r"`[^`]+`", str(row.get("answer", "")))
    if code_blocks:
        bonus = min(len(code_blocks) * 15, 30)
        score += bonus
        reasons.append(f"BONUS +{bonus}: {len(code_blocks)} code block(s) found")
    elif inline_code:
        score += 5
        reasons.append(f"BONUS +5: Inline code references found")

    # Penalize empty or very short answers
    # Strip code blocks before counting prose words to avoid undercounting
    prose_only = re.sub(r"```[\s\S]*?```", "", str(row.get("answer", "")))
    prose_only = re.sub(r"`[^`]+`", "", prose_only)
    word_count = len(prose_only.split())
    if word_count < 5:
        score -= 25
        reasons.append("PENALTY -25: Answer is empty or too short")
    elif word_count < 20:
        score -= 10
        reasons.append("PENALTY -10: Answer prose is very brief (<20 words, excluding code)")

    # Penalize missing email
    email = str(row.get("email", "")).strip()
    if not email or email.lower() in ("nan", "none", ""):
        score -= 10
        reasons.append("PENALTY -10: Missing email address")

    score = max(0.0, min(100.0, score))
    return round(score, 2), reasons


def assign_tier(score: float) -> str:
    if score >= TIER_THRESHOLDS["Fast-Track"]:
        return "Fast-Track"
    elif score >= TIER_THRESHOLDS["Standard"]:
        return "Standard"
    elif score >= TIER_THRESHOLDS["Review"]:
        return "Review"
    else:
        return "Reject"


# ── MAIN ──────────────────────────────────────────────────────────────────────
def run(csv_path: str = "dummy_data.csv"):
    # Load & clean
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()

    for col in ["name", "email", "github", "answer"]:
        if col not in df.columns:
            df[col] = ""
    df.fillna("", inplace=True)
    df = df[df["name"].str.strip() != ""]   # drop rows with no name

    results = []
    for _, row in df.iterrows():
        score, reasons = score_candidate(row)
        tier = assign_tier(score)
        results.append(
            {
                "name":    row["name"],
                "email":   row["email"],
                "score":   score,
                "tier":    tier,
                "reasons": " | ".join(reasons),
            }
        )

    results_df = (
        pd.DataFrame(results)
        .sort_values("score", ascending=False)
        .reset_index(drop=True)
    )
    results_df.index += 1  # 1-based rank

    output_path = "scored_candidates.csv"
    results_df.to_csv(output_path, index_label="rank")

    # ── Pretty Print ──
    print("\n" + "=" * 72)
    print("  HIRING AGENT — CANDIDATE SCORING REPORT")
    print("=" * 72)
    tier_order = ["Fast-Track", "Standard", "Review", "Reject"]
    for tier in tier_order:
        tier_df = results_df[results_df["tier"] == tier]
        if tier_df.empty:
            continue
        print(f"\n▶ {tier.upper()} ({len(tier_df)} candidate(s))")
        print("-" * 72)
        for rank, row in tier_df.iterrows():
            print(f"  #{rank:<3} {row['name']:<20} Score: {row['score']:>6}  |  {row['email']}")
            for reason in row["reasons"].split(" | "):
                print(f"        → {reason}")
    print("\n" + "=" * 72)
    print(f"  Full results saved to: {output_path}")
    print("=" * 72 + "\n")

    return results_df


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "dummy_data.csv"
    run(csv_file)