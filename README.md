# Intake Informatics Lab

A driver and intake catalogues providing access to hundreds of terabytes of Met Office data.

## Licence

Please note that individual datasets have different licenses and not all are fully open, e.g. some prohibit non-commercial use.

*Please ensure that you full understand the licence terms of the dataset before using that data.*

If you use the catalogues made available in this package the licences are described [in the 'Datasets' section below](#datasets).
If accessing the data direct or creating your own catalogue or instance of the driver the licence should be found in `LICENCE.txt` or `LICENCE.md` at the data root.

The code in this repository is made available under the MIT Licence.

## Datasets

### air_quality

Gridded dataset of air quality approximations for the UK for 01/01/20 to present. Created from multiple forecasts stitched in to a continuous time-series. For more information see [air quality technical details](https://metdatasa.blob.core.windows.net/covid19-response/README_data_air_quality.html).

#### License
Users are required to acknowledge the Met Office as the source of these data by including the following attribution statement in any resulting products, publications or applications:
"Contains Met Office data licensed under the Open Government Licence v3.0"

This data is made available under [Open Government License](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

### weather_continuous_timeseries

UK numerical weather model output from the UK Met Office. Data is from the very early time steps of the model following data assimilation, stitched into a continuous time series from many model runs. This data approximates an observation dataset. UK only from 01/01/20-present.

See the data [README](https://metdatasa.blob.core.windows.net/covid19-response/README_data.html) and the [technical docs](https://metdatasa.blob.core.windows.net/covid19-response/README_data_processing.pdf).

*Note:* The dataset contains global as well as UK data but the catalogue in this package currently only offers the UK. 


#### License
Users are required to acknowledge the Met Office as the source of these data by including the following attribution statement in any resulting products, publications or applications:
"Contains Met Office data licensed under the Open Government Licence v3.0"

This data is made available under [Open Government License](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).


### weather_forecasts

Weather forecast model output form the [Met Offices MOGREP UK and MOGREPS G models](https://www.metoffice.gov.uk/research/weather/ensemble-forecasting/mogreps), delayed by 24 hours. These models run as lagged ensemble but for simplicity in this catalogue it's being treated as more runs of less members in an un-lagged fashion.

#### License
This data is made available under a Creative Commons licence (https://creativecommons.org/licenses/by-nc-nd/4.0/).

This data is free to use for non-commercial purposes under the terms of the licence.
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
