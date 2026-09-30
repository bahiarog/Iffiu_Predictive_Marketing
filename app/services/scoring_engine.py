"""Persona Scoring Engine v2 — Properly calibrated using Rekognition data

Key changes from v1:
- Base scores use full 0-100 range based on actual Rekognition signals
- Persona weights MODULATE (±20%) instead of MULTIPLY (×0.5)
- Risk thresholds: <35 high, 35-60 medium, >60 low
- Better signal extraction from attention/brand/combined scores
- Clarity properly rewards text presence and brand score
- Action rewards CTA keywords, brand visibility, combined score
"""
from sqlalchemy.orm import Session
from app.models.models import Persona, PersonaResult, RekognitionResult, KampaScore
import json
import logging
import math

logger = logging.getLogger(__name__)


def safe_list(val):
    if val is None: return []
    if isinstance(val, str):
        try: return json.loads(val)
        except: return []
    return val if isinstance(val, list) else []

def safe_dict(val):
    if val is None: return {}
    if isinstance(val, str):
        try: return json.loads(val)
        except: return {}
    return val if isinstance(val, dict) else {}

def get_texts(detected_text):
    items = safe_list(detected_text)
    result = []
    for t in items:
        if isinstance(t, str):
            result.append(t.lower())
        elif isinstance(t, dict):
            result.append(t.get("text", "").lower())
    return result

def get_label_names(top_labels):
    items = safe_list(top_labels)
    result = []
    for l in items:
        if isinstance(l, str):
            result.append(l.lower())
        elif isinstance(l, dict):
            result.append(l.get("name", "").lower())
    return result

def clamp(val, lo=0, hi=100):
    return max(lo, min(hi, round(val, 1)))


def calculate_persona_score(persona, d):
    """
    Calculate persona-specific scores from Rekognition data.
    
    d = dict with: attention_score, brand_score, combined_score,
        face_count, face_frame_count, text_frame_count, total_frames,
        dominant_emotion, emotion_confidence, texts[], labels[], emotions{}
    """
    attn = d.get("attention_score") or 0
    brand = d.get("brand_score") or 0
    combined = d.get("combined_score") or 0
    fc = d.get("face_count", 0)
    ff = d.get("face_frame_count", 0)
    tf = d.get("text_frame_count", 0)
    total = d.get("total_frames", 0)
    dom_emotion = d.get("dominant_emotion", "") or ""
    conf = d.get("emotion_confidence", 0) or 0
    texts = d.get("texts", [])
    labels = d.get("labels", [])
    emotions = d.get("emotions", {})

    # ══════════════════════════════════════════════════════════
    # TRUST (Vertrauenswürdigkeit & Markensicherheit)
    # Signals: faces present, positive emotions, familiar labels,
    #          attention score, brand consistency
    # ══════════════════════════════════════════════════════════
    trust = 20  # base

    # Attention score (0-100) is a strong trust signal
    if attn > 0:
        trust += attn * 0.35  # up to +35

    # Face presence builds trust significantly
    if fc >= 50:
        trust += 20
    elif fc >= 20:
        trust += 16
    elif fc >= 5:
        trust += 12
    elif fc >= 1:
        trust += 8

    # Positive emotions build trust
    happy = emotions.get("HAPPY", 0) if isinstance(emotions, dict) else 0
    calm = emotions.get("CALM", 0) if isinstance(emotions, dict) else 0
    if dom_emotion == "HAPPY":
        trust += 8
    elif dom_emotion == "CALM":
        trust += 5

    # Brand score indicates consistency
    if brand > 80:
        trust += 10
    elif brand > 50:
        trust += 6

    # Familiar environment labels
    trust_labels = {"home", "family", "office", "person", "people", "smile",
                    "handshake", "portrait", "photography", "adult", "man", "woman"}
    label_hits = sum(1 for l in labels if l in trust_labels)
    trust += min(label_hits * 2, 10)

    # Persona modulation: tradition-oriented personas value trust more
    tradition_mod = ((persona.tradition_score or 50) - 50) * 0.08
    trust = clamp(trust + tradition_mod)

    # ══════════════════════════════════════════════════════════
    # CLARITY (Botschaftsklarheit & Markenerkennbarkeit)
    # Signals: brand_score, text presence, text density,
    #          combined score, label coherence
    # ══════════════════════════════════════════════════════════
    clarity = 15  # base

    # Brand score is the strongest clarity signal
    if brand > 0:
        clarity += brand * 0.30  # up to +30

    # Combined score reflects overall message quality
    if combined > 0:
        clarity += combined * 0.15  # up to +15

    # Text analysis — sweet spot is moderate text
    text_count = len(texts)
    if text_count == 0:
        clarity += 5   # clean but no message
    elif 1 <= text_count <= 3:
        clarity += 20  # very clear
    elif 4 <= text_count <= 6:
        clarity += 14  # good
    elif 7 <= text_count <= 10:
        clarity += 8   # getting busy
    else:
        clarity += 2   # cluttered

    # Text frame ratio (for video)
    if total > 0:
        text_ratio = tf / total
        if 0.2 <= text_ratio <= 0.6:
            clarity += 8   # good text presence
        elif text_ratio > 0.8:
            clarity += 3   # overwhelming
        elif text_ratio > 0:
            clarity += 5

    # Brand keywords in text
    brand_keywords = {"ionos", "strato", "1&1", "gmx", "web.de"}
    brand_in_text = sum(1 for t in texts if any(b in t for b in brand_keywords))
    if brand_in_text > 0:
        clarity += 8

    # Status-conscious personas care about polish
    status_mod = ((persona.status_score or 50) - 50) * 0.06
    clarity = clamp(clarity + status_mod)

    # ══════════════════════════════════════════════════════════
    # EMOTION (Emotionale Wirkung & Engagement)
    # Signals: dominant emotion, confidence, face presence,
    #          emotional diversity, attention score
    # ══════════════════════════════════════════════════════════
    emotion = 10  # base

    # Attention score correlates with emotional engagement
    if attn > 0:
        emotion += attn * 0.25  # up to +25

    # Dominant emotion type
    emotion_bonus = {
        "HAPPY": 18, "SURPRISED": 14, "CALM": 8,
        "SAD": 10, "FEAR": 8, "CONFUSED": 5,
        "ANGRY": 3, "DISGUSTED": 2
    }
    emotion += emotion_bonus.get(dom_emotion, 0)

    # Emotion confidence
    if conf > 0:
        emotion += conf * 0.12  # up to +12

    # Face presence = emotional connection
    if fc >= 50:
        emotion += 18
    elif fc >= 20:
        emotion += 14
    elif fc >= 5:
        emotion += 10
    elif fc >= 1:
        emotion += 6

    # Face-to-frame ratio (video: more face time = more emotion)
    if total > 0 and ff > 0:
        face_ratio = ff / total
        emotion += min(face_ratio * 15, 12)
    elif fc > 0 and total == 0:
        emotion += 8  # image with face

    # Emotional diversity bonus
    if isinstance(emotions, dict):
        strong_emotions = sum(1 for v in emotions.values() if isinstance(v, (int, float)) and v > 10)
        if strong_emotions >= 3:
            emotion += 6

    # Persona modulation
    emotion = clamp(emotion)

    # ══════════════════════════════════════════════════════════
    # ACTION (Handlungsaufforderung & Conversion)
    # Signals: combined score, CTA keywords, brand presence,
    #          person in frame, visual richness
    # ══════════════════════════════════════════════════════════
    action = 10  # base

    # Combined score is a strong action predictor
    if combined > 0:
        action += combined * 0.25  # up to +25

    # Brand score = intentional messaging
    if brand > 80:
        action += 10
    elif brand > 50:
        action += 6

    # CTA keyword detection
    cta_keywords = {"jetzt", "hier", "gratis", "free", "buy", "shop", "now",
                    "click", "call", "angebot", "bestellen", "testen", "start",
                    "los", "entdecken", "mehr", "anmelden", "download", "try",
                    "get", "save", "deal", "offer", "buchen", "registrieren"}
    cta_count = sum(1 for t in texts if any(k in t for k in cta_keywords))
    action += min(cta_count * 10, 20)

    # Brand name in text = deliberate action driving
    if brand_in_text > 0:
        action += 8

    # Person/face signals intent
    person_labels = {"person", "people", "face", "man", "woman", "adult", "child"}
    if any(l in labels for l in person_labels):
        action += 6

    # Visual complexity (rich scene = more engaging)
    label_count = len(labels)
    if label_count >= 12:
        action += 6
    elif label_count >= 6:
        action += 3

    # Persona modulation
    action = clamp(action)

    # ══════════════════════════════════════════════════════════
    # COMBINED SCORE
    # ══════════════════════════════════════════════════════════
    # Weighted average with persona-specific emphasis
    wt = persona.weight_trust or 0.5
    wc = persona.weight_clarity or 0.5
    we = persona.weight_emotion or 0.5
    wa = persona.weight_action or 0.5
    total_w = wt + wc + we + wa

    # Weights modulate the MIX, not the magnitude
    combined_score = clamp(
        (trust * wt + clarity * wc + emotion * we + action * wa) / total_w
    )

    # Risk assessment
    risk = "low" if combined_score >= 60 else "medium" if combined_score >= 35 else "high"

    return {
        "trust_score": trust,
        "clarity_score": clarity,
        "emotion_score": emotion,
        "action_score": action,
        "combined_score": combined_score,
        "risk_level": risk,
    }


def run_scoring(db, creative_id, user_id):
    rek = db.query(RekognitionResult).filter(RekognitionResult.creative_id == creative_id).first()
    if not rek:
        logger.error(f"No rekognition result for creative {creative_id}")
        return None

    # Build data dict from actual Rekognition results
    emotions = {}
    fd = safe_dict(rek.face_details)
    if isinstance(fd, dict):
        emotions = fd.get("emotions", {})
    if isinstance(emotions, list):
        emotions = {}

    d = {
        "attention_score": rek.attention_score or 0,
        "brand_score": rek.brand_score or 0,
        "combined_score": rek.combined_score or 0,
        "face_count": rek.face_count or 0,
        "face_frame_count": rek.face_frame_count or 0,
        "text_frame_count": rek.text_frame_count or 0,
        "total_frames": rek.total_frames or 0,
        "dominant_emotion": rek.dominant_emotion or "",
        "emotion_confidence": rek.emotion_confidence or 0,
        "texts": get_texts(rek.detected_text),
        "labels": get_label_names(rek.top_labels),
        "emotions": emotions,
    }

    personas = db.query(Persona).filter(
        Persona.is_active == True,
        (Persona.user_id == None) | (Persona.user_id == user_id)
    ).order_by(Persona.sort_order).all()

    if not personas:
        logger.error("No personas found")
        return None

    # Clear old results
    db.query(PersonaResult).filter(PersonaResult.creative_id == creative_id).delete()

    results = []
    for p in personas:
        scores = calculate_persona_score(p, d)
        pr = PersonaResult(creative_id=creative_id, persona_id=p.id, **scores)
        db.add(pr)
        results.append({
            "persona_name": p.name, "persona_slug": p.slug,
            "avatar_emoji": p.avatar_emoji, **scores
        })

    cnt = len(results)
    overall = clamp(sum(r["combined_score"] for r in results) / cnt)
    trust_avg = clamp(sum(r["trust_score"] for r in results) / cnt)
    clarity_avg = clamp(sum(r["clarity_score"] for r in results) / cnt)
    emotion_avg = clamp(sum(r["emotion_score"] for r in results) / cnt)
    action_avg = clamp(sum(r["action_score"] for r in results) / cnt)
    risk = "low" if overall >= 60 else "medium" if overall >= 35 else "high"

    # Upsert KampaScore
    ks = db.query(KampaScore).filter(KampaScore.creative_id == creative_id).first()
    if ks:
        ks.overall_score = overall
        ks.risk_level = risk
        ks.trust_avg = trust_avg
        ks.clarity_avg = clarity_avg
        ks.emotion_avg = emotion_avg
        ks.action_avg = action_avg
        ks.persona_count = cnt
    else:
        ks = KampaScore(
            user_id=user_id, creative_id=creative_id,
            overall_score=overall, risk_level=risk,
            trust_avg=trust_avg, clarity_avg=clarity_avg,
            emotion_avg=emotion_avg, action_avg=action_avg,
            persona_count=cnt,
        )
        db.add(ks)

    db.commit()

    logger.info(f"Creative {creative_id}: overall={overall} risk={risk} "
                f"T={trust_avg} C={clarity_avg} E={emotion_avg} A={action_avg}")

    return {
        "overall_score": overall, "risk_level": risk, "persona_count": cnt,
        "trust_avg": trust_avg, "clarity_avg": clarity_avg,
        "emotion_avg": emotion_avg, "action_avg": action_avg,
        "persona_results": results,
    }
