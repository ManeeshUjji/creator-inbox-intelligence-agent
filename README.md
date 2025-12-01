# Creator Inbox Intelligence Agent

An AI-powered multi-agent system that processes a creator’s inbox end-to-end:
- triages emails into categories + priority,
- retrieves relevant knowledge base entries,
- logs follow-up tickets,
- generates draft replies.

This is the **final implementation** for the Kaggle x OpenAI Agents Capstone Project.

---

## Project Goals

Creators receive sponsorship requests, fan messages, platform alerts, invoices, disputes, spam — and manually sorting them wastes hours.  

This project builds an **autonomous multi-agent inbox assistant** that:
1. Classifies and prioritizes incoming email  
2. Pulls relevant knowledge base snippets  
3. Suggests follow-up actions (tickets)  
4. Writes a draft response  
5. Produces evaluation metrics for its decisions  

The result is a reliable workflow that behaves like a human inbox manager.

---

## System Architecture

### **Triage Agent**
Classifies emails into structured categories and assigns a P1–P4 priority.

### **Knowledge Base Agent**
Uses similarity search over the KB to retrieve relevant entries.

### **Reply Agent**
Generates a draft reply based on triage + KB context.

### **Ticket Logger Tool**
Automatically opens or updates tickets when the email requires follow-up.

### **Orchestrator Agent**
Coordinates the entire pipeline:
Email → Triage → KB Search → Ticket Decision → Draft Reply → Output

---

## Repository Structure

```
creator-inbox-intelligence-agent/
│
├── core/
│ ├── agents/
│ ├── tools/
│ └── ...
│
├── datasets/
│ ├── inbox.csv
│ ├── knowledge_base.csv
│ └── tickets.csv
│
├── evaluation/
│ └── artifacts/
│
├── notebooks/
│ ├── creator_inbox_agent.ipynb # development notebook
│ └── creator_inbox_agent_final.ipynb # final polished notebook
│
├── docs/
│ ├── Part1_Full_Blueprint.docx
│ ├── Part2_Documentation.docx
│ ├── Part3_Tools_Detailed_Report.docx
│ ├── Part4_Detailed_Report.docx
│ └── Part5_Detailed_Report.docx
│
│
├── README.md
└── requirements.txt
```


---

## Notebooks

### **creator_inbox_agent_final.ipynb** (Main Deliverable)
Includes:
- full pipeline demo  
- pretty-printed email runs  
- KB search examples  
- misclassification analysis  
- evaluation results  
- clean code architecture  

This is the notebook intended for Kaggle reviewers and recruiters.

---

## Evaluation

Evaluation results include:
- category accuracy  
- priority accuracy  
- ticket correctness  
- example misclassifications  
- latency measurements  

Artifacts live in:
evaluation/artifacts/


and are viewable inside the final notebook.

---

## Extending the Project

Future improvements:
- embedding-based KB search  
- fine-tuned triage classifier  
- fraud/spam detection agent  
- automated negotiation logic  
- Gmail/IMAP real email integration  
- dashboard for tracking agent drift  

---

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Run notebook:

```
notebooks/creator_inbox_agent_final.ipynb
```

If you use Colab, the notebook auto-clones the repo.

---

## 👤 Author
Built by **Maneesh Ujji** as part of the Kaggle x OpenAI Agents Capstone.






