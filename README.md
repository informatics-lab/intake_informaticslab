# Intake Informatics Lab

Intake catalogues and associated drivers which provide access to hundreds of terabytes of Met Office data.

## Licence

Please note that individual datasets have different licences and not all are fully open, e.g. some prohibit non-commercial use.

*Please ensure that you fully understand the licence terms of the dataset before using the data.*

If using the catalogues made available in this package, the licences are described [in the 'Datasets' section below](#datasets).
If accessing the data directly, or creating your own catalogue (and/or instance of the driver), the licence is found in `LICENCE.txt` or `LICENCE.md` at the data root.

The code in this repository is made available under the MIT Licence.

## Datasets

### air_quality

Gridded dataset of air quality approximations for the UK from 2020-01-01 to present. Created from multiple forecasts, and stitched into a continuous time-series. For more information see [air quality technical details](https://metdatasa.blob.core.windows.net/covid19-response/README_data_air_quality.html).

#### Licence
Users are required to acknowledge the Met Office as the source of these data by including the following attribution statement in any resulting products, publications or applications:
"Contains Met Office data licensed under the Open Government Licence v3.0"

These data are made available under an [Open Government Licence](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

### weather_continuous_timeseries

UK numerical weather prediction output from the UK Met Office. Data are from the very early time steps of the model following data assimilation, stitched into a continuous time series from many forecast model runs. These data were designed to approximate an observation dataset. Covers the UK from 2020-01-01 to present.

See the data [README](https://metdatasa.blob.core.windows.net/covid19-response/README_data.html) and the [technical docs](https://metdatasa.blob.core.windows.net/covid19-response/README_data_processing.pdf).

*Note:* The underlying dataset contains global as well as UK data, but the catalogue provided in this package currently only offers the UK data.


#### Licence
Users are required to acknowledge the Met Office as the source of these data by including the following attribution statement in any resulting products, publications or applications:
"Contains Met Office data licensed under the Open Government Licence v3.0"

These data are made available under an [Open Government Licence](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).


### weather_forecasts

Weather forecast model output from the [Met Office's MOGREPS-UK and MOGREPS-G models](https://www.metoffice.gov.uk/research/weather/ensemble-forecasting/mogreps), delayed by 24 hours.

#### Licence
These data are made available under a Creative Commons licence (https://creativecommons.org/licenses/by-nc-nd/4.0/).

The data are free to use for non-commercial purposes under the terms of the licence.
You must ensure that you acknowledge the source of this data as prescribed by this licence.
Data or any derivatives made using the data are for internal use only and may not be distributed or otherwise shared.


## Installing

### PyPI

```shell
pip install intake_informaticslab
```

### Anaconda

```shell
conda install -c conda-forge -c informaticslab intake_informaticslab
```
