import os
import re
import time
import io
import requests
from typing import Dict, Any, Optional
from xml.etree import ElementTree as ET
from Bio import Entrez
from Bio.Blast import NCBIXML
from dotenv import load_dotenv

from app.database import supabase

# Load environment
load_dotenv()

# Configure Entrez
Entrez.email = os.getenv("NCBI_EMAIL", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", None)
if NCBI_API_KEY:
    Entrez.api_key = NCBI_API_KEY

# BLAST endpoint
BLAST_URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"

# Polling configuration
POLL_INTERVAL = 3
POLL_MAX_TIME = 150


def clean_sequence(seq: str) -> str:
    """Normalize DNA sequence: keep ACTG, remove whitespace, convert U→T."""
    cleaned = re.sub(r"[^ACGTUacgtu]", "", seq)
    cleaned = cleaned.replace("U", "T").upper()
    return cleaned


# -----------------------------
# BLAST SUBMIT (REQUESTS ONLY)
# -----------------------------
def submit_blast(sequence: str) -> Optional[str]:
    """Submit query to NCBI BLAST, return RID if successful."""
    data = {
        "CMD": "Put",
        "PROGRAM": "blastn",
        "DATABASE": "nt",
        "QUERY": sequence,
        "MEGABLAST": "on",
        "EMAIL": Entrez.email,  # NCBI requires this
    }

    headers = {
        "User-Agent": "SIH-EDNA-TOOL/1.0"
    }

    try:
        resp = requests.post(BLAST_URL, data=data, headers=headers, timeout=30)
        print("\nBLAST SUBMIT RESPONSE:")
        print(resp.text[:300])

        resp.raise_for_status()
        text = resp.text

        # Extract RID
        m = re.search(r"RID = ([A-Z0-9\-]+)", text)
        if m:
            rid = m.group(1).strip()
            print("RID FOUND:", rid)
            return rid

        print("NO RID FOUND — BLAST rejected the query.")
        return None

    except Exception as e:
        print("BLAST SUBMIT ERROR:", e)
        return None


# -----------------------------
# BLAST POLLING (REQUESTS ONLY)
# -----------------------------
def poll_blast_for_rid(rid: str) -> Optional[str]:
    """Poll BLAST until result XML is ready."""
    start = time.time()

    while True:
        if time.time() - start > POLL_MAX_TIME:
            print("BLAST TIMEOUT")
            return None

        params = {
            "CMD": "Get",
            "RID": rid,
            "FORMAT_TYPE": "XML"
        }

        try:
            resp = requests.get(BLAST_URL, params=params, timeout=30)
            resp.raise_for_status()
            text = resp.text

            if "Status=WAITING" in text:
                print("BLAST WAITING...")
                time.sleep(POLL_INTERVAL)
                continue

            if "Status=FAILED" in text or "Status=UNKNOWN" in text:
                print("BLAST FAILED response:", text[:300])
                return None

            if "<BlastOutput" in text:
                print("BLAST READY — XML RECEIVED")
                return text

        except Exception as e:
            print("BLAST POLL ERROR:", e)
            time.sleep(POLL_INTERVAL)
            continue


# -----------------------------
# PARSE BLAST XML
# -----------------------------
def parse_blast_xml_for_top_hit(xml_text: str) -> Optional[Dict[str, Any]]:
    """Parse BLAST XML and extract top hit."""
    try:
        handle = io.StringIO(xml_text)
        blast_record = NCBIXML.read(handle)
    except Exception as e:
        print("BLAST XML PARSE ERROR:", e)
        return None

    if not blast_record.alignments:
        print("NO BLAST ALIGNMENTS FOUND")
        return None

    top_alignment = blast_record.alignments[0]
    top_hsp = top_alignment.hsps[0]

    hit_def = top_alignment.hit_def
    accession = top_alignment.accession
    identity_pct = (top_hsp.identities / top_hsp.align_length) * 100
    print("HIT DEF RAW:", hit_def)

    return {
        "hit_def": hit_def,
        "accession": accession,
        "identity_pct": round(identity_pct, 3),
        "align_len": top_hsp.align_length,
        "evalue": top_hsp.expect,
        "score": top_hsp.bits
    }


# -----------------------------
# NCBI TAXONOMY
# -----------------------------
def fetch_taxonomy_for_name(name: str) -> Optional[Dict[str, Any]]:
    """Fetch taxonomy for species name via Entrez."""
    try:
        search = Entrez.esearch(db="taxonomy", term=name, retmode="xml")
        rec = Entrez.read(search)
        taxids = rec.get("IdList", [])
        if not taxids:
            print("TAXONOMY NOT FOUND")
            return None

        taxid = taxids[0]
        ef = Entrez.efetch(db="taxonomy", id=taxid, retmode="xml")
        records = Entrez.read(ef)

        lineage = records[0].get("LineageEx", [])
        tax = {}
        for item in lineage:
            rank = item.get("Rank")
            sci = item.get("ScientificName")
            if rank and sci:
                tax[rank] = sci

        curr = records[0]
        tax[curr.get("Rank")] = curr.get("ScientificName")

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
        print("TAXONOMY ERROR:", e)
        return None


# -----------------------------
# FULL PIPELINE
# -----------------------------
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
        supabase.table("edna_data").insert(result).execute()
        return result

    rid = submit_blast(seq)
    if not rid:
        return {
            "raw_sequence": seq,
            "species": None,
            "score": None,
            "identity": None,
            "evalue": None,
            "taxonomy": None,
            "note": "blast_submit_failed"
        }

    xml = poll_blast_for_rid(rid)
    if not xml:
        return {
            "raw_sequence": seq,
            "species": None,
            "score": None,
            "identity": None,
            "evalue": None,
            "taxonomy": None,
            "note": "blast_poll_failed"
        }

    top = parse_blast_xml_for_top_hit(xml)
    if not top:
        return {
            "raw_sequence": seq,
            "species": None,
            "score": None,
            "identity": None,
            "evalue": None,
            "taxonomy": None,
            "note": "no_hits_found"
        }

    # extract species from hit_def
    # -----------------------------
    # Extract species from hit_def
    # -----------------------------
    hit_def = top["hit_def"]
    hit_def_words = hit_def.split()
    species_guess = None

    # Debug print so we can inspect
    print("EXTRACTING FROM HIT_DEF:", hit_def)

    # Rule: First two words typically "Genus species"
    if len(hit_def_words) >= 2:
        w1, w2 = hit_def_words[0], hit_def_words[1]

        # Case 1: Standard BLAST naming (Genus species ...)
        if w1[0].isupper() and w2[0].islower():
            species_guess = f"{w1} {w2}"

        # Case 2: Rare case where both are Capitalized
        elif w1[0].isupper() and w2[0].isupper():
            species_guess = f"{w1} {w2}"

    # Fallback — always use first two words
    if species_guess is None and len(hit_def_words) >= 2:
        species_guess = f"{hit_def_words[0]} {hit_def_words[1]}"

    print("EXTRACTED SPECIES:", species_guess)

    taxonomy = taxonomy = fetch_taxonomy_for_name(species_guess.split()[0] + " " + species_guess.split()[1]) \
           if species_guess and len(species_guess.split()) >= 2 else None


    record = {
        "raw_sequence": seq,
        "species": species_guess,
        "score": float(top["score"]),
        "identity": float(top["identity_pct"]),
        "evalue": float(top["evalue"]),
        "taxonomy": taxonomy
    }

    supabase.table("edna_data").insert(record).execute()
    return record