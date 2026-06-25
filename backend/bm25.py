# bm25.py
from collections import defaultdict
from stats import compute_time_decay
from repository import get_doc_dates


def bm25_score(tf, idf, doc_len, avgdl, k1=1.5, b=0.75):
    tf = float(tf)
    idf = float(idf)
    doc_len = float(doc_len)
    avgdl = float(avgdl)

    return idf * ((tf * (k1 + 1)) /
           (tf + k1 * (1 - b + b * (doc_len / avgdl))))
    

def calculate_scores(rows, avgdl):
    scores = defaultdict(float)

    for row in rows:
        bm25 = bm25_score(
            tf=float(row["tf"]),
            idf=float(row["idf"]),
            doc_len=float(row["doc_len"]),
            avgdl=float(avgdl)
        )
        scores[row["doc_id"]] += bm25

    return scores

def rerank_with_time_decay(ranked_docs, doc_dates, alpha=0.8):
    final_scores = []

    for doc_id, bm25_score_val in ranked_docs:
        created_at = doc_dates.get(doc_id)

        if created_at:
            decay = compute_time_decay(created_at)
            final_score = alpha * bm25_score_val + (1 - alpha) * decay
        else:
            final_score = bm25_score_val

        final_scores.append((doc_id, final_score))

    return sorted(final_scores, key=lambda x: x[1], reverse=True)

def rank_documents(scores, top_n=10):
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]