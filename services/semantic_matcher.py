from sentence_transformers import SentenceTransformer, util

_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def semantic_score(resume_text, jd_text):
    if not (resume_text and jd_text):
        return 0.0
    try:
        model = _get_model()
        resume_embedding = model.encode(resume_text, convert_to_tensor=True)
        jd_embedding = model.encode(jd_text, convert_to_tensor=True)
        score = util.pytorch_cos_sim(resume_embedding, jd_embedding)
        return round(max(0.0, float(score[0][0]) * 100), 2)
    except Exception:
        return 0.0