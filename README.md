# Bacteria Simulation Project

## Overview
EcoGenesys; Guardians of the BioSphere. This project simulates the behavior and evolution of bacteria in a virtual environment. The simulation includes various parameters and traits that influence the behavior and survival of the bacteria. The goal is to identify a set of traits for the bacteria to either lead to a steady-state or leading to all bacteria dying. When steady-state is achieved, the bacteria traits are deemed to be non-invasive; otherwise, it's either invasive or simply not well-adapted to the environment.

Promo Video: https://www.youtube.com/watch?v=NGI1KkS6CXY&ab_channel=reservoir247

## Features
- **Simulation Environment:** Provides a virtual environment where bacteria can live, move, and interact with each other.
- **Genetic Traits:** Bacteria have genetic traits such as tendrils, absorption capacity, membrane strength, and photosynthesis, which influence their behavior and survival.
- **Dynamic Environment:** The simulation includes dynamic factors such as sunlight availability and random events that affect the bacteria population.
- **Statistical Analysis:** Tracks various metrics over time, such as population count, deaths, average lifespan, and average genetic traits, providing insights into the behavior and adaptations of the bacteria population.

Sample screenshot:
![Screenshot (644)](https://github.com/ibra2407/bacteria/assets/113652688/16e12af6-0ee1-4224-8fa1-53a6b3101de5)

## Getting Started
To run the simulation locally, follow these steps:

1. Download the project file. Only the "bacteria.py" file is truly needed.
2. Install necessary libraries either through Command Prompt "pip install {library name}" or:
   ```bash
      pip install -r requirements.txt
3. Run "bacteria.py". A Pygame screen should pop up. Note that because this is an Agent-Based simulation, it is computationally intensive.
4. An Excel file "simulation_data.xlsx" containing the simulation data (up until the latest time you ran it or when all bacterias have died) will automatically be downloaded into the same folder as bacteria.py. Further output analysis can be done using that data separately.
5. This video explains the simulation project in detail: https://www.youtube.com/watch?v=sSySu3bpQIY&ab_channel=reservoir247

#### Selected to be featured at SUTD's ESD SMA Project Showcase
![showcase](https://github.com/ibra2407/bacteria/assets/113652688/7204e34a-2a97-45bc-8bd5-d7be90d69e46)




