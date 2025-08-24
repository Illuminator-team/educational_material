# Illuminator examples

Welcome! This repository contains a collection of example applications of the [Illuminator](https://github.com/Illuminator-team/Illuminator).

To learn more about the Illuminator, please visit the [website](https://illuminator-team.github.io/Illuminator/). 

## Content

The examples are organized in different categories:
- 📁 **configurations** - sample configuration and data input files for the Illuminator.
- 🐍 **scripts** - Python scripts demonstrating how to perform various tasks with the Illuminator.
- 📓 **tutorials** - Jupyter Notebooks that showcase how to use the Illuminator interactively and visualize results.

## Running

The examples are available as Jupyter Notebooks (`.ipynb`), input configurations (`.yaml`) and python scripts (`.py`). To start using the examples, download the repository and install the dependencies:

```bash
# Download a copy of the repository
git clone https://github.com/Illuminator-team/educational_material.git
cd educational_material

# Install the dependencies within a conda environment
conda env create -f environment.yml
conda activate illuminator-examples
```
### Tutorials

To run the tutorials:

```bash
# Open the repository 
cd educational_material

# Activate the conda environment
conda activate illuminator-examples

# Launch JupyterLab
jupyter lab
```

This will open JupyterLab in your browser, where you can run the notebooks interactively.

### Configurations

To run the Illuminator with one of the sample configurations: 

```bash
# Open the repository 
cd educational_material

# Open a configuration folder, for example:
cd configurations/tutorial4

# Activate the conda environment
conda activate illuminator-examples

# Run the Illuminator using a sample configuration 
illuminator scenario run Tutorial4.yaml
```

### Scripts

Instructions coming soon. (TODO)

### Tests

The `tests` directory is primarily intended for developers — either those contributing new examples or developing new Illuminator features.

It includes tests that verify:
- Compatibility of the examples with the latest version of the [Illuminator PyPI package](https://pypi.org/project/illuminator/).
- Correct behavior of examples (i.e. checking whether expected output files are generated and contain valid data).

To run the tests:

(TODO)

## Contribute

Are you using the Illuminator in an interesting or innovative way? Consider sharing your use case with the community by contributing an example to this repository!

We welcome contributions in the form of:
- 📓 Jupyter Notebooks – tutorials that demonstrate workflows or features.
- 📁 Sample configurations – .yaml files along with any required input data.
- 🐍 Python scripts – code examples of how to use Illuminator.

To ensure clarity and usability, all contributed examples must be compatible with the latest version of the [Illuminator PyPI package](https://pypi.org/project/illuminator/) and include documentation explaining how to run them and what users can learn from them.

Please read our Contributing Guidelines for details on how to propose an addition, formatting standards, and review procedures.

We’re excited to see how you’re using Illuminator — and we’d love to highlight your work!
