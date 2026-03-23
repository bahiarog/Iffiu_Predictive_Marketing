"""
IFFIU Persona Generator — Kundenangepasste Personas

Generiert 3 individuelle Personas basierend auf:
- Branche des Kunden
- Unternehmensgröße
- 3 beschriebene Produkte

Die Personas haben menschliche Namen, konkretes Alter und sind
direkt auf die Produkte des Kunden zugeschnitten.
"""

from sqlalchemy.orm import Session
from app.models.models import Persona, UserProfile
import random

# ─── Persona-Bibliothek nach Branche ────────────────────────────────────────
#
# Jede Branche hat 6+ Persona-Templates.
# Felder:
#   name, age, emoji, color_hex,
#   description_template (nutzt {products} placeholder),
#   weight_trust, weight_clarity, weight_emotion, weight_action,
#   tradition_score, status_score, income_level, education

INDUSTRY_PERSONAS = {

    "mode": [
        {
            "slug_tpl": "style-entdeckerin",
            "name": "Emma", "age": 24,
            "emoji": "👗", "color_hex": "#e91e8c",
            "tradition_score": 20, "status_score": 65,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.35, "weight_clarity": 0.50,
            "weight_emotion": 0.95, "weight_action": 0.80,
            "desc": "Style-Entdeckerin, 24. Liebt neue Trends, ist auf TikTok & Instagram aktiv. Kauft impulsiv bei emotionalen Creatives. Besonders empfänglich für: {products}.",
        },
        {
            "slug_tpl": "premium-käuferin",
            "name": "Sophie", "age": 36,
            "emoji": "💎", "color_hex": "#9c27b0",
            "tradition_score": 40, "status_score": 85,
            "income_level": "high", "education": "high",
            "weight_trust": 0.80, "weight_clarity": 0.70,
            "weight_emotion": 0.60, "weight_action": 0.45,
            "desc": "Premium-Käuferin, 36. Qualitätsbewusst, markentreu, kauft durchdacht. Reagiert auf Vertrauen und Substanz. Ihre Welt: {products}.",
        },
        {
            "slug_tpl": "klassische-stilbewusste",
            "name": "Claudia", "age": 52,
            "emoji": "👒", "color_hex": "#795548",
            "tradition_score": 70, "status_score": 60,
            "income_level": "high", "education": "medium",
            "weight_trust": 0.85, "weight_clarity": 0.80,
            "weight_emotion": 0.40, "weight_action": 0.35,
            "desc": "Klassische Stilbewusste, 52. Zeitlose Eleganz, keine schnellen Trends. Kauft selten aber hochwertig. Sucht Qualität bei: {products}.",
        },
        {
            "slug_tpl": "schnäppchenjägerin",
            "name": "Laura", "age": 29,
            "emoji": "🛍️", "color_hex": "#ff5722",
            "tradition_score": 45, "status_score": 30,
            "income_level": "low", "education": "medium",
            "weight_trust": 0.50, "weight_clarity": 0.85,
            "weight_emotion": 0.70, "weight_action": 0.90,
            "desc": "Schnäppchenjägerin, 29. Vergleicht Preise, liebt Sales. Reagiert auf klare Angebote und Action-Calls. Kauft {products} nur beim besten Preis.",
        },
        {
            "slug_tpl": "nachhaltigkeits-shopperin",
            "name": "Mia", "age": 31,
            "emoji": "🌿", "color_hex": "#4caf50",
            "tradition_score": 50, "status_score": 55,
            "income_level": "medium", "education": "high",
            "weight_trust": 0.80, "weight_clarity": 0.65,
            "weight_emotion": 0.75, "weight_action": 0.40,
            "desc": "Nachhaltigkeits-Shopperin, 31. Kauft bewusst, fair & ökologisch. Vertraut Marken mit klarer Haltung. Entscheidet bei {products} nach Werten.",
        },
        {
            "slug_tpl": "teen-trendsetter",
            "name": "Lena", "age": 19,
            "emoji": "✨", "color_hex": "#ff4081",
            "tradition_score": 10, "status_score": 50,
            "income_level": "low", "education": "low",
            "weight_trust": 0.25, "weight_clarity": 0.40,
            "weight_emotion": 0.95, "weight_action": 0.85,
            "desc": "Teen Trendsetter, 19. Setzt Trends bevor sie Mainstream sind. Kauft spontan und emotional. Begeistert von {products} wenn es viral geht.",
        },
    ],

    "tech": [
        {
            "slug_tpl": "tech-early-adopter",
            "name": "Lukas", "age": 28,
            "emoji": "🚀", "color_hex": "#2196f3",
            "tradition_score": 15, "status_score": 70,
            "income_level": "high", "education": "high",
            "weight_trust": 0.40, "weight_clarity": 0.60,
            "weight_emotion": 0.75, "weight_action": 0.90,
            "desc": "Tech Early Adopter, 28. Will immer das Neueste. Entscheidet schnell, teilt seine Meinung online. Begeistert von {products} wenn es innovativ ist.",
        },
        {
            "slug_tpl": "digital-professional",
            "name": "Thomas", "age": 42,
            "emoji": "💼", "color_hex": "#1565c0",
            "tradition_score": 35, "status_score": 80,
            "income_level": "high", "education": "high",
            "weight_trust": 0.70, "weight_clarity": 0.85,
            "weight_emotion": 0.45, "weight_action": 0.65,
            "desc": "Digital Professional, 42. Entscheider in mittelgroßem Unternehmen. Kauft nach ROI-Kalkulation. Bewertet {products} rational und zahlenbasiert.",
        },
        {
            "slug_tpl": "tech-pragmatiker",
            "name": "Michael", "age": 55,
            "emoji": "🔧", "color_hex": "#546e7a",
            "tradition_score": 60, "status_score": 65,
            "income_level": "high", "education": "high",
            "weight_trust": 0.85, "weight_clarity": 0.90,
            "weight_emotion": 0.25, "weight_action": 0.50,
            "desc": "Tech-Pragmatiker, 55. Kein Spielzeug — er will zuverlässige Lösungen. Vertraut Anbietern die langfristig da sind. Kauft {products} nur wenn es wirklich funktioniert.",
        },
        {
            "slug_tpl": "startup-gründerin",
            "name": "Julia", "age": 33,
            "emoji": "⚡", "color_hex": "#ff6f00",
            "tradition_score": 20, "status_score": 60,
            "income_level": "medium", "education": "high",
            "weight_trust": 0.55, "weight_clarity": 0.70,
            "weight_emotion": 0.65, "weight_action": 0.85,
            "desc": "Startup-Gründerin, 33. Budget-bewusst, aber investiert in was Wachstum bringt. Kauft {products} wenn der Value klar ist.",
        },
        {
            "slug_tpl": "it-admin",
            "name": "Stefan", "age": 38,
            "emoji": "🖥️", "color_hex": "#37474f",
            "tradition_score": 50, "status_score": 45,
            "income_level": "medium", "education": "high",
            "weight_trust": 0.80, "weight_clarity": 0.95,
            "weight_emotion": 0.20, "weight_action": 0.55,
            "desc": "IT-Admin, 38. Skeptisch, technikgetrieben, will Dokumentation und Support. Kauft {products} erst nach ausführlichem Test.",
        },
        {
            "slug_tpl": "digital-native-freelancer",
            "name": "Anna", "age": 26,
            "emoji": "🌐", "color_hex": "#00bcd4",
            "tradition_score": 10, "status_score": 55,
            "income_level": "medium", "education": "high",
            "weight_trust": 0.45, "weight_clarity": 0.65,
            "weight_emotion": 0.70, "weight_action": 0.80,
            "desc": "Digital-Native Freelancerin, 26. Selbstständig, remote-first, tool-affin. Kauft {products} wenn es ihren Workflow verbessert.",
        },
    ],

    "food": [
        {
            "slug_tpl": "genuss-hedonist",
            "name": "Marco", "age": 35,
            "emoji": "🍷", "color_hex": "#c62828",
            "tradition_score": 30, "status_score": 65,
            "income_level": "high", "education": "medium",
            "weight_trust": 0.55, "weight_clarity": 0.50,
            "weight_emotion": 0.90, "weight_action": 0.70,
            "desc": "Genuss-Hedonist, 35. Lebt für gutes Essen und besondere Erlebnisse. Kauft {products} wenn der erste Eindruck begeistert.",
        },
        {
            "slug_tpl": "familien-einkäuferin",
            "name": "Sandra", "age": 41,
            "emoji": "🏠", "color_hex": "#f57f17",
            "tradition_score": 65, "status_score": 45,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.80, "weight_clarity": 0.85,
            "weight_emotion": 0.55, "weight_action": 0.65,
            "desc": "Familien-Einkäuferin, 41. Kauft für die ganze Familie, pragmatisch und verlässlich. Vertraut {products} wenn Qualität und Preis stimmen.",
        },
        {
            "slug_tpl": "gesundheitsbewusste",
            "name": "Nina", "age": 32,
            "emoji": "🥗", "color_hex": "#558b2f",
            "tradition_score": 45, "status_score": 60,
            "income_level": "medium", "education": "high",
            "weight_trust": 0.85, "weight_clarity": 0.70,
            "weight_emotion": 0.60, "weight_action": 0.45,
            "desc": "Gesundheitsbewusste, 32. Achtet auf Inhaltsstoffe, Bio und Herkunft. Kauft {products} nur mit klaren Qualitätssignalen.",
        },
        {
            "slug_tpl": "food-entdecker",
            "name": "Ben", "age": 27,
            "emoji": "🌮", "color_hex": "#e65100",
            "tradition_score": 15, "status_score": 50,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.35, "weight_clarity": 0.45,
            "weight_emotion": 0.90, "weight_action": 0.80,
            "desc": "Food-Entdecker, 27. Probiert alles Neue, teilt seine Erlebnisse auf Social Media. Kauft {products} aus Neugier.",
        },
        {
            "slug_tpl": "budget-haushalt",
            "name": "Petra", "age": 48,
            "emoji": "🛒", "color_hex": "#78909c",
            "tradition_score": 70, "status_score": 25,
            "income_level": "low", "education": "low",
            "weight_trust": 0.75, "weight_clarity": 0.90,
            "weight_emotion": 0.40, "weight_action": 0.70,
            "desc": "Budget-Haushalt, 48. Kauft nach Preis und Gewohnheit. Kauft {products} nur wenn der Preis überzeugt.",
        },
    ],

    "gesundheit": [
        {
            "slug_tpl": "vorsorge-bewusste",
            "name": "Dr. Andrea", "age": 47,
            "emoji": "🏥", "color_hex": "#0097a7",
            "tradition_score": 50, "status_score": 80,
            "income_level": "high", "education": "high",
            "weight_trust": 0.95, "weight_clarity": 0.85,
            "weight_emotion": 0.35, "weight_action": 0.40,
            "desc": "Vorsorge-Bewusste, 47. Gut informiert, stellt hohe Ansprüche an Evidenz. Vertraut {products} nur mit klinischen Belegen.",
        },
        {
            "slug_tpl": "fitness-enthusiast",
            "name": "Max", "age": 30,
            "emoji": "💪", "color_hex": "#ff5252",
            "tradition_score": 25, "status_score": 60,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.60, "weight_clarity": 0.65,
            "weight_emotion": 0.80, "weight_action": 0.85,
            "desc": "Fitness-Enthusiast, 30. Optimiert Körper und Geist. Kauft {products} wenn es seine Performance steigert.",
        },
        {
            "slug_tpl": "senior-gesundheitsuser",
            "name": "Hans", "age": 68,
            "emoji": "👴", "color_hex": "#5d4037",
            "tradition_score": 85, "status_score": 40,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.95, "weight_clarity": 0.90,
            "weight_emotion": 0.30, "weight_action": 0.30,
            "desc": "Senior Gesundheitsnutzer, 68. Braucht einfache, klare Kommunikation. Kauft {products} nur wenn er versteht was es macht.",
        },
        {
            "slug_tpl": "wellbeing-millennialin",
            "name": "Jana", "age": 34,
            "emoji": "🧘", "color_hex": "#7b1fa2",
            "tradition_score": 40, "status_score": 58,
            "income_level": "medium", "education": "high",
            "weight_trust": 0.75, "weight_clarity": 0.60,
            "weight_emotion": 0.80, "weight_action": 0.50,
            "desc": "Wellbeing-Millennialin, 34. Ganzheitlicher Ansatz: Körper, Geist, Seele. Kauft {products} wenn es ihren Lifestyle ergänzt.",
        },
    ],

    "immobilien": [
        {
            "slug_tpl": "erstvermögensaufbauer",
            "name": "Tobias", "age": 33,
            "emoji": "🏗️", "color_hex": "#1976d2",
            "tradition_score": 45, "status_score": 60,
            "income_level": "medium", "education": "high",
            "weight_trust": 0.80, "weight_clarity": 0.75,
            "weight_emotion": 0.50, "weight_action": 0.65,
            "desc": "Erst-Vermögensaufbauer, 33. Kauft seine erste Immobilie, informiert sich ausführlich. Entscheidet bei {products} nach Sicherheit und Rendite.",
        },
        {
            "slug_tpl": "premium-investor",
            "name": "Dr. Klaus", "age": 58,
            "emoji": "🏰", "color_hex": "#1a237e",
            "tradition_score": 65, "status_score": 95,
            "income_level": "high", "education": "high",
            "weight_trust": 0.90, "weight_clarity": 0.75,
            "weight_emotion": 0.30, "weight_action": 0.55,
            "desc": "Premium-Investor, 58. Mehrere Objekte im Portfolio. Kauft {products} auf Basis von Rendite-Analysen und persönlicher Beratung.",
        },
        {
            "slug_tpl": "familie-eigenheim",
            "name": "Katrin", "age": 39,
            "emoji": "🏡", "color_hex": "#ef6c00",
            "tradition_score": 60, "status_score": 50,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.85, "weight_clarity": 0.80,
            "weight_emotion": 0.60, "weight_action": 0.50,
            "desc": "Familie & Eigenheim, 39. Kauft für die Zukunft der Familie. Vertraut {products} wenn Lage, Qualität und Sicherheit stimmen.",
        },
    ],

    "auto": [
        {
            "slug_tpl": "performance-fahrer",
            "name": "Kevin", "age": 38,
            "emoji": "🏎️", "color_hex": "#b71c1c",
            "tradition_score": 30, "status_score": 75,
            "income_level": "high", "education": "medium",
            "weight_trust": 0.50, "weight_clarity": 0.55,
            "weight_emotion": 0.90, "weight_action": 0.85,
            "desc": "Performance-Fahrer, 38. Lebt für PS und Fahrerlebnis. Kauft {products} wenn es ihn begeistert und sein Status-Gefühl bedient.",
        },
        {
            "slug_tpl": "familienauto-käufer",
            "name": "Markus", "age": 44,
            "emoji": "🚗", "color_hex": "#37474f",
            "tradition_score": 60, "status_score": 50,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.80, "weight_clarity": 0.85,
            "weight_emotion": 0.45, "weight_action": 0.60,
            "desc": "Familienauto-Käufer, 44. Sicherheit, Platz, Zuverlässigkeit zählen. Kauft {products} nach rationaler Abwägung.",
        },
        {
            "slug_tpl": "öko-mobilist",
            "name": "Felix", "age": 36,
            "emoji": "⚡", "color_hex": "#2e7d32",
            "tradition_score": 40, "status_score": 65,
            "income_level": "high", "education": "high",
            "weight_trust": 0.75, "weight_clarity": 0.70,
            "weight_emotion": 0.65, "weight_action": 0.55,
            "desc": "Öko-Mobilist, 36. Fährt elektrisch aus Überzeugung, nicht aus Zwang. Kauft {products} wenn Reichweite, Ladeinfra und Nachhaltigkeit stimmen.",
        },
    ],

    "reise": [
        {
            "slug_tpl": "luxury-traveler",
            "name": "Christine", "age": 49,
            "emoji": "✈️", "color_hex": "#0288d1",
            "tradition_score": 35, "status_score": 90,
            "income_level": "high", "education": "high",
            "weight_trust": 0.80, "weight_clarity": 0.60,
            "weight_emotion": 0.70, "weight_action": 0.50,
            "desc": "Luxury Traveler, 49. 5-Sterne oder gar nicht. Buchungsentscheidung bei {products} hängt von Exklusivität und Service ab.",
        },
        {
            "slug_tpl": "backpacker",
            "name": "Jonas", "age": 25,
            "emoji": "🎒", "color_hex": "#ff8f00",
            "tradition_score": 10, "status_score": 40,
            "income_level": "low", "education": "medium",
            "weight_trust": 0.30, "weight_clarity": 0.50,
            "weight_emotion": 0.90, "weight_action": 0.85,
            "desc": "Backpacker, 25. Budget-Reiser, Abenteuer vor Komfort. Kauft {products} impulsiv wenn die Emotion stimmt.",
        },
        {
            "slug_tpl": "familien-urlauber",
            "name": "Birgit", "age": 43,
            "emoji": "🏖️", "color_hex": "#f9a825",
            "tradition_score": 55, "status_score": 45,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.85, "weight_clarity": 0.80,
            "weight_emotion": 0.60, "weight_action": 0.55,
            "desc": "Familien-Urlauber, 43. Plant sorgfältig, bucht früh. Vertraut {products} wenn Bewertungen und Sicherheit stimmen.",
        },
    ],

    "sport": [
        {
            "slug_tpl": "leistungssportler",
            "name": "David", "age": 27,
            "emoji": "🏆", "color_hex": "#ffd600",
            "tradition_score": 20, "status_score": 65,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.55, "weight_clarity": 0.60,
            "weight_emotion": 0.85, "weight_action": 0.95,
            "desc": "Leistungssportler, 27. Performance ist alles. Kauft {products} nur wenn es ihm messbare Vorteile bringt.",
        },
        {
            "slug_tpl": "fitness-einsteiger",
            "name": "Lisa", "age": 34,
            "emoji": "🏃", "color_hex": "#e91e63",
            "tradition_score": 50, "status_score": 50,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.70, "weight_clarity": 0.80,
            "weight_emotion": 0.65, "weight_action": 0.70,
            "desc": "Fitness-Einsteigerin, 34. Motiviert aber unverfahren. Kauft {products} wenn es einfach und motivierend kommuniziert ist.",
        },
        {
            "slug_tpl": "outdoor-abenteurer",
            "name": "Simon", "age": 31,
            "emoji": "⛰️", "color_hex": "#4e342e",
            "tradition_score": 35, "status_score": 55,
            "income_level": "medium", "education": "high",
            "weight_trust": 0.65, "weight_clarity": 0.70,
            "weight_emotion": 0.75, "weight_action": 0.80,
            "desc": "Outdoor-Abenteurer, 31. Wandern, Klettern, Radfahren — braucht zuverlässige Ausrüstung. Kauft {products} nach Qualität und Echtheit.",
        },
    ],

    "finanzen": [
        {
            "slug_tpl": "vermögensaufbauer",
            "name": "Patrick", "age": 36,
            "emoji": "📈", "color_hex": "#1b5e20",
            "tradition_score": 40, "status_score": 70,
            "income_level": "high", "education": "high",
            "weight_trust": 0.85, "weight_clarity": 0.90,
            "weight_emotion": 0.30, "weight_action": 0.60,
            "desc": "Vermögensaufbauer, 36. Investiert langfristig, informiert sich gründlich. Kauft {products} nur nach ausführlicher Prüfung.",
        },
        {
            "slug_tpl": "altersvorsorge-planer",
            "name": "Renate", "age": 54,
            "emoji": "🏦", "color_hex": "#1a237e",
            "tradition_score": 70, "status_score": 55,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.95, "weight_clarity": 0.85,
            "weight_emotion": 0.25, "weight_action": 0.35,
            "desc": "Altersvorsorge-Planerin, 54. Sicherheit vor Rendite. Kauft {products} nur bei absolutem Vertrauen in den Anbieter.",
        },
        {
            "slug_tpl": "fintech-nutzer",
            "name": "Alex", "age": 29,
            "emoji": "📱", "color_hex": "#00b0ff",
            "tradition_score": 15, "status_score": 60,
            "income_level": "medium", "education": "high",
            "weight_trust": 0.60, "weight_clarity": 0.75,
            "weight_emotion": 0.55, "weight_action": 0.85,
            "desc": "Fintech-Nutzer, 29. Digital-first, liebt einfache UX. Kauft {products} wenn Onboarding reibungslos und transparent ist.",
        },
    ],

    "handel": [
        {
            "slug_tpl": "schnäppchenjäger",
            "name": "Jürgen", "age": 45,
            "emoji": "🛒", "color_hex": "#e65100",
            "tradition_score": 60, "status_score": 30,
            "income_level": "low", "education": "low",
            "weight_trust": 0.60, "weight_clarity": 0.90,
            "weight_emotion": 0.55, "weight_action": 0.85,
            "desc": "Schnäppchenjäger, 45. Kauft nur mit Rabatt. Reagiert stark auf klare Preis-Kommunikation bei {products}.",
        },
        {
            "slug_tpl": "qualitätskäufer",
            "name": "Elisabeth", "age": 52,
            "emoji": "⭐", "color_hex": "#4a148c",
            "tradition_score": 65, "status_score": 70,
            "income_level": "high", "education": "high",
            "weight_trust": 0.90, "weight_clarity": 0.75,
            "weight_emotion": 0.45, "weight_action": 0.40,
            "desc": "Qualitätskäuferin, 52. Kauft weniger, aber besser. Entscheidet bei {products} nach Bewertungen und Markenwerten.",
        },
        {
            "slug_tpl": "convenience-shopper",
            "name": "Florian", "age": 31,
            "emoji": "⚡", "color_hex": "#00838f",
            "tradition_score": 35, "status_score": 50,
            "income_level": "medium", "education": "medium",
            "weight_trust": 0.65, "weight_clarity": 0.70,
            "weight_emotion": 0.60, "weight_action": 0.80,
            "desc": "Convenience-Shopper, 31. Hauptsache schnell & einfach. Kauft {products} wenn Lieferzeit und UX stimmen.",
        },
    ],
}

# Fallback für unbekannte Branchen
FALLBACK_PERSONAS = [
    {
        "slug_tpl": "qualitätsorientierter",
        "name": "Stefan", "age": 43,
        "emoji": "⭐", "color_hex": "#1565c0",
        "tradition_score": 55, "status_score": 65,
        "income_level": "high", "education": "high",
        "weight_trust": 0.85, "weight_clarity": 0.80,
        "weight_emotion": 0.40, "weight_action": 0.50,
        "desc": "Qualitätsorientierter Käufer, 43. Kauft durchdacht und informiert. Bewertet {products} nach Qualität und Vertrauen.",
    },
    {
        "slug_tpl": "pragmatischer-nutzer",
        "name": "Maria", "age": 37,
        "emoji": "🎯", "color_hex": "#2e7d32",
        "tradition_score": 50, "status_score": 50,
        "income_level": "medium", "education": "medium",
        "weight_trust": 0.70, "weight_clarity": 0.75,
        "weight_emotion": 0.55, "weight_action": 0.65,
        "desc": "Pragmatische Nutzerin, 37. Will Lösungen, keine Versprechen. Kauft {products} wenn Nutzen klar erkennbar ist.",
    },
    {
        "slug_tpl": "preisbewusster-entscheider",
        "name": "Andreas", "age": 50,
        "emoji": "💡", "color_hex": "#e65100",
        "tradition_score": 65, "status_score": 40,
        "income_level": "medium", "education": "medium",
        "weight_trust": 0.75, "weight_clarity": 0.85,
        "weight_emotion": 0.35, "weight_action": 0.70,
        "desc": "Preisbewusster Entscheider, 50. Vergleicht sorgfältig. Reagiert auf klare Preis-Leistungs-Kommunikation bei {products}.",
    },
]

# Größen-Modifikator: passt Weights leicht an
COMPANY_SIZE_MODIFIERS = {
    "startup":  {"weight_action": +0.10, "weight_emotion": +0.05, "weight_trust": -0.05},
    "mittel":   {"weight_trust": +0.05, "weight_clarity": +0.05},
    "gross":    {"weight_trust": +0.10, "weight_clarity": +0.10, "weight_action": -0.05},
}


def _format_products(product_1: str, product_2: str, product_3: str) -> str:
    """Erstellt lesbaren Produktstring"""
    products = [p.strip() for p in [product_1, product_2, product_3] if p and p.strip()]
    if len(products) == 0:
        return "Ihre Produkte"
    if len(products) == 1:
        return products[0]
    return ", ".join(products[:-1]) + " und " + products[-1]


def _apply_size_modifier(template: dict, company_size: str) -> dict:
    """Passt Persona-Weights anhand der Unternehmensgröße an"""
    mods = COMPANY_SIZE_MODIFIERS.get(company_size, {})
    result = template.copy()
    for field, delta in mods.items():
        result[field] = round(min(max(result.get(field, 0.5) + delta, 0.1), 1.0), 2)
    return result


def generate_custom_personas(db: Session, profile: "UserProfile") -> list:
    """
    Erzeugt 3 kundenangepasste Personas basierend auf dem UserProfile.
    Speichert sie in der DB als user-spezifische Personas (user_id gesetzt).
    Gibt die Persona-Objekte zurück.
    """
    # Alte Custom-Personas dieses Users löschen
    db.query(Persona).filter(
        Persona.user_id == profile.user_id,
        Persona.category == "custom"
    ).delete()

    industry_key = profile.industry.lower()
    pool = INDUSTRY_PERSONAS.get(industry_key, FALLBACK_PERSONAS)

    # Nimm max 3 Personas aus dem Pool (erste 3 — nach Relevanz sortiert)
    selected = pool[:3] if len(pool) >= 3 else pool + FALLBACK_PERSONAS[:3 - len(pool)]

    product_str = _format_products(
        profile.product_1 or "",
        profile.product_2 or "",
        profile.product_3 or "",
    )

    created_personas = []
    for i, tpl in enumerate(selected):
        tpl = _apply_size_modifier(tpl, profile.company_size)

        slug = f"custom-{profile.user_id}-{tpl['slug_tpl']}"
        name = f"{tpl['name']}, {tpl['age']}"
        desc = tpl["desc"].replace("{products}", product_str)

        persona = Persona(
            user_id=profile.user_id,
            slug=slug,
            name=name,
            category="custom",
            age_range=str(tpl["age"]),
            gender="mixed",
            income_level=tpl["income_level"],
            education=tpl["education"],
            tradition_score=tpl["tradition_score"],
            status_score=tpl["status_score"],
            weight_trust=tpl["weight_trust"],
            weight_clarity=tpl["weight_clarity"],
            weight_emotion=tpl["weight_emotion"],
            weight_action=tpl["weight_action"],
            avatar_emoji=tpl["emoji"],
            color_hex=tpl["color_hex"],
            description_de=desc,
            sort_order=i + 1,
            is_active=True,
        )
        db.add(persona)
        created_personas.append(persona)

    db.commit()
    for p in created_personas:
        db.refresh(p)

    return created_personas


def get_user_personas(db: Session, user_id: int) -> list:
    """
    Gibt die aktiven Personas eines Users zurück.
    Custom-Personas (category='custom') haben Vorrang vor System-Defaults.
    """
    custom = db.query(Persona).filter(
        Persona.user_id == user_id,
        Persona.category == "custom",
        Persona.is_active == True,
    ).order_by(Persona.sort_order).all()

    if custom:
        return custom

    # Fallback: System-Standard-Personas
    return db.query(Persona).filter(
        Persona.user_id.is_(None),
        Persona.is_active == True,
    ).order_by(Persona.sort_order).all()
