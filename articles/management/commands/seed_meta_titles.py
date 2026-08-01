"""
Fill in SEO titles that target Moldovan search queries.

Why this exists
---------------
Search Console (90 days) showed penitadreptului.md averaging position 8.0 with a
7.1% CTR — better than precedentia.md on both counts — yet only 1180 impressions
against precedentia's 19500. The site ranks fine; it is simply shown for very
few queries.

Checking the SERP explained why. For "cercetarea la fata locului procedura
penala" the entire first page is Romanian (.ro) sites — legeaz.net,
euroavocatura.ro, wolterskluwer.ro — competing on a market roughly eight times
larger with far older domains. Add a Moldovan marker to the same query
("... Republica Moldova CPP") and penitadreptului.md is first, with no .ro
domains present at all.

The article bodies are already Moldovan (one carries 19 mentions of CPP, 11 of
Moldova) — but the titles were neutral, so they advertised the fight the site
cannot win. Each title below keeps the author's original wording and appends the
statute the article actually rests on.

Article numbers are not invented: they were counted from each published text,
and only used where a number clearly dominates. Articles whose most-cited norm
is art. 5/6 (the ECHR fair-trial articles, not the CPP) get a plain Moldovan
qualifier instead.

Usage:
    python manage.py seed_meta_titles          # preview only
    python manage.py seed_meta_titles --apply  # write to the database
"""

from django.core.management.base import BaseCommand

from articles.models import Article

# slug -> SEO title. Kept under ~60 chars so Google shows it unshortened
# alongside the " | Penița Dreptului" suffix.
META_TITLES = {
    # --- statute is unambiguous: the number dominates the text ---
    "arestul-preventiv": "Arestul preventiv (art. 308 CPP RM)",
    "art-313-a-cpp": "Art. 313 CPP RM în procesul penal",
    "audierea-copiilor": "Audierea copiilor (art. 110 CPP RM)",
    "banuit-statut-procesual": "Bănuitul — statut procesual (art. 63 CPP RM)",
    "cercetarea-la-fata-locului": "Cercetarea la fața locului (art. 118 CPP RM)",
    "conexarea-si-disjungerea-cauzelor-penale":
        "Conexarea și disjungerea cauzelor penale (art. 42 CPP RM)",
    "controlul-de-catre-procuror-al-legalitaii-urmariri":
        "Legalitatea urmăririi penale (art. 298 CPP RM)",
    "controlul-judiciar-al-urmarii-penale":
        "Controlul judiciar al urmăririi penale (art. 311-313 CPP RM)",
    "echipe-comune-de-investigatii":
        "Echipe comune de investigații (art. 540 CPP RM)",
    "efectuarea-actiunilor-de-urmarire-penala":
        "Efectuarea acțiunilor de urmărire penală (art. 279 CPP RM)",
    "libera-apreciere-a-probelor":
        "Libera apreciere a probelor (art. 101 CPP RM)",
    "procedura-aplicarii-masurilor-de-protecie-a-victim":
        "Protecția victimelor violenței în familie (art. 215 CPP)",
    "revizuirea-procesului-penal": "Revizuirea procesului penal (art. 464 CPP RM)",
    "ridicarea-provizorie-a-permisului-de-conducere":
        "Ridicarea permisului de conducere (art. 182 CPP RM)",
    "valoarea-probanta-a-msi":
        "Valoarea probantă a MSI (art. 94 CPP RM)",
    "accelerarea-urmaririi-penale":
        "Accelerarea urmăririi penale (art. 20 CPP RM)",
    "controlul-judiciar-al-masurilor-speciale-de-investigatii-in-procesul-penal":
        "Controlul judiciar al MSI (art. 132 CPP RM)",
    "punerea-sub-invinuire-si-inaintarea-acuzarii":
        "Punerea sub învinuire și înaintarea acuzării (art. 281 CPP RM)",

    # --- most-cited norm is the ECHR, not the CPP: qualify by country only ---
    "audierea-martorilor": "Audierea martorilor în procesul penal al RM",
    "termenul-rezonabil": "Termenul rezonabil în procesul penal al RM",
    "terminarea-urmaririi-penale": "Terminarea urmăririi penale în procesul penal al RM",
    "lipsa-de-publicitate-a-urmaririi-penale":
        "Lipsa de publicitate a urmăririi penale în RM",
    "infaptuirea-justitiei": "Înfăptuirea justiției în procesul penal al RM",
    "respectarea-dreptului-la-aparare-a-persoanelor-banuite":
        "Dreptul la apărare al persoanei bănuite în RM",
    "caile-de-atac-in-procesul-penal": "Căile de atac în procesul penal al RM",
    "citarea-partilor-pe-cauzele-penale-in-instantele-de-apel":
        "Citarea părților în apelul penal (RM)",
    "erori-de-drept-in-apelul-penal": "Erori de drept în apelul penal (RM)",
    "participarea-procurorului-in-apelul-penal":
        "Participarea procurorului în apelul penal (RM)",
    "accesul-victimei-si-partii-vatamate-la-materialele-dosarului-in-cadrul-urmaririi-penale":
        "Accesul victimei la materialele dosarului penal (RM)",
    "utilizarea-instrumentelor-investigative":
        "Instrumente investigative în procesul penal al RM",

    # --- English-language articles: keep English, add the jurisdiction ---
    "freedom-of-self-incrimination":
        "Freedom from self-incrimination in Moldovan criminal procedure",
    "the-inviolability-of-the-person":
        "Inviolability of the person (art. 166 CPP of Moldova)",
}


class Command(BaseCommand):
    help = "Set Article.meta_title for Moldova-targeted search titles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply", action="store_true",
            help="Write the titles. Without it, only prints what would change.",
        )
        parser.add_argument(
            "--overwrite", action="store_true",
            help="Also replace meta_titles that were already set by hand.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        overwrite = options["overwrite"]

        changed = skipped = missing = 0
        for slug, title in sorted(META_TITLES.items()):
            article = Article.objects.filter(slug=slug).first()
            if article is None:
                self.stdout.write(self.style.WARNING(f"  no such article: {slug}"))
                missing += 1
                continue

            if article.meta_title and not overwrite:
                skipped += 1
                continue

            self.stdout.write(f"  {article.name[:44]:<45} -> {title}")
            if apply_changes:
                article.meta_title = title
                article.save(update_fields=["meta_title"])
            changed += 1

        # Anything published later simply falls back to its own name.
        untouched = Article.objects.exclude(slug__in=META_TITLES).count()

        self.stdout.write("")
        self.stdout.write(
            f"{changed} to set, {skipped} already set (kept), "
            f"{missing} slugs not found, {untouched} articles not in the list"
        )
        if not apply_changes:
            self.stdout.write(self.style.WARNING("dry run — rerun with --apply to write"))
        else:
            self.stdout.write(self.style.SUCCESS("meta titles written"))
