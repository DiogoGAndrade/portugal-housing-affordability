# Phase 4 - exploratory results (generated, preliminary)

Descriptive/exploratory. Municipal medians carry no published sampling error; p-values are indicative.

## 1. Sensitivity of I2 (2024, A=80 m2) to alternative inputs
```
                        variant  n_both  spearman_vs_headline  median_ratio_alt_over_headline  share_changing_quintile
income: gross per tax household     299                 1.000                           0.962                    0.020
       income: net per taxpayer     299                 0.998                           1.219                    0.060
      price: new dwellings only     152                 0.927                           1.159                    0.382
 price: existing dwellings only     297                 0.991                           0.965                    0.128
```
Area A rescales I2 linearly, so it changes levels but never ranks.

## 2. Kruskal-Wallis across NUTS II (municipalities, 2024)
```
                 metric  n_municipalities  n_groups       H  p_value  epsilon_sq
          i2_years_80m2               299         9 123.763      0.0       0.415
i6_price_vs_income_real               283         9  77.680      0.0       0.275
```

## 3. Spatial autocorrelation (mainland municipalities, Queen contiguity, 999 permutations)
- {'variable': 'ln_i2', 'n': 273, 'islands_after_subset': 0, 'morans_I': 0.7653618277145828, 'p_sim': 0.001, 'lisa_significant_5pct': {'LL': 61, 'HH': 55, 'HL': 3}}
- {'variable': 'i6_price_vs_income_real', 'n': 259, 'islands_after_subset': 0, 'morans_I': 0.4188046675374039, 'p_sim': 0.001, 'lisa_significant_5pct': {'HH': 40, 'LL': 28, 'LH': 5, 'HL': 5}}

## 4. Clustering exploration (k-means, standardised ln price, ln income, I6 price; 2024)
```
 k  silhouette  stability_ARI_mean
 2       0.359               0.972
 3       0.285               0.764
 4       0.274               0.837
 5       0.279               0.833
 6       0.298               0.793
 7       0.285               0.656
 8       0.271               0.673
```
Best silhouette at k=2. Silhouette < 0.25 would indicate weak structure; interpret as a descriptive typology, not discrete types.
```
 cluster   n  median_ln_price  median_ln_income  median_i6_price_vs_income_real                                               share_by_nuts2
       0 152            7.245             9.610                           0.279 {'Norte': 0.2, 'Centro': 0.17, 'Oeste e Vale do Tejo': 0.16}
       1 131            6.407             9.509                           0.015            {'Norte': 0.36, 'Centro': 0.35, 'Alentejo': 0.17}
```

## 5. Who is missing a rent value (2024)
```
{
 "n": 308,
 "with_rent": 244,
 "ln_price": {
  "median_with_rent": 1043.497005266427,
  "median_without_rent": 508.9999999999999,
  "n_without": 59,
  "mannwhitney_p": 1.1925834565497743e-13
 },
 "ln_income": {
  "median_with_rent": 14224.499991212355,
  "median_without_rent": 13189.0,
  "n_without": 55,
  "mannwhitney_p": 4.787155997148289e-08
 },
 "share_with_rent_by_nuts2": {
  "Alentejo": 0.68,
  "Algarve": 0.94,
  "Centro": 0.84,
  "Grande Lisboa": 1.0,
  "Norte": 0.78,
  "Oeste e Vale do Tejo": 0.97,
  "Península de Setúbal": 1.0,
  "Região Autónoma da Madeira": 0.55,
  "Região Autónoma dos Açores": 0.42
 }
}
```

## 6. Payment scenario
Excluded from the published report: BPstat reuse terms were not found. The code remains; run `python -m housing_pt.phase4 --with-bpstat` for a local analysis written to reports/local/ (git-ignored).
