# SpeedTestAnalysis


## Note that using uv
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

## Note that kaleido
```toml
# NOTE: https://github.com/astral-sh/uv/issues/7703
[tool.uv]
constraint-dependencies = ["kaleido!=0.2.1.post1"]
```
```ps1
uv add kaleido
```

## Note that to export the plot as offline HTML

see. https://stackoverflow.com/a/59819140/3363518
```py
import plotly
plotly.offline.plot(fig, filename='path/to/offline/index.html')
```

## Note that to deploy Cloudflare pages

```ps1
npm install -g wrangler
npx wrangler pages project create speedtestanalysis --production-branch production
npx wrangler pages deploy dist --project-name speedtestspeedtestanalysis --branch production
```
