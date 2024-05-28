<!-- PROJECT TITLE -->
<br />
<div align="center">
  <!-- LOGO MAYBE -->
  <a href="https://github.com/sabotack/NFOpt">
    <img src="logo.png" alt="Logo" width="150" height="150">
  </a>
  <h3 align="center">NFOpt</h3>

  <p align="center">
    A network flow optimizer
    <br />
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about">About The Project</a></li>
    <li><a href="#features">Features</a></li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributors">Contributors</a></li>
  </ol>
</details>

## About
NFOpt (Network Flow Optimizer) is a tool designed to optimize network flow by setting up problems as Linear Programming (LP) minimization problems.
The optimizer can generate a baseline using uniform path splitting ratios for traffic, while available optimization models (average utilization, maximum utilization, and squared utilization) yield optimized ratios and utilization.
Additionally, it can also be used to solve a multi-commodity flow problem over the network resulting in new optimized paths and their respective ratios.

## Features
- Generates baseline with uniform path splitting ratios
- Optimizes network flow using LP with option for several minimization objectives
  - Average Utilization
  - Maximum Utilization
  - Squared Utilization
- Utilizes multicommodity flow problem for path optimization

## Getting Started

### Prerequisites
- [Python 3.x](https://www.python.org/downloads/)
- [Poetry](https://python-poetry.org/docs/)
- A [Gurobi](https://www.gurobi.com/) license

### Installation
1. Clone the repository:
    ```
    git clone https://github.com/sabotack/P6.git
    cd P6
    ```
2. Install the required dependencies:
    ```
    poetry install
    ```
3. Set up environment variables:
   - Create a new file named: `variables.env`
   - Edit `variables.env` to include the necessary environment variables listed in `variables.env-example`

### Data Format
Before you can start using the tool, ensure the following steps are completed:

1. **Data Formatting:** Make sure your data is formatted according to the examples provided in the `sample-data` directory.
2. **Environment Variables:** Set the environment variable for the data directory correctly in the `variables.env` file. <br> You can use the `variables.env-example` file as a reference for the required environment variables and their values. <br> Rename `variables.env-example` to `.env` and update it with the appropriate information.

### Usage
- Running baseline calculations:
    ```
    poetry run p6 baseline [day]
    ```
    > where [day] is an optional argument describing the day of data to use as an integer (default is 1).

- Running optimization models:
    ```
    poetry run p6 type [day]
    ```
  > where type can be either 'average', 'max' or 'squared'.


#### Optional Arguments
|     Argument       | Shortened | Description                                           |
|--------------------|-----------|-------------------------------------------------------|
| `--help`           | `-h`      | Displays information about all available arguments.   |
| `--use-ratios`     | `-ur`     | Use existing path ratios for calculations, requires `DAY`, `TYPE`, and `DATE` in the format `1 squared 20240131`. <br><br> `DAY` is the day of data the ratios you want to use are from. <br> `TYPE` is the type of optimization that the ratios are from. <br> `DATE` is the date the ratios are from. |
| `--use-paths`      | `-up`     | Use existing paths for calculations, requires `DAY`, `DATE`, and `USERATIOS?` (`True` or `False`) in the format `1 20240131 False`. <br><br> `DAY` is the day of data the paths are from. <br> `DATE` is the date the paths are from. <br> `USERATIOS` indicates whether the ratios associated with the paths should be used or if new ones should be calculated instead. |
| `--save-lp-models` | `-slpm`   | Save LP models of optimization to a file.             |



## Contributors
- **sabotack** (Ali Sajad Khorami)
- **EmilML** (Emil Monrad Laursen)
- **SBejer** (Simon Mikkelsen Bejer)
- **ViktorPlatz** (Viktor Platz)
