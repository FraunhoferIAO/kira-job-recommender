# KIRA Project

## Table of Contents
1. [Description](#description)
2. [KIRA Demonstrator](#kira-demonstrator)
3. [Project Overview](#project-overview)
4. [License](#license)

## Description

KIRA refers to AI-supported matching 🧩 of individual and labour market-related requirements for further vocational training. In this project, we are investigating whether it is possible to match people with occupations based on their future skills profile and thus open up new perspectives for further training.

In doing so, we are responding to the shortage of skilled labour by supporting people through targeted further development with a focus on future skills. These are needed to cope with a volatile, uncertain, complex and ambiguous world (VUCA world).

KIRA was a public research project funded by the BMBF as part of the [INVITE](https://www.bibb.de/de/120851.php) innovation competition. 

⏱ Duration: 01.09.2021 - 31.08.2024

🤝🏻 Research partners involved: 

- Fraunhofer IAO
- Fraunhofer Austria
- WBS TRAINING AG
- Duale Hochschule Baden-Württemberg
- Hochschule Heilbronn


## KIRA Demonstrator

We have developed a demonstrator that can be used to test our recommendation algorithm.

Try it out at: [KIRA Demonstrator](https://kira-demonstrator.netlify.app/)


## Project Overview

The project has the following file strucutre:

```
├── api/                    # KIRA Frontend
│—— data/
|    |—— ESCO/              # All standard ESCO file templates (need to be downloaded here: https://esco.ec.europa.eu/en/use-esco/download)
|    |—— FutureSkills/      # Files related to FutureSkill Mappings and Occupation FS Profiles used in the data preparation and recommendation pipelines
|    |—— Misc/              # Miscelanious data not directly used in the pipeline
|    └── UserData/          # Folder for user data export
|—— notebooks/              # Jupyter Notebook to demonstrate functionality of pipeline
└── src/                    # Directory with source code
```
