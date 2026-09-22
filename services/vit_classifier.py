"""
Plant Identification Vision Transformer (ViT-B) Service
Model: juppy44/plant-identification-2m-vit-b
Fine-tuned on 2,000,000 GBIF / iNaturalist occurrences across 14,000+ plant & tree species.
Provides high-precision botanical species classification and maps scientific taxonomy
to English and Gujarati vernacular names for the SMC Tree Census.
"""
import os
import re
from pathlib import Path
from PIL import Image

# Global singletons for model caching to avoid reloading weights on every request
_vit_processor = None
_vit_model = None
_model_load_attempted = False
_model_load_error = None

# Botanical taxonomy dictionary for common urban trees in Gujarat / Surat
BOTANICAL_TAXONOMY = {
    "azadirachta indica": {
        "english": "Neem / Indian Lilac",
        "gujarati": "લીમડો",
        "family": "Meliaceae",
        "ecological": "Highly medicinal, excellent air purifier, repels pests, and provides cooling shade.",
        "growth_stage": "Mature",
        "avg_age": 25
    },
    "ficus benghalensis": {
        "english": "Banyan Tree",
        "gujarati": "વડ (વડલો)",
        "family": "Moraceae",
        "ecological": "Sacred keystone species supporting extensive bird, bat, and insect biodiversity.",
        "growth_stage": "Old",
        "avg_age": 60
    },
    "ficus religiosa": {
        "english": "Sacred Fig / Peepal",
        "gujarati": "પીપળ (પીપળો)",
        "family": "Moraceae",
        "ecological": "Remarkable 24-hour oxygen-releasing tree with high cultural and medicinal value.",
        "growth_stage": "Mature",
        "avg_age": 40
    },
    "delonix regia": {
        "english": "Gulmohar / Royal Poinciana",
        "gujarati": "ગુલમહોર",
        "family": "Fabaceae",
        "ecological": "Ornamental avenue tree with vivid crimson blossoms, moderate wind and heat resistance.",
        "growth_stage": "Mature",
        "avg_age": 18
    },
    "polyalthia longifolia": {
        "english": "False Ashoka / Mast Tree",
        "gujarati": "આસોપાલવ",
        "family": "Annonaceae",
        "ecological": "Popular noise-reducing and windbreak avenue tree frequently planted along Surat urban roads.",
        "growth_stage": "Mature",
        "avg_age": 15
    },
    "mangifera indica": {
        "english": "Mango Tree",
        "gujarati": "આંબો",
        "family": "Anacardiaceae",
        "ecological": "High carbon sequestration, fruit-bearing canopy supporting avian diversity.",
        "growth_stage": "Mature",
        "avg_age": 30
    },
    "tamarindus indica": {
        "english": "Tamarind Tree",
        "gujarati": "આંબલી",
        "family": "Fabaceae",
        "ecological": "Drought-hardy tree with long lifespan, dense windbreak canopy, and sour pod fruits.",
        "growth_stage": "Mature",
        "avg_age": 50
    },
    "alstonia scholaris": {
        "english": "Devil's Tree / Saptaparni",
        "gujarati": "સપ્તપર્ણી",
        "family": "Apocynaceae",
        "ecological": "Fast-growing evergreen tree with whorled leaves and strongly fragrant autumnal blossoms.",
        "growth_stage": "Young",
        "avg_age": 12
    },
    "cassia fistula": {
        "english": "Golden Shower / Amaltas",
        "gujarati": "ગરમાળો",
        "family": "Fabaceae",
        "ecological": "Native deciduous tree with showy pendulous yellow flower clusters; attracts honeybees.",
        "growth_stage": "Mature",
        "avg_age": 20
    },
    "peltophorum pterocarpum": {
        "english": "Yellow Gulmohar / Copperpod",
        "gujarati": "પીળો ગુલમહોર",
        "family": "Fabaceae",
        "ecological": "Urban hardy shade tree with bright yellow erect flower panicles.",
        "growth_stage": "Mature",
        "avg_age": 15
    },
    "syzygium cumini": {
        "english": "Jamun / Black Plum",
        "gujarati": "જાંબુડો",
        "family": "Myrtaceae",
        "ecological": "High moisture-tolerant tree with dense canopy and edible anthocyanin-rich fruits.",
        "growth_stage": "Mature",
        "avg_age": 35
    },
    "pithecellobium dulce": {
        "english": "Manila Tamarind / Madras Thorn",
        "gujarati": "ગોરસ આંબલી",
        "family": "Fabaceae",
        "ecological": "Spiny drought-resilient nitrogen-fixing tree thriving in Surat's saline/alluvial soil.",
        "growth_stage": "Mature",
        "avg_age": 22
    },
    "bauhinia variegata": {
        "english": "Mountain Ebony / Orchid Tree",
        "gujarati": "કાંચનાર",
        "family": "Fabaceae",
        "ecological": "Butterfly-shaped leaves and orchid-like blossoms; traditional medicinal value.",
        "growth_stage": "Young",
        "avg_age": 10
    },
    "pongamia pinnata": {
        "english": "Indian Beech / Karanj",
        "gujarati": "કરંજ",
        "family": "Fabaceae",
        "ecological": "Hardy nitrogen-fixing avenue tree; seed oil is utilized for bio-diesel and folk medicine.",
        "growth_stage": "Mature",
        "avg_age": 20
    },
    "moringa oleifera": {
        "english": "Drumstick Tree",
        "gujarati": "સરગવો",
        "family": "Moringaceae",
        "ecological": "Rapidly growing nutrient-dense tree thriving in subtropical urban backyards.",
        "growth_stage": "Young",
        "avg_age": 8
    },
    "terminalia catappa": {
        "english": "Indian Almond / Tropical Almond",
        "gujarati": "બદામ (દેશી બદામ)",
        "family": "Combretaceae",
        "ecological": "Broad pagoda-tiered canopy providing immense street shade in coastal climates.",
        "growth_stage": "Mature",
        "avg_age": 20
    },
    "aegle marmelos": {
        "english": "Bael / Wood Apple",
        "gujarati": "બીલી",
        "family": "Rutaceae",
        "ecological": "Sacred indigenous tree with aromatic trifoliate leaves and medicinal hard-shelled fruits.",
        "growth_stage": "Mature",
        "avg_age": 25
    },
    "butea monosperma": {
        "english": "Flame of the Forest / Palash",
        "gujarati": "ખાખરો (કેસૂડો)",
        "family": "Fabaceae",
        "ecological": "Drought-deciduous tree famous for brilliant orange-vermilion blooms during Holi.",
        "growth_stage": "Mature",
        "avg_age": 25
    },
    "cocos nucifera": {
        "english": "Coconut Palm",
        "gujarati": "નાળિયેરી",
        "family": "Arecaceae",
        "ecological": "Signature coastal palm of South Gujarat supporting microclimatic humidity.",
        "growth_stage": "Mature",
        "avg_age": 30
    },
    "roystonea regia": {
        "english": "Royal Palm",
        "gujarati": "રોયલ પામ",
        "family": "Arecaceae",
        "ecological": "Architectural ornamental palm with columnar grey trunk and crownshaft.",
        "growth_stage": "Mature",
        "avg_age": 20
    }
}


def get_hf_token():
    """Retrieve Hugging Face token from environment or user cache."""
    token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
    if token and token.strip() and not token.strip().startswith('your_'):
        return token.strip()
        
    cache_path = Path.home() / ".cache" / "huggingface" / "token"
    if cache_path.exists():
        try:
            tok = cache_path.read_text().strip()
            if tok:
                return tok
        except Exception:
            pass
    return None


def get_vit_pipeline(model_id="juppy44/plant-identification-2m-vit-b"):
    """
    Lazy load and cache Vision Transformer processor and model.
    Returns (processor, model, error_message).
    """
    global _vit_processor, _vit_model, _model_load_attempted, _model_load_error
    
    if _vit_model is not None and _vit_processor is not None:
        return _vit_processor, _vit_model, None
        
    if _model_load_attempted and _model_load_error is not None:
        return None, None, _model_load_error
        
    _model_load_attempted = True
    
    try:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        import torch
    except ImportError:
        _model_load_error = "PyTorch or Transformers not installed in environment. Run `pip install torch transformers`."
        return None, None, _model_load_error
        
    token = get_hf_token()
    
    try:
        _vit_processor = AutoImageProcessor.from_pretrained(
            model_id,
            token=token
        )
        _vit_model = AutoModelForImageClassification.from_pretrained(
            model_id,
            token=token
        )
        _vit_model.eval()
        _model_load_error = None
        return _vit_processor, _vit_model, None
    except Exception as e:
        err_msg = str(e)
        if "403" in err_msg or "gated" in err_msg.lower() or "restricted" in err_msg.lower() or "authorized" in err_msg.lower():
            _model_load_error = (
                f"Access to '{model_id}' is restricted on Hugging Face. "
                f"Please open https://huggingface.co/{model_id} in your browser and click 'Acknowledge / Request Access' "
                f"using your Hugging Face account."
            )
        elif "401" in err_msg or "token" in err_msg.lower():
            _model_load_error = (
                f"Hugging Face authentication required for '{model_id}'. "
                f"Please add your HF_TOKEN to .env or run `huggingface-cli login`."
            )
        else:
            _model_load_error = f"Error loading model {model_id}: {err_msg}"
            
        return None, None, _model_load_error


def classify_species_vit(image_path, top_k=3):
    """
    Run Vision Transformer inference on image_path.
    Returns:
    {
        "success": bool,
        "botanical_name": str,
        "confidence_score": float,
        "top_candidates": list,
        "error": str (if failed)
    }
    """
    processor, model, err = get_vit_pipeline()
    if err:
        return {"success": False, "error": err}
        
    try:
        import torch
        from PIL import Image
        
        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        inputs = processor(images=image, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)
            
        top_probs, top_indices = torch.topk(probs, k=min(top_k, logits.shape[-1]))
        
        top_candidates = []
        for prob, idx in zip(top_probs[0], top_indices[0]):
            label = model.config.id2label.get(idx.item(), f"class_{idx.item()}")
            # Clean label formatting (GBIF species often have underscores or author citations)
            clean_label = label.replace("_", " ").strip()
            # If label contains author citation (e.g. 'Azadirachta indica A.Juss.'), extract genus and species
            parts = clean_label.split()
            if len(parts) >= 2:
                botanical_clean = f"{parts[0]} {parts[1]}"
            else:
                botanical_clean = clean_label
                
            top_candidates.append({
                "species": botanical_clean,
                "raw_label": clean_label,
                "score": round(prob.item(), 4)
            })
            
        best = top_candidates[0]
        return {
            "success": True,
            "botanical_name": best["species"],
            "confidence_score": best["score"],
            "top_candidates": top_candidates
        }
    except Exception as e:
        return {"success": False, "error": f"ViT inference failed: {str(e)}"}


def enrich_botanical_metadata(botanical_name, confidence_score):
    """
    Map scientific botanical name to Gujarat / Surat census attributes:
    - English common name
    - Gujarati name in Gujarati script
    - Family
    - Estimated age, growth stage, ecological value
    """
    clean_key = botanical_name.lower().strip()
    entry = BOTANICAL_TAXONOMY.get(clean_key)
    
    # Fuzzy lookup if exact match not found
    if not entry:
        for known_key, known_val in BOTANICAL_TAXONOMY.items():
            genus = known_key.split()[0]
            if clean_key.startswith(genus):
                entry = known_val
                break
                
    if confidence_score >= 0.75:
        conf_label = "High"
    elif confidence_score >= 0.40:
        conf_label = "Medium"
    else:
        conf_label = "Low"
        
    if entry:
        return {
            "common_name_english": entry["english"],
            "common_name_gujarati": entry["gujarati"],
            "botanical_name": botanical_name,
            "family": entry["family"],
            "health_condition": "Good",
            "estimated_age": entry.get("avg_age", 20),
            "growth_stage": entry.get("growth_stage", "Mature"),
            "description": f"Identified via ViT botanical classifier as {entry['english']} ({botanical_name}). Exhibits characteristic canopy spread and foliage.",
            "confidence": conf_label,
            "ecological_notes": entry["ecological"]
        }
    else:
        # Fallback for species outside the top-20 Gujarat lookup table
        genus = botanical_name.split()[0] if " " in botanical_name else botanical_name
        return {
            "common_name_english": f"{botanical_name} (Plant)",
            "common_name_gujarati": f"{genus} વૃક્ષ",
            "botanical_name": botanical_name,
            "family": "Plantae",
            "health_condition": "Good",
            "estimated_age": 15,
            "growth_stage": "Mature",
            "description": f"Botanical identification matched to species {botanical_name} via Vision Transformer with {round(confidence_score*100, 1)}% probability.",
            "confidence": conf_label,
            "ecological_notes": "Valuable green cover contributing to urban biodiversity, microclimate moderation, and carbon reduction in Surat."
        }


def analyze_with_juppy44(image_path):
    """
    End-to-end tree analysis using juppy44/plant-identification-2m-vit-b.
    Returns standard SMC Tree Census JSON schema.
    """
    res = classify_species_vit(image_path)
    if not res.get("success"):
        return res
        
    botanical = res["botanical_name"]
    score = res["confidence_score"]
    
    census_data = enrich_botanical_metadata(botanical, score)
    census_data["top_candidates"] = res.get("top_candidates", [])
    
    return {
        "success": True,
        "data": census_data,
        "provider": "juppy44/plant-identification-2m-vit-b"
    }
