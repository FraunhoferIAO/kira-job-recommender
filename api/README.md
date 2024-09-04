# API Overview

## Table of Contents

1. [Introduction](#introduction)
2. [Available Endpoints](#available-endpoints)
3. [How to Run API](#how-to-run-api)
4. [How to Update API](#how-to-update-api)

## Introduction

This directory contains the code for an API that provides an interface to the recommendation system.

## Available endpoints

### POST /recommendations

**Description**

Job recommendations for a given user profile.

**Input Parameters**

- `profile` (dict[str, int]): FS short name\* and scores
- `preferenced_sectors` (list[int], optional): Sectors in which the user is interested
- `last_job` (dict(uri: str, liked: number), optional): Last job of the user (uri + whether he liked the job)
- `second_last_job` (dict(uri:str, liked: number), optional): See last_job
- `previous_job` (dict(uri:str, liked: number), optional): See last_job
- `job_recommendations`: (list(uri: str), optional): Previous job recommendations, sorted from first given recommendation to last one
- `job_ratings`: (list(uri: int), optional): User ratings for previous job recommendations (-1 = don't like, 0 = no rating, 1 = like)

\*(see renaming_helper.py)

\*\*(see kldb_helper.py, mapSectorsToNumbers())

**Example**

`POST /recommendations`

Request Body:

```json
{
  "profile": {
    "FS1": 69,
    "FS2": 47,
    "FS3": 72,
    "FS4": 72,
    "FS5": 69,
    "FS6": 61,
    "FS7": 64,
    "FS8": 72,
    "FS9": 67,
    "FS10": 64
  },
  "preferenced_sectors": [3, 6],
  "last_job": {
    "uri": "http://data.europa.eu/esco/occupation/d3edb8f8-3a06-47a0-8fb9-9b212c006aa2",
    "liked": true
  },
  "second_last_job": {
    "id": 2,
    "uri": "http://data.europa.eu/esco/occupation/2b292d4d-1905-45ec-a7c0-1ca7b45a4162",
    "liked": true
  },
  "previous_job": {
    "uri": "http://data.europa.eu/esco/occupation/15dfabf5-71e0-400e-af48-4c6f92ef4392",
    "liked": false
  },
  "job_recommendations": [
    "http://data.europa.eu/esco/occupation/3ce9c89d-6f1a-48b5-942d-386e46e2fd06"
  ],
  "job_ratings": [1]
}
```

Response:

```json
{
  "description": "Wasserbautechniker/innen helfen Ingenieuren bei der Entwicklung und dem Bau von Wasserversorgungs- und Kläanlagen. Sie überwachen die Einhaltung der Gesundheitsschutz- und Sicherheitsvorschriften, überprüfen die Wasserqualität und sorgen für die Einhaltung der wasserrechtlichen Vorschriften.\r\n\t",
  "label": "Wasserbautechniker/Wasserbautechnikerin",
  "profile": {
    "FS1": 65.73296834090714,
    "FS10": 63.267150258415526,
    "FS2": 66.72858377055073,
    "FS3": 67.3765881002006,
    "FS4": 68.88668939243846,
    "FS5": 77.17138792415545,
    "FS6": 67.41125729311521,
    "FS7": 67.43212597243067,
    "FS8": 71.71237926067425,
    "FS9": 64.52484452617288
  },
  "skills": [
    {
      "label": "Einhaltung der Umweltschutzvorschriften gewährleisten"
    },
    {
      "label": "Parameter der Wasserqualität bestimmen"
    }
    // ... other skills
  ],
  "uri": "http://data.europa.eu/esco/occupation/13331bd9-0599-47c0-9812-29650c218de3"
}
```

### GET /occupations

**Description**

Job profiles for a list of given URIs.

**Input Parameters**

Pass list of uris to parameter `uri_list`.

**Example**

`POST /occupations?uri_list=http://data.europa.eu/esco/occupation/3ce9c89d-6f1a-48b5-942d-386e46e2fd06,http://data.europa.eu/esco/occupation/13331bd9-0599-47c0-9812-29650c218de3`

Answer as in the example above.

### How to Run API

```sh
# Setup virtual environment
cd api
python -m venv venv # create env
.\venv\Scripts\activate # activate
pip install -r requirements.txt # install packages

# Start in development mode
cd ../..
python kira-webscraping/api/app.py
```

### How to Update API

To update the API with new data, follow these steps:

1. Place new reference user profiles to /data/UserData
2. Run `data_prep.py` with updated settings (e.g. in Mapper) to generate new occupation profiles
3. Replace paths in `app.py` to new user_profiles and occupation_profiles
