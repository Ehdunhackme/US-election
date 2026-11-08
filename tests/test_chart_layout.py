from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from election_forecast.charts import Figures
from election_forecast.report import no_poll_chart

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("mobile", [False, True])
@pytest.mark.parametrize("chart", ["validation", "close", "diagnostics", "no_poll", "training"])
def test_wrapped_headers_clear_panel_titles(tmp_path, mobile, chart):
    artist = Figures(tmp_path, ROOT, dark=True, mobile=mobile)
    checked = []

    def inspect(fig, slug):
        try:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            heading, subtitle = [text.get_window_extent(renderer) for text in fig.texts[:2]]
            assert heading.y0 - subtitle.y1 >= 5, slug
            panel_top = max(ax.get_tightbbox(renderer).y1 for ax in fig.axes)
            assert subtitle.y0 - panel_top >= 8, slug
            for legend in fig.legends:
                bounds = legend.get_window_extent(renderer)
                assert subtitle.y0 - bounds.y1 >= 5, slug
                assert bounds.y0 - panel_top >= 5, slug
            checked.append(slug)
        finally:
            plt.close(fig)

    artist.save = inspect
    if chart == "no_poll":
        no_poll_chart(
            artist,
            pd.read_csv(ROOT / "reports/historical-cycle-scores.csv"),
            pd.read_csv(ROOT / "reports/masked-poll-scores.csv"),
        )
    elif chart == "training":
        artist.training(pd.read_csv(ROOT / "reports/training-data.csv"))
    else:
        data = pd.read_csv(ROOT / "reports/historical-predictions.csv")
        if chart == "diagnostics":
            artist.diagnostics(data)
        else:
            artist.validation(data, close=chart == "close")
    assert len(checked) == 1
