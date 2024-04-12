# Bacteria Simulation Project

## Overview
This project simulates the behavior and evolution of bacteria in a virtual environment. The simulation includes various parameters and traits that influence the behavior and survival of the bacteria.

## Features
- **Simulation Environment:** Provides a virtual environment where bacteria can live, move, and interact with each other.
- **Genetic Traits:** Bacteria have genetic traits such as tendrils, absorption capacity, membrane strength, and photosynthesis, which influence their behavior and survival.
- **Dynamic Environment:** The simulation includes dynamic factors such as sunlight availability and random events that affect the bacteria population.
- **Statistical Analysis:** Tracks various metrics over time, such as population count, deaths, average lifespan, and average genetic traits, providing insights into the behavior and adaptations of the bacteria population.

## Getting Started
To run the simulation locally, follow these steps:

1. Download the project file. Only the "bacteria.py" file is truly needed.
2. Install necessary libraries:
   ```bash
      pip install -r requirements.txt
3. Run "bacteria.py". A Pygame screen should pop up. Note that because this is an Agent-Based simulation, it is computationally intensive.
4. An Excel file "simulation_data.xlsx" containing the simulation data (up until the latest time you ran it or when all bacterias have died) will automatically be downloaded into the same folder as bacteria.py. Further output analysis can be done using that data separately.


