# Notebooks for FloodAdapt backend setup

These python notebooks will guide the use through creating an instance of the [FloodAdapt](https://www.deltares.nl/en/software-and-data/products/floodadapt) backend. This includes setting up a [SFINCS](https://www.deltares.nl/en/software-and-data/products/sfincs) compound flooding model and a [Delft-FIAT](https://www.deltares.nl/en/software-and-data/products/delft-fiat-flood-impact-assessment-tool) impact assesment model using the [HydroMT](https://deltares.github.io/hydromt/latest/) model builder. The notebooks also include creating the configuration files for various types of scenarios.

## Installation
For Windows users, first install Windows Subsystem for Linux (WSL) and Docker desktop, then activate WSL and follow the steps below:
To run the notebook, first install the environment by executing
```bash
git clone git@github.com:interTwin-eu/DT-flood.git
cd DT-flood
conda env create -f environment.yml
pip install .
```
This will create a conda environment called DT-Flood

## Running the notebooks
### Order of the notebooks
There is a particular order in which to run the notebooks:
  1. SetupSFINCS
  2. SetupFIAT, SetupWFLOW (no particular order)
  3. SetupSite
  4. ConfigureFullScenario
  5. VisualizeScenario (WIP)
The ConfigureFullScenario notebook will setup a particular run of the model chain and execute the run in the final cell. The output of the scenario can be visualized in the VisualizeScenario notebook.

### Necessary input data
Currently the interface to data is a HydroMT DataCatalog (see [here](https://deltares.github.io/hydromt/latest/user_guide/data_prepare_cat.html) for more details). What data it should contain is indicated in the notebooks. 
This will change later.

### Running scenarios
The WFLOW and SFINCS models are executed using docker containers, please make sure docker is installed.

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
