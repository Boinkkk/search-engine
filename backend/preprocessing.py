from collections import defaultdict
import re 
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

MONTHS_ID = {
    1: "januari", 2: "februari", 3: "maret", 4: "april",
    5: "mei", 6: "juni", 7: "juli", 8: "agustus",
    9: "september", 10: "oktober", 11: "november", 12: "desember",
}

def normalize_date_in_text(text):
    def replace_date(match):
        day, month, year = map(int, match.groups())
        month_str = MONTHS_ID.get(month, str(month))
        return f"{month_str} {year}"

    return re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", replace_date, str(text))


def bucket_number(value_str):
    """
    Mengubah angka menjadi representasi bucket yang informatif.
    1.500.000 → 'jutaan', 250.000 → 'ratusan ribu', dll.
    """
    try:
        n = float(value_str.replace(".", "").replace(",", "."))
    except ValueError:
        return value_str

    if n >= 1_000_000_000_000:
        return "triliunan"
    elif n >= 1_000_000_000:
        return "miliaran"
    elif n >= 1_000_000:
        return "jutaan"
    elif n >= 100_000:
        return "ratusan ribu"
    elif n >= 10_000:
        return "puluhan ribu"
    elif n >= 1_000:
        return "ribuan"
    else:
        return str(int(n)) 

def bucket_percent(value_str):
    try:
        n = float(value_str)
    except ValueError:
        return value_str

    if n <= 5:
        return "kecil"
    elif n <= 25:
        return "rendah"
    elif n <= 50:
        return "sedang"
    elif n <= 75:
        return "tinggi"
    else:
        return "sangat tinggi"


def normalize_symbols(text):
    text = str(text)

    text = re.sub(
        r"\bUS\$\s?([\d.,]+)",
        lambda m: f"{bucket_number(m.group(1))} dollar",
        text, flags=re.IGNORECASE
    )
    text = re.sub(
        r"\$\s?([\d.,]+)",
        lambda m: f"{bucket_number(m.group(1))} dollar",
        text
    )
    text = re.sub(
        r"\bRp\.?\s?([\d.,]+)",
        lambda m: f"{bucket_number(m.group(1))} rupiah",
        text, flags=re.IGNORECASE
    )

    text = re.sub(
        r"(\d+(?:[.,]\d+)?)\s*%",
        lambda m: f"persen {bucket_percent(m.group(1))}",
        text
    )
    text = re.sub(r"(\d+)\s*deg", "derajat", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d+)\s?km\b", "kilometer", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d+)\s?kg\b", "kilogram", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d+)\s?m\b", "meter", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d+)\s?h\b", "jam", text, flags=re.IGNORECASE)
    
    text = re.sub(
        r"\b(\d+)k\b",
        lambda m: bucket_number(str(int(m.group(1)) * 1_000)),
        text, flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(\d+)m\b",
        lambda m: bucket_number(str(int(m.group(1)) * 1_000_000)),
        text, flags=re.IGNORECASE
    )

    return text

def remove_non_year_numbers(text):
    """
    Pertahankan tahun (1900–2099) sebagai token bermakna untuk BM25.
    Hapus angka lain yang tidak memiliki konteks semantik.
    """
    # Tandai tahun dulu dengan placeholder
    text = re.sub(r"\b((?:19|20)\d{2})\b", r"TAHUN\1", text)
    # Hapus angka lain
    text = re.sub(r"\b\d+\b", "", text)
    # Kembalikan tahun
    text = re.sub(r"TAHUN((?:19|20)\d{2})", r"\1", text)
    return text


def preprocessing(text):
    
    stop_factory = StopWordRemoverFactory() 
    stop_words = set(stop_factory.get_stop_words()) 
    stem_factory = StemmerFactory() 
    stemmer = stem_factory.create_stemmer()
    
    
    text = normalize_date_in_text(text)
    text = normalize_symbols(text)
    text = text.lower()
    text = re.sub(r"^.*?,\s*cnbc indonesia\s*-\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = remove_non_year_numbers(text)   # ← tambahan step
    text = re.sub(r"\s+", " ", text).strip()
    tokens = text.split()
    tokens = [t for t in tokens if t not in stop_words]
    tokens = [stemmer.stem(t) for t in tokens]
    
    return tokens