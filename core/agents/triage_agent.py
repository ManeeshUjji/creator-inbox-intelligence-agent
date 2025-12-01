
from typing import Dict, Any, Optional

from core.tools.code_execution_tool import exec_read_csv, exec_write_csv
from core.tools.kb_search_tool import search_kb
from core.agents.types import Email, TriageResult


class TriageAgent:
    """
    TriageAgent

    Responsibilities:
    - Take a single Email.
    - Decide category + priority using simple rules (and optionally KB hints).
    - Optionally suggest a ticket (follow-up task).
    - Write the updated category/priority back into inbox.csv via code_execution_tool.

    Interface:
    - __init__()
    - run(email: Email) -> TriageResult
    """

    def __init__(self):
        # you can add config here later if needed
        pass

    # --------- PUBLIC API ---------
    def run(self, email: Email) -> TriageResult:
        """
        Run triage on a single email.

        1. Infer category + priority using simple rules.
        2. Optionally use KB search for spam / policy hints.
        3. Update inbox.csv for this email_id.
        4. Return a TriageResult.
        """
        category = self._infer_category(email)
        priority = self._infer_priority(email, category)

        ticket_suggestion = self._maybe_suggest_ticket(email, category, priority)

        # Write back to inbox.csv
        self._update_inbox_row(email.email_id, category, priority)

        return TriageResult(
            email_id=email.email_id,
            category=category,
            priority=priority,
            ticket_suggestion=ticket_suggestion,
        )

    # --------- INTERNAL HELPERS ---------
    def _infer_category(self, email: Email) -> str:
        text = f"{email.subject} {email.body_text}".lower()

        # Brand / sponsorship
        if any(word in text for word in ["sponsor", "sponsorship", "brand deal", "partnership", "campaign", "integration"]):
            # Very simple: assume new inquiry vs negotiation
            if any(word in text for word in ["follow up", "renegotiate", "counter", "rate change", "update terms"]):
                return "Brand/Sponsorship – Negotiation & Follow-up"
            return "Brand/Sponsorship – New Inquiry"

        # Creator collaboration
        if any(word in text for word in ["collab", "collaboration", "collaborate", "duet", "co-create"]):
            return "Creator Collaboration"

        # UGC / content
        if any(word in text for word in ["ugc", "user-generated", "whitelisting", "usage rights"]):
            return "UGC / Content Creation Request"

        # PR / media / interviews
        if any(word in text for word in ["interview", "press", "media request", "podcast", "feature you", "article about you"]):
            return "PR / Media / Interviews"

        # Events / speaking
        if any(word in text for word in ["event", "conference", "speaking slot", "panel", "keynote"]):
            return "Events / Speaking / Appearances"

        # Management / legal
        if any(word in text for word in ["representation", "management", "agency", "talent manager", "contract review"]):
            return "Management / Representation / Legal"

        # Platform / account
        if any(word in text for word in ["account", "suspicious login", "password reset", "policy violation", "community guidelines"]):
            return "Platform / Account Notifications"

        # Business ops
        if any(word in text for word in ["invoice", "payment", "payout", "billing", "tax", "w9"]):
            return "Business Operations / Admin"

        # Support / customers
        if any(word in text for word in ["refund", "order", "shipping", "customer support", "support ticket"]):
            return "Customer Support (for creators selling products)"

        # Spam / phishing heuristics
        if any(word in text for word in ["lottery", "wire transfer", "prince", "crypto double", "earn $$$ fast"]):
            return "Spam / Phishing / Irrelevant"

        # Fallback: maybe use KB to detect spam/policy
        kb_hits = search_kb(text, top_k=3, min_score=0.1)
        if kb_hits:
            spam_like = any(
                (hit.get("category") or "").lower().startswith("spam")
                for hit in kb_hits
            )
            if spam_like:
                return "Spam / Phishing / Irrelevant"

        # Ultimate fallback
        return "Other / Uncategorized"

    def _infer_priority(self, email: Email, category: str) -> str:
        text = f"{email.subject} {email.body_text}".lower()

        # Super urgent / critical
        if any(word in text for word in ["urgent", "immediately", "asap", "24 hours", "deadline"])            or "account" in category.lower() and any(w in text for w in ["compromised", "hacked", "disabled"]):
            return "P0"  # Critical

        # High value: sponsorship, PR, events, management/legal
        if category in [
            "Brand/Sponsorship – New Inquiry",
            "Brand/Sponsorship – Negotiation & Follow-up",
            "PR / Media / Interviews",
            "Events / Speaking / Appearances",
            "Management / Representation / Legal",
        ]:
            return "P1"  # High

        # Customer support + business ops: important but normal
        if category in [
            "Business Operations / Admin",
            "Customer Support (for creators selling products)",
            "Platform / Account Notifications",
        ]:
            return "P2"  # Normal

        # Collabs / UGC / community
        if category in [
            "Creator Collaboration",
            "UGC / Content Creation Request",
            "Community / Fan Mail",
        ]:
            return "P2"  # Normal

        # Spam
        if category == "Spam / Phishing / Irrelevant":
            return "P4"  # Ignore/Spam

        # Default
        return "P3"  # Low

    def _maybe_suggest_ticket(
        self,
        email: Email,
        category: str,
        priority: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Decide if this email should create a ticket.

        Very simple rules for now:
        - Sponsorship, PR, Events, Management/Legal -> suggest follow-up ticket.
        - P0 critical platform/account issues -> suggest security ticket.
        """
        high_follow_up_categories = [
            "Brand/Sponsorship – New Inquiry",
            "Brand/Sponsorship – Negotiation & Follow-up",
            "PR / Media / Interviews",
            "Events / Speaking / Appearances",
            "Management / Representation / Legal",
        ]

        if category in high_follow_up_categories:
            return {
                "needed": True,
                "type": "Follow-up",
                "reason": f"Important opportunity: {category}",
                "suggested_priority": priority,
            }

        if priority == "P0":
            return {
                "needed": True,
                "type": "Account / Security",
                "reason": "Critical issue or deadline detected",
                "suggested_priority": "P0",
            }

        return None

    def _update_inbox_row(self, email_id: int, category: str, priority: str) -> None:
        """
        Load inbox.csv via exec_read_csv, update the row for email_id,
        and write back using exec_write_csv.
        """
        df = exec_read_csv("inbox.csv")

        if "email_id" not in df.columns:
            raise ValueError("inbox.csv is missing 'email_id' column.")

        mask = df["email_id"] == email_id
        if not mask.any():
            raise ValueError(f"No inbox row found for email_id={email_id}")

        df.loc[mask, "category"] = category
        df.loc[mask, "priority"] = priority

        exec_write_csv(df, "inbox.csv")
