from django.db import migrations


# Уникальные SEO-excerpt'ы для каждой статьи (1-2 предложения, ~150-220 знаков).
# Используются как meta description / og:description / twitter:description.
# Цель: убрать "thin description" из PDF-метаданных (CZU/ISSN/DOI),
# которые попадали в Google и снижали CTR в выдаче.
EXCERPTS = {
    "accesul-victimei-si-partii-vatamate-la-materialele":
        "Studiu juridic privind accesul victimei și părții vătămate la materialele dosarului în faza urmăririi penale: cadrul normativ, garanții procesuale și jurisprudența relevantă din Republica Moldova.",
    "citarea-partilor-pe-cauzele-penale-in-instantele-d":
        "Analiza procedurii de citare a părților în instanțele de apel pe cauzele penale: cerințe legale, efecte ale viciilor de citare și soluții pentru asigurarea contradictorialității.",
    "audierea-martorilor":
        "Analiza jurisprudenței privind audierea martorilor în cauzele penale, cu accent pe respectarea dreptului la un proces echitabil prevăzut de art. 6 CEDO.",
    "controlul-judiciar-al-urmarii-penale":
        "Examinarea controlului judiciar al urmăririi penale în al doilea grad de jurisdicție: controverse doctrinare, lacune legislative și propuneri de reglementare.",
    "termenul-rezonabil":
        "Respectarea termenului rezonabil în urmărirea penală: standardele Convenției Europene a Drepturilor Omului și transpunerea lor în legislația Republicii Moldova.",
    "infaptuirea-justitiei":
        "Înfăptuirea justiției ca atribuție exclusivă a instanțelor judecătorești — principiu fundamental al procesului penal și implicațiile sale practice în legislația națională.",
    "punerea-sub-invinuire-si-inaintarea-acuzarii":
        "Studiu privind procedura punerii sub învinuire și înaintarea acuzării în procesul penal: condiții legale, garanții procesuale și efecte juridice asupra calității de învinuit.",
    "respectarea-dreptului-la-aparare-a-persoanelor-ban":
        "Respectarea dreptului la apărare al persoanelor bănuite: cadrul normativ intern al Republicii Moldova și jurisprudența relevantă a Curții Europene a Drepturilor Omului.",
    "cercetarea-la-fata-locului":
        "Analiza ingerinței cercetării la fața locului în viața privată: garanțiile procesuale prevăzute de legislația penală a Republicii Moldova și standardele europene aplicabile.",
    "freedom-of-self-incrimination":
        "Studiu academic în limba engleză privind libertatea persoanei de a nu se autoincrimina — dreptul la tăcere ca garanție procesuală fundamentală în procesul penal.",
    "valoarea-probanta-a-msi":
        "Valoarea probantă a rezultatelor măsurilor speciale de investigații în procesul penal: cadrul normativ, criterii de admisibilitate și jurisprudență relevantă.",
    "lipsa-de-publicitate-a-urmaririi-penale":
        "Analiza principiului lipsei de publicitate a urmăririi penale și a regulilor de acces al părților la materialele dosarului în această etapă a procesului penal.",
    "the-inviolability-of-the-person":
        "Cercetare academică în limba engleză privind inviolabilitatea persoanei ca principiu fundamental al procesului penal — garanții constituționale și standarde internaționale.",
    "conexarea-si-disjungerea-cauzelor-penale":
        "Studiu privind conexarea și disjungerea cauzelor penale: condițiile legale, criteriile aplicate de practica judiciară și efectele asupra desfășurării procesului penal.",
    "caile-de-atac-in-procesul-penal":
        "Garantarea accesului liber la justiție prin intermediul căilor ordinare de atac în procesul penal — analiză a regimului juridic și a practicii instanțelor moldovenești.",
    "controlul-de-catre-procuror-al-legalitaii-urmariri":
        "Analiza atribuțiilor procurorului în controlul legalității urmăririi penale: limitele de exercitare, obligațiile procesuale și impactul asupra garanțiilor părților.",
    "controlul-judiciar-al-masurilor-speciale-de-invest":
        "Studiu detaliat privind controlul judiciar al măsurilor speciale de investigații: regimul autorizării, cerințele de motivare și protecția dreptului la viața privată.",
    "echipe-comune-de-investigatii":
        "Echipele comune de investigații ca formă modernă a asistenței juridice internaționale în materie penală: cadrul normativ, condițiile de constituire și avantajele practice.",
    "erori-de-drept-in-apelul-penal":
        "Identificarea și analiza erorilor de drept comise de instanțele de apel în cauzele penale — temeiuri pentru casarea deciziilor și remediile procesuale disponibile.",
    "libera-apreciere-a-probelor":
        "Principiul liberei aprecieri a probelor în procesul penal: limitele puterii discreționare a judecătorului, criteriile raționamentului probator și jurisprudența relevantă.",
    "audierea-copiilor":
        "Particularitățile audierii copiilor în procesul penal — garanții speciale, mecanisme de protecție și standarde internaționale privind interesul superior al minorului.",
    "banuit-statut-procesual":
        "Analiza limitelor discreției de atribuire a calității de bănuit sau învinuit și a dreptului la informare cu privire la acuzațiile aduse în procesul penal.",
    "participarea-procurorului-in-apelul-penal":
        "Studiu de drept comparat privind participarea procurorului în apelul penal: practici din alte state și concluzii pentru reforma procesual-penală a Moldovei.",
    "procedura-aplicarii-masurilor-de-protecie-a-victim":
        "Procedura aplicării măsurilor de protecție a victimelor violenței în familie: cadrul legal, etapele intervenției și rolul instituțiilor implicate.",
    "revizuirea-procesului-penal":
        "Revizuirea procesului penal și casarea hotărârilor după pronunțarea unei decizii a Curții Europene a Drepturilor Omului — mecanisme procesuale și efecte juridice.",
    "ridicarea-provizorie-a-permisului-de-conducere":
        "Procedura ridicării provizorii a permisului de conducere a mijloacelor de transport: cadrul normativ național, garanțiile procesuale și standardele de calitate a legii.",
    "terminarea-urmaririi-penale":
        "Terminarea urmăririi penale și trimiterea cauzei în judecată: cadrul juridic național, etapele procesuale și conformitatea cu standardele europene.",
    "utilizarea-instrumentelor-investigative":
        "Studiu privind impactul utilizării instrumentelor investigative asupra drepturilor omului în diverse proceduri penale: garanții procesuale și echilibrul cu interesul public.",
    "accelerarea-urmaririi-penale":
        "Procedura de examinare a cererilor de accelerare a urmăririi penale — mecanism procesual de protecție a dreptului la judecată într-un termen rezonabil.",
    "arestul-preventiv":
        "Evoluția jurisprudenței privind procedura aplicării arestului preventiv și a prelungirii acestei măsuri — cadrul legal, criteriile de motivare și standardele europene.",
    "art-313-a-cpp":
        "Interpretarea sintagmei „alte acțiuni care afectează drepturile și libertățile constituționale ale persoanei” din art. 313 alin. (2) pct. 3) CPP al Republicii Moldova.",
    "efectuarea-actiunilor-de-urmarire-penala":
        "Efectuarea acțiunilor procesuale la faza urmăririi penale conform legislației Republicii Moldova: condiții, modalități de realizare și garanții pentru părți.",
}


def populate_excerpts(apps, schema_editor):
    Article = apps.get_model("articles", "Article")
    for slug, excerpt in EXCERPTS.items():
        Article.objects.filter(slug=slug).update(excerpt=excerpt)


def reverse_excerpts(apps, schema_editor):
    Article = apps.get_model("articles", "Article")
    Article.objects.filter(slug__in=EXCERPTS.keys()).update(excerpt=None)


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0003_article_excerpt_article_seo_content"),
    ]

    operations = [
        migrations.RunPython(populate_excerpts, reverse_excerpts),
    ]
