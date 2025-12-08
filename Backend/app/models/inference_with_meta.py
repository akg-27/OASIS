# inference_with_meta.py
import argparse
import os
import json
import pandas as pd

# ML imports (only needed if running image mode)
try:
    import torch
    import timm
    import torchvision.transforms as T
    from PIL import Image
except Exception:
    torch = None
    timm = None
    T = None
    Image = None


# ---------------------------------------
# FIX 1: REMOVE argparse from import time
# ---------------------------------------

# Update metadata CSV path to backend folder structure
BASE_DIR = os.path.dirname(__file__)
META_PATH = os.path.join(BASE_DIR, "saved_artifacts", "metadata.csv")
# rename your CSV accordingly if needed

# Load metadata once (for FastAPI reuse)
meta_df = pd.read_csv(META_PATH, dtype=str)
meta_indexed = meta_df.drop_duplicates(subset=['scientific_name']).set_index('scientific_name')


def lookup_by_scientific(name):
    if name in meta_indexed.index:
        return meta_indexed.loc[name].to_dict()
    return None


def lookup_by_locality(locality):
    matched = meta_df[meta_df['locality'].str.contains(locality, case=False, na=False)]
    results = []
    for _, row in matched.iterrows():
        results.append(row.to_dict())
    return results


def image_mode(image_path, model_path, topk=3):
    if torch is None:
        raise RuntimeError("PyTorch/timm not available. Install requirements.")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    ckpt = torch.load(model_path, map_location='cpu')
    classes = ckpt.get('classes')
    if classes is None:
        raise RuntimeError("Checkpoint missing 'classes'")

    model = timm.create_model('resnet50', pretrained=False, num_classes=len(classes))
    model.load_state_dict(ckpt['model_state'])
    model.eval()

    trans = T.Compose([T.Resize((224,224)), T.ToTensor()])
    img = Image.open(image_path).convert('RGB')
    x = trans(img).unsqueeze(0)

    with torch.no_grad():
        out = model(x)
        probs = torch.softmax(out, dim=1).squeeze().tolist()

    topk_idx = sorted(enumerate(probs), key=lambda ip: -ip[1])[:topk]
    preds = []
    for i, p in topk_idx:
        name = classes[i]
        meta = lookup_by_scientific(name)
        preds.append({
            "scientific_name": name,
            "confidence": float(p),
            "family": meta.get('family','') if meta else '',
            "locality": meta.get('locality','') if meta else '',
            "detail_url": meta.get('detail_url','') if meta else ''
        })
    return {"input_image": os.path.basename(image_path), "predictions": preds}


def scientific_mode(name):
    meta = lookup_by_scientific(name)
    if meta is None:
        return {"query": name, "found": False}
    return {"query": name, "found": True, "record": meta}


def locality_mode(locality):
    results = lookup_by_locality(locality)
    if not results:
        return {"query": locality, "found": False}

    species = {}
    for r in results:
        sp = r.get('scientific_name','')
        if sp not in species:
            species[sp] = {
                "scientific_name": sp,
                "family": r.get('family',''),
                "locality": r.get('locality',''),
                "detail_url": r.get('detail_url','')
            }
    return {"query": locality, "found": True, "species": list(species.values())}


# ---------------------------------------
# FIX 2: SAFE CLI EXECUTION BLOCK
# ---------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inference + lookup for otolith project")
    parser.add_argument('--model', default='models/saved_artifacts/model.pt')
    parser.add_argument('--image')
    parser.add_argument('--scientific_name')
    parser.add_argument('--locality')
    parser.add_argument('--metadata_csv', default=META_PATH)
    parser.add_argument('--topk', type=int, default=3)
    args = parser.parse_args()

    # Mode selection
    modes = [bool(args.image), bool(args.scientific_name), bool(args.locality)]
    if sum(modes) != 1:
        print("Error: use exactly one of --image, --scientific_name, --locality")
        exit(1)

    if args.image:
        out = image_mode(args.image, args.model, topk=args.topk)
    elif args.scientific_name:
        out = scientific_mode(args.scientific_name)
    else:
        out = locality_mode(args.locality)

    print(json.dumps(out, indent=2))
