# inference_retrieval.py
import numpy as np, json, os, argparse
from PIL import Image
import torchvision.transforms as T
import timm, torch
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(__file__)  # directory where inference file lives
EMB_PATH = os.path.join(BASE_DIR, "saved_artifacts", "embeddings.npz")


# --------------------
# LOAD MODEL & INDEX ON IMPORT
# (this must stay outside for FastAPI to reuse single load)
# --------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = timm.create_model("resnet50", pretrained=True)
model.reset_classifier(0)
model = model.to(device)
model.eval()

trans = T.Compose([T.Resize((224,224)), T.ToTensor()])

# embeddings and metadata must load only once globally
data = np.load(EMB_PATH, allow_pickle=True)
embs = data['embeddings']
meta = data['meta']


def embed_image(path):
    img = Image.open(path).convert('RGB')
    x = trans(img).unsqueeze(0).to(device)
    with torch.no_grad():
        feat = model.forward_features(x)
        feat = torch.nn.functional.adaptive_avg_pool2d(feat,1).squeeze().cpu().numpy()
        feat = feat / (np.linalg.norm(feat) + 1e-10)
    return feat


def inference_retrieval(query_path, topk=5):
    q = embed_image(query_path)

    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(q.reshape(1, -1), embs).squeeze()

    idx = sims.argsort()[::-1][:topk]

    preds = []
    for i in idx:
        m = meta[int(i)]
        preds.append({
            'image': m['image'],
            'scientific_name': m.get('scientific_name', ''),
            'family': m.get('family', ''),
            'locality': m.get('locality', ''),
            'detail_url': m.get('detail_url', ''),
            'score': float(sims[int(i)])
        })

    return {
        'query_image': os.path.basename(query_path),
        'results': preds
    }


# -------------------------
# CLI MODE ONLY (no effect during FastAPI import)
# -------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', required=True)
    parser.add_argument('--emb_file', default='data/processed/embeddings.npz')
    parser.add_argument('--topk', type=int, default=5)
    args = parser.parse_args()

    out = inference_retrieval(args.query, args.topk)
    print(json.dumps(out, indent=2))
