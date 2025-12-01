
import logging
from typing import List, Optional

from core.tools.code_execution_tool import exec_read_csv
from core.tools.ticket_logger_tool import log_ticket
from core.agents.types import Email, TriageResult, KBContext, ReplyResult
from core.agents.triage_agent import TriageAgent
from core.agents.kb_agent import KnowledgeBaseAgent
from core.agents.reply_agent import ReplyAgent


logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[ORCH] %(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class OrchestratorAgent:
    """
    Main pipeline controller:
    - Load email + thread
    - Run triage
    - Run KB search
    - Generate reply
    - Create ticket if needed
    - Log each step for observability
    """

    def __init__(self):
        self.triage_agent = TriageAgent()
        self.kb_agent = KnowledgeBaseAgent(top_k=5, min_score=0.05)
        self.reply_agent = ReplyAgent()

    # ------------------ PUBLIC ------------------
    def process_email(self, email_id: int) -> ReplyResult:

        logger.info(f"Processing email_id={email_id}")

        email, thread_emails = self._load_email_and_thread(email_id)
        logger.info(
            f"Loaded email_id={email.email_id} in thread_id={email.thread_id} "
            f"(thread length={len(thread_emails)})"
        )

        # 1) TRIAGE
        triage_result: TriageResult = self.triage_agent.run(email)
        logger.info(
            f"Triage: category='{triage_result.category}', priority='{triage_result.priority}'"
        )

        # 2) KB SEARCH
        kb_context: KBContext = self.kb_agent.run(email, triage_result, thread_emails)
        hit_count = kb_context.debug_info.get("hit_count", len(kb_context.kb_entries))
        logger.info(
            f"KB search: query='{kb_context.debug_info.get('query')}', hits={hit_count}"
        )

        # 3) REPLY
        reply_result: ReplyResult = self.reply_agent.run(
            email, triage_result, kb_context, thread_emails
        )
        logger.info(
            f"Reply generated: subject='{reply_result.reply_subject}'"
        )

        # 4) OPTIONAL TICKET
        self._maybe_log_ticket(reply_result)

        logger.info(f"Finished email_id={email_id}")
        return reply_result

    # ------------------ BATCH ------------------
    def process_batch(self, email_ids: Optional[List[int]] = None):
        df = exec_read_csv("inbox.csv")

        if email_ids is None:
            email_ids = list(df["email_id"].astype(int))

        logger.info(f"Batch processing {len(email_ids)} email(s).")

        results = []
        for eid in email_ids:
            results.append(self.process_email(eid))

        logger.info("Batch complete.")
        return results

    # ------------------ INTERNAL ------------------
    def _load_email_and_thread(self, email_id: int):
        df = exec_read_csv("inbox.csv")

        mask = df["email_id"] == email_id
        if not mask.any():
            raise ValueError(f"No inbox row found for email_id={email_id}")

        row = df[mask].iloc[0]
        thread_id = int(row["thread_id"])

        thread_df = df[df["thread_id"] == thread_id].copy()

        if "received_datetime_utc" in thread_df.columns:
            thread_df = thread_df.sort_values("received_datetime_utc")
        else:
            thread_df = thread_df.sort_values("email_id")

        thread_emails = []
        for _, r in thread_df.iterrows():
            thread_emails.append(
                Email(
                    email_id=int(r["email_id"]),
                    thread_id=int(r["thread_id"]),
                    creator_id=str(r["creator_id"]),
                    from_name=str(r["from_name"]),
                    from_email=str(r["from_email"]),
                    to_email=str(r["to_email"]),
                    subject=str(r["subject"]),
                    body_text=str(r["body_text"]),
                    category=r.get("category"),
                    priority=r.get("priority"),
                    status=r.get("status"),
                    metadata={
                        "received_datetime_utc": r.get("received_datetime_utc"),
                        "raw_source": r.get("raw_source"),
                        "assigned_to": r.get("assigned_to"),
                        "last_action": r.get("last_action"),
                        "last_action_datetime_utc": r.get("last_action_datetime_utc"),
                        "ticket_id": r.get("ticket_id"),
                        "notes": r.get("notes"),
                    },
                )
            )

        current_email = next(e for e in thread_emails if e.email_id == email_id)
        return current_email, thread_emails

    def process_email_with_timings(self, email_id):
      """
      Same as process_email, but returns timing info for key stages.
      """
      timings = {}

      t_start = time.time()
      # triage
      t0 = time.time()
      triage_out = self.triage_agent.classify(self.load_email(email_id))
      t1 = time.time()
      timings["triage"] = t1 - t0

      # kb search
      t2 = time.time()
      kb_out = self.kb_agent.search_kb(triage_out)
      t3 = time.time()
      timings["kb_search"] = t3 - t2

      # reply agent
      reply_out = self.reply_agent.generate_reply(triage_out, kb_out)

      # final time
      t_end = time.time()

      # Return same structure as normal plus timings
      return reply_out, timings

    def _maybe_log_ticket(self, reply_result: ReplyResult):
        action = reply_result.follow_up_action

        if not action:
            logger.info("No follow-up action.")
            return

        if not action.get("create_ticket"):
            logger.info("Follow-up action present, but create_ticket=False.")
            return

        payload = action["ticket_payload"]

        ticket_data = {
            "creator_id": payload["creator_id"],
            "email_id": payload["email_id"],
            "type": payload["type"],
            "title": payload["title"],
            "description": payload["description"],
            "priority": payload["priority"],
            "status": "open",
            "created_by": "orchestrator_agent",
            "assigned_to": "inbox_manager",
        }

        row = log_ticket(ticket_data)
        logger.info(
            f"Ticket logged: ticket_id={row['ticket_id']} for email_id={row['email_id']}"
        )
