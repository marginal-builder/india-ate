"""Unit tests for IFCTNutritionAdapter (ICMR-NIN IFCT 2017)."""

from pathlib import Path

import pytest

from india_ate.adapters.ifct_nutrition import IFCTNutritionAdapter
from india_ate.models import FoodItem, ScientificStandard, Substance


def test_ifct_nutrition_adapter_parses_and_quarantines() -> None:
    csv_bytes = (
        b"code,name,scie,grup,enerc,protcnt,fatce,fibtg,choavldf,ca,fe,zn,vitc\n"
        b'"A001","Amaranth seed, black","Amaranthus","Cereals",'
        b"1490,14.59,5.74,7.02,59.98,0.181,0.00933,0.00266,0\n"
        b'"","Missing Code Food","Unknown","Cereals",'
        b"100,1.0,0.5,1.0,10.0,0.01,0.001,0.001,0\n"
        b'"A999","Bad Numeric Food","Unknown","Cereals",'
        b"notanumber,1.0,0.5,1.0,10.0,0.01,0.001,0.001,0\n"
    )

    adapter = IFCTNutritionAdapter()
    rows = adapter.parse(csv_bytes)
    batch = adapter.validate_and_emit_batch(rows)

    assert len(batch.quarantined) == 2
    items = [e for e in batch.entities if isinstance(e, FoodItem)]
    substances = [e for e in batch.entities if isinstance(e, Substance)]
    standards = [e for e in batch.entities if isinstance(e, ScientificStandard)]

    assert len(items) == 1
    assert items[0].item_id == "item:in:ifct:A001"
    assert items[0].ifct_code == "A001"
    assert len(substances) == 9
    assert len(standards) == 9
    prot = next(s for s in standards if s.substance_id == "sub:ifct:protcnt")
    assert prot.value == 14.59
    assert prot.unit == "g/100g"
    assert len(adapter.validate_and_emit(rows)) == len(batch.entities)


def test_ifct_nutrition_adapter_fetch_from_local_corpus() -> None:
    corpus_csv = Path(
        "/Users/pinkcitykid/Projects/india-ate/ifct2017/compositions/index.csv"
    )
    if not corpus_csv.exists():
        return
    adapter = IFCTNutritionAdapter(csv_path=corpus_csv)
    raw = adapter.fetch()
    rows = adapter.parse(raw)
    batch = adapter.validate_and_emit_batch(rows[:5])
    items = [e for e in batch.entities if isinstance(e, FoodItem)]
    assert len(items) == 5
    assert items[0].ifct_code == "A001"


def test_ifct_nutrition_adapter_fetch_without_path_raises() -> None:
    with pytest.raises(ValueError, match="csv_path is required"):
        IFCTNutritionAdapter().fetch()
