# System Architecture & Design

Tämä dokumentaatio selittää Daily Insight Agentin rakennetta niin, että:
- ✅ Toinen kehittäjä ymmärtää kaiken koodin tarkoituksen
- ✅ AI voi analysoida ja kehittää järjestelmää
- ✅ Uusia ominaisuuksia voi lisätä ymmärtäen kokonaisuuden

---

## 1. Järjestelmän yleiskuvaus

### Mitä se tekee?

Daily Insight Agent on **kolmiosainen AI-järjestelmä** joka:
1. **Lukee** ulkoista sisältöä (RSS, päiväkirja, tavoitteet)
2. **Analysoi** sinun ajattelumalleja ja poikkeamia
3. **Antaa** konkreettista päivittäistä neuvoa

### Filosofia: Erikoistuneet agentit

Koska yleinen tekoäly tekee huonoja päätöksiä, käytämme **kolmea erikoistunutta agenttia**:

```
┌─────────────────────────────────┐
│    Reader Agent                 │
│    (objektiivinen yhteenveto)  │
│    - Ei arvosteluja            │
│    - Säilyttää alkuperäisen    │
│      äänen lainauksin          │
│    - Faktavs. mielipiteet      │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│    Reflection Agent             │
│    (sisäisen maailman tutkija)  │
│    - Näkee harhat              │
│    - Tunnistaa poikkeamat      │
│      tavoitteista              │
│    - Objektiivinen tarkkailija │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│    Coach Agent                  │
│    (synteesit & neuvonta)       │
│    - Yhdistää Reader +          │
│      Reflection                 │
│    - Antaa 1 konkreettinen      │
│      vinkki päivälle            │
└─────────────────────────────────┘
```

**Miksi erilliset agentit?**
- Reader ei koskaan näe päiväkirjaa (puolueeton ulkoisista lähteistä)
- Reflection ei koskaan näe uutisia (fokus sisäiseen)
- Coach saa molemmat näkökulmat = parempi neuvo

---

## 2. Data Flow - Kuinka data liikkuu

```
┌──────────────────────────────────────────────────┐
│ COLLECTION PHASE (Keruu)                         │
├──────────────────────────────────────────────────┤
│                                                  │
│ DiaryCollector    → Lukee data/diary/*.md       │
│ GoalsCollector    → Lukee data/goals/goals.txt  │
│ RSSCollector      → Hakee RSS-syötteet          │
│ WhatsAppCollector → Lukee viestit               │
│ YouTubeCollector  → Haetaan videoita (stub)     │
│ TelegramCollector → Haetaan viestejä (stub)     │
│                                                  │
│ ↓                                                │
│ Raw items (eri formaatissa)                      │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ NORMALIZATION PHASE (Standardi muoto)            │
├──────────────────────────────────────────────────┤
│                                                  │
│ normalize_items() muuntaa kaikki:                │
│                                                  │
│ "Diary entry" → ContentItem                      │
│ "RSS article" → ContentItem                      │
│ "Goal text"   → ContentItem                      │
│                                                  │
│ Jokainen ContentItem sisältää:                   │
│ - content: teksti                                │
│ - source: lähde (DIARY, RSS, jne)               │
│ - timestamp: milloin                             │
│ - metadata: lisätiedot                           │
│                                                  │
│ ↓                                                │
│ List[ContentItem] (yhtenäinen muoto)            │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ DEDUPLICATION PHASE (Ei duplikaatteja)           │
├──────────────────────────────────────────────────┤
│                                                  │
│ deduplicate_items() vertaa MD5-hasheja:          │
│                                                  │
│ Vanhat itemit: hash1, hash2, hash3               │
│ Uudet itemit:  hash3, hash4, hash5               │
│                          ↑ duplikaatti!          │
│ → Pidetään vain: hash4, hash5                   │
│                                                  │
│ ↓                                                │
│ new_items (vain uudet, ei duplikaatteja)        │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ STORAGE PHASE (Tallennus)                        │
├──────────────────────────────────────────────────┤
│                                                  │
│ save_items() tallentaa SQLite:iin                │
│ Kaikki itemit historialleen:                     │
│ - insights.db                                    │
│   - table: content_items                         │
│     - id, content, source, timestamp, hash      │
│                                                  │
│ ↓                                                │
│ Pysyvä tallennus (DB)                            │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ AGENT ANALYSIS PHASE (AI-analyysi)               │
├──────────────────────────────────────────────────┤
│                                                  │
│ STEP 1: Reader Agent                             │
│   Input: new_items                               │
│   Output: {summary, quotes, topics, sources}    │
│                                                  │
│ STEP 2: Reflection Agent                         │
│   Input: goals + recent diary                    │
│   Output: {observations, biases, alignment}     │
│                                                  │
│ STEP 3: Coach Agent                              │
│   Input: reader_output + reflection_output      │
│   Output: {tip, action, warnings}               │
│                                                  │
│ ↓                                                │
│ DailyInsight (strukturoitu lopputulos)          │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ OUTPUT PHASE (Julkaisu)                          │
├──────────────────────────────────────────────────┤
│                                                  │
│ Tulosten muuntaminen:                            │
│   - index.html (kaunis sivu)                     │
│   - YYYY-MM-DD.json (data)                       │
│   - git commit & push                            │
│   - GitHub Pages päivittyy                       │
│                                                  │
│ ↓                                                │
│ https://daily-insights.com (näkyy pilvessä)    │
└──────────────────────────────────────────────────┘
```

---

## 3. Komponentit yksityiskohtaisesti

### 3.1 Collectors - Data input layer

**Tarkoitus**: Lukea eri lähteistä ja muuntaa standardiksi

**Jokainen collector:**
```python
class BaseCollector(ABC):
    def __init__(self, source_type: SourceType):
        self.source_type = source_type
    
    @abstractmethod
    def collect(self) -> List[ContentItem]:
        """Lukee lähteestä ja palauttaa ContentItem:ejä"""
```

**Kerääjät:**

| Collector | Lähde | Luokka | Tiedosto |
|-----------|-------|--------|----------|
| DiaryCollector | `data/diary/*.md` | Paikallinen | diary_collector.py |
| GoalsCollector | `data/goals/goals.txt` | Paikallinen | goals_collector.py |
| RSSCollector | `data/rss_sources.txt` | Etä-API | rss_collector.py |
| WhatsAppCollector | `data/whatsapp_exports/*.txt` | Paikallinen | whatsapp_export_collector.py |
| YouTubeCollector | YouTube API | Etä-API | youtube_collector.py (stub) |
| TelegramCollector | Telegram API | Etä-API | telegram_collector.py (stub) |

**Esimerkki DiaryCollector:**
```python
def collect(self) -> List[ContentItem]:
    diary_items = []
    for file in Path(config.DIARY_DIR).glob("*.md"):
        content = file.read_text()
        item = ContentItem(
            content=content,
            source=SourceType.DIARY,
            timestamp=file.stat().st_mtime,
            metadata={"filename": file.name}
        )
        diary_items.append(item)
    return diary_items
```

**Laajentaminen**: Lisää uusi collector:
```python
class LinkedInCollector(BaseCollector):
    def __init__(self):
        super().__init__(SourceType.LINKEDIN)
    
    def collect(self) -> List[ContentItem]:
        # Hae LinkedIn-postaukset
        # Muuta ContentItem:iksi
        # Palauta lista
```

---

### 3.2 Services - Data processing layer

#### normalize.py
**Mitä**: Muuntaa kaikki ContentItem-standardiin

```python
def normalize_items(items: List) -> List[ContentItem]:
    """
    Ottaa sekoituksen eri muotoja:
    - strings (teksti)
    - dicts (JSON)
    - ContentItem (jo standardissa)
    - custom objektit
    
    Palauttaa List[ContentItem]
    """
```

Miksi? Koska eri keräilijät palauttavat eri formaatissa.

#### deduplicate.py
**Mitä**: Poistaa duplikaatit MD5-hashilla

```python
def deduplicate_items(
    new_items: List[ContentItem],
    existing_hashes: Set[str]
) -> List[ContentItem]:
    """
    Vertaa new_items:ien hasheja olemassa oleviin.
    Palauttaa vain uudet (ei duplikaatteja).
    
    Esimerkki:
    - new_items hash: abc123, def456, ghi789
    - existing hashes: abc123 ← duplikaatti
    - palautetaan: def456, ghi789
    """
```

Miksi? Koska RSS-syötteet voivat antaa samoja artikkeleita uudelleen.

#### storage.py
**Mitä**: SQLite-tietokanta-käyttöliittymä

```python
class StorageService:
    def save_items(self, items: List[ContentItem]) -> int:
        """Tallentaa itemit tietokantaan"""
    
    def get_existing_hashes(self) -> Set[str]:
        """Hakee kaikki olemassa olevat hashit"""
    
    def get_recent_items(self, source: SourceType, days: int = 7):
        """Hakee viimeaikaiset itemit lähteestä"""
```

**Tietokanta rakenne:**
```sql
CREATE TABLE content_items (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    source TEXT NOT NULL,  -- DIARY, RSS, GOALS, jne
    timestamp REAL NOT NULL,
    hash TEXT UNIQUE,  -- MD5 deduplikaatiota varten
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### openai_client.py
**Mitä**: Wrapper OpenAI API:lle

```python
class OpenAIClient:
    def call(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1000
    ) -> str:
        """
        Soittaa OpenAI API:lle ja palauttaa vastauksen.
        Hallinnoi retry-logiiaa ja virheitä.
        """
```

Käyttö:
```python
response = openai_client.call(
    system_prompt="You are a summarizer",
    user_message="Summarize this article: ...",
    max_tokens=500
)
```

#### daily_pipeline.py
**Mitä**: Ohjelmoi koko prosessia

```python
class DailyPipeline:
    def run(self) -> DailyInsight:
        """
        1. Kerää kaikista lähteistä
        2. Normalisoi
        3. Deduplikoi
        4. Tallentaa
        5. Ajaa 3 agenttia järjestyksessä
        6. Palauttaa DailyInsight
        """
```

---

### 3.3 Agents - AI thinking layer

#### Reader Agent
```python
class ReaderAgent(BaseAgent):
    """Objektiivin yhteenveto ulkoisesta sisällöstä"""
    
    def think(self, agent_input: AgentInput) -> dict:
        """
        Input: päivän uudet itemit
        
        Output:
        {
            "summary": "2-3 lauseen yhteenveto",
            "key_topics": ["aihe1", "aihe2"],
            "quotes": [
                {"quote": "siteetti teksti", "source": "lähde"}
            ],
            "facts_vs_opinions": {
                "facts": ["fakta1", "fakta2"],
                "opinions": ["mielipide1"]
            }
        }
        
        Periaatteet:
        - Ei hallusinaatioita
        - Säilytä lainaukset
        - Objektiivinen
        """
```

**Prompt-template** (system prompt):
```
Olet objektiivinen sisällön yhteenveto-tekijä.

TEHTÄVÄ:
Lue annetut artikkelit/sisältö ja:
1. Tee 2-3 lauseen yhteenveto
2. Tunnista pääaiheet (max 3)
3. Poimi tärkeät lainaukset
4. Erota faktat mielipiteistä

RAJOITUKSET:
- Älä hallusinointi
- Säilytä alkuperäinen ääni
- Ole objektiivinen
- Ei henkilökohtaisia arvioita

SISÄLTÖ:
{content_here}
```

#### Reflection Agent
```python
class ReflectionAgent(BaseAgent):
    """Analysoi käyttäjän sisäistä maailmaa"""
    
    def think(self, agent_input: AgentInput) -> dict:
        """
        Input: tavoitteet + viimeaikaiset päiväkirjamerkinnät
        
        Output:
        {
            "observations": [
                "Merkittävä havainto",
                "Toinen trendi"
            ],
            "biases": [
                {
                    "name": "Confirmation Bias",
                    "evidence": "Todisteita päiväkirjasta"
                }
            ],
            "alignment": {
                "aligned": ["Tavoite 1 etenee"],
                "misaligned": ["Tavoite 2 jumissa"],
                "unclear": ["Tavoite 3 - epäselvää"]
            },
            "patterns": ["Toistuva aihe 1", "Trendi 2"],
            "blindspots": ["Mitä käyttäjä ei näe"],
            "hypothesis": "Mikä on todella meneillään?"
        }
        
        Periaatteet:
        - Olet viisas tarkkailija, ei vahvistaja
        - Etsi ristiriitoja
        - Tunnista harhat
        - Sisällytä epävarmuus
        """
```

**Harhat joita seurataan:**
- Confirmation bias (etsii vain vahvistusta)
- Availability heuristic (arvioi muistiin jääneet)
- Sunk cost fallacy (jatkaa menneisyyden takia)
- Narrative fallacy (luo tarinoita selitykseksi)
- Recency bias (korostaa viimeaikaisia)

#### Coach Agent
```python
class CoachAgent(BaseAgent):
    """Syntetisoi ja antaa käytännön neuvoa"""
    
    def think(self, agent_input: AgentInput) -> dict:
        """
        Input: Reader output + Reflection output + tavoitteet
        
        Output:
        {
            "practical_tip": "Yksi konkreettinen vinkki",
            "one_day_action": "Mitä tehdä tänään (aika-arviot)",
            "warnings": ["Riski 1", "Huomio 2"],
            "confidence": 0.85
        }
        
        Periaatteet:
        - YKSI vinkki, ei lista
        - Mahdollista toteuttaa yhdessä päivässä
        - Spesifi, ei yleinen
        - Sidottu dataan
        """
```

---

### 3.4 Data Models - Tietorakenteet

#### ContentItem
```python
@dataclass
class ContentItem:
    """Universaali sisällön rakenne"""
    content: str              # Sisältö
    source: SourceType        # DIARY, RSS, GOALS, jne
    timestamp: float          # Milloin luotu (unix time)
    metadata: dict = None     # Lisätiedot (tiedostonimi, jne)
    hash: str = None         # MD5 deduplikaatiota varten (auto-generoitu)

# Esimerkki:
ContentItem(
    content="Tänään tein merkittävää edistystä projektissa",
    source=SourceType.DIARY,
    timestamp=1716201600,
    metadata={"filename": "2026-05-21.md"}
)
```

#### AgentInput
```python
@dataclass
class AgentInput:
    """Input agenteille"""
    new_items: List[ContentItem]      # Uudet itemit
    goals: str                        # Tavoitteet (teksti)
    recent_diary: List[str]           # Viimeaikaiset merkinnät
    existing_items: List[ContentItem] # Historiaa kontekstiksi
```

#### DailyInsight
```python
@dataclass
class DailyInsight:
    """Lopullinen tulos"""
    id: str                           # UUID
    created_at: datetime
    
    # Reader Agent output
    summary: str
    key_topics: List[str]
    important_quotes: List[dict]
    
    # Reflection Agent output
    key_observations: List[str]
    thinking_biases: List[dict]
    
    # Coach Agent output
    practical_tip: str
    one_day_action: str
    warnings: List[str]
```

---

## 4. Koodin organisaatio

```
app/
├── __init__.py
├── config.py                    ← Ympäristön asetukset
├── main.py                      ← FastAPI endpoint
├── models.py                    ← Dataclass-määritelmät
│
├── agents/
│   ├── base_agent.py           ← Abstrakti base-luokka
│   ├── reader_agent.py         ← Yhteenveto-tekijä
│   ├── reflection_agent.py     ← Analyysi
│   └── coach_agent.py          ← Neuvo
│
├── collectors/
│   ├── base_collector.py       ← Abstrakti base-luokka
│   ├── diary_collector.py      ← Lukee päiväkirjaa
│   ├── goals_collector.py      ← Lukee tavoitteita
│   ├── rss_collector.py        ← Hakee RSS-syötteitä
│   ├── whatsapp_export_collector.py ← WhatsApp
│   ├── youtube_collector.py    ← YouTube (stub)
│   └── telegram_collector.py   ← Telegram (stub)
│
├── services/
│   ├── normalize.py            ← Standardi muoto
│   ├── deduplicate.py          ← Duplikaatit pois
│   ├── storage.py              ← SQLite
│   ├── openai_client.py        ← OpenAI API
│   └── daily_pipeline.py       ← Orkestrointi
│
└── prompts/                     ← System prompts
    ├── reader_prompt.md
    ├── reflection_prompt.md
    └── coach_prompt.md

scripts/
├── generate_insight.py         ← GitHub Actions pääskripti
└── upload_to_onedrive.py      ← OneDrive-backup

data/
├── diary/                      ← Päiväkirja-tiedostot
├── goals/                      ← Tavoitteet
├── whatsapp_exports/           ← WhatsApp-viestit
├── rss_sources.txt             ← RSS-feed linkit
└── daily_insights/             ← Generoitavat tulokset

.github/workflows/
└── daily-insight.yml           ← GitHub Actions ajoitus

tests/
├── test_collectors.py
├── test_services.py
└── test_agents.py              ← Yksikkötestit
```

---

## 5. Suoritussekvenssi (Execution Flow)

### Milloin GitHub Actions käynnistää:
```
Päivittäin 06:00 UTC (tai workflow_dispatch manuaalisesti)
    ↓
.github/workflows/daily-insight.yml
    ↓
scripts/generate_insight.py
    ↓
DailyPipeline().run()
```

### DailyPipeline.run() vaiheet:

```
1. COLLECT
   - Kutsu kaikkia collectoreja
   - Tuloksena: List[mixed items]

2. NORMALIZE
   - Muunta kaikki ContentItem:iksi
   - Tuloksena: List[ContentItem]

3. DEDUPLICATE
   - Vertaa hasheja
   - Tuloksena: List[ContentItem] (vain uudet)

4. STORE
   - Tallenna SQLite:iin
   - Tuloksena: tallennettujen määrä

5. LOAD CONTEXT
   - Lataa tavoitteet tiedostosta
   - Lataa viimeaikaiset päiväkirjamerkinnät

6. RUN AGENTS (SEKVENTIAALINEN)
   
   a) ReaderAgent.think(new_items)
      ↓
      reader_output = {summary, quotes, topics, ...}
   
   b) ReflectionAgent.think(goals, diary)
      ↓
      reflection_output = {observations, biases, patterns, ...}
   
   c) CoachAgent.think(reader_output, reflection_output)
      ↓
      coach_output = {tip, action, warnings}

7. COMBINE
   - Yhdistä kaikki outputit DailyInsight:ksi

8. SAVE
   - Tallenna DailyInsight tietokantaan

9. RETURN
   - Palauta DailyInsight objekti
```

---

## 6. Laajentamispisteet (Extension Points)

### Uusi Collector lisääminen

```python
# 1. Luo uusi tiedosto: app/collectors/example_collector.py

from app.collectors.base_collector import BaseCollector
from app.models import ContentItem, SourceType

class ExampleCollector(BaseCollector):
    def __init__(self):
        super().__init__(SourceType.EXAMPLE)  # Lisää SourceType ensin
    
    def collect(self) -> List[ContentItem]:
        items = []
        # Hakulogiikka tähän
        return items

# 2. Lisää SourceType enumiin (app/models.py)

class SourceType(str, Enum):
    EXAMPLE = "example"

# 3. Lisää pipelineen (app/services/daily_pipeline.py)

from app.collectors.example_collector import ExampleCollector

self.collectors.append(ExampleCollector())
```

### Uusi Agent lisääminen

```python
# 1. Luo uusi tiedosto: app/agents/custom_agent.py

from app.agents.base_agent import BaseAgent
from app.models import AgentInput

class CustomAgent(BaseAgent):
    def think(self, agent_input: AgentInput) -> dict:
        system_prompt = self._load_system_prompt("custom")
        # AI-logiikka
        return {"key": "value"}

# 2. Luo prompt-tiedosto: app/prompts/custom_prompt.md

# 3. Lisää pipelineen (app/services/daily_pipeline.py)

custom_output = CustomAgent().think(agent_input)
```

---

## 7. Tekniset yksityiskohdat

### Salasanojen hallinta
- API-avaimet `.env` tiedostossa (ei koodissa)
- GitHub Actionissa: Secrets
- Paikallisesti: `.env.example` malli

### Virheenkäsittely
- Collector epäonnistuu? → Jatka muista
- OpenAI API kaatuu? → Palaa osittaisella tuloksella
- Tietokanta kaatuu? → Logged error

### Performance
- RSS-haku on hitain (verkosta)
- OpenAI-kutsut ovat kalleimpia (token-pohjainen)
- Deduplikaatio on nopea (hash-vertailu)

### Turvallisuus
- Vain viimeaikaiset päiväkirjamerkinnät → OpenAI (ei historian)
- WhatsApp-yhteenvedot (ei täysiä viestejä)
- SQLite paikallinen (ei pilvessä oletuksena)

---

## 8. Kehittäjille: Testaus

```bash
# Yksikkötestit
pytest tests/test_collectors.py -v

# Integraatiotestit
pytest tests/test_services.py -v

# Pipeline-testit
pytest tests/ -v

# Coverage
pytest --cov=app tests/
```

---

## 9. Yhteenveto: Mitä AI:lle pitäisi kertoa

Kun kopioitaan koko README.md + tämä tiedosto AI:lle:

✅ **AI ymmärtää:**
- Kolmen agentin filosofia (erikoistumus)
- Data flow (collection → normalization → analysis)
- Komponenttien arkkitehtuuri
- Laajentamispisteet
- Testausstrategia
- Turvallisuusperiaatteet

✅ **AI voi kehittää:**
- Uusia agentteja (Risk Analyzer, Trend Detector)
- Uusia collectoreja (LinkedIn, Twitter)
- Parempia prompteja
- Uusia ominaisuuksia
- Rakennetta refaktoroida

✅ **Ihminen ymmärtää:**
- Miksi järjestelmä on rakennettu näin
- Kuinka lisätä uusia asioita
- Kuinka testata muutoksia
- Kuinka fii korjata virheitä
