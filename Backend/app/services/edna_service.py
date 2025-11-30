import os
import re
import time
import io
import requests
import logging
from typing import Dict, Any, Optional
from Bio import Entrez
from Bio.Blast import NCBIXML
from dotenv import load_dotenv
from app.database import supabase

# -----------------------------
# LOGGINGS
# -----------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("edna_service")
load_dotenv()

Entrez.email = os.getenv("NCBI_EMAIL", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", None)
if NCBI_API_KEY:
    Entrez.api_key = NCBI_API_KEY

BLAST_URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
POLL_INTERVAL = 3
POLL_MAX_TIME = 150


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean_sequence(seq: str) -> str:
    """Normalize DNA sequence: keep ACTG, remove whitespace, convert U→T."""
    cleaned = re.sub(r"[^ACGTUacgtu]", "", seq)
    cleaned = cleaned.replace("U", "T").upper()
    return cleaned


def save_record(record: Dict[str, Any], update_id: Optional[str] = None) -> Dict[str, Any]:
    """Insert or update Supabase row."""
    cleaned = {k: (None if (isinstance(v, float) and v != v) else v) for k, v in record.items()}

    if update_id:
        res = supabase.table("edna_data").update(cleaned).eq("id", update_id).execute()
        logger.info("Updated edna_data id=%s", update_id)
        return res.data

    res = supabase.table("edna_data").insert(cleaned).execute()
    logger.info("Inserted new edna_data record")
    return res.data


# ---------------------------------------------------------
# BLAST SUBMIT
# ---------------------------------------------------------

def submit_blast(sequence: str) -> Optional[str]:
    data = {
        "CMD": "Put",
        "PROGRAM": "blastn",
        "DATABASE": "nt",
        "QUERY": sequence,
        "MEGABLAST": "on",
        "EMAIL": Entrez.email
    }

    headers = {"User-Agent": "SIH-EDNA-TOOL/1.0"}

    try:
        resp = requests.post(BLAST_URL, data=data, headers=headers, timeout=30)
        resp.raise_for_status()
        text = resp.text

        m = re.search(r"RID = ([A-Z0-9\-]+)", text)
        if m:
            rid = m.group(1).strip()
            logger.info("BLAST RID FOUND: %s", rid)
            return rid

        logger.error("BLAST submit failed — no RID found")
        return None

    except Exception as e:
        logger.error("BLAST SUBMIT ERROR: %s", e)
        return None


# ---------------------------------------------------------
# BLAST POLLING
# ---------------------------------------------------------

def poll_blast_for_rid(rid: str) -> Optional[str]:
    start = time.time()

    while True:
        if time.time() - start > POLL_MAX_TIME:
            logger.error("BLAST TIMEOUT for RID %s", rid)
            return None

        params = {"CMD": "Get", "RID": rid, "FORMAT_TYPE": "XML"}

        try:
            resp = requests.get(BLAST_URL, params=params, timeout=30)
            resp.raise_for_status()
            text = resp.text

            if "Status=WAITING" in text:
                time.sleep(POLL_INTERVAL)
                continue

            if "Status=FAILED" in text or "Status=UNKNOWN" in text:
                logger.error("BLAST FAILED for RID %s", rid)
                return None

            if "<BlastOutput" in text:
                logger.info("BLAST XML READY for RID %s", rid)
                return text

        except Exception as e:
            logger.error("BLAST POLL ERROR for RID %s: %s", rid, e)
            time.sleep(POLL_INTERVAL)
            continue


# ---------------------------------------------------------
# PARSE BLAST XML
# ---------------------------------------------------------

def parse_blast_xml_for_top_hit(xml_text: str) -> Optional[Dict[str, Any]]:
    try:
        handle = io.StringIO(xml_text)
        blast_record = NCBIXML.read(handle)
    except Exception as e:
        logger.error("BLAST XML PARSE ERROR: %s", e)
        return None

    if not blast_record.alignments:
        logger.info("NO BLAST ALIGNMENTS FOUND")
        return None

    top_alignment = blast_record.alignments[0]
    top_hsp = top_alignment.hsps[0]

    hit_def = top_alignment.hit_def
    accession = top_alignment.accession
    identity_pct = (top_hsp.identities / top_hsp.align_length) * 100

    return {
        "hit_def": hit_def,
        "accession": accession,
        "identity_pct": round(identity_pct, 3),
        "align_len": top_hsp.align_length,
        "evalue": top_hsp.expect,
        "score": top_hsp.bits
    }


# ---------------------------------------------------------
# TAXONOMY
# ---------------------------------------------------------

def fetch_taxonomy_for_name(name: str) -> Optional[Dict[str, Any]]:
    try:
        search = Entrez.esearch(db="taxonomy", term=name, retmode="xml")
        rec = Entrez.read(search)
        ids = rec.get("IdList", [])
        if not ids:
            return None

        ef = Entrez.efetch(db="taxonomy", id=ids[0], retmode="xml")
        records = Entrez.read(ef)

        lineage = records[0].get("LineageEx", [])
        tax = {item.get("Rank"): item.get("ScientificName")
               for item in lineage if item.get("Rank")}

        curr = records[0]
        tax[curr.get("Rank")] = curr.get("ScientificName")

        # Fallback for missing order
        if "order" not in tax:
            for item in lineage:
                sci = item.get("ScientificName", "")
                if sci.endswith("formes") or sci.endswith("iformes"):
                    tax["order"] = sci
                    break

        return {
            "kingdom": tax.get("superkingdom") or tax.get("kingdom"),
            "phylum": tax.get("phylum"),
            "class": tax.get("class"),
            "order": tax.get("order"),
            "family": tax.get("family"),
            "genus": tax.get("genus"),
            "species": curr.get("ScientificName")
        }

    except Exception as e:
        logger.error("TAXONOMY ERROR: %s", e)
        return None


# ---------------------------------------------------------
# MAIN ANALYSIS (INSERT)
# ---------------------------------------------------------

def analyze_sequence_and_store(sequence: str) -> Dict[str, Any]:
    seq = clean_sequence(sequence)

    if len(seq) < 50:
        result = {
            "raw_sequence": seq,
            "species": None,
            "score": None,
            "identity": None,
            "evalue": None,
            "taxonomy": None,
            "note": "sequence_too_short"
        }
        save_record(result)
        return result

    rid = submit_blast(seq)
    if not rid:
        result = {"raw_sequence": seq, "note": "blast_submit_failed"}
        save_record(result)
        return result

    xml = poll_blast_for_rid(rid)
    if not xml:
        result = {"raw_sequence": seq, "blast_rid": rid, "note": "blast_poll_failed"}
        save_record(result)
        return result

    top = parse_blast_xml_for_top_hit(xml)
    if not top:
        result = {"raw_sequence": seq, "blast_rid": rid, "note": "no_hits_found"}
        save_record(result)
        return result

    # Species extraction
    hit_def = top["hit_def"]
    hit_words = hit_def.split()
    species_guess = None
    if len(hit_words) >= 2 and hit_words[0][0].isupper():
        species_guess = f"{hit_words[0]} {hit_words[1]}"
    elif len(hit_words) >= 2:
        species_guess = f"{hit_words[0]} {hit_words[1]}"

    taxonomy = fetch_taxonomy_for_name(species_guess) if species_guess else None

    record = {
        "raw_sequence": seq,
        "species": species_guess,
        "score": float(top["score"]),
        "identity": float(top["identity_pct"]),
        "evalue": float(top["evalue"]),
        "taxonomy": taxonomy,
        "blast_rid": rid
    }

    save_record(record)
    return record
