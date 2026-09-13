# LITERATURE — HOLC boundary design / firearm violence

Built 2026-09-13 for `D:\Gun Violence\displacement\` (multi-city HOLC boundary-discontinuity paper).

**Every citation below was resolved against Crossref or the PDF's own first page — none are
recalled from memory.** Where the two disagreed, the artefact wins and the discrepancy is noted.
Filenames were assigned from URLs at download time and then *corrected* against the extracted
title/author page; several were wrong on the first pass (see CORRECTIONS at the bottom).

48 PDFs. Prefix letter = tier. Papers with no PDF are listed as **[NO PDF]** with a reason —
absence of a file is never silent here.

**Update 2026-09-13 (later):** Nate supplied the three paywalled papers that gated the contribution
paragraph — **Mitre-Becerril 2026, Xu 2023, Swope et al. 2025**. All three verified against their
own title pages and filed. The acquisition queue is renumbered accordingly.

---

## READ-FIRST PATH (in this order)

| # | Paper | Why first |
|---|-------|-----------|
| 1 | **Aaronson, Hartley & Mazumder 2021** (01) | The design we are replicating and extending. Read the boundary section. |
| 2 | **Cattaneo, Titiunik & Yu 2026, "Theory and Practice"** (05) | State of the art on exactly our estimator. Synthesises 80+ BD papers. Post-dates every applied paper below. |
| 3 | **Mehranbod et al. 2022** (04) | The multi-city firearm result we contradict. Their own finding of non-uniformity across cities is the bridge to ours. |
| 4 | **Xu 2023, "Where Did Redlining Matter?"** (03) | Independent, non-firearm evidence that the redlining effect is *regionally heterogeneous*. Our conclusion, arrived at from another direction. |
| 5 | **Swope, Markley, Whittaker & Hillier 2025** (02) | The critical-methods indictment of exactly the literature we are joining. Read before writing a single framing sentence. |

---

## 01 — SPINE: HOLC boundary / causal-economics designs
*The papers whose identification strategy we inherit.*

- **Aaronson, D., Hartley, D., & Mazumder, B. (2021).** The Effects of the 1930s HOLC "Redlining" Maps. *American Economic Journal: Economic Policy*, 13(4), 355–392. doi:10.1257/pol.20190414
  `S_AaronsonHartleyMazumder_2017_EffectsOfHOLCMaps_ChiFedWP2017-12.pdf` — PDF is Chicago Fed WP 2017-12, **revised August 2020** (per its own cover), i.e. the working-paper version of the AEJ article.
  **USE:** the source of the boundary design, the propensity-score comparison boundaries, and the "pre-existing differences" critique we must answer. Our §5.1 pooled-interface estimator is the weaker cousin of their boundary-FE spec.

- **Aaronson, D., Faber, J., Hartley, D., Mazumder, B., & Sharkey, P. (2021).** The long-run effects of the 1930s HOLC "redlining" maps on place-based measures of economic opportunity and socioeconomic success. ***Regional Science and Urban Economics***, 86, 103622. doi:10.1016/j.regsciurbeco.2020.103622
  `S_Aaronson_etal_2020_LongRunEffects_PlaceBasedOpportunity_ChiFedWP2020-33.pdf` (Chicago Fed WP 2020-33)
  ⚠ **Commonly miscited as Journal of Urban Economics — it is RSUE.** Crossref-verified. Do not propagate the error.

- **Aaronson, D., Hartley, D., Mazumder, B., & Stinson, M. (2022).** The Long-run Effects of the 1930s Redlining Maps on Children. Chicago Fed WP 2022-13 / Census CES-WP-22-56.
  `S_Aaronson_etal_2022_LongRunEffectsRedliningMaps_Children_ChiFedWP2022-13.pdf`
  `S_Aaronson_etal_2022_LongRunEffectsRedlining_Children_CES-WP-22-56.pdf` (both kept — the CES version carries the disclosure-review detail)

- **Anders, J. (2023).** The long run effects of de jure discrimination in the credit market: How redlining increased crime. *Journal of Public Economics*, 222, 104857. doi:10.1016/j.jpubeco.2023.104857
  `S_Anders_2023_RedliningIncreasedCrime_SpatialRD_JPubE-JMP.pdf` — PDF is the **Dec 2019 job-market-paper version**, not the published article. Page/figure numbers will not match JPubE.
  **USE:** ⭐ the closest economics analogue to our outcome. Spatial RD on redlining → crime, **in Los Angeles**. We estimate LA at RR 1.412 (robust, our second-strongest city). Direct comparison point. Also the city-level population-cutoff instrument — an identification route we did not take and should say why.

- **Krimmel, J. (2018).** Persistence of Prejudice: Estimating the Long Term Effects of Redlining. *SocArXiv / working paper* (PDF draft dated 14 Nov 2017).
  `S_Krimmel_2018_PersistenceOfPrejudice.pdf`
  **USE:** cited in our **Amendment 3** as the precedent for boundary/segment fixed effects. His finding of *convergence* in homeownership and segregation but *persistence* in housing supply and density is the template for "the effect depends which outcome you pick" — we extend it to "and which city."

- **Faber, J. W. (2020).** We Built This: Consequences of New Deal Era Intervention in America's Racial Geography. *American Sociological Review*, 85(5), 739–775. doi:10.1177/0003122420948464
  `S_Faber_2020_WeBuiltThis_ASR.pdf`
  **USE:** the city-level (appraised vs unappraised) design. Important because it finds effects at a scale *above* the boundary — relevant to our whole-grade vs band divergence (the "Baltimore signature").

**[NO PDF] Appel, I. & Nickerson, J. (2016).** Pockets of Poverty: The Long-Term Effects of Redlining. SSRN 2852856. — RD on HOLC boundaries, 4.8% lower 1990 home prices. *Download returned a truncated non-PDF from the Atlanta Fed mirror; SSRN requires login.*

- **Mitre-Becerril, D. (2026).** The Long-Term Effects of Structural Discrimination on Public Safety: The 1930s Redlining Maps. *Crime & Delinquency*, 1–36. doi:10.1177/00111287261425622
  `S_MitreBecerril_2026_StructuralDiscrimination_PublicSafety_SpatialRD_CrimeDelinquency.pdf` ✅ **obtained 2026-09-13**
  **USE:** ⭐⭐ **the single closest published design to ours**: incident-level data from **48 police departments**, spatial RD across colour-grade boundaries at small bandwidth. Read in full before writing the contribution paragraph — see `MITRE_BECERRIL_READ.md` for the overlap assessment.

---

## 02 — HOLC CRITIQUE / REVISIONIST
*Why the exposure may not mean what the health literature assumes. This tier protects us.*

- **Fishback, P., Rose, J., Snowden, K. A., & Storrs, T. (2024).** New Evidence on Redlining by Federal Housing Programs in the 1930s. *Journal of Urban Economics*, 141, 103462. doi:10.1016/j.jue.2022.103462
  `C_Fishback_etal_2021_NewEvidenceRedliningFederalHousing_NBERw29244.pdf` (NBER WP 29244, Sept 2021)
  **USE:** ⛔ the hardest challenge to the whole field. FHA exclusion *predates* the HOLC maps and barely changes after them; HOLC itself lent into redlined areas. If the maps did not allocate credit, our D/C contrast is measuring **what the appraisers saw**, not what the policy did. Our causal language must survive this paper.

- **Hillier, A. E. (2003).** Redlining and the Home Owners' Loan Corporation. *Journal of Urban History*, 29(4), 394–420. doi:10.1177/0096144203029004002
  `C_Hillier_2003_RedliningAndTheHOLC_JUH.pdf`
  **USE:** the original revisionist finding — HOLC grades do not explain Philadelphia lending patterns except interest rates; the maps were **not widely distributed**. Note our Philadelphia estimate (1.460) is our *strongest* city, in the city where Hillier showed the map did least work. That tension is worth a paragraph, not a footnote.

- **Michney, T. M., & Winling, L. (2019).** New Perspectives on New Deal Housing Policy: Explicating and Mapping HOLC Loans to African Americans. *Journal of Urban History*, 46(1), 150–180. doi:10.1177/0096144218819429
  `C_WinlingMichney_2021_RootsOfRedlining_JAH.pdf` ⚠ **filename is misleading** — the PDF is actually *"The Roots of Redlining: Academic, Governmental, and Professional Networks in the Making of the New Deal Lending Regime,"* Winling & Michney, *Journal of American History* (2021). Both papers are by the same pair; **the PDF is the JAH one, not the JUH one.** The JUH article above is **[NO PDF]**.

- **Markley, S. (2023).** Federal 'redlining' maps: A critical reappraisal. *Urban Studies*, 61(2), 195–213. doi:10.1177/00420980231182336 — **[NO PDF]**, paywalled.
  **USE:** names the two camps, "HOLC Culpablism" and "HOLC Scepticism," and proposes reading the maps as a window onto real-estate racial ideology. Best available framing vocabulary for our discussion section.

- **Markley, S. N., & Holloway, S. R. (2024).** Underestimating Racism? Decoupling Race and Redlining. *Annals of the AAG*, 114(7), 1464–1482. doi:10.1080/24694452.2024.2350993 — **[NO PDF]**, paywalled.
  **USE:** ⭐ postwar Black population growth concentrated in redlined areas that *already had* Black residents or were adjacent to them. This is a demographic-composition mechanism operating **at the boundary** — plausibly the same thing our band-width/composition-imbalance result is detecting from the other side. High priority to obtain.

- **Mallach, A. (2024).** Shifting the Redlining Paradigm: The Home Owners' Loan Corporation Maps and the Construction of Urban Racial Inequality. *Housing Policy Debate*, 34(6), 891–917. doi:10.1080/10511482.2024.2321226
  `C_Mallach_2024_ShiftingTheRedliningParadigm_HousingPolicyDebate.pdf` (author's accepted manuscript)

- **Swope, C., Markley, S., Whittaker, S., & Hillier, A. (2025).** How and Why Does Redlining Matter for Present-Day Health? Critical Perspectives on Causality, Cartography, and Capitalism. *American Journal of Public Health*, 115(5), 769–779. doi:10.2105/AJPH.2024.308000
  `C_Swope_etal_2025_HowAndWhyDoesRedliningMatter_AJPH.pdf` ✅ **obtained 2026-09-13**. Note it carries a companion piece: "See also Winling, p. 649."
  **USE:** ⭐⭐ argues HOLC maps are **symptoms, not causes**. Written by the scoping-review author *and* two leading HOLC sceptics. This is the review-2 objection to our paper, published in advance. Obtain and answer it explicitly.

- **Gupta, A. (2022).** Coloring Inside the Lines: The Jagged Legacy of the HOLC Neighborhood Risk Maps. arXiv:2212.04117.
  `C_Gupta_2022_ColoringInsideTheLines_HOLCRiskMaps_PREPRINT.pdf`
  ⚠ **Unrefereed single-author student preprint (UCSD).** Kept for its boundary-geometry treatment only. **Do not cite as evidence.**

**[NO PDF] Thomas, K. A., Storrs, T. B., Xu, W., & Faber, J. W. (2026).** New-deal mortgage programmes benefited white borrowers disproportionately. *Nature*, 657(8131), 414–419. doi:10.1038/s41586-026-10850-8 — 29,921 linked FHA/VA loans 1935–47; 2.1% of FHA loans to Black borrowers vs 9.9% population share. *Paywalled.* The newest and most authoritative evidence on **who actually got the credit** — matters because it partly rescues the mechanism Fishback et al. attack, by relocating it from HOLC to FHA/VA.

---

## 03 — NEIGHBOURS: redlining → health / environment
*The literature our outcome sits inside. Establishes the convention we are criticising.*

- **Swope, C. B., Hernández, D., & Cushing, L. J. (2022).** The Relationship of Historical Redlining with Present-Day Neighborhood Environmental and Health Outcomes: A Scoping Review and Conceptual Model. *Journal of Urban Health*, 99(6), 959–983. doi:10.1007/s11524-022-00665-z
  `H_Swope_etal_2022_RedliningHealth_ScopingReview.pdf` (UCLA eScholarship postprint)
  **USE:** the field-defining review + conceptual model. Cite for "what this literature does."

- **Krieger, N., Van Wye, G., Huynh, M., Waterman, P. D., Maduro, G., Li, W., et al. (2020).** Structural Racism, Historical Redlining, and Risk of Preterm Birth in New York City, 2013–2017. *AJPH*, 110(7), 1046–1053. doi:10.2105/AJPH.2020.305656 — **[NO PDF]**, paywalled.
- **Krieger, N., et al. (2020).** Cancer Stage at Diagnosis, Historical Redlining, and Current Neighborhood Characteristics. *American Journal of Epidemiology*.
  `H_Krieger_etal_2020_CancerStage_HistoricalRedlining_AmJEpi.pdf`
  **USE:** the canonical whole-polygon exposure assignment we depart from. Krieger's ITS/areal approach is the foil for our boundary approach.

- **Hoffman, J. S., Shandas, V., & Pendleton, N. (2020).** The Effects of Historical Housing Policies on Resident Exposure to Intra-Urban Heat: A Study of 108 US Urban Areas. *Climate*, 8(1), 12. doi:10.3390/cli8010012
  `H_Hoffman_etal_2020_IntraUrbanHeat_Climate.pdf`
  **USE:** the most-cited multi-city redlining study. 94% of areas show the same sign — the *uniformity* claim our heterogeneity result challenges for a different outcome.

- **Conzelmann, C., Salazar-Miranda, A., Phan, T., & Hoffman, J. (2022/2024).** Long-term Effects of Redlining on Climate Risk Exposure. Richmond Fed WP 22-09R; published version in *Nature Cities*.
  `H_Conzelmann_etal_2022_RedliningClimateRisk_RichmondFedWP22-09R.pdf`
  `H_Conzelmann_etal_2024_RedliningClimateRisk_NatureCities.pdf`
  ⚠ Originally filed under "Salazar-Miranda" — **lead author is Conzelmann** (verified from cover page). Corrected.
  **USE:** ⭐ they run a **boundary design on HOLC C/D lines** for an environmental outcome. Closest methodological sibling outside the health literature. Compare their bandwidth choices to ours.

- `H_2023_HistoricRedlining_OilGasWells.pdf` — Historic redlining and the siting of oil and gas wells in the United States. *J. Exposure Science & Environmental Epidemiology* (2023). Environmental-exposure exemplar.
- `H_NCRC_Richardson_etal_2018_HOLCMaps_SegregationInequality.pdf` — NCRC (Richardson, Mitchell et al.), *HOLC "Redlining" Maps: The persistent structure of segregation and economic inequality.* **Advocacy-organisation report, not peer-reviewed** — cite for the descriptive national picture only.
- `H_Urban_2023_AssessingLegaciesHistoricalRedlining.pdf` — Urban Institute, *Assessing the Legacies of Historical Redlining.* Policy report, same caveat.

**[NO PDF] Lee, E. K., Donley, G., Ciesielski, T. H., Gill, I., Yamoah, O., Roche, A., et al. (2022).** Health outcomes in redlined versus non-redlined neighborhoods: A systematic review and meta-analysis. *Social Science & Medicine*, 294, 114696. doi:10.1016/j.socscimed.2021.114696 — **the** meta-analysis in this field (12 studies). *Paywalled.* Our DerSimonian–Laird pooling should be positioned against theirs; in particular, whether they reported a **prediction interval** (we do, and it is what called our own out-of-sample failure).

- **Xu, W. (2023).** Where Did Redlining Matter? Regional Heterogeneity and the Uneven Distribution of Advantage. *Annals of the AAG*, 113(8), 1939–1959. doi:10.1080/24694452.2023.2205514
  `H_Xu_2023_WhereDidRedliningMatter_RegionalHeterogeneity_AnnalsAAG.pdf` ✅ **obtained 2026-09-13**
  **USE:** ⭐⭐ **our conclusion, reached independently and earlier, for housing outcomes**: Bayesian hierarchical model, FHA influence 1940–70, regional heterogeneity in whether the grading mattered. This is the paper that makes our finding "a replication in a new outcome" rather than "an anomaly."

**[NO PDF] Xu, W. (2021).** Legacies of Institutionalized Redlining: A Comparison Between Speculative and Implemented Mortgage Risk Maps in Chicago, Illinois. *Housing Policy Debate*, 32(2), 249–274. doi:10.1080/10511482.2020.1858924 — Chicago-specific; relevant because Chicago is our leave-one-out co-primary.

**[NO PDF] Kraus, N. T., Connor, S., Shoda, K., Moore, S. E., & Irani, E. (2023).** Historic redlining and health outcomes: A systematic review. *Public Health Nursing*, 41, 287–296. doi:10.1111/phn.13276

---

## 04 — NEIGHBOURS: redlining → firearm violence
*Our exact outcome. This is the tier we are arguing with.*

- **Mehranbod, C. A., Gobaud, A. N., Jacoby, S. F., Uzzi, M., Bushover, B. R., & Morrison, C. N. (2022).** Historical redlining and the epidemiology of present-day firearm violence in the United States: A multi-city analysis. *Preventive Medicine*, 165(Pt A), 107207. doi:10.1016/j.ypmed.2022.107207
  `F_Mehranbod_etal_2022_HistoricalRedlining_FirearmViolence_MultiCity_PrevMed.pdf`
  **USE:** ⭐⭐ **the paper our Amendment 3 contradicts.** They report dose–response HOLC→firearm death and explicitly test **spatial non-stationarity**, concluding associations "did not appear to be uniform across US cities." Our result is the boundary-design version of their own non-stationarity finding. Frame as extension-and-sharpening, not refutation.

- **Jacoby, S. F., Dong, B., Beard, J. H., Wiebe, D. J., & Morrison, C. N. (2018).** The enduring impact of historical and structural racism on urban violence in Philadelphia. *Social Science & Medicine*, 199, 87–95. doi:10.1016/j.socscimed.2017.05.038
  `F_Jacoby_etal_2018_EnduringImpact_Philadelphia.pdf`
  **USE:** the origin paper for HOLC→firearm violence, and **Philadelphia** — our strongest city (1.460). Their single-city result and ours agree; say so.

- **Poulson, M., Neufeld, M. Y., Dechert, T., Allee, L., & Kenzik, K. M. (2021).** Historic redlining, structural racism, and firearm violence: A structural equation modeling approach. *The Lancet Regional Health – Americas*, 3, 100052. doi:10.1016/j.lana.2021.100052
  `F_Poulson_etal_2021_HistoricRedlining_FirearmViolence_SEM_LancetRegHealth.pdf`
  **USE:** the mediation account (homeownership, poverty, education, segregation). Our design deliberately does **not** condition on these — §8 forbids conditioning on `pct_black`. Explain the estimand difference.

- **Gobaud, A. N., Morrison, C. N., Branas, C. C., Jacoby, S., Kramer, M., & Adkins-Jackson, P. B. (2024).** Measuring the effect of historical structural racism on community firearm violence in US cities. *Social Science & Medicine*, 361, 117355. doi:10.1016/j.socscimed.2024.117355
  `F_Gobaud_etal_2024_MeasuringHistoricalStructuralRacism_CommunityFirearmViolence_SocSciMed.pdf`
  **USE:** same group as Mehranbod, on **measurement**. Directly relevant to our claim that band width buys effect size.

- **Uzzi, M., Aune, K. T., Marineau, L., Jones, F. K., et al. (2023).** An intersectional analysis of historical and contemporary structural racism on non-fatal shootings in Baltimore, Maryland. *Injury Prevention*.
  `F_Uzzi_etal_2023_IntersectionalStructuralRacism_NonfatalShootings_Baltimore_InjPrev.pdf`
- **So, M., El Baassiri, M. G., Price, M. D., Byrne, J. P., Haut, E. R., & Nasr, I. W. (2024).** Examining the Influence of Historical Redlining on Firearm Injuries in Current Day Baltimore, Maryland. (PMC11230467; also Research Square rs-4534823)
  `F_So_etal_2024_Redlining_FirearmInjuries_Baltimore.pdf`
  **USE:** ⭐⭐ **both are Baltimore, and both find a positive association** (So et al.: 2.24× per unit HOLC score, at **ZIP-code** resolution). Our Baltimore band estimate **reverses** (0.798, strengthening to 0.694 under the shooting-only restriction) while our whole-grade contrast is positive. That is the sharpest single illustration of the paper's methodological point: *the sign depends on the spatial resolution of the exposure.* These two papers are the comparison that makes it concrete. Note So et al. use ZIP codes — the coarsest unit in the field.

- **Uzzi, M., Ocampo, P., Wical, W., Aune, K., McComas, M., & Dean, L. T. (2026).** Spatial Association of Area-Level Credit Scores and Firearm Violence. *American Journal of Preventive Medicine*.
  `F_Uzzi_etal_2026_AreaLevelCreditScores_FirearmViolence_AJPM.pdf`

- **Edwards, J. R., Ong, C., Barber, S., Headen, I., Tabb, L. P., De Roos, A. J., & Schinasi, L. H. (2025).** Methodologic Strategies for Quantifying Associations of Historical and Contemporary Mortgage Discrimination on Population Health Equity: A Systematic Review. *Journal of Racial and Ethnic Health Disparities*, 12, 3353–3364. doi:10.1007/s40615-024-02137-3
  `F_Edwards_etal_2025_MethodologicStrategies_MortgageDiscrimination_SystematicReview_JREHD.pdf`
  **USE:** ⭐⭐ **the citation our methodological contribution needs.** 45 papers reviewed; 34 use HOLC maps; and in their words *"the construction and parametrization of … redlining and the spatial assignment of HOLC grades to contemporary addresses or neighborhoods varied substantially across studies."* They identify the problem; we quantify what it costs, three ways.

- **Barboza-Salerno, G., et al. (2025).** Redlining, reinvestment, and racial segregation: a Bayesian spatial analysis of mortgage lending trajectories and firearm-related violence. *Injury Epidemiology*, 12, 23. doi:10.1186/s40621-025-00579-9
  `F_BarbozaSalerno_etal_2025_Redlining_Reinvestment_Segregation_FirearmViolence_InjEpi.pdf`
- **Lee, D. B., Contreras, L. M., Rupp, L., Cook, S. H., Zimmerman, M. A., Carter, P. M., Theall, K. P., Bennett, R., & Fleckman, J. M. (2026).** Racism and racial disparities in firearm violence: A scoping review. *American Journal of Community Psychology*. doi:10.1002/ajcp.70064
  `F_Lee_etal_2026_RacismRacialDisparities_FirearmViolence_ScopingReview_AJCP.pdf` — most recent field review.
- `F_2025_ViolentInjuryAdolescents_HistoricRedlining_AJCP.pdf` — Exploring the link between the risk of violent injury in adolescents and historic redlining practices. *AJCP* (2025), doi:10.1002/ajcp.70005.

**[NO PDF] Benns, M., Ruther, M., Nash, N., Bozeman, M., Harbrecht, B., & Miller, K. (2020).** The impact of historical racism on modern gun violence: Redlining in the city of Louisville, KY. *Injury*, 51(10), 2192–2198. doi:10.1016/j.injury.2020.06.042 — the famous "5× greater risk" single-city estimate. *Paywalled (Elsevier).*

**[NO PDF] Jay, J. (2024/2025).** Redlining, Root Causes, and a Firearm Injury Scholarship of Consequence. *AJPH*. doi:10.2105/AJPH.2024.307933 — commentary; the "so what should this field do" piece. Useful for our discussion.

**[NO PDF] Abduljaleel, O., Davidowitz, C., Dong, G., Ghildiyal, A., Greenfield, B., Hossain, M., et al. (2025).** The Impact of Historical and Modern-Day Redlining on Firearm Violence: A Decade-Long Multilevel Study of 38 States. *Journal of Racial and Ethnic Health Disparities*. doi:10.1007/s40615-025-02795-x

---

## 05 — METHODS: boundary / geographic RD
*The technical standard we must meet or explicitly decline.*

- **Cattaneo, M. D., Titiunik, R., & Yu, R. (2026).** Boundary Discontinuity Designs: Theory and Practice. arXiv:2511.06474v3 (13 Feb 2026). Prepared for the 2025 Econometric Society World Congress.
  `M_CattaneoTitiunikYu_2026_BoundaryDiscontinuityDesigns_TheoryPractice.pdf`
  **USE:** ⭐⭐ synthesises 80+ BD papers and gives current recommendations. **Written after every applied paper in tiers 01–04.** Our design must be described in its vocabulary, and any departure (we use band rate ratios, not local polynomial) justified against it.

- **Cattaneo, M. D., Titiunik, R., & Yu, R. (2026).** Estimation and Inference in Boundary Discontinuity Designs: Distance-Based Methods. arXiv:2510.26051 (dated 26 May 2026).
  `M_CattaneoTitiunikYu_2026_BDD_DistanceBasedMethods.pdf`
  **USE:** ⭐⭐ **distance-based** BD methods — i.e. exactly our signed-distance gradient and band construction. If our bandwidth behaviour has a known name and known pathology, it is in here. Read before finalising the band-width figure.

- **Bugni, F. A., Crippa, F., & Restrepo, D. (2026).** Manipulation Testing in Boundary Discontinuity Designs. arXiv:2609.00350 (31 Aug 2026).
  `M_Bugni_Crippa_Restrepo_2026_ManipulationTesting_BDD.pdf`
  **USE:** ⭐⭐ the first manipulation test for general boundary shapes. Their logic — *absent manipulation, observations near the boundary should split evenly between treated and control within groups defined by projection onto the boundary, tested via binomial balance tests on k-means groups* — is **structurally our segment-FE conditional binomial**, but deployed as a diagnostic. Our donut-hole test and density-at-the-line check are a hand-rolled version of this. **Cite it, and consider running the real test on the LA geocoding asymmetry.**

- **Keele, L. J., & Titiunik, R. (2015).** Geographic Boundaries as Regression Discontinuities. *Political Analysis*, 23(1), 127–155. doi:10.1093/pan/mpu014 — **[NO PDF]**, paywalled (Cambridge).
  **USE:** the **compound treatment** problem — a geographic boundary bundles many treatments at once. This is the strongest available framing for our composition-imbalance result: widening the band admits more compound treatment. Obtain.

- **Keele, L., Titiunik, R., & Zubizarreta, J. R. (2014/2015).** Enhancing a Geographic Regression Discontinuity Design Through Matching. *JRSS-A*, 178, 223–239. doi:10.1111/rssa.12056 — **[NO PDF]**.
- **Keele, L., & Titiunik, R. (2016).** Natural Experiments Based on Geography. *Political Science Research and Methods*, 4, 65–95. doi:10.1017/psrm.2015.4 (+ erratum doi:10.1017/psrm.2015.37) — **[NO PDF]**.
- **Cattaneo, M. D., & Titiunik, R. (2022).** Regression Discontinuity Designs. *Annual Review of Economics*, 14, 821–851. doi:10.1146/annurev-economics-051520-021409 — **[NO PDF]**.

- **Black, S. E. (1999).** Do Better Schools Matter? Parental Valuation of Elementary Education. *Quarterly Journal of Economics*, 114(2), 577–599. doi:10.1162/003355399556070
  `M_Black_1999_DoBetterSchoolsMatter_BoundaryDesign_QJE.pdf` — the origin of the boundary design.

- **Gelman, A., & Imbens, G. (2019).** Why High-Order Polynomials Should Not Be Used in Regression Discontinuity Designs. *JBES*, 37(3), 447–456. doi:10.1080/07350015.2017.1366909
  `M_GelmanImbens_2019_HighOrderPolynomials_RD.pdf` — supports our local/binned gradient over a global fit. Relevant to the bandwidth-instability near-miss.

**[NO PDF] Dell, M. (2010).** The Persistent Effects of Peru's Mining *Mita*. *Econometrica*, 78(6), 1863–1903. doi:10.3982/ECTA8121 — the canonical geographic RD for persistence. *All mirrors returned HTML.*
- `M_Karakas_2025_MitaDoubleML_GeoRD_MASTERSTHESIS.pdf` — a double-ML reanalysis of Dell. ⚠ **UCLA master's thesis, unrefereed.** Kept only as a pointer to Dell's design; **do not cite.**

---

## 06 — METHODS: meta-analysis & spatial inference

- **DerSimonian, R., & Laird, N. (1986).** Meta-analysis in clinical trials. *Controlled Clinical Trials*, 7(3), 177–188. doi:10.1016/0197-2456(86)90046-2
  `M_DerSimonianLaird_1986_MetaAnalysisClinicalTrials.pdf` — our pooling estimator.

- **IntHout, J., Ioannidis, J. P. A., Rovers, M. M., & Goeman, J. J. (2016).** Plea for routinely presenting prediction intervals in meta-analysis. *BMJ Open*, 6(7), e010247. doi:10.1136/bmjopen-2015-010247
  `M_IntHout_etal_2016_PredictionIntervals_MetaAnalysis_BMJOpen.pdf`
  **USE:** ⭐⭐ **the methodological hero of our paper.** They show prediction intervals change the conclusion in >70% of significant heterogeneous meta-analyses. Our Wave-1 PI was **[0.899, 1.740]** — published before Wave 2 was fetched, and it contained the Wave-2 null. This is the citation that turns our failed replication into a demonstration.

- **Higgins, J. P. T., & Thompson, S. G. (2002).** Quantifying heterogeneity in a meta-analysis. *Statistics in Medicine*, 21(11), 1539–1558. doi:10.1002/sim.1186 — **[NO PDF]**, Wiley paywall. Source of I² (ours: 77.6%).

- **Conley, T. G. (1999).** GMM estimation with cross sectional dependence. *Journal of Econometrics*, 92(1), 1–45. doi:10.1016/S0304-4076(98)00084-0 — **[NO PDF]**, paywalled.
  `M_Jeanty_2012_ConleySpatialHAC_StataImplementation.pdf` — Jeanty (2012), Stata implementation; a readable exposition of the estimator.
- **Lehner, A. (2026).** Bandwidth Selection for Spatial HAC Standard Errors. arXiv:2603.03997.
  `M_Lehner_2026_BandwidthSelection_SpatialHAC.pdf` — relevant to justifying our 500 m bootstrap cluster size.
- **Cameron, A. C., & Miller, D. L. (2015).** A Practitioner's Guide to Cluster-Robust Inference. *Journal of Human Resources*, 50(2), 317–372. doi:10.3368/jhr.50.2.317 — **[NO PDF]**; author's site returned an empty file.

**[NO PDF] Kelly, M. (2019/2024).** The Standard Errors of Persistence. CEPR DP13783 / *Journal of Development Economics*. — ⛔⛔ **the paper most dangerous to ours.** Across 27 persistence studies, replacing the explanatory variable with spatial noise often *improves* fit. Demands reported Moran statistics and noise simulations. **Our sham-boundary placebo (RR 1.020, contains 1) is precisely the noise simulation Kelly asks for — that is a selling point, but only if we cite him and say so.** Obtain.

---

## 07 — GUN VIOLENCE & NEIGHBOURHOOD MECHANISM
*Why a neighbourhood boundary could plausibly matter for shootings at all.*

- **Sampson, R. J., Raudenbush, S. W., & Earls, F. (1997).** Neighborhoods and Violent Crime: A Multilevel Study of Collective Efficacy. *Science*, 277(5328), 918–924. doi:10.1126/science.277.5328.918 — **[NO PDF]** (host returned an empty file).
  `G_NIJ_CollectiveEfficacy_ReduceViolence.pdf` — NIJ research brief covering the same programme of work; usable stand-in for the descriptive claim only.

- **Branas, C. C., South, E., Kondo, M. C., Hohl, B. C., Bourgois, P., Wiebe, D. J., et al. (2018).** Citywide cluster randomized trial to restore blighted vacant land and its effects on violence, crime, and fear. *PNAS*, 115(12), 2946–2951. doi:10.1073/pnas.1718503115
  `G_Branas_etal_2018_VacantLandRCT_PNAS.pdf`
  **USE:** the only randomised evidence that the **built environment** causally moves shootings. Our mechanism story depends on something like this being true.

- `G_2023_ResidentialRacialSegregation_FirearmFatalities.pdf` — ecological study of residential racial segregation and firearm fatality risk (PMC10012477).
- `G_NeighborhoodSegregation_TreeCover_FirearmViolence.pdf` — Neighborhood segregation, tree cover and firearm violence (USDA Forest Service TreeSearch 65424).

**[NO PDF] Lyons, C. J., Vélez, M. B., & Chen, X. (2023).** Inheriting the Grade: HOLC "Redlining" Maps and Contemporary Neighborhood Crime. *Socius*, 9. doi:10.1177/23780231231197030 — HOLC grades predict violence and burglary ~70 years on; mediated by disadvantage, segregation, housing instability. **Journal is fully open access but SAGE blocked automated download — grab it manually in a browser, it is free.**

**[NO PDF] Powell, R., & Porter, J. (2022).** Redlining, Concentrated Disadvantage, and Crime. *American Journal of Criminal Justice*, 48, 1132–1156. doi:10.1007/s12103-022-09688-3

---

## 08 — DATA SOURCES

- **Nelson, R. K., Winling, L., Marciano, R., & Connolly, N., et al.** *Mapping Inequality: Redlining in New Deal America.* American Panorama, ed. R. K. Nelson & E. L. Ayers. Digital Scholarship Lab, University of Richmond. https://dsl.richmond.edu/panorama/redlining/
  ⚠ Licensed **CC BY-NC-SA 4.0**. Our local copy: `historical_mechanism/holc_redlining/mappinginequality.json`. **Record the access date in the paper.**
  Mirrors worth knowing: Virginia Tech Figshare (doi 10.7294/…, see data.lib.vt.edu/articles/dataset/Mapping_Inequality/14113463) and a GeoParquet/PMTiles build at source.coop/cboettig/mappinginequality.
- **ACS 5-year tract tables** — denominators, areally interpolated into band polygons (see `multi_city_boundary_design.py:interp`).
- **Per-city open-data portals** — Socrata / CKAN / ArcGIS FeatureServer / Carto. Adapters and manifests in `displacement/fetch_city_shootings.py`. Known traps recorded there: NYC ships lat/lon **swapped**; Seattle's `'-'` offence class; Boston's tz-naive/tz-aware concat; Kansas City polygons labelled MO that lie in Kansas.

---

## CLAIM → CITATION MAP

| Our claim | Cite |
|---|---|
| Boundary design is the right identification strategy | Black 1999; Dell 2010; Keele & Titiunik 2015; Aaronson et al. 2021 |
| …and here is how it should be done in 2026 | Cattaneo, Titiunik & Yu 2026 (both papers) |
| Our donut/density check has a formal counterpart | Bugni, Crippa & Restrepo 2026 |
| Redlining→firearm violence is an established literature | Jacoby et al. 2018; Benns et al. 2020; Poulson et al. 2021; Mehranbod et al. 2022 |
| …whose exposure measurement is inconsistent | **Edwards et al. 2025**; Gobaud et al. 2024 |
| …and whose effect is **not uniform across cities** | **Mehranbod et al. 2022** (their own non-stationarity); **Xu 2023**; our 11-city result — the gap **Mitre-Becerril 2026** leaves open by pooling 48 cities without a per-city effect |
| The pooled boundary effect is smaller than the field claims | **Mitre-Becerril 2026** (6–15% with pre-period controls, vs ~30% in Anders 2023 / Lyons et al. 2023) — our result extends this from "smaller" to "wrong object" |
| Area-denominated counts ≠ population-denominated rates | **Mitre-Becerril 2026** uses crimes per hexagon with no contemporary population denominator; we interpolate ACS population into the bands |
| Band width buys effect size via composition imbalance | Keele & Titiunik 2015 (compound treatment); Markley & Holloway 2024; our three triangulating tests |
| Sign flips with spatial resolution of exposure | **So et al. 2024 & Uzzi et al. 2023 (Baltimore, positive, ZIP/tract) vs our Baltimore band (0.694–0.798)** |
| Pooled effects hide heterogeneity; report prediction intervals | **IntHout et al. 2016**; Higgins & Thompson 2002; DerSimonian & Laird 1986 |
| Spatial persistence results need a noise null | **Kelly 2019** — answered by our sham-boundary placebo (1.020, contains 1) |
| Clustered inference at the segment | Conley 1999; Cameron & Miller 2015; Lehner 2026 |
| The exposure may not be the policy | **Fishback et al. 2024**; Hillier 2003; Michney & Winling 2019; Swope et al. 2025; Thomas et al. 2026 |
| Neighbourhood environment causally affects shootings | Branas et al. 2018; Sampson et al. 1997 |

---

## ACQUISITION QUEUE (paywalled, ranked)

✅ **Obtained 2026-09-13 (Nate, via library):** Mitre-Becerril 2026 · Xu 2023 · Swope et al. 2025.
The three that gated the contribution paragraph are in.

1. **Kelly 2019**, Standard Errors of Persistence — we already satisfy it; must cite it.
2. **Keele & Titiunik 2015**, *Political Analysis* — compound treatment framing.
3. **Lee et al. 2022**, *SSM* meta-analysis — the pooling precedent.
4. **Markley & Holloway 2024**, *Annals AAG* — composition mechanism at the boundary.
5. **Winling (2025)**, *AJPH* p. 649 — the companion comment to Swope et al.; short, and it is the other half of that exchange.
6. Lyons et al. 2023, *Socius* — **free**, just needs a browser.
7. Benns et al. 2020; Markley 2023; Thomas et al. 2026 (*Nature*).

---

## CORRECTIONS MADE DURING THE BUILD

Recorded because a filename assigned from a URL is not evidence of what the file contains.

1. `H_SalazarMiranda_*` → **`H_Conzelmann_*`** — lead author is Conzelmann, not Salazar-Miranda.
2. `M_Cattaneo_etal_2026_ManipulationTesting` → **`M_Bugni_Crippa_Restrepo_2026_...`** — Cattaneo is thanked in the acknowledgements, not an author.
3. `C_Mallach_2024_HOLCMapsAndRedlining` → **`..._ShiftingTheRedliningParadigm_HousingPolicyDebate`** — true published title.
4. `M_BandwidthSelection_SpatialHAC` → **`M_Lehner_2026_...`**.
5. `C_ColoringInsideTheLines` → **`C_Gupta_2022_..._PREPRINT`** — unrefereed student preprint, downgraded.
6. `M_MitaDoubleMachineLearning` → **`M_Karakas_2025_..._MASTERSTHESIS`** — unrefereed, downgraded, do-not-cite.
7. **Aaronson et al. "place-based" paper is in *Regional Science and Urban Economics*, not *Journal of Urban Economics*** — my first DOI guess 404'd; Crossref title search corrected it. This error is common in the wild; do not inherit it.
8. `C_WinlingMichney_2021_RootsOfRedlining_JAH.pdf` — the file is the *Journal of American History* "Roots of Redlining" article, **not** the *Journal of Urban History* "New Perspectives" article it was downloaded in search of. Both are cited above; only one has a PDF.
