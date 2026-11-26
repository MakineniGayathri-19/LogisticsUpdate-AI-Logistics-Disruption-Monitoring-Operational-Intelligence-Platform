"""Historical Event Comparison Service.
Implements TF-IDF vectorization and cosine similarity to benchmark
incoming disruptions against historical incidents.
Extracts nuanced comparisons, key differences, and actionable operational observations.
"""
import re
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils.logger import logger
from utils.validators import clean_text

def _extract_keywords(text: str) -> set:
    """Extract significant lowercase words filtering standard stopwords."""
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    stopwords = {
        "this", "that", "with", "from", "have", "been", "were", "what", "when",
        "where", "which", "will", "would", "could", "should", "their", "there",
        "about", "after", "before", "during", "while", "into", "through"
    }
    return {w for w in words if w not in stopwords}

def _analyze_differences(current: Dict[str, Any], historical: Dict[str, Any]) -> Dict[str, Any]:
    """Identify substantive similarities, key differences, and operational lessons."""
    cur_cat = current.get("category", "Other")
    hist_cat = historical.get("category", "Other")
    cur_loc = current.get("location", "Unspecified")
    hist_loc = historical.get("location", "Unspecified")
    cur_sev = current.get("severity", "Unknown")
    hist_sev = historical.get("severity", "Unknown")

    cur_kw = _extract_keywords(f"{current.get('title', '')} {current.get('description', '')}")
    hist_kw = _extract_keywords(f"{historical.get('title', '')} {historical.get('description', '')}")

    common_terms = list(cur_kw.intersection(hist_kw))[:5]
    distinct_cur = list(cur_kw - hist_kw)[:4]

    differences = []
    if cur_cat != hist_cat:
        differences.append(f"Category mismatch: Current is '{cur_cat}' whereas precedent was '{hist_cat}'.")
    if cur_loc != hist_loc:
        differences.append(f"Geographic variance: Occurred in '{cur_loc}' vs precedent in '{hist_loc}'.")
    if cur_sev != hist_sev:
        differences.append(f"Severity delta: Current rated '{cur_sev}' vs historical '{hist_sev}'.")
    if distinct_cur:
        differences.append(f"Current unique operational factors: {', '.join(distinct_cur)}.")

    observations = []
    if cur_cat == hist_cat and cur_loc.lower() in hist_loc.lower():
        observations.append("Direct precedent match: Same category and regional geography.")
    elif cur_cat == hist_cat:
        observations.append("Modal / Category precedent: Operational tactics from precedent can be adapted cross-region.")
    else:
        observations.append("Contextual precedent: Supply chain bottleneck patterns share logistical characteristics.")

    return {
        "common_factors": common_terms,
        "key_differences": differences or ["No major categorical divergence."],
        "operational_observations": observations
    }

def compare_disruption_with_history(current_event: Dict[str, Any], top_n: int = 3) -> Dict[str, Any]:
    """Compare a current disruption against all stored historical events.
    Uses TF-IDF feature matrix and cosine similarity scoring.
    """
    from database import repositories
    past_events = repositories.get_all_historical_events()

    if not past_events:
        return {
            "current_event": current_event,
            "similar_events": [],
            "message": "No historical events available for comparison."
        }

    cur_title = clean_text(current_event.get("title", ""))
    cur_desc = clean_text(current_event.get("description", ""))
    cur_cat = current_event.get("category", "")
    cur_loc = current_event.get("location", "")

    # Weighted query string
    cur_text = f"{cur_title} {cur_title} {cur_desc} {cur_cat} {cur_loc}".strip()
    if not cur_text:
        return {
            "current_event": current_event,
            "similar_events": [],
            "message": "Insufficient text content in current event to compute similarity."
        }

    corpus = [cur_text]
    valid_past = []

    cur_id = str(current_event.get("event_id") or current_event.get("id") or "")

    for pe in past_events:
        pe_id = str(pe.get("event_id") or pe.get("id") or "")
        # Prevent self comparison
        if cur_id and pe_id and cur_id == pe_id:
            continue
        p_title = clean_text(pe.get("title", ""))
        p_desc = clean_text(pe.get("description", ""))
        p_cat = pe.get("category", "")
        p_loc = pe.get("location", "")
        p_text = f"{p_title} {p_title} {p_desc} {p_cat} {p_loc}".strip()
        if p_text:
            corpus.append(p_text)
            valid_past.append(pe)

    if not valid_past:
        return {
            "current_event": current_event,
            "similar_events": [],
            "message": "No valid distinct historical precedents found."
        }

    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        tfidf = vectorizer.fit_transform(corpus)
        sim_scores = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()

        top_indices = sim_scores.argsort()[-top_n:][::-1]
        matches = []
        for idx in top_indices:
            score = float(sim_scores[idx])
            pe = valid_past[idx]
            diff_analysis = _analyze_differences(current_event, pe)

            matches.append({
                "similarity": score,
                "similarity_percentage": round(score * 100, 1),
                "event": pe,
                "title": pe.get("title"),
                "category": pe.get("category"),
                "location": pe.get("location"),
                "previous_response": pe.get("response", ""),
                "historical_outcome": pe.get("outcome", ""),
                "common_factors": diff_analysis["common_factors"],
                "key_differences": diff_analysis["key_differences"],
                "operational_observations": diff_analysis["operational_observations"]
            })

        return {
            "current_event": current_event,
            "similar_events": matches,
            "top_match_score": matches[0]["similarity"] if matches else 0.0
        }
    except Exception as e:
        logger.error(f"Error during TF-IDF comparison: {e}")
        return {
            "current_event": current_event,
            "similar_events": [],
            "error": str(e)
        }
