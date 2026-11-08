# Website files

The portfolio owns the deployed article, styling and display assets. The model,
training inputs and benchmarks stay in this repository.

After rebuilding the analysis, run this from the portfolio checkout:

```sh
npm run sync:midterms -- /path/to/US-election
npm run build
```

The import copies the generated article, responsive figures, result downloads,
fixed predictions, fallback snapshot and live-result browser code. It does not
copy Python models, training data, dependencies or research workflows. The normal
website build uses committed files and does not need this repository or GitHub.

The React files here mirror the article integration. The live comparison in
`live/` is also embedded in the standalone preview built with `npm run article`.
It refreshes directly from civicAPI while visible and retains saved results if
the feed is unavailable. See [live comparison details](../docs/live-results.md).
