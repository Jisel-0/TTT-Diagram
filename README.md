# README

## Introduction

This repository provides Python scripts for **calculating and plotting phase transformation diagrams** (TTT, CCT) and **phase fractions** (ferrite, pearlite, bainite, martensite) for steels under various cooling conditions. The implementation draws heavily on two primary references:

1. **Li et al. (1998), _Metallurgical and Materials Transactions B_**  
   “A Computational Model for the Prediction of Steel Hardenability”  
   This paper describes a thermodynamics-based approach to model the development of microstructure and hardness in steels, including Jominy end-quench tests. It emphasizes coupling finite-element heat-transfer models with reaction-kinetics equations that incorporate Ae1, Ae3, and Bainite Start (Bs) temperatures. It also proposes modifications to older “Kirkaldy-style” models for better predictions under continuous cooling.

2. **Saunders et al.**  
   “The Calculation of TTT and CCT Diagrams for General Steels”  
   This work extends the TTT/CCT calculation capability to more highly alloyed steels (e.g., tool steels, 13 %Cr steels) by integrating thermodynamic models (to obtain equilibrium transformations like Ae3, Ms, etc.) with a kinetic model. The authors validate their approach against a broad experimental dataset and highlight the significance of grain size, composition, and the necessity of an accurate martensite start (Ms) model for high-alloy steels.

These scripts also incorporate insights from the **[transformation-diagrams repository by arthursn](https://github.com/arthursn/transformation-diagrams)**, which provides foundational code for TTT and CCT diagram plotting and the usage of empirical/semitheoretical reaction-kinetics equations.  

Lastly, the concept of **prior austenite grain size** is crucial in calculating steel hardenability. We rely on **Table 4 from ASTM E112** (see the attached image) to relate **ASTM grain size numbers** to average grain area, diameter, intercept counts, etc. This table helps the model account for the effect of grain size on nucleation sites and overall transformation kinetics.

---

## Code Overview

The main Python files are:

1. **`transformation_models_modified.py`**  
   - **Core Models**  
     - Defines the `Alloy` class (with composition, grain size, and critical temperatures Ae1, Ae3, Bs, Ms).  
     - Implements thermodynamic-based equations (e.g., Ae3 from Andrews or Li’s approach, Ms from Andrews, etc.) and reaction-kinetics formulas for ferrite, pearlite, bainite, and martensite transformations.  
     - Integrates methods to compute transformation times under isothermal and continuous cooling (CCT).  
     - Includes hardness estimation based on Maynier-like empirical equations, using phase fractions plus cooling rate at 700 °C.  
   - **Grain Size**  
     - Accepts an ASTM grain size number `gs`. You can cross-reference **ASTM E112 Table 4** to interpret how this G-number relates to actual grain intercepts, diameter, or area.  

2. **`plot_phase_fractions.py`**  
   - **Plots Phase Fraction Evolution**  
     - Reads user arguments (initial temperature, total time, cooling rate, composition, etc.).  
     - Instantiates an `Alloy` object and a `TransformationDiagrams` object.  
     - If the cooling rate is zero (isothermal), it plots TTT; otherwise, it can plot CCT.  
     - Also shows how each phase fraction (ferrite, pearlite, bainite, martensite) evolves over time/temperature.

3. **`plot_diagrams.py`**  
   - **Plots TTT (and optionally CCT) Diagrams**  
     - Also uses `Alloy` and `TransformationDiagrams`.  
     - Can export the TTT data to an Excel file (`.xlsx`) if desired.  
     - Shows Ae1, Ae3, Bs, Ms lines on the diagram.  

In each script, the user may be prompted (via `input()`) to **select which empirical equation** to use for Ms, Bs, Ac1, Ac3. For instance, you might see a bar chart of different Ms predictions, then type the name of the equation you want.

---

## Using the Code

1. **Install Dependencies**  
   Make sure you have Python 3 plus the following libraries installed:
   ```bash
   pip install numpy pandas matplotlib scipy openpyxl
   ```

2. **Run `plot_phase_fractions.py`**  
   Example:
   ```bash
   python plot_phase_fractions.py -Tini 900 -t 100 -phi 5 -g 7 \
       -C 0.4 -Mn 1.2 -Si 0.3 -Cr 1.0 -Ni 0.5 -Mo 0.2
   ```
   - `-Tini 900`: Starting temperature 900 °C  
   - `-t 100`: Simulate 100 s total  
   - `-phi 5`: Cooling rate of 5 °C/s  
   - `-g 7`: ASTM grain size 7 (you can cross-check actual grain diameter from the **ASTM E112** table).  
   - Composition arguments: `-C`, `-Mn`, `-Si`, `-Cr`, `-Ni`, `-Mo`, etc.

3. **Run `plot_diagrams.py`**  
   Example:
   ```bash
   python plot_diagrams.py -g 7 -C 0.4 -Si 0.3 -Mn 1.2 -Ni 0.5 -Mo 0.2 -Cr 1.0 -Tini 900 -e
   ```
   - Plots TTT and CCT diagrams for the specified composition.  
   - `-e` can export TTT data to an Excel file.  

4. **Interactive Equation Selection**  
   - On running, you’ll see a bar chart (for Ms, Bs, Ac1, or Ac3).  
   - Type the exact name of the equation you want to use.  
   - The chosen value is then used for subsequent calculations.

---

## About the Grain Size (ASTM E112 Table 4)

- **ASTM E112** provides relationships between the **grain size number** (G) and:
  - **Grains per unit area** at 1× and 100× magnifications  
  - **Average grain area**  
  - **Average grain diameter**  
  - **Mean intercept length**  

- Our code typically uses the **ASTM G number** to scale the transformation kinetics. Larger grain size (smaller G number) generally leads to faster transformations (fewer boundaries), while smaller grains (bigger G number) can accelerate nucleation but sometimes slow growth.

- By referencing Table 4 from E112, you can interpret how a G number (e.g., 7 or 8) translates into micrometers of average diameter or intercept counts per mm, which are physically meaningful for describing microstructure.

---

## Repository and License

- The approach here is **inspired** by the [transformation-diagrams GitHub repo](https://github.com/arthursn/transformation-diagrams), but **expanded** with additional interactive Ms/Bs/Ac1/Ac3 equations, usage of advanced references for TTT/CCT, and better grain-size handling.  
- Please check each script’s docstrings for usage details.  
- License terms may follow the original repository or a standard open-source license (MIT/BSD); see the repository for clarifications.

---

## References

1. **Li et al. (1998)**, “A Computational Model for the Prediction of Steel Hardenability,” _Metallurgical and Materials Transactions B_, 29B, 661–672.  
2. **Saunders et al.**, “The Calculation of TTT and CCT Diagrams for General Steels,” internal report/paper describing advanced thermodynamic–kinetic integration.  
3. [transformation-diagrams by arthursn](https://github.com/arthursn/transformation-diagrams).  
4. **ASTM E112** – “Standard Test Methods for Determining Average Grain Size,” Table 4 for uniform, randomly oriented, equiaxed grains.

Feel free to open issues or pull requests to improve the code or add new equations for critical temperatures and transformation kinetics. Happy modeling!
