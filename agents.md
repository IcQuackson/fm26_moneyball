# AGENTS.md

## Objective

Build a local dashboard for **Football Manager 2026 moneyball analysis** using only the columns present in the FM export below. The dashboard must let the user upload a semicolon-delimited CSV, compute statistically grounded scores, and inspect any selected player against the correct peer cohort.

The scoring logic is defined in `math_model.md`. Do not improvise alternative formulas. Do not introduce manual feature weights. Do not use columns not present in the export.

## Non-negotiable constraints

1. **Use only these input columns** from the FM export:

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

2. **No manual weights** in any score. All weights must come from data:
   - empirical Bayes shrinkage hyperparameters estimated from the cohort
   - robust regression coefficients estimated from the cohort
   - PCA / factor-analysis loadings estimated from the cohort
   - optional forecast coefficients estimated from historical panels only

3. **Same-league analysis is mandatory.**
   - The current export has no `League` column.
   - Therefore the app must treat **one uploaded CSV as one league-specific cohort**.
   - If the user uploads a mixed-league file later, the app must show a warning that same-league assumptions are violated.

4. **Position-specific analysis is mandatory.**
   - Never compare all players together.
   - Compute scores inside broad role cohorts only.

5. **Leakage columns must not enter the performance score**:
   - `Ability`
   - `Potential`
   - `Recommendation`
   - `Rating`

6. **Market columns must not enter the performance score**:
   - `Transfer Value`
   - `Wage`
   - They are used only for cost/value scoring.

7. **Team-strength control is restricted to data actually present in the file.**
   - Use `Pts/Gm` as the only team-strength covariate.
   - Do not invent possession, xGD, or wage-bill club controls unless such columns are later added to the upload format.

8. **Historical cumulative columns are display-only, not model inputs**:
   - `AT League Goals`
   - `AT League Apps`
   - `AT Gls`
   - `AT Apps`

9. **Derived duplicates must be reduced to a primitive basis.**
   - Do not feed totals, per-90 versions, and percentages for the same event family into the same PCA block if they are mechanically redundant.
   - Follow the primitive feature definitions in `math_model.md`.

## Expected product

Build a dashboard with these capabilities:

### 1. Data load
- Upload FM CSV exported with `;` separator.
- Parse numeric strings robustly.
- Show row count, role counts, missingness, and detected league-homogeneous assumption.

### 2. Cohort construction
- Map each player to one or more broad roles from `Position`:
  - `GK`
  - `CB`
  - `FB_WB`
  - `DM`
  - `CM`
  - `AM_W`
  - `ST`
- If a player is multi-positional, compute scores for every eligible broad role and expose them in separate tabs/cards.

### 3. Model pipeline
Implement this order exactly:

1. load + clean
2. parse roles
3. build primitive metrics
4. estimate shrinkage
5. standardize within role
6. residualize by `Pts/Gm`
7. compute role-family latent scores
8. compute overall performance score
9. compute cost score
10. compute value gap
11. compute uncertainty score
12. render player page + cohort views

### 4. Main screens

#### A. Cohort overview
- filters: role, club, age band, minutes band
- table with:
  - player
  - club
  - age
  - minutes
  - performance score
  - cost score
  - value gap
  - uncertainty score
- scatter plot:
  - x = cost score
  - y = performance score
  - point size = minutes
  - color = uncertainty score
- table must be sortable and exportable

#### B. Player detail page
For the selected player and selected eligible role:
- headline cards:
  - performance score
  - cost score
  - value gap
  - uncertainty score
- family score radar or bar chart
- percentile table versus same-role cohort
- raw adjusted metrics used in each family
- team-strength adjustment panel showing:
  - raw metric
  - `Pts/Gm`-adjusted residual metric
- uncertainty panel showing:
  - minutes
  - bootstrap dispersion
  - shrinkage intensity
- market panel showing:
  - parsed transfer value
  - parsed wage
  - cost percentile

#### C. Diagnostics page
- cohort size by role
- missingness heatmap
- dropped columns list
- correlation matrix of primitive metrics
- PCA/factor explained variance by family
- bootstrap stability summaries
- warnings when a role cohort is too small for stable factor extraction

## Implementation requirements

### Preferred stack
- Python 3.11+
- `pandas`, `numpy`, `scikit-learn`, `scipy`, `statsmodels`
- dashboard layer: `Streamlit`

Equivalent stack is acceptable only if it reproduces the same math and traceability.

### Required modules
Create these modules or equivalent:

- `src/io.py`
- `src/roles.py`
- `src/parse_numeric.py`
- `src/primitives.py`
- `src/shrinkage.py`
- `src/standardize.py`
- `src/team_adjustment.py`
- `src/family_scores.py`
- `src/performance_score.py`
- `src/cost_score.py`
- `src/uncertainty.py`
- `src/model_artifacts.py`
- `src/ui/overview.py`
- `src/ui/player_detail.py`
- `src/ui/diagnostics.py`

### Determinism
- Set random seeds everywhere randomness appears.
- Persist fitted artifacts for each uploaded file hash.
- Recompute only when the input file changes.

### Data validation
The app must fail loudly when required columns are missing. It must not silently continue with altered math.

### Numeric parsing
Handle FM-style numeric strings:
- currency strings in `Transfer Value` and `Wage`
- percentages
- commas used as thousand separators
- empty strings
- hyphens
- mixed string/numeric columns

Keep the original raw value alongside the parsed numeric value for debugging.

## Acceptance criteria

The build is acceptable only if all of the following are true:

1. Every displayed score can be traced back to exact formulas in `math_model.md`.
2. No performance score uses `Ability`, `Potential`, `Recommendation`, `Rating`, `Transfer Value`, or `Wage`.
3. Every performance score is computed **inside a broad role cohort**, never globally.
4. Team-strength adjustment uses **only** `Pts/Gm`.
5. Every weighted combination is estimated from data, not hard-coded by hand.
6. The player detail page exposes both:
   - the final score
   - the intermediate family/component scores
7. The app shows clear warnings for:
   - too-small role cohorts
   - missing mandatory columns
   - mixed-league uploads
   - unstable scores caused by low minutes
8. Output tables can be exported to CSV.

## Minimum test coverage

Implement tests for:

- semicolon CSV loading
- numeric parsing for currencies and percentages
- role parsing from FM position strings
- primitive metric construction
- shrinkage monotonicity with minutes/attempts
- sign orientation of PCA/factor scores
- invariance of same input -> same output
- exclusion of leakage columns from performance score
- correct use of `Pts/Gm` in team adjustment
- player with multiple eligible roles
