# Overview Data Folder

The Data folder is designed to be used with the pipeline class. Each folder serves a standardized purpose along the pipline. Files will be named in a way that encodes their meta data (i.e. paramters used for creation) in order to make them reusable (still WIP)


## Structure
The structure of the Data folder is as follows:

- `data/`
    - `ESCO/`
        - All standard [ESCO files](https://esco.ec.europa.eu/en/use-esco/download)
    - `FutureSkills/`
        - Files relateed to FutureSkill Mappings and Occupation FS Profiles
        - `FutureSkillMappings/`
            - `final/`
                - contains skill-fs-mapping dict
            - `processed/`
                - (manual) esco-fs-mapping, processed to be used in the pipeline class
            - `raw/`
                - (manual) mappings, that have no shape restrictions
        - `OccupationFSProfiles/`
             - `vanilla/`
                - occupation - fs mappings as created based on the input the mapping file
            - `transformed/`
                - occupation - fs mappings transformed to be more aligned with user-fs profiles (used for matching)
    - `Misc`
        - miscelanious data that is not used directly in the pipeline
    - `UserData`
        - Folder for user data export (strucutre still WIP)

## Mapping Tables

There are different versions of the mapping files. The original files can be found in data/FutureSkills/raw, to be used in the pipline they have been processed to the required shape. The usable mapping files in the folder data/FutureSkills/processed are as follows:
* MappingTable_manual.csv : Manual mapping of ESCO Skills to future skills.
* MappingTable_auto_extended.csv : Usage of a llm that was trained to assign ESCO skills to descriptions (https://competence-io.netlify.app/) to get ESCO skills that match the Future Skills. Manual extension and verification of that list was done.
* MappingTable_bert_name.csv : Usage of a BERT model for text classification (https://huggingface.co/distilbert/distilbert-base-uncased-finetuned-sst-2-english), that was fine-tuned with the content of MappingTable_auto_extended.csv. The ESCO skill names have been used in this version.
* MappingTable_bert_description.csv : Usage of a BERT mode for text classification (https://huggingface.co/distilbert/distilbert-base-uncased-finetuned-sst-2-english), that was fine-tuned with the content of Mapping_Table_aut_extended.csv. The ESCO skill descriptions have been used in this version.  



