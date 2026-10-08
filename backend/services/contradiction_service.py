from __future__ import annotations

import re
from typing import Sequence

from rapidfuzz import fuzz

from backend.models.schemas import Claim, Evidence, Finding, QuoteRef

_STOP_WORDS = {
	"about", "after", "against", "also", "been", "before", "being", "from",
	"have", "into", "just", "more", "most", "over", "said", "same", "that",
	"their", "them", "then", "there", "these", "they", "this", "those", "were",
	"when", "which", "with", "would",
}
_NEGATIONS = {"no", "not", "never", "neither", "without", "absent", "denied"}
_OPPOSITES = (
	("intact", "damaged"),
	("intact", "broken"),
	("present", "missing"),
	("covered", "excluded"),
	("approved", "rejected"),
	("paid", "unpaid"),
	("before", "after"),
	("within", "outside"),
	("authorized", "unauthorized"),
	("compliant", "noncompliant"),
)


def _tokens(text: str) -> set[str]:
	return {
		token
		for token in re.findall(r"[a-z0-9]+", text.lower())
		if (len(token) > 2 or token in _NEGATIONS) and token not in _STOP_WORDS
	}


def _opposes(claim_text: str, evidence_text: str) -> bool:
	claim_tokens = _tokens(claim_text)
	evidence_tokens = _tokens(evidence_text)
	if bool(claim_tokens & _NEGATIONS) != bool(evidence_tokens & _NEGATIONS):
		return True
	return any(
		(left in claim_tokens and right in evidence_tokens)
		or (right in claim_tokens and left in evidence_tokens)
		for left, right in _OPPOSITES
	)


def detect_contradictions(
	claims: Sequence[Claim], evidence: Sequence[Evidence]
) -> list[Finding]:
	"""Return conservative claim/evidence conflicts with links to their source quotes.

	A candidate is emitted only when the texts share enough topic terms and have an
	explicit negation or a known opposing term. The source quote verification flags
	are preserved, so unverified extraction never becomes scoreable evidence.
	"""
	findings: list[Finding] = []
	for claim in claims:
		for item in evidence:
			claim_terms = _tokens(claim.text)
			evidence_terms = _tokens(item.text)
			shared_terms = claim_terms & evidence_terms
			if len(shared_terms) < 2 or not _opposes(claim.text, item.text):
				continue
			similarity = fuzz.token_set_ratio(claim.text, item.text)
			if similarity < 35:
				continue

			finding_id = f"contradiction:{claim.id}:{item.id}"
			findings.append(
				Finding(
					id=finding_id,
					finding_type="contradiction",
					source="rule",
					severity="medium" if similarity >= 55 else "low",
					favors="user" if claim.speaker == "company" else "neutral",
					explanation=(
						"The claim and evidence share topic terms but contain opposing "
						"wording. Review both source documents before drawing a conclusion."
					),
					left_item_id=claim.id,
					right_item_id=item.id,
					quotes=[
						QuoteRef(
							doc_id=claim.source_doc_id,
							page=claim.page,
							quote=claim.quote,
							verified=claim.quote_verified,
						),
						QuoteRef(
							doc_id=item.source_doc_id,
							page=item.page,
							quote=item.quote,
							verified=item.quote_verified,
						),
					],
				)
			)
	return findings
