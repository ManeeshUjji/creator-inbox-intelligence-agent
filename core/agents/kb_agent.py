
from typing import Optional, List

from core.tools.kb_search_tool import search_kb
from core.agents.types import Email, KBContext, TriageResult


class KnowledgeBaseAgent:
    """
    KnowledgeBaseAgent

    Responsibilities:
    - Take an Email (and optionally TriageResult + thread emails).
    - Build a search query from subject + body (+ category hint + prior thread context).
    - Call kb_search_tool.search_kb(...)
    - Return a KBContext with top-N relevant entries.

    Interface:
    - __init__(top_k: int = 5, min_score: float = 0.0)
    - run(
        email: Email,
        triage: Optional[TriageResult] = None,
        thread_emails: Optional[List[Email]] = None
      ) -> KBContext
    """

    def __init__(self, top_k: int = 5, min_score: float = 0.1):
        self.top_k = top_k
        self.min_score = min_score

    def run(
        self,
        email: Email,
        triage: Optional[TriageResult] = None,
        thread_emails: Optional[List[Email]] = None,
    ) -> KBContext:
        """
        Build a text query from the email (and optional triage + thread context),
        then retrieve top KB entries using TF-IDF + cosine similarity.
        """
        parts = [email.subject or "", email.body_text or ""]

        # If we already know the category from triage, use it as a hint
        if triage is not None and triage.category:
            parts.append(triage.category)

        # If there is a thread, fold in previous subjects (lightweight context)
        if thread_emails:
            for msg in thread_emails:
                # skip the current email itself
                if msg.email_id == email.email_id:
                    continue
                if msg.subject:
                    parts.append(msg.subject)

        query = " ".join(p for p in parts if p).strip()
        if not query:
            query = "generic email"

        kb_hits = search_kb(
            query=query,
            top_k=self.top_k,
            min_score=self.min_score,
        )

        debug_info = {
            "query": query,
            "hit_count": len(kb_hits),
            "thread_length": len(thread_emails) if thread_emails else 1,
        }

        return KBContext(
            email_id=email.email_id,
            kb_entries=kb_hits,
            debug_info=debug_info,
        )
