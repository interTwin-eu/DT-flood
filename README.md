# Notebooks for FloodAdapt backend setup

These python notebooks will guide the use through creating an instance of the [FloodAdapt](https://www.deltares.nl/en/software-and-data/products/floodadapt) backend. This includes setting up a [SFINCS](https://www.deltares.nl/en/software-and-data/products/sfincs) compound flooding model and a [Delft-FIAT](https://www.deltares.nl/en/software-and-data/products/delft-fiat-flood-impact-assessment-tool) impact assesment model using the [HydroMT](https://deltares.github.io/hydromt/latest/) model builder. The notebooks also include creating the configuration files for various types of scenarios.

## Installation

To run the notebook, first install the environment by executing
```bash
conda env create -f environment.yml
```
This will create a conda environment called DT-Flood

## Running the notebooks
### Order of the notebooks
There is a particular order in which to run the notebooks:
  1. SetupSFINCS
  2. SetupFIAT
  3. SetupSite
  4. SetupMeasure, SetupEvent, SetupProjection (in no particular order)
  5. SetupStrategy
  6. SetupScenario
  7. SetupMetricsConfig, SetupGraphicsConfig (still in development)
When these steps are completed a backend ready for running scenarios should be set up. Scenarios are run through the RunScenario notebook. This will also create the infographics.

### Necessary input data
Currently the SetupSFINCS notebook uses data avaible only internally within Deltares. To provide your own data, prepare a [data catalog](https://deltares.github.io/hydromt/latest/user_guide/data_prepare_cat.html) and change the `data_libs` argument of the `hydromt.DataCatalog` and the `SfincsModel` functions. To setup a SFINCS model, the following type of data is used:
  - Topograhpy
  - Bathymetry
  - Waterlevel timeseries at the domain boundary
  - Meteorological data: windspeeds, airpressure, precipitation
  - Soil infiltration curves (optional)
  - Land use (optional)
When providing your own data, please consult the [HydroMT](https://deltares.github.io/hydromt/latest/user_guide/data_conventions.html) documentation for data conventions.

A geojson for setting up a model domain in the Humber delta is provided.

The Delft-FIAT as-is will use the JRC vulnerability curves, which are provided together with a data catalog for reading them in (the root in the data catalog does need updating).

### Running scenarios
To run a FloodAdapt scenario, the [SFINCS](https://github.com/Deltares/SFINCS) and [Delft-FIAT](https://deltares.github.io/Delft-FIAT/stable/) executables are necessary. Make sure they are installed in the folder DT-flood/system/[fiat,sfincs] so FloodAdapt knows where to find the executables.  

# Template for interTwin repositories

This repository is to be used as a repository template for creating a new interTwin
repository, and is aiming at being a clean basis promoting currently accepted
good practices.

It includes:

- License information
- Copyright and author information
- Code of conduct and contribution guidelines
- Templates for PR and issues
- Code owners file for automatic assignment of PR reviewers
- [GitHub actions](https://github.com/features/actions) workflows for linting
  and checking links

Content is based on:

- [Contributor Covenant](http://contributor-covenant.org)
- [Semantic Versioning](https://semver.org/)
- [Chef Cookbook Contributing Guide](https://github.com/chef-cookbooks/community_cookbook_documentation/blob/master/CONTRIBUTING.MD)

## GitHub repository management rules

All changes should go through Pull Requests.

### Merge management

- Only squash should be enforced in the repository settings.
- Update commit message for the squashed commits as needed.

### Protection on main branch

To be configured on the repository settings.

- Require pull request reviews before merging
  - Dismiss stale pull request approvals when new commits are pushed
  - Require review from Code Owners
- Require status checks to pass before merging
  - GitHub actions if available
  - Other checks as available and relevant
  - Require branches to be up to date before merging
- Include administrators
