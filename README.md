# Malaysia CPI dashboard

Interactive state and national CPI plus selected item prices. Nothing has been uploaded to GitHub or published. The local standalone `CPI Dashboard.html` is a snapshot; the GitHub version reads the JSON files in `dist`.

## Upload to GitHub when ready

Extract `CPI Dashboard - GitHub ready.zip` and upload its **contents** to the root of your GitHub repository, including `.github/workflows`. Do not upload the original Excel files or the `.openai` directory. The archive already contains the validated data and application.

1. Enable Actions in the repository. The workflows must be on the repository's default branch.
2. Open **Actions → Refresh monthly data → Run workflow** to verify the first run.
3. From then on, the workflow checks daily at **14:17 Malaysia time** for monthly releases. GitHub schedules can be delayed. Both DOSM CPI files and every detected price workbook are downloaded again, so revisions within existing files are captured. New matching workbooks in the folder are also discovered.
4. After a change, the validated JSON and source CSV files are committed to your repository. Without a data change, there is no data commit.

No API key is needed while the linked folder and its files remain publicly readable. No Codex reminder or background process on your PC is required. The workflow is supplied locally and **is not active yet**.

## Publish later, separately

The refresh workflow only updates repository data. Publishing is disabled by default.

When you decide to publish:

1. In repository **Settings → Pages → Build and deployment**, choose **GitHub Actions**.
2. Under **Settings → Secrets and variables → Actions → Variables**, create a repository variable named `ENABLE_PAGES` with the value `true`.
3. Run **Actions → Publish dashboard to GitHub Pages** manually for the first publication.
4. Subsequent successful refresh workflow runs will deploy the current `dist` directory automatically. The separate publication workflow is intentional: a commit created with `GITHUB_TOKEN` does not itself trigger another push workflow.

Setting `ENABLE_PAGES` to `false` prevents future deployments but does not remove an already published website. Review your GitHub plan and Pages visibility before enabling it; a public Pages site exposes the dashboard's included data.

## Sources and calculations

- State CPI: https://open.dosm.gov.my/data-catalogue/cpi_state
- National CPI: https://open.dosm.gov.my/data-catalogue/cpi_headline
- CPI classification: https://open.dosm.gov.my/data-catalogue/mcoicop
- Item prices: https://drive.google.com/drive/folders/1WI1UGcwgFKXJdqe08WI5sQTxRSI-ok33
- DOSM data license: CC BY 4.0.

Malaysia CPI uses the official national series, never an average of state indices. Malaysia item prices come from the workbook's Malaysia sheet. Malaysia is selectable in both views, appears in the data table and CSV export, and is the default comparison. The country benchmark sits above the state bars and is excluded from state rankings.

YoY = `(current / same month last year - 1) * 100`. MoM uses the previous month. Missing prior data returns unavailable. CPI uses 2010 = 100 and does not rank absolute living costs across states. Rates calculated from rounded indices may differ slightly from separately published rounded inflation rates.

The item explorer defaults to the full monthly timeline from January 2019. Reviewed name variants and related specifications share an item family. Original labels and observed prices remain in the data. Notes below the chart list definition periods and units, including later-starting items. Only clear spelling/wording aliases with the same unit are treated as comparable. Other definition changes create line breaks and suppress YoY/MoM across different definitions. There is no backcasting, interpolation or price conversion.

DOSM's workbooks explicitly flag unit changes from August 2024 and specification changes from March 2025. Where a row carries the later unit across its full history, earlier 2024 columns use the preceding unit according to that dated note. For example, fabric softener uses 2 L before August 2024 and 3 L thereafter. Continued, unnumbered rows are included when the item name follows the preceding numbered item, retaining the 2023 toilet-paper and liquid-soap pack changes. Workbook month headers are authoritative. Positive numeric values are used. Coverage changes from 100 to 120 selected items. A later first observation means first available in these files, not necessarily a newly introduced product.

## Failure handling and limitations

Downloads and parsing happen in a temporary directory. Missing required columns, inaccessible workbooks, absent Malaysia data, duplicate CPI keys or disappearance of historical observations fail the refresh before any live data replacement. GitHub marks the run failed; existing deployed data remains available. Check the Actions logs and GitHub notification settings if a scheduled update fails.

The public Drive folder listing is parsed from Google's HTML because anonymous listing has no configured Drive API credentials. This was verified with the four current files. It can break if Google changes its markup, adds a login requirement or paginates a large folder. A failed check does not fabricate new data. Revisit the listing integration if the folder grows substantially; an authenticated, paginated Drive API would be preferable at that point. Files must retain the `DATABASE PURATA HARGA` title prefix and Excel/Google Sheets format. Unexpected new workbook layouts require parser review.

GitHub scheduled workflows run on the default branch and may be delayed or disabled by repository inactivity. Protected branches may require a pull-request based update flow instead of direct bot commits. Check Actions after setup and periodically thereafter.

## Local maintenance

With Python 3.12+:

```sh
python -m pip install -r requirements.txt
python refresh.py
python -m http.server 8765 --directory dist
```

Then open http://localhost:8765. For another standalone snapshot, run `python standalone.py` from the development checkout (it writes `CPI Dashboard.html` one directory above the project). The existing standalone file does not update by itself.

`dist/update-status.json` records the processing time of the most recent data change and the data coverage dates. A successful daily check with no data changes preserves that timestamp to avoid unnecessary commits.
