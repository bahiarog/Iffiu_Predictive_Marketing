"""Creative Recommendations Engine"""
from typing import List, Dict

def generate_recommendations(overall_score: float, dimensions: dict, persona_results: list) -> dict:
    """Generate actionable recommendations based on scores"""
    recs = []
    strengths = []

    trust = dimensions.get("trust_avg", 0)
    clarity = dimensions.get("clarity_avg", 0)
    emotion = dimensions.get("emotion_avg", 0)
    action = dimensions.get("action_avg", 0)

    # Identify strengths
    for name, val in [("Trust", trust), ("Clarity", clarity), ("Emotion", emotion), ("Action", action)]:
        if val >= 65:
            strengths.append({"dimension": name, "score": val, "icon": "✅"})

    # Identify weaknesses and generate recommendations
    if trust < 50:
        recs.append({
            "title": "Vertrauenssignale stärken",
            "icon": "🛡️",
            "severity": "high" if trust < 30 else "medium",
            "problem": f"Trust-Score liegt bei {trust}. Zielgruppen vertrauen dem Creative nicht ausreichend.",
            "actions": [
                "Echte Gesichter/Personen einsetzen (erhöht Vertrauen um ~15 Punkte)",
                "Bekannte Symbole oder Gütesiegel integrieren",
                "Warme, einladende Farbpalette verwenden",
                "Testimonials oder Social Proof einbauen",
            ],
            "quick_win": "Ein freundliches Gesicht mit Blickkontakt in den ersten 3 Sekunden zeigen.",
        })

    if clarity < 50:
        recs.append({
            "title": "Klarheit der Botschaft verbessern",
            "icon": "📝",
            "severity": "high" if clarity < 30 else "medium",
            "problem": f"Clarity-Score bei {clarity}. Die Kernbotschaft ist nicht deutlich genug.",
            "actions": [
                "Maximal 1-2 Textbotschaften pro Creative",
                "Größere, lesbare Schrift verwenden",
                "Kontrast zwischen Text und Hintergrund erhöhen",
                "Überflüssige visuelle Elemente entfernen",
            ],
            "quick_win": "Die Hauptbotschaft auf 5 Wörter oder weniger reduzieren.",
        })

    if emotion < 50:
        recs.append({
            "title": "Emotionale Wirkung steigern",
            "icon": "❤️",
            "severity": "high" if emotion < 30 else "medium",
            "problem": f"Emotion-Score bei {emotion}. Das Creative löst zu wenig emotionale Resonanz aus.",
            "actions": [
                "Stärkere emotionale Trigger einsetzen (Freude, Überraschung)",
                "Storytelling-Elemente einbauen",
                "Musik/Sound-Design optimieren (bei Video)",
                "Nahaufnahmen von Gesichtern mit Emotionen zeigen",
            ],
            "quick_win": "Ein Moment der Überraschung oder Freude in die ersten 5 Sekunden einbauen.",
        })

    if action < 50:
        recs.append({
            "title": "Call-to-Action verstärken",
            "icon": "🎯",
            "severity": "high" if action < 30 else "medium",
            "problem": f"Action-Score bei {action}. Die Handlungsaufforderung ist zu schwach.",
            "actions": [
                "Klaren CTA einbauen ('Jetzt kaufen', 'Mehr erfahren')",
                "CTA visuell hervorheben (Kontrastfarbe, Animation)",
                "Dringlichkeit erzeugen (zeitlich begrenzt, limitiert)",
                "QR-Code oder URL prominent platzieren",
            ],
            "quick_win": "Einen kontrastreichen Button mit '→ Jetzt entdecken' am Ende einblenden.",
        })

    # Weak personas
    weak_personas = [p for p in persona_results if p.get("combined_score", 100) < 45]
    if weak_personas:
        names = ", ".join(p.get("persona_name", "?") for p in weak_personas[:3])
        recs.append({
            "title": f"Schwache Personas gezielt ansprechen",
            "icon": "👥",
            "severity": "medium",
            "problem": f"{len(weak_personas)} Persona(s) reagieren negativ: {names}",
            "actions": [
                "Zielgruppen-spezifische Varianten erstellen",
                "A/B Test mit angepassten Creatives durchführen",
                "Visuelle Codes der schwachen Segmente recherchieren",
            ],
            "quick_win": "Für die schwächste Persona eine eigene Creative-Variante erstellen.",
            "personas": [{"name": p.get("persona_name"), "score": p.get("combined_score")} for p in weak_personas[:5]],
        })

    # Summary
    if overall_score >= 70:
        summary = f"Sehr gutes Creative (Score: {overall_score}). Kleinere Optimierungen möglich."
        priority = "low"
    elif overall_score >= 50:
        summary = f"Solides Creative (Score: {overall_score}). Gezielte Verbesserungen empfohlen."
        priority = "medium"
    else:
        summary = f"Creative braucht Überarbeitung (Score: {overall_score}). Mehrere Dimensionen kritisch."
        priority = "high"

    return {
        "summary": summary,
        "priority": priority,
        "strengths": strengths,
        "recommendations": recs,
        "overall_score": overall_score,
    }
