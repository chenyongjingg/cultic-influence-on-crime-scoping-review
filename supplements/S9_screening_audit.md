# S9. Full-corpus audit of the screening decisions

The audit runs on the machine set of 191 included records, before the author's exclusions; the corpus analysed in the paper is the 163 that remain (S9b).

This is not a human adjudication and is not presented as one. It is the part of the check that can be computed: the decisions are replayed from the stored fields, the two error classes the 50-record read identified are counted over the whole corpus, and every headline percentage is recomputed with the flagged records removed.

## A. Does the artefact do what Section 2.4 says

| Check | Result |
|---|---|
| Decisions re-derived from the four flags | 0 of 628 differ |
| Inclusions re-derived from the stored fields, against `included.jsonl` | 0 symmetric difference |

A zero here is a check on the pipeline, not on the model: it shows that the rule described in the paper is the rule the artefact applied.

## B. "Cult" as a figure of speech, whole corpus

| | Records |
|---|---|
| Text in which every group term is metaphorical | 34 of 628 screened |
| ... of which included | 1 |

- `10.1108/jfc-01-2024-0054` — Crypto collapse: the cult of personality and the normalisation of fraud in FTX and Celsius

## C. Included records whose own evidence names no group

Neither the title nor the span the model quoted in support of the group criterion contains a group term. The criterion may still be true — a record can name a specific group without using a generic word — but the model's own evidence does not show it, and these are the records where it is most likely to have gone wrong.

**29 of 191 included records.**

- `10.1093/9780197679951.003.0014` — Exorcizing
                    <i>Devilsdorp</i>
- `0a62cd6624f0e188b8a47cca1b9e42707c142b04` — Holy Entrepreneurship and the Commodification of the Sacred: A Critical Synthetic Realist Analysis of Faith, Markets, and Exploitation in a Global Context
- `1303e4df5c82785fa381789234143364acf4fb9b` — Features of the situation of crimes against life and health committed by members of youth informal groups (associations)
- `f7c5fc316f97a626238f069685dbca899b321ece` — Heresy and Hypocrisy of the Church: A Marxist Analysis of Okezie Nwoka's God of Mercy
- `559a0e578ab76d936f15b29646c1545b0f5361bb` — A (NÃO) CONTRIBUIÇÃO DA TIPIFICAÇÃO DO CRIME DE CURANDEIRISMO PARA A DEMONIZAÇÃO DAS RELIGIÕES DE MATRIZES AFRICANAS
- `fde4a7cfb1d524420ccb6dcea8e3d7ff4aee71e7` — Cybernetic Hive Minds: A Review
- `20529993` — Charles Manson and the family: the application of sociological theories to multiple murder.
- `a0c5110fb2cd6a878bc80199dd7f8e3602fb8e9a` — “F*cking politeness” and “staying sexy” while doing it: intimacy, interactivity and the feminist politics of true crime podcasts
- `02544deb407ef2272f8370e727387a3f250656bf` — Fetishes and Monuments
- `291132848` — Organized crime in lithuania - criminological analysis of the criminal organization "agurkiniai".
- `72635f8ce3134f7484eb14f119dd3539` — Maschinengewehre und ein Wettbewerb der Revolutionsprojekte: Der Prozess gegen Ėduard Limonov
- `fec914a1ee6bca5b4fbf415244f116d13944807d` — China’s Struggle against the Xie Jiao
- `6d29664704122afabecd5842118f33de347dabed` — Jesus Built My Strawman: The Church of the Ecumenical Redemption International and “Minister” Edward Jay Robin Belanger
- `03e3b4fb131d61356c5a95597e6b5a4993be2965` — Rhetoric and realities of magic
- `26227027` — Aum Shinrikyo's Chemical and Biological Weapons: More Than Sarin.
- `1cf1fc9fba4e436aa898b8c0e9196798` — Feitiçarias, territórios e resistências marginais
- `fbfe6ee99c82eed2cbce5f832cc9d103a647a6de` — Problems Of Countering The Ideology Of Religious Extremism Among Young People
- `5a1e598cc070e3db3d0751567f765300f04332ef` — Viewpoint: existential education in the era of personal cybernetics
- `8d25db198c97c678569ff03a7461f4087ec54047` — Criminal law qualification of violations of sanitary rules and regulations on the prevention of infectious diseases during religious beliefs, confessions or the
- `0c442dea4d16de86b3ad3d8fcaccc68f3c1e9df3` — Kings, Priests, and Power in the Neo-Assyrian Period
- `29589292` — The "Bestie of Satana" murders
- `0883d21d711dbf737b5a183ffd6c6c1e9272e132` — Fake News
- `11863233` — Prisoners of hate.
- `b3e4ba201490ea9eed60b3a89e95afa4d424becd` — Protecting the Tsar's Honor and Insulting the Supreme Authority: Power Scenarios and Social Practices in the Late 19th and Early 20th Centuries
- `00f9774666a60c9bb6de8d069bf0ebf1a0284985` — Annals of Gullibility
- `99d855606f2648349f4c6e92e230892e` — On the issue of legal status of spiritual Christians Molokans in the Russian Empire
- `120185676` — Satanic Ritual Abuse From Then to Now: The Impact of the Controversies of the 1980s and 1990s on the Treatment for Survivors of Extreme Abuse
- `fd608b212b40319513cd8ef338b5d711d1664888` — THE FORMATION AND ACTIVITIES OF THE NATIONAL SOCIALIST LABOR PARTY OF RUSSIA: FROM THE HISTORY OF THE EMERGENCE OF RUSSIAN FASCISM DURING THE SECOND WORLD WAR (
- `b5d245464e1f466e95f405d66b1be136` — Nordkoreanske migranter i Kina. Konversion og socialt pres.

The union of B and C is **30 records**; that is the list a human should read.

## D. How much of the result depends on the flagged records

Percentages over the 170 included records carrying an abstract.

| Construct | Base | Minus metaphor | Minus no-group-evidence | Minus both | Max drift (pp) |
|---|---|---|---|---|---|
| C1_group_def | 5.9 (10/170) | 5.9 (10/169) | 7.1 (10/141) | 7.1 (10/140) | 1.2 |
| C2_role | 14.7 (25/170) | 14.8 (25/169) | 14.2 (20/141) | 14.3 (20/140) | 0.5 |
| C3_duration | 4.1 (7/170) | 4.1 (7/169) | 4.3 (6/141) | 4.3 (6/140) | 0.2 |
| C5_instrument | 1.2 (2/170) | 1.2 (2/169) | 1.4 (2/141) | 1.4 (2/140) | 0.2 |
| C8_legal | 20.6 (35/170) | 20.7 (35/169) | 19.9 (28/141) | 20.0 (28/140) | 0.7 |

No record was removed: the corpus reported in the manuscript is unchanged by this table. What the table shows is the size of the dependence, which is what a reader needs in order to decide how much weight the percentages carry.