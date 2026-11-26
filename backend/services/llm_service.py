"""Generate local evidence-based operational reports without external AI APIs."""

from typing import Any, Dict, Tuple

LOCAL_REPORT_PROVIDER = "Local evidence-based template (not AI)"


def _value(value: Any, missing: str = "Not recorded") -> str:
    if value is None or not str(value).strip():
        return missing
    return str(value).strip()


def _historical_matches(matches: list[Dict[str, Any]]) -> str:
    if not matches:
        return "No stored historical precedents matched this event."

    lines = []
    for match in matches:
        score = match.get("similarity_percentage")
        score_text = f"{float(score):.1f}%" if isinstance(score, (int, float)) else "not calculated"
        lines.extend([
            f"- {_value(match.get('title'), 'Untitled precedent')} (text similarity: {score_text})",
            f"  Category: {_value(match.get('category'))}; location: {_value(match.get('location'))}",
        ])
    return "\n".join(lines)


def _historical_responses(matches: list[Dict[str, Any]]) -> str:
    if not matches:
        return "No operational responses or outcomes are recorded for matching precedents."
    return "\n".join(
        f"- {_value(match.get('title'), 'Untitled precedent')}: "
        f"response: {_value(match.get('previous_response'))}; "
        f"outcome: {_value(match.get('historical_outcome'))}"
        for match in matches
    )


def generate_brief(
    event: Dict[str, Any],
    comparison_data: Dict[str, Any],
) -> Tuple[str, str]:
    """Build a 13-section report from stored event facts and historical comparisons."""
    title = _value(event.get("title"), "Untitled disruption")
    source_name = _value(event.get("source_name"))
    source_url = _value(event.get("source_url"))
    description = _value(event.get("description"))
    severity_justification = _value(
        event.get("severity_justification"),
        "No severity justification is recorded.",
    )
    matches = comparison_data.get("similar_events", [])
    historical_summary = _historical_matches(matches)
    historical_responses = _historical_responses(matches)

    report = f"""LOGISTICSUPDATE — OPERATIONAL REPORT
Generated locally from stored application data. This is not an AI-generated report.

1. EXECUTIVE SUMMARY
{title}
Severity: {_value(event.get("severity"))} | Status: {_value(event.get("status"))}
Location: {_value(event.get("location"))}

2. CURRENT DISRUPTION DETAILS
Description: {description}
Published date: {_value(event.get("published_date"))}

3. DISRUPTION CATEGORY
{_value(event.get("category"))}

4. LOCATION
{_value(event.get("location"))}

5. SEVERITY AND JUSTIFICATION
Recorded severity: {_value(event.get("severity"))}
Recorded justification: {severity_justification}
The report does not independently verify the severity.

6. POTENTIAL OPERATIONAL IMPACT
The source record does not confirm specific operational impacts. Check affected routes,
facilities, shipments, and schedules with the responsible operators.

7. HISTORICAL EVENT COMPARISON
Matches are based on text similarity against historical events stored in this application.
They are not predictions or proof that events will have the same outcome.
{historical_summary}

8. PREVIOUS OPERATIONAL RESPONSES
{historical_responses}

9. KEY CHANGES AND DYNAMICS
The application has no verified event timeline for this record. Check the cited source
for updates before drawing conclusions about changes or recovery.

10. RECOMMENDED MONITORING ACTIONS
- Review the cited source for updates.
- Confirm operational status with the responsible authority or operator.
- Identify shipments and routes that may require follow-up.

11. OPERATIONAL CONSIDERATIONS
These are general review prompts, not confirmed impacts or event-specific instructions.
Use operator judgment before taking action.

12. SOURCE REFERENCES
Source: {source_name}
URL: {source_url}

13. DATA LIMITATIONS AND UNCERTAINTIES
This report is assembled by a local template, not generative AI. It uses the event record
and stored precedents available to the application. Missing fields are not inferred.
Similarity scores are text-matching results, not probabilities or forecasts.
"""
    return report, LOCAL_REPORT_PROVIDER
