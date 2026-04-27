from django.db import migrations, models


# Уникальный SEO-контент для каждой книги (HTML, ~1000-1500 знаков).
# Цель: убрать thin content (~1400 знаков на странице книги до правки)
# и дать Google уникальный, релевантный текст для индексации.
SEO_CONTENT = {
    "caile-de-atac-in-procesul-penal": """
<h2>Despre lucrare</h2>
<p><strong>„Căile de atac în procesul penal"</strong>, semnată de <a href="/tudor-osoianu/">Tudor Osoianu</a>, este un ghid practic destinat avocaților, procurorilor și magistraților care activează în domeniul justiției penale din Republica Moldova. Lucrarea oferă o expunere clară și structurată a mecanismelor de contestare a hotărârilor judecătorești, însoțită de exemple din practica judiciară și de referințe la jurisprudența Curții Supreme de Justiție și a Curții Europene a Drepturilor Omului.</p>
<h3>Subiecte cheie abordate</h3>
<ul>
    <li>Apelul în procesul penal: termene, condiții de admisibilitate și efecte juridice</li>
    <li>Recursul ordinar și recursul în interesul legii — limitele controlului judiciar</li>
    <li>Revizuirea procesului penal după pronunțarea hotărârilor CtEDO</li>
    <li>Greșeli frecvente în redactarea cererilor de atac și remediile procesuale</li>
    <li>Standardele europene aplicabile căilor de atac în materie penală</li>
</ul>
<h3>Cui îi este utilă cartea</h3>
<p>Avocaților specializați în cauze penale, procurorilor implicați în participarea la judecarea apelurilor și recursurilor, judecătorilor instanțelor de apel și recurs, precum și studenților și masteranzilor la facultățile de drept. Lucrarea îmbină rigoarea academică cu utilitatea practică, oferind soluții pentru situațiile întâlnite zilnic în activitatea profesională.</p>
""".strip(),

    "procedurile-standard-de-operare-pentru-politie": """
<h2>Despre lucrare</h2>
<p><strong>„Procedurile Standard de Operare pentru Poliție"</strong> de <a href="/tudor-osoianu/">Tudor Osoianu</a> sintetizează un set complet de reguli și orientări menite să asigure intervenții profesionale, proporționale și conforme cu standardele internaționale privind protecția drepturilor omului. Cartea explică principiile fundamentale ale activității polițienești, responsabilitățile ofițerilor în diferite situații operaționale și mecanismele de control intern și extern.</p>
<h3>Conținut și teme principale</h3>
<ul>
    <li>Principiile legalității, proporționalității și necesității în acțiunile poliției</li>
    <li>Procedurile de reținere, percheziție și efectuarea acțiunilor de urmărire penală</li>
    <li>Folosirea forței și a mijloacelor speciale — limite și garanții</li>
    <li>Standardele Convenției Europene a Drepturilor Omului aplicabile activității polițienești</li>
    <li>Documentarea acțiunilor și obligația de raportare</li>
</ul>
<h3>Destinatari</h3>
<p>Ofițeri de poliție în activitate, formatori și instructori la academiile de specialitate, juriști care evaluează legalitatea acțiunilor polițienești și organizații care monitorizează respectarea drepturilor omului în cadrul intervențiilor poliției.</p>
""".strip(),

    "rights-of-suspects-in-police-detention": """
<h2>About the publication</h2>
<p><strong>"Rights of Suspects in Police Detention"</strong> by <a href="/tudor-osoianu/">Tudor Osoianu</a> is a regional study conducted under the umbrella of the Legal Aid Reformers Network (LARN), simultaneously in Georgia, Ukraine and Moldova. The research methodology builds upon a similar initiative in England and Wales and focuses on the practical effectiveness of safeguards available to suspects during the first hours of police detention.</p>
<h3>Key research areas</h3>
<ul>
    <li>The right to be informed about detention and the underlying accusations</li>
    <li>Access to a lawyer and the right to legal aid in pre-trial proceedings</li>
    <li>The right to silence and protection against self-incrimination</li>
    <li>Treatment of vulnerable suspects (minors, persons with disabilities)</li>
    <li>Comparative analysis between Moldova, Georgia and Ukraine</li>
</ul>
<h3>Audience</h3>
<p>Defense lawyers, criminal procedure scholars, human rights monitors, police trainers and policy makers working on reform of pre-trial detention systems in Eastern European jurisdictions.</p>
""".strip(),

    "tactica-efectuarii-audierilor": """
<h2>Despre lucrare</h2>
<p><strong>„Tactica efectuării audierilor"</strong> de <a href="/dinu-ostavciuc/">Dinu Ostavciuc</a> este un ghid metodic dedicat ofițerilor de urmărire penală, axat pe tehnicile și strategiile eficiente de audiere a persoanelor implicate în procesul penal. Lucrarea îmbină fundamentele criminalisticii cu psihologia judiciară, oferind recomandări practice pentru obținerea declarațiilor veridice cu respectarea garanțiilor procesuale.</p>
<h3>Tactici și teme prezentate</h3>
<ul>
    <li>Pregătirea audierii: studierea materialelor cauzei, formularea întrebărilor</li>
    <li>Tactici de audiere a martorilor, victimelor, bănuiților și învinuiților</li>
    <li>Particularitățile audierii copiilor și persoanelor vulnerabile</li>
    <li>Detectarea minciunii și interpretarea limbajului non-verbal</li>
    <li>Documentarea audierii și valoarea probantă a declarațiilor</li>
    <li>Erori frecvente în efectuarea audierilor și remediile procesuale</li>
</ul>
<h3>Cui îi este utilă cartea</h3>
<p>Ofițerilor de urmărire penală, procurorilor, ofițerilor de investigații, formatorilor de la academiile MAI și studenților masteranzi în drept procesual penal și criminalistică.</p>
""".strip(),

    "ghidul-pentru-ofiterii-de-politie-privind-respecta": """
<h2>Despre lucrare</h2>
<p>Acest <strong>ghid practic</strong> de <a href="/tudor-osoianu/">Tudor Osoianu</a> oferă un cadru modern pentru formarea polițiștilor în domeniul respectării drepturilor și garanțiilor procesuale ale persoanei. Materialul prezintă proceduri corecte, exemple aplicative și recomandări operative pentru asigurarea legalității reținerii și a celorlalte acțiuni procesuale, în conformitate cu legislația națională și standardele europene.</p>
<h3>Subiecte cheie</h3>
<ul>
    <li>Cadrul legal al reținerii și informarea persoanei despre drepturi</li>
    <li>Asistența obligatorie a apărătorului la primele etape ale urmăririi penale</li>
    <li>Folosirea legitimă a forței și interzicerea tratamentelor degradante</li>
    <li>Documentarea acțiunilor procesuale: procese-verbale, înregistrări, martori asistenți</li>
    <li>Răspunderea pentru încălcările procedurale și mecanismele de control intern</li>
</ul>
<h3>Pentru cine este destinat</h3>
<p>Pentru ofițerii de poliție în activitate, instructorii din cadrul academiilor MAI, juriștii din serviciile de control intern, precum și pentru avocații care apără persoanele implicate în acțiuni de reținere.</p>
""".strip(),

    "cercetarea-infractiunilor-din-materia-crimei-organ": """
<h2>Despre lucrare</h2>
<p><strong>„Cercetarea infracțiunilor din materia crimei organizate"</strong> de <a href="/dinu-ostavciuc/">Dinu Ostavciuc</a> este un ghid metodic dedicat ofițerilor de urmărire penală, axat pe particularitățile investigării criminalității organizate. Lucrarea oferă orientări practice, metode eficiente de lucru și recomandări concrete pentru documentarea grupărilor criminale, demonstrarea legăturilor dintre membri și probarea faptelor săvârșite în cadrul organizației.</p>
<h3>Domenii abordate</h3>
<ul>
    <li>Definirea criminalității organizate și a grupurilor criminale organizate în legislația națională</li>
    <li>Tactici de investigare: măsuri speciale de investigații, supraveghere operativă, agentul sub acoperire</li>
    <li>Particularitățile audierii membrilor grupurilor criminale și a martorilor protejați</li>
    <li>Documentarea legăturilor financiare, a circuitelor de spălare a banilor</li>
    <li>Cooperarea internațională și asistența juridică în materie penală</li>
</ul>
<h3>Audiență țintă</h3>
<p>Ofițerilor de urmărire penală specializați în cauze de criminalitate organizată, procurorilor, analiștilor criminali, formatorilor și cercetătorilor în domeniul criminalisticii.</p>
""".strip(),

    "investigarea-infractiunilor-cu-caracter-extremist": """
<h2>Despre lucrare</h2>
<p><strong>„Investigarea infracțiunilor cu caracter extremist"</strong> de <a href="/dinu-ostavciuc/">Dinu Ostavciuc</a> este un ghid metodic destinat ofițerilor de urmărire penală, axat pe particularitățile documentării și probării faptelor extremiste. Lucrarea oferă metode operative, repere juridice și recomandări practice pentru gestionarea eficientă a investigațiilor sensibile, cu respectarea standardelor de protecție a libertății de exprimare.</p>
<h3>Conținut</h3>
<ul>
    <li>Cadrul legal național și internațional privind extremismul și discursul instigator la ură</li>
    <li>Particularități de calificare juridică și demarcația față de libertatea de exprimare</li>
    <li>Tactici de investigare a infracțiunilor motivate de ură (rasă, religie, etnie, orientare)</li>
    <li>Probarea elementului subiectiv: motivul discriminatoriu și instigarea la violență</li>
    <li>Cercetarea infracțiunilor săvârșite în mediul online și pe rețelele sociale</li>
</ul>
<h3>Cui îi este destinată</h3>
<p>Ofițerilor de urmărire penală, procurorilor specializați în cauze de extremism, analiștilor de informații și formatorilor în domeniul drepturilor omului și combaterii discursului instigator la ură.</p>
""".strip(),

    "metodica-cercetarii-traficului-de-copii": """
<h2>Despre lucrare</h2>
<p><strong>„Metodica cercetării traficului de copii"</strong> de <a href="/dinu-ostavciuc/">Dinu Ostavciuc</a> oferă instrumente practice și orientări clare pentru investigarea infracțiunilor de trafic de minori. Lucrarea abordează tacticile speciale, particularitățile probatorii și procedurile specifice necesare pentru protecția victimelor minore și destructurarea rețelelor de trafic.</p>
<h3>Conținut metodic</h3>
<ul>
    <li>Cadrul legal național și internațional privind traficul de copii</li>
    <li>Identificarea victimelor minore și interviul protejat cu participarea psihologului</li>
    <li>Tehnici operative de investigare: măsuri speciale, supraveghere, infiltrare</li>
    <li>Cooperarea cu organizațiile internaționale (Europol, Interpol, OIM)</li>
    <li>Garanții procesuale speciale pentru minori — interesul superior al copilului</li>
    <li>Asistența psihologică și socială a victimelor pe durata procesului penal</li>
</ul>
<h3>Destinatari</h3>
<p>Ofițerilor de urmărire penală specializați în cauze de trafic de persoane, procurorilor, ofițerilor de poliție din unități specializate, asistenților sociali, psihologilor judiciari și formatorilor în domeniul protecției copilului.</p>
""".strip(),

    "respectarea-drepturilor-omului-in-cadrul-urmaririi": """
<h2>Despre monografie</h2>
<p>Monografia <strong>„Respectarea drepturilor omului în cadrul urmăririi penale"</strong> semnată de <a href="/tudor-osoianu/">Tudor Osoianu</a> și <a href="/dinu-ostavciuc/">Dinu Ostavciuc</a> reprezintă o analiză aprofundată a garanțiilor fundamentale ale persoanei în faza pretrial. Lucrarea examinează normativul procesual penal național, raportându-l la standardele europene (CEDO, Recomandările Consiliului Europei) și internaționale (Pactul ONU, Principiile de la Beijing).</p>
<h3>Teme de cercetare</h3>
<ul>
    <li>Garanțiile dreptului la apărare în faza urmăririi penale</li>
    <li>Inviolabilitatea persoanei: arestul, percheziția, ridicarea de obiecte</li>
    <li>Dreptul la viața privată și ingerințele autorităților de urmărire</li>
    <li>Termenul rezonabil al urmăririi penale și remediile procesuale</li>
    <li>Standardele CtEDO aplicabile detenției preventive și interogatoriului</li>
    <li>Garanțiile procesuale speciale pentru persoane vulnerabile</li>
</ul>
<h3>Public țintă</h3>
<p>Cercetători în științele juridice, doctoranzi, magistrați, procurori, ofițeri de urmărire penală, avocați specializați și formatori în domeniul drepturilor omului. Lucrarea servește atât ca instrument de referință academică, cât și ca ghid practic pentru evaluarea legalității acțiunilor procesuale.</p>
""".strip(),

    "cai-de-atac-monografie-2026": """
<h2>Despre monografie</h2>
<p>Această <strong>monografie științifică</strong> semnată de <a href="/tudor-osoianu/">Tudor Osoianu</a> și <a href="/dinu-ostavciuc/">Dinu Ostavciuc</a> este dedicată analizei aprofundate a căilor de atac în procesul penal din Republica Moldova. Lucrarea abordează aspectele teoretice și practice ale contestării hotărârilor judecătorești, oferind o viziune complexă asupra mecanismelor de control judiciar și a evoluției jurisprudenței recente.</p>
<h3>Structură și conținut</h3>
<ul>
    <li>Sistemul căilor de atac în procesul penal: clasificare și principii generale</li>
    <li>Apelul: condiții de exercitare, efecte, judecarea apelului</li>
    <li>Recursul ordinar — temeiuri, motive de casare și soluționare</li>
    <li>Recursul în interesul legii — instrument de unificare a practicii judiciare</li>
    <li>Revizuirea procesului penal — temeiuri și efecte</li>
    <li>Standardele Curții Europene a Drepturilor Omului în materia controlului judiciar</li>
    <li>Drept comparat: căile de atac în alte sisteme procesual-penale europene</li>
</ul>
<h3>Public țintă</h3>
<p>Magistrați ai instanțelor de apel și recurs, procurori, avocați specializați în cauze penale, doctoranzi și cercetători în științele juridice, formatori la institutele de pregătire profesională a magistraților și studenți la programele de masterat în drept procesual penal.</p>
""".strip(),
}


def populate_seo_content(apps, schema_editor):
    Book = apps.get_model("books", "Book")
    for slug, content in SEO_CONTENT.items():
        Book.objects.filter(slug=slug).update(seo_content=content)


def reverse_seo_content(apps, schema_editor):
    Book = apps.get_model("books", "Book")
    Book.objects.filter(slug__in=SEO_CONTENT.keys()).update(seo_content=None)


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0004_add_timestamps_for_seo"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="seo_content",
            field=models.TextField(
                blank=True,
                null=True,
                help_text="Расширенное HTML-описание книги для SEO-индексации. Если пусто — рендерится generic-блок.",
            ),
        ),
        migrations.RunPython(populate_seo_content, reverse_seo_content),
    ]
