# math_model.md

## 1. Scope

This document defines the exact mathematics for the FM26 moneyball dashboard.

The objective is to condense the FM export into statistically grounded player scores without manually guessing metric weights.

The dashboard must support **current-season cross-sectional scoring** from a single same-league export. The export does **not** contain a `League` column, so one uploaded file is treated as one league-specific cohort.

An optional future-season forecasting extension can be added later if multiple season files exist. The current dashboard must already work from one file.

## 2. Input contract

### 2.1 Required file format
- semicolon-delimited CSV
- one row per player
- one uploaded file = one same-league cohort

### 2.2 Columns present in the current export
- `Inf`
- `Player`
- `Nation`
- `Club`
- `Position`
- `Age`
- `Ability`
- `Potential`
- `Transfer Value`
- `Wage`
- `AT League Goals`
- `Recommendation`
- `Pres A`
- `Poss Won/90`
- `K Tck/90`
- `K Tck`
- `Itc`
- `Int/90`
- `Clr/90`
- `Clearances`
- `Blk/90`
- `Pres A/90`
- `Pres C`
- `Pres C/90`
- `Shts Blckd/90`
- `Tck R`
- `Tck A`
- `Tck C`
- `Tck/90`
- `Shts Blckd`
- `Blk`
- `Shot/90`
- `Shot %`
- `ShT/90`
- `ShT`
- `Shots From Outside The Box Per 90 minutes`
- `Shots`
- `Goals From Outside The Box`
- `Free Kick Shots`
- `xG/shot`
- `Conv %`
- `Svt`
- `Svp`
- `Svh`
- `Sv %`
- `xSv %`
- `xGP/90`
- `xGP`
- `PsP`
- `Poss Lost/90`
- `Ps C/90`
- `Ps C`
- `Ps A/90`
- `Pas A`
- `Pas %`
- `OP-KP/90`
- `KP/90`
- `Key`
- `CCC`
- `Ch C/90`
- `Pr passes/90`
- `Asts/90`
- `Off`
- `Sprints/90`
- `Drb/90`
- `Saves/90`
- `Drb`
- `Dist/90`
- `Distance`
- `MLG`
- `Yel`
- `xG`
- `Tcon/90`
- `Red cards`
- `Pts/Gm`
- `PoM`
- `Pen/R`
- `Pens S`
- `Pens Saved Ratio`
- `Pens Saved`
- `Pens Faced`
- `Pens`
- `NP-xG/90`
- `NP-xG`
- `Mins/Gm`
- `Minutes`
- `Goals per 90 minutes`
- `Goals Conceded`
- `Goals`
- `Game Win Ratio`
- `Fouls Made`
- `Fouls Against`
- `xG/90`
- `xG-OP`
- `xA/90`
- `xA`
- `Con/90`
- `Cln/90`
- `Clean Sheets`
- `Rating`
- `Mins/Gl`
- `Assists`
- `OP-Crs C`
- `OP-Crs A`
- `Cr C`
- `Cr A`
- `Hdrs`
- `Hdrs A`
- `Hdr %`
- `Preferred Foot`
- `Right Foot`
- `Left Foot`
- `Height`
- `OP-Cr %`
- `Appearances`
- `OP-Crs C/90`
- `OP-Crs A/90`
- `Hdrs L/90`
- `Cr C/90`
- `Crs A/90`
- `Cr C/A`
- `AT League Apps`
- `AT Gls`
- `AT Apps`
- `K Hdrs/90`
- `Hdrs W/90`
- `Aer A/90`
- `Actual Playing Time`

## 3. Column usage policy

### 3.1 Performance-score exclusions
These columns must never enter the performance score because they are leakage, market outputs, or cumulative history:

- leakage:
  - `Ability`
  - `Potential`
  - `Recommendation`
  - `Rating`

- market-only:
  - `Transfer Value`
  - `Wage`

- historical accumulation:
  - `AT League Goals`
  - `AT League Apps`
  - `AT Gls`
  - `AT Apps`

- identifiers / metadata:
  - `Inf`
  - `Player`
  - `Nation`
  - `Club`
  - `Position`
  - `Preferred Foot`
  - `Right Foot`
  - `Left Foot`
  - `Height`

### 3.2 Context-only columns
These columns are not direct skill inputs:
- `Pts/Gm` -> used only as team-strength control
- `Minutes` -> exposure for shrinkage and uncertainty
- `Appearances`
- `Mins/Gm`
- `Actual Playing Time`
- `Age` -> display now, optional forecast covariate later

### 3.3 Outcome-like columns
These are allowed only when specifically mapped into a primitive family and adjusted for team strength where necessary:
- `Goals per 90 minutes`
- `Goals`
- `Assists`
- `xG`
- `xG/90`
- `xA`
- `xA/90`
- `NP-xG`
- `NP-xG/90`
- `Con/90`
- `xGP/90`
- `xGP`
- `Saves/90`
- `Sv %`
- `xSv %`

## 4. Role cohorts

### 4.1 Broad-role mapping from `Position`
A player may belong to multiple broad roles. Compute scores for every eligible broad role.

Use these rules:

- `GK` if `Position` contains `GK`
- `CB` if `Position` contains `D (C)`
- `FB_WB` if `Position` contains `D (L)` or `D (R)` or `WB (L)` or `WB (R)` or side-back equivalents
- `DM` if `Position` contains `DM`
- `CM` if `Position` contains `M (C)` but not `AM (C)` and not `DM`
- `AM_W` if `Position` contains any of:
  - `AM (C)`
  - `AM (L)`
  - `AM (R)`
  - `M (L)`
  - `M (R)`
- `ST` if `Position` contains `ST`

If a player is eligible for multiple broad roles, the dashboard must compute and show a separate scorecard for each role.

## 5. Primitive metric basis

The model must not feed raw duplicates into the same latent block. Totals, per-90 rates, and success percentages for the same event family are mechanically related. Reduce the export to a primitive basis.

### 5.1 Exposure
Define:

\[
E_i = \max(\text{Minutes}_i / 90,\ 1e-6)
\]

### 5.2 Recomputed percentages from counts
Where counts and attempts are present, recompute the rate from counts instead of trusting the text export directly:

- pass completion:
\[
p^{pass}_i = \frac{\text{Ps C}_i}{\text{Pas A}_i}
\]

- tackle success:
\[
p^{tackle}_i = \frac{\text{Tck C}_i}{\text{Tck A}_i}
\]

- header win rate:
\[
p^{header}_i = \frac{\text{Hdrs}_i}{\text{Hdrs A}_i}
\]

- shot-on-target rate:
\[
p^{sot}_i = \frac{\text{ShT}_i}{\text{Shots}_i}
\]

- crossing completion:
\[
p^{cross}_i = \frac{\text{Cr C}_i}{\text{Cr A}_i}
\]

- open-play crossing completion:
\[
p^{opcross}_i = \frac{\text{OP-Crs C}_i}{\text{OP-Crs A}_i}
\]

- penalty conversion:
\[
p^{pen}_i = \frac{\text{Pens S}_i}{\text{Pens}_i}
\]

- penalty save rate:
\[
p^{pensave}_i = \frac{\text{Pens Saved}_i}{\text{Pens Faced}_i}
\]

If denominator is missing or zero, set the primitive to missing and let the family model handle it.

### 5.3 Rate primitives
Prefer rate form when available. If only counts are needed for shrinkage, infer implied counts from rate × exposure:

\[
y_i = r_i E_i
\]

This is acceptable because FM exports rates and totals from the same event log.

### 5.4 Derived residual primitives
Create these non-redundant residual features:

- finishing over expected:
\[
\Delta^{finish}_i = \text{Goals per 90 minutes}_i - \text{xG/90}_i
\]

- assist over expected:
\[
\Delta^{assist}_i = \text{Asts/90}_i - \text{xA/90}_i
\]

- shot quality:
\[
q^{shot}_i = \text{xG/shot}_i
\]

- possession security penalty:
\[
s^{loss}_i = -\text{Poss Lost/90}_i
\]

- discipline penalty:
\[
s^{discipline}_i = -(z(\text{Fouls Made}_i) + z(\text{Yel}_i) + z(\text{Red cards}_i) + z(\text{MLG}_i))
\]

The final implementation should store all raw pieces separately before any aggregation.

## 6. Empirical Bayes shrinkage

Shrink unstable player metrics toward the role-level cohort mean. This prevents low-minute players from dominating on noise.

Shrinkage is estimated **within each broad role cohort**.

### 6.1 Binomial-style metrics
For metrics built from successes and attempts, use beta-binomial shrinkage:

\[
\tilde p_{ij} = \frac{y_{ij} + \alpha_j}{n_{ij} + \alpha_j + \beta_j}
\]

where:
- \(y_{ij}\) = successes for player \(i\), metric \(j\)
- \(n_{ij}\) = attempts
- \(\alpha_j, \beta_j\) are estimated from the cohort by method of moments or maximum likelihood

Apply this to:
- pass completion
- tackle success
- header win rate
- shot-on-target rate
- crossing completion
- open-play crossing completion
- penalty conversion
- penalty save rate

### 6.2 Rate metrics
For event rates per 90, use Gamma-Poisson shrinkage:

\[
\tilde \lambda_{ij} = \frac{y_{ij} + k_j \mu_j}{E_i + k_j}
\]

where:
- \(y_{ij}\) = event count or implied count
- \(E_i\) = player exposure in 90s
- \(\mu_j\) = cohort mean event rate
- \(k_j\) = prior strength estimated from the cohort

Apply this to all count/rate metrics used in the family blocks, including:
- `Pres A/90`
- `Pres C/90`
- `Poss Won/90`
- `K Tck/90`
- `Int/90`
- `Tck/90`
- `Clr/90`
- `Blk/90`
- `Shts Blckd/90`
- `Shot/90`
- `ShT/90`
- `Pr passes/90`
- `KP/90`
- `OP-KP/90`
- `Ch C/90`
- `Asts/90`
- `Drb/90`
- `Sprints/90`
- `Dist/90`
- `NP-xG/90`
- `xG/90`
- `xA/90`
- `OP-Crs C/90`
- `OP-Crs A/90`
- `Cr C/90`
- `Crs A/90`
- `Hdrs W/90`
- `Hdrs L/90`
- `K Hdrs/90`
- `Aer A/90`
- `Saves/90`
- `xGP/90`
- `Con/90`
- `Cln/90`

### 6.3 Metrics with no clean count model
For metrics such as `xG/shot`, `xG-OP`, `xSv %`, use exposure-weighted normal shrinkage:

\[
\tilde x_{ij} = w_{ij} x_{ij} + (1 - w_{ij}) \bar x_j
\]

with

\[
w_{ij} = \frac{E_i}{E_i + \tau_j}
\]

and \(\tau_j\) estimated from the cohort by minimizing out-of-sample error.

## 7. Within-role standardization

After shrinkage, standardize every primitive **inside the broad role cohort**.

Use inverse-normal rank transformation, not plain z-score:

\[
z_{ij} = \Phi^{-1}\left( \frac{\operatorname{rank}(x_{ij}) - 0.5}{N_j} \right)
\]

where:
- \(N_j\) = number of non-missing observations in that role for metric \(j\)
- higher should always mean better

For metrics where lower is better, multiply by \(-1\) before transformation:
- `Poss Lost/90`
- `Fouls Made`
- `Yel`
- `Red cards`
- `MLG`
- `Off`
- `Hdrs L/90`
- `Con/90`

## 8. Team-strength adjustment using `Pts/Gm`

The export does not contain league strength or possession controls. The only allowed team-strength proxy is `Pts/Gm`.

For each primitive metric \(j\) inside each role cohort \(r\), fit a robust linear model:

\[
z_{ij} = a_{rj} + b_{rj} \cdot z(\text{Pts/Gm}_i) + \varepsilon_{ij}
\]

Use the residual as the team-adjusted metric:

\[
z^{adj}_{ij} = \varepsilon_{ij}
\]

Implementation notes:
- use Huber regression or another robust linear estimator
- fit only when at least 2 distinct `Pts/Gm` values exist inside the role cohort
- if the role cohort is too small or `Pts/Gm` has no variance, fall back to unadjusted \(z_{ij}\) and flag the score as less reliable

## 9. Family score construction

Family scores are interpretable sub-scores. Their weights must come from data, not from hand-picked coefficients.

For each role, define family blocks from the available primitives. Inside each family block:
1. collect adjusted primitives
2. drop constant features
3. impute remaining missing values with role-median adjusted values
4. fit PCA
5. keep PC1 as the family score
6. orient the sign so larger means better football value
7. rescale to a 0-100 percentile scale for UI display

### 9.1 Sign orientation rule
For a PCA component vector \(v\), choose its sign so that its correlation with the mean of positively oriented features is positive.

### 9.2 Family definitions by role

#### GK
- `shot_stopping`
  - `Saves/90`
  - `Sv %` or shrunk save rate
  - `xSv %`
  - `xGP/90`
  - `p^{pensave}`

- `handling_prevention`
  - `Svh`
  - `Svp`
  - `Svt`
  - `Con/90` (negative orientation)
  - `Cln/90`

- `distribution_security`
  - `Ps A/90`
  - pass completion
  - `PsP`
  - `Pr passes/90`

#### CB
- `disruption`
  - `Pres C/90`
  - `Poss Won/90`
  - `K Tck/90`
  - `Int/90`
  - `Tck/90`
  - tackle success

- `box_defending`
  - `Clr/90`
  - `Blk/90`
  - `Shts Blckd/90`

- `aerial_control`
  - `Hdrs W/90`
  - header win rate
  - `K Hdrs/90`
  - `Aer A/90`
  - `Hdrs L/90` (negative orientation)

- `progression_security`
  - `Ps A/90`
  - pass completion
  - `PsP`
  - `Pr passes/90`
  - `Poss Lost/90` (negative orientation)

- `discipline_security`
  - `Fouls Made`
  - `Yel`
  - `Red cards`
  - `MLG`

#### FB_WB
- `defending`
  - `Pres C/90`
  - `Poss Won/90`
  - `K Tck/90`
  - `Int/90`
  - `Tck/90`
  - tackle success

- `progression`
  - `PsP`
  - `Pr passes/90`
  - `Ps A/90`
  - pass completion
  - `Drb/90`

- `wide_creation`
  - `OP-Crs C/90`
  - `OP-Crs A/90`
  - open-play crossing completion
  - `Cr C/90`
  - `Crs A/90`
  - crossing completion
  - `KP/90`
  - `OP-KP/90`
  - `Ch C/90`
  - `xA/90`

- `engine`
  - `Sprints/90`
  - `Dist/90`

- `discipline_security`
  - `Poss Lost/90` (negative orientation)
  - `Fouls Made`
  - `Yel`
  - `Red cards`
  - `MLG`

#### DM
- `ball_winning`
  - `Pres C/90`
  - `Poss Won/90`
  - `K Tck/90`
  - `Int/90`
  - `Tck/90`
  - tackle success

- `retention_security`
  - pass completion
  - `Ps A/90`
  - `Poss Lost/90` (negative orientation)

- `progression`
  - `PsP`
  - `Pr passes/90`
  - `Ps A/90`
  - `OP-KP/90`
  - `KP/90`

- `creation`
  - `Ch C/90`
  - `CCC`
  - `xA/90`
  - `Asts/90`

- `discipline`
  - `Fouls Made`
  - `Yel`
  - `Red cards`
  - `MLG`

#### CM
- `retention`
  - pass completion
  - `Ps A/90`
  - `Poss Lost/90` (negative orientation)

- `progression`
  - `PsP`
  - `Pr passes/90`
  - `Drb/90`

- `creation`
  - `KP/90`
  - `OP-KP/90`
  - `Ch C/90`
  - `CCC`
  - `xA/90`
  - `Asts/90`

- `ball_winning`
  - `Pres C/90`
  - `Poss Won/90`
  - `K Tck/90`
  - `Int/90`
  - `Tck/90`
  - tackle success

- `shot_contribution`
  - `Shot/90`
  - `ShT/90`
  - `xG/90`
  - `NP-xG/90`
  - `xG/shot`
  - finishing over expected

#### AM_W
- `threat`
  - `Shot/90`
  - `ShT/90`
  - shot-on-target rate
  - `xG/90`
  - `NP-xG/90`
  - `xG/shot`
  - finishing over expected
  - `Goals per 90 minutes`

- `creation`
  - `KP/90`
  - `OP-KP/90`
  - `Ch C/90`
  - `CCC`
  - `xA/90`
  - `Asts/90`

- `progression_carrying`
  - `PsP`
  - `Pr passes/90`
  - `Drb/90`
  - pass completion
  - `Ps A/90`

- `pressing_work`
  - `Pres A/90`
  - `Pres C/90`
  - `Sprints/90`
  - `Dist/90`

- `discipline_security`
  - `Poss Lost/90` (negative orientation)
  - `Off` (negative orientation)
  - `Fouls Made`
  - `Yel`
  - `MLG`

#### ST
- `threat_volume`
  - `Shot/90`
  - `ShT/90`
  - `xG/90`
  - `NP-xG/90`
  - `Goals per 90 minutes`

- `finishing_quality`
  - shot-on-target rate
  - `Conv %`
  - `xG/shot`
  - finishing over expected

- `link_creation`
  - `KP/90`
  - `OP-KP/90`
  - `Ch C/90`
  - `xA/90`
  - `Asts/90`
  - pass completion
  - `PsP`

- `pressing`
  - `Pres A/90`
  - `Pres C/90`
  - `Poss Won/90`

- `aerial_presence`
  - `Hdrs W/90`
  - header win rate
  - `K Hdrs/90`
  - `Aer A/90`

## 10. Overall performance score

The overall current-season performance score must also be data-driven.

Inside each role cohort:
1. collect all family scores for that role
2. standardize them
3. fit PCA on the family-score matrix
4. use PC1 as the overall performance score
5. orient the sign so that it correlates positively with the mean of the family scores
6. convert to a 0-100 percentile scale for the UI

Formally:

\[
F_i = [f_{i1}, \dots, f_{iK}]
\]

\[
\text{PerfRaw}_i = \text{PC1}(F_i)
\]

\[
\text{PerformanceScore}_i = 100 \times \frac{\operatorname{rank}(\text{PerfRaw}_i) - 0.5}{N}
\]

This is the required current-season score for dashboard v1.

## 11. Cost score

Cost must remain separate from performance.

Parse `Transfer Value` and `Wage` into numeric values. Use log transform after adding a small positive offset where necessary:

\[
v_i = \log(1 + \text{TransferValueNumeric}_i)
\]
\[
w_i = \log(1 + \text{WageNumeric}_i)
\]

Inside each role cohort:
1. standardize \(v_i\) and \(w_i\)
2. fit PCA
3. use PC1 as the cost score
4. orient so larger means more expensive
5. convert to 0-100 percentile scale

\[
\text{CostRaw}_i = \text{PC1}([z(v_i), z(w_i)])
\]

\[
\text{CostScore}_i = 100 \times \frac{\operatorname{rank}(\text{CostRaw}_i) - 0.5}{N}
\]

## 12. Value gap

Value gap is the moneyball score.

\[
\text{ValueGapRaw}_i = z(\text{PerfRaw}_i) - z(\text{CostRaw}_i)
\]

\[
\text{ValueGapScore}_i = 100 \times \frac{\operatorname{rank}(\text{ValueGapRaw}_i) - 0.5}{N}
\]

Interpretation:
- high score -> underpriced relative to performance
- low score -> overpriced relative to performance

## 13. Uncertainty score

Uncertainty must be a separate score, not hidden inside performance.

Build three uncertainty primitives inside each role cohort:

### 13.1 Exposure uncertainty
\[
u^{exp}_i = \frac{1}{\sqrt{E_i + 1}}
\]

### 13.2 Bootstrap instability
For each role cohort:
1. bootstrap the cohort rows with replacement
2. refit the full family-score and performance-score pipeline
3. record the player's `PerfRaw`
4. compute bootstrap standard deviation

\[
u^{boot}_i = \operatorname{sd}(\text{PerfRaw}^{(1)}_i, \dots, \text{PerfRaw}^{(B)}_i)
\]

Use a fixed seed. A default of `B = 200` is acceptable.

### 13.3 Shrinkage intensity
For each primitive, compute the degree of pull toward the cohort mean. Aggregate by mean absolute shrinkage across primitives used for that role:

\[
u^{shrink}_i = \frac{1}{J_i} \sum_{j=1}^{J_i} |x_{ij} - \tilde x_{ij}|
\]

### 13.4 Final uncertainty score
Inside each role cohort:
1. standardize `u^exp`, `u^boot`, `u^shrink`
2. fit PCA
3. use PC1 as uncertainty raw score
4. orient so larger means more uncertain
5. convert to 0-100 percentile scale

## 14. Missing data rules

Inside each role-family block:
- drop features that are constant in that role
- drop features missing for all players in that role
- impute remaining missing adjusted values with role-median adjusted value
- record dropped and imputed features in diagnostics

A role-family score may be computed only if at least 2 non-constant primitives remain after filtering.

A role performance score may be computed only if at least 2 family scores exist.

If not, return `NA` and a warning.

## 15. Diagnostics and traceability

For every displayed score, the app must expose:
- role cohort used
- raw primitive values
- shrunk primitive values
- standardized values
- `Pts/Gm`-adjusted residual values
- family score loadings
- overall score loadings
- cost score loadings
- uncertainty score loadings

## 16. Optional extension: true future-performance forecast

This is not required for dashboard v1 because the current upload format is single-season.

If historical season panels are later added:
1. compute all current-season family scores for season \(t\)
2. build a target from season \(t+1\) role-specific performance score
3. fit Elastic Net with cross-validation:
\[
g_{i,t+1} = \beta_0 + \beta^\top F_{i,t} + s(\text{Age}_{i,t}) + \epsilon_i
\]
4. use predicted \(g_{i,t+1}\) as the forecast score

Until historical panels exist, do not fabricate a forecast score.

## 17. Output schema for the dashboard

For each player-role row, produce:

- `player`
- `club`
- `position`
- `broad_role`
- `minutes`
- `pts_per_game`
- `performance_raw`
- `performance_score`
- `cost_raw`
- `cost_score`
- `value_gap_raw`
- `value_gap_score`
- `uncertainty_raw`
- `uncertainty_score`
- one column per family raw score
- one column per family percentile score
- diagnostics metadata

## 18. Sanity checks

The implementation must satisfy all of these:

1. No performance score changes when only `Transfer Value` or `Wage` changes.
2. No performance score changes when only `Ability`, `Potential`, `Recommendation`, or `Rating` changes.
3. Higher minutes should reduce uncertainty, all else equal.
4. Team adjustment must remove the linear relationship between adjusted primitive and `Pts/Gm` inside role, up to estimation error.
5. A player can have different scores in different eligible broad roles.
6. Every score shown in the UI must be reproducible from persisted artifacts.
