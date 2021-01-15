import intake
import intake_informaticslab
import os

mogreps_cat = intake.open_catalog(
    os.path.join(intake_informaticslab.CATALOG_DIR, "mogreps_cat.yaml")
)

cat = intake.catalog.Catalog.from_dict(
    {"weather_forecasts": mogreps_cat}, name="Met Office Datasets"
)


def test_instantiation_of_specific_mogreps_cat_item():
    plevels = cat.weather_forecasts.mogreps_uk().pressure_level(license_accepted=True)
    ds = plevels.to_dask()
    print(ds)
