"""
IFFIU Scoring Engine — Sinus-Milieu Persona Simulation
Python port of KAMPA's calc-score.php

Each Sinus-Milieu has unique reaction weights for Trust/Clarity/Emotion/Action.
The engine computes how each persona segment would respond to a creative.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import Persona, PersonaResult, KampaScore, RekognitionResult

# ─── Default Sinus-Milieu Personas ───────────────────────────────────────

DEFAULT_PERSONAS = [
    {
        "slug": "konservativ-etablierte", "name": "Konservativ-Etablierte",
        "age_range": "40-70", "gender": "mixed", "income_level": "high", "education": "high",
        "tradition_score": 75, "status_score": 85,
        "weight_trust": 0.85, "weight_clarity": 0.70, "weight_emotion": 0.35, "weight_action": 0.40,
        "avatar_emoji": "🏛️", "color_hex": "#1e3a5f",
        "description_de": "Das klassische Establishment. Verantwortungs- und Erfolgsethik. Reagieren auf Vertrauen und Substanz.",
        "sort_order": 1,
    },
    {
        "slug": "liberal-intellektuelle", "name": "Liberal-Intellektuelle",
        "age_range": "30-70", "gender": "mixed", "income_level": "high", "education": "high",
        "tradition_score": 40, "status_score": 90,
        "weight_trust": 0.60, "weight_clarity": 0.80, "weight_emotion": 0.55, "weight_action": 0.35,
        "avatar_emoji": "📚", "color_hex": "#4a90d9",
        "description_de": "Aufgeklärte Bildungselite. Vielfalt, Nachhaltigkeit, Kultur. Reagieren auf klare, differenzierte Botschaften.",
        "sort_order": 2,
    },
    {
        "slug": "performer", "name": "Performer",
        "age_range": "25-55", "gender": "mixed", "income_level": "high", "education": "high",
        "tradition_score": 30, "status_score": 80,
        "weight_trust": 0.45, "weight_clarity": 0.55, "weight_emotion": 0.70, "weight_action": 0.90,
        "avatar_emoji": "🚀", "color_hex": "#e63946",
        "description_de": "Effizienzorientierte Leistungselite. Global, digital, statusbewusst. Reagieren stark auf Action und Dynamik.",
        "sort_order": 3,
    },
    {
        "slug": "expeditive", "name": "Expeditive",
        "age_range": "18-35", "gender": "mixed", "income_level": "medium", "education": "high",
        "tradition_score": 15, "status_score": 70,
        "weight_trust": 0.30, "weight_clarity": 0.45, "weight_emotion": 0.90, "weight_action": 0.75,
        "avatar_emoji": "✨", "color_hex": "#9b59b6",
        "description_de": "Kreative Avantgarde. Unkonventionell, vernetzt, mental flexibel. Reagieren auf Emotion und Überraschung.",
        "sort_order": 4,
    },
    {
        "slug": "adaptiv-pragmatische", "name": "Adaptiv-Pragmatische",
        "age_range": "20-45", "gender": "mixed", "income_level": "medium", "education": "medium",
        "tradition_score": 50, "status_score": 50,
        "weight_trust": 0.65, "weight_clarity": 0.75, "weight_emotion": 0.50, "weight_action": 0.65,
        "avatar_emoji": "🎯", "color_hex": "#2ecc71",
        "description_de": "Die moderne bürgerliche Mitte. Pragmatisch, anpassungsbereit, nutzenorientiert.",
        "sort_order": 5,
    },
    {
        "slug": "sozialoekologen", "name": "Sozialökologische",
        "age_range": "30-60", "gender": "mixed", "income_level": "medium", "education": "high",
        "tradition_score": 55, "status_score": 65,
        "weight_trust": 0.80, "weight_clarity": 0.65, "weight_emotion": 0.70, "weight_action": 0.30,
        "avatar_emoji": "🌿", "color_hex": "#27ae60",
        "description_de": "Konsumkritisches, nachhaltigkeitsorientiertes Milieu. Reagieren auf Vertrauen und emotionale Tiefe.",
        "sort_order": 6,
    },
    {
        "slug": "buergerliche-mitte", "name": "Bürgerliche Mitte",
        "age_range": "30-65", "gender": "mixed", "income_level": "medium", "education": "medium",
        "tradition_score": 60, "status_score": 45,
        "weight_trust": 0.75, "weight_clarity": 0.80, "weight_emotion": 0.40, "weight_action": 0.55,
        "avatar_emoji": "🏠", "color_hex": "#f39c12",
        "description_de": "Der leistungs- und anpassungsbereite Mainstream. Streben nach gesicherter Existenz und sozialer Anerkennung.",
        "sort_order": 7,
    },
    {
        "slug": "traditionelle", "name": "Traditionelle",
        "age_range": "55-80", "gender": "mixed", "income_level": "low", "education": "low",
        "tradition_score": 90, "status_score": 30,
        "weight_trust": 0.90, "weight_clarity": 0.85, "weight_emotion": 0.20, "weight_action": 0.25,
        "avatar_emoji": "🏡", "color_hex": "#92400e",
        "description_de": "Sicherheits- und ordnungsliebende ältere Generation. Reagieren auf Vertrauen, Einfachheit und Bewährtes.",
        "sort_order": 8,
    },
    {
        "slug": "prekaere", "name": "Prekäre",
        "age_range": "35-65", "gender": "mixed", "income_level": "low", "education": "low",
        "tradition_score": 70, "status_score": 15,
        "weight_trust": 0.70, "weight_clarity": 0.90, "weight_emotion": 0.45, "weight_action": 0.60,
        "avatar_emoji": "🔧", "color_hex": "#78716c",
        "description_de": "Um Orientierung und Teilhabe bemühte Unterschicht. Reagieren auf einfache, direkte Botschaften.",
        "sort_order": 9,
    },
    {
        "slug": "konsum-hedonisten", "name": "Konsum-Hedonisten",
        "age_range": "18-40", "gender": "mixed", "income_level": "low", "education": "medium",
        "tradition_score": 50, "status_score": 25,
        "weight_trust": 0.30, "weight_clarity": 0.45, "weight_emotion": 0.85, "weight_action": 0.70,
        "avatar_emoji": "🎮", "color_hex": "#e11d48",
        "description_de": "Die spaß- und erlebnisorientierte untere Mittelschicht. Reagieren auf Spaß, Action und Entertainment.",
        "sort_order": 10,
    },
]


def seed_default_personas(db: Session):
    """Insert default Sinus-Milieu personas if none exist"""
    count = db.query(Persona).filter(Persona.user_id.is_(None)).count()
    if count > 0:
        return
    
    for p in DEFAULT_PERSONAS:
        persona = Persona(**p, category="sinus")
        db.add(persona)
    db.commit()


def calculate_persona_scores(db: Session, creative_id: int, user_id: int, 
                              rekognition_data: Optional[dict] = None) -> dict:
    """
    Calculate Sinus-Milieu persona scores for a creative.
    
    Args:
        db: Database session
        creative_id: ID of the creative being analyzed
        user_id: Owner user ID
        rekognition_data: Dict with attention, brand, combined, emotions, labels, etc.
    
    Returns:
        Dict with overall_score, risk_level, persona_results[]
    """
    
    # Get active personas (system defaults + user custom)
    personas = db.query(Persona).filter(
        Persona.is_active == True,
        (Persona.user_id.is_(None)) | (Persona.user_id == user_id)
    ).order_by(Persona.sort_order).all()
    
    if not personas:
        seed_default_personas(db)
        personas = db.query(Persona).filter(Persona.user_id.is_(None)).order_by(Persona.sort_order).all()
    
    # Base scores from Rekognition
    if rekognition_data:
        base_trust = _calc_trust(rekognition_data)
        base_clarity = _calc_clarity(rekognition_data)
        base_emotion = _calc_emotion(rekognition_data)
        base_action = _calc_action(rekognition_data)
        has_rekog = True
    else:
        # No Rekognition data — use neutral baseline
        base_trust = base_clarity = base_emotion = base_action = 50.0
        has_rekog = False
    
    # Delete previous results for this creative
    db.query(PersonaResult).filter(PersonaResult.creative_id == creative_id).delete()
    
    results = []
    total_score = 0
    
    for persona in personas:
        # Apply persona-specific weights
        trust = round(min(base_trust * persona.weight_trust * 1.8, 100), 1)
        clarity = round(min(base_clarity * persona.weight_clarity * 1.8, 100), 1)
        emotion = round(min(base_emotion * persona.weight_emotion * 1.8, 100), 1)
        action = round(min(base_action * persona.weight_action * 1.8, 100), 1)
        
        combined = round((trust + clarity + emotion + action) / 4, 1)
        
        # Generate reasoning
        reasoning = _generate_reasoning(persona, trust, clarity, emotion, action, combined)
        
        pr = PersonaResult(
            creative_id=creative_id,
            persona_id=persona.id,
            trust_score=trust,
            clarity_score=clarity,
            emotion_score=emotion,
            action_score=action,
            combined_score=combined,
            reasoning=reasoning,
        )
        db.add(pr)
        
        results.append({
            "persona_id": persona.id,
            "name": persona.name,
            "slug": persona.slug,
            "avatar_emoji": persona.avatar_emoji,
            "color_hex": persona.color_hex,
            "age_range": persona.age_range,
            "income_level": persona.income_level,
            "tradition_score": persona.tradition_score,
            "status_score": persona.status_score,
            "trust_score": trust,
            "clarity_score": clarity,
            "emotion_score": emotion,
            "action_score": action,
            "combined_score": combined,
            "reasoning": reasoning,
        })
        total_score += combined
    
    # Overall score
    overall = round(total_score / len(personas), 1) if personas else 0
    risk = "low" if overall >= 65 else "medium" if overall >= 40 else "high" if overall >= 25 else "critical"
    
    # Save/update KAMPA score
    ks = db.query(KampaScore).filter(KampaScore.creative_id == creative_id).first()
    avgs = {
        "trust_avg": round(sum(r["trust_score"] for r in results) / len(results), 1),
        "clarity_avg": round(sum(r["clarity_score"] for r in results) / len(results), 1),
        "emotion_avg": round(sum(r["emotion_score"] for r in results) / len(results), 1),
        "action_avg": round(sum(r["action_score"] for r in results) / len(results), 1),
    }
    
    if ks:
        ks.overall_score = overall
        ks.risk_level = risk
        ks.persona_count = len(personas)
        ks.rekognition_available = has_rekog
        for k, v in avgs.items():
            setattr(ks, k, v)
    else:
        ks = KampaScore(
            user_id=user_id, creative_id=creative_id,
            overall_score=overall, risk_level=risk,
            persona_count=len(personas), rekognition_available=has_rekog,
            **avgs
        )
        db.add(ks)
    
    db.commit()
    
    return {
        "overall_score": overall,
        "risk_level": risk,
        "persona_count": len(personas),
        "rekognition_available": has_rekog,
        "persona_results": results,
        **avgs,
    }


# ─── Dimension Calculators ──────────────────────────────────────────────

def _calc_trust(data: dict) -> float:
    """Trust = face presence + positive emotions + brand text"""
    face_ratio = min((data.get("face_frame_count", 0) / max(data.get("total_frames", 1), 1)) * 100, 100)
    has_smile = any(e.get("type") == "HAPPY" and e.get("confidence", 0) > 50 for e in data.get("top_emotions", []))
    text_bonus = min(len(data.get("detected_text", [])) * 8, 30)
    return min(face_ratio * 0.5 + (20 if has_smile else 0) + text_bonus + 15, 100)

def _calc_clarity(data: dict) -> float:
    """Clarity = text presence + label richness"""
    text_count = len(data.get("detected_text", []))
    label_count = len(data.get("top_labels", []))
    return min(text_count * 12 + label_count * 3 + 20, 100)

def _calc_emotion(data: dict) -> float:
    """Emotion = dominant emotion confidence + face presence"""
    emo_conf = data.get("emotion_confidence", 0)
    face_ratio = min((data.get("face_frame_count", 0) / max(data.get("total_frames", 1), 1)) * 100, 100)
    return min(emo_conf * 0.6 + face_ratio * 0.3 + 10, 100)

def _calc_action(data: dict) -> float:
    """Action = dynamic labels + text calls to action"""
    labels = [l.get("name", "") for l in data.get("top_labels", [])]
    action_labels = {"Person", "People", "Face", "Text", "Urban", "Architecture", "Car", "Sport"}
    action_count = sum(1 for l in labels if l in action_labels)
    text_count = len(data.get("detected_text", []))
    return min(action_count * 10 + text_count * 8 + 15, 100)


def _generate_reasoning(persona, trust, clarity, emotion, action, combined) -> str:
    """Generate human-readable reasoning for persona score"""
    parts = []
    if combined >= 70:
        parts.append(f"Starke Resonanz bei {persona.name}.")
    elif combined >= 45:
        parts.append(f"Moderate Resonanz bei {persona.name}.")
    else:
        parts.append(f"Schwache Resonanz bei {persona.name}.")
    
    dims = [("Trust", trust), ("Clarity", clarity), ("Emotion", emotion), ("Action", action)]
    best = max(dims, key=lambda x: x[1])
    worst = min(dims, key=lambda x: x[1])
    
    if best[1] >= 60:
        parts.append(f"Besonders stark bei {best[0]} ({best[1]}).")
    if worst[1] < 40:
        parts.append(f"Schwach bei {worst[0]} ({worst[1]}) — hier besteht Optimierungspotenzial.")
    
    return " ".join(parts)
