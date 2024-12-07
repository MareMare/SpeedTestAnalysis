# SpeedTestAnalysis

## Overview
This project analyzes internet speed test data and visualizes the results using Plotly.

## Features
- Automatically triggers analysis and deployment when CSV files are committed.
- Loads and prepares speed test data from a CSV file.
- Calculates median download and upload speeds.
- Plots graphs of download and upload speeds with medians.
- Saves the plots as HTML files with Japanese metadata.
- Deploys the results to Cloudflare Pages.

## Output
- The script generates an HTML file containing the plot, which is saved in the dist directory.
- Upon commit, the results are automatically deployed to Cloudflare Pages.

## Continuous Deployment

This project uses GitHub Actions for continuous deployment. When a CSV file is committed, the analysis.py script is automatically executed, and the results are deployed to Cloudflare Pages. The deployment process is defined in [`cd.yml`](.github/workflows/cd.yml)

### Workflow Trigger
- The workflow is triggered on:
  - Push events to the main branch that include changes to .py, .toml, or .csv files.
  - Pull requests to the main branch with changes to the same file types.

### Deployment Steps
1. The project environment is set up using uv and Python.
2. The analysis.py script is executed to process the data.
3. The results are deployed to Cloudflare Pages using the Cloudflare Wrangler Action.

### Deployment URL
Upon successful deployment, the URL of the deployed site is printed in the GitHub Actions summary.

## Related Repositories
The following are related repositories:
- [CloudflareSpeedTester](https://github.com/MareMare/CloudflareSpeedTester)
- [GitHubCommit](https://github.com/MareMare/GitHubCommit)
- [SpeedTestAnalysis](https://github.com/MareMare/SpeedTestAnalysis)

## Developer Notes
<details><summary>notes for me</summary>

- using uv
```ps1
# create project
uv init --app --python 3.10
# add dependencies to project
uv add pandas plotly
```

```ps1
# virtual env
uv venv
uv sync
python.exe analysis.py
```
or
```ps1
uv run analysis.py
```

- kaleido
```toml
# NOTE: https://github.com/astral-sh/uv/issues/7703
[tool.uv]
constraint-dependencies = ["kaleido!=0.2.1.post1"]
```
```ps1
uv add kaleido
```

- plot export

see. https://stackoverflow.com/a/59819140/3363518
```py
import plotly
plotly.offline.plot(fig, filename='path/to/offline/index.html')
```

- deployment to Cloudflare pages

```ps1
npm install -g wrangler
npx wrangler pages project create speedtestanalysis --production-branch production
npx wrangler pages deploy dist --project-name speedtestspeedtestanalysis --branch production
```

</details>
