"""
This class implements the pipeline for the KIRA project.
It consists of the following steps:
1. Skill Mapper: Create FS Mappings and save it to the correct location
2. Mapper: Create Occ_FS_Mapping and save it to the correct location
3. Transformer: Create the transformed Occupation_FS_Profile and save it to the correct location
"""

import json
import os
import sys 
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd

from src.interfaces.mapperAbstract import Mapper
from src.interfaces.occMapperAbstract import OccMapper
from src.interfaces.transformerAbstract import Transformer


class DataPrepPipeline:
    """
    Data Preparation Pipeline for the KIRA project.

    Attributes:
        mapper (Mapper): Mapper object for skill mapping.
        occ_mapper (OccMapper): OccMapper object for occupation-skill mapping.
        transformer (Transformer): Transformer object for transforming profiles.
        data_path (str): Base path for data storage.
        path_dict (dict): Dictionary of paths used in the pipeline.
        reference_timestamp (str): Reference timestamp for file naming.
        timestamp (str): Current timestamp for file naming.
    """

    def __init__(
        self,
        mapper: Optional[Mapper] = None,
        occ_mapper: Optional[OccMapper] = None,
        transformer: Optional[Transformer] = None,
        data_path: str = "data/",
    ):
        self.data_path = data_path
        self.mapper = mapper
        self.occ_mapper = occ_mapper
        self.transformer = transformer

        # Set reference timestamp from transformer if available, otherwise use current time
        self.reference_timestamp = self.transformer.reference_timestamp
        if self.reference_timestamp is None:
            self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        else:
            self.timestamp = self.reference_timestamp.split("_")[-1].split(".")[0]

        self.path_dict = {
            "ESCO_path": f"{data_path}ESCO/",
            "mapper_input": f"{data_path}FutureSkills/FutureSkillMappings/processed/",
            "mapper_output": f"{data_path}FutureSkills/FutureSkillMappings/final/",
            "transformed_occ_fs_profiles": f"{data_path}FutureSkills/OccupationFSProfiles/",
            "ESCO2kldb": f"{data_path}Misc/esco2kldb_multiple_assignment.csv",
            "UserData": f"{data_path}UserData/",
        }

    """
    Full Pipeline
    """

    def run(self) -> pd.DataFrame:
        """
        Run the full data preparation pipeline.

        Returns:
            pd.DataFrame: DataFrame of transformed occupation profiles.
        """
        # check if transformed occupation profiles are available
        transformed_profiles = self.get_or_create_transformed_profiles()
        return transformed_profiles

    """
    Mapper Block
    """

    def get_or_create_mappings(self) -> Dict[str, Any]:
        """
        Retrieve or create skill mappings.

        Returns:
            dict: Dictionary of skill mappings.
        """
        assert self.mapper is not None, "Mapper not defined"
        mapping_name = self.mapper.mapping_name
        self.check_mapping_location()
        try:
            mappings = self.__get_mappings_json(mapping_name)
            print("Mappings are available!")
        except:
            print(f"File {mapping_name}.json not found in {self.path_dict['mapper_output']}, creating a new one")
            mappings = self.__create_mappings()
            self.__save_final_mappings(mappings)
        return mappings

    # get the mappings from the json file and return fs skills dict
    def __get_mappings_json(self, mapping_name) -> Dict[str, Any]:
        """
        Retrieve skill mappings from a JSON file.

        Args:
            mapping_name (str): Name of the mapping file.

        Returns:
            dict: Dictionary of skill mappings.
        """
        with open(f"{self.path_dict['mapper_output']}{mapping_name}.json", "r") as json_file:
            fs_dict = json.load(json_file)
        return fs_dict

    # create the mapping dict
    def __create_mappings(self) -> Dict[str, Any]:
        """
        Create skill mappings using the mapper.

        Returns:
            dict: Dictionary of skill mappings.
        """
        mappings = self.mapper.create_fs_dict(esco_path=self.path_dict["ESCO_path"])
        return mappings

    # save final mappings in json format
    def __save_final_mappings(self, mappings: Dict[str, Any]) -> None:
        """
        Save the final skill mappings to a JSON file.

        Args:
            mappings (dict): Dictionary of skill mappings.
        """
        json.dump(
            mappings, open(f"{self.path_dict['mapper_output']}/{self.mapper.mapping_name}_{self.timestamp}.json", "w")
        )

    # check that the provided mapping file is in the correct/expected location and format, create copy if not
    def check_mapping_location(self) -> None:
        """
        Check if the mapping file is in the correct location and format. Create a copy if not.
        """
        correct_path = f"{self.data_path}FutureSkills/FutureSkillMappings/processed/"
        print(f"Checking if {self.mapper.mapping_name} is at correct loaction")

        # check if file exists and is in correct file format
        if f"{self.mapper.mapping_name}.csv" not in os.listdir(correct_path):
            print(
                f"File {self.mapper.mapping_name}.csv not found in {correct_path}, creating a copy in {correct_path}"
            )
            shutil.copy(f"{self.mapper.mapping_path}", correct_path)
        else:
            print("Processed file for mapping is present in processed folder!")

    """
    Occupation-FS-Mapper Block
    """

    def get_or_create_occ_fs_mapping(self) -> pd.DataFrame:
        """
        Retrieve or create occupation-skill mappings.

        Returns:
            pd.DataFrame: DataFrame of occupation-skill mappings.
        """
        assert self.occ_mapper is not None, "OccFSMapper not defined"

        # check if vanilla profiles are available
        vanilla_file = f"{self.mapper.mapping_name}_weighted={self.occ_mapper.weighted}_{self.timestamp}.csv"
        vanilla_path = f"{self.path_dict['transformed_occ_fs_profiles']}vanilla//"

        if vanilla_file in os.listdir(vanilla_path):
            print("Occupation FS mappings already avilable!")
            occ_fs_df = pd.read_csv(f"{vanilla_path}{vanilla_file}", index_col=0)
        else:
            print("Nothing found in vanilla folder...Now the Occupation FS Mapping is done.")
            fs_dict = self.get_or_create_mappings()
            occ_fs_df = self.occ_mapper.create_occ_fs_mapping(fs_dict, self.path_dict["ESCO_path"])
            self.__save_occ_fs_profiles_vanilla(occ_fs_df)
        return occ_fs_df

    def __save_occ_fs_profiles_vanilla(self, occ_fs_profiles: pd.DataFrame) -> None:
        """
        Save occupation-skill profiles to the vanilla folder.

        Args:
            occ_fs_profiles (pd.DataFrame): DataFrame of occupation-skill profiles.
        """
        # save occ fs profiles in vanilla folder
        occ_fs_profiles.to_csv(
            f"{self.path_dict['transformed_occ_fs_profiles']}vanilla//{self.mapper.mapping_name}_weighted={self.occ_mapper.weighted}_{self.timestamp}.csv"
        )

    """
    Transformer Block
    """

    def get_or_create_transformed_profiles(self) -> pd.DataFrame:
        """
        Retrieve or create transformed occupation profiles.

        Returns:
            pd.DataFrame: DataFrame of transformed occupation profiles.
        """
        assert self.transformer is not None, "Transformer not defined"

        if self.transformer.reference_user_profiles is None:
            print("Please provide Reference User Profiles.")
            sys.exit()

        # Check if transformed profiles are available
        transformed_file = f"{self.mapper.mapping_name}_k={self.transformer.n_neighbors}_{self.timestamp}.csv"
        transformed_path = f"{self.path_dict['transformed_occ_fs_profiles']}transformed//"

        if transformed_file in os.listdir(transformed_path):
            transformed_profiles = pd.read_csv(f"{transformed_path}{transformed_file}", index_col=0)
            print(transformed_file)
            print("is already available!")
        else:

            occ_fs_mappings = self.get_or_create_occ_fs_mapping()
            transformed_profiles = self.transformer.transform(occ_fs_mappings)
            self.__save_transformed_profiles(transformed_profiles)

        return transformed_profiles

    def __save_transformed_profiles(self, transformed_profiles) -> None:
        """
        Save transformed occupation profiles to the transformed folder.

        Args:
            transformed_profiles (pd.DataFrame): DataFrame of transformed occupation profiles.
        """
        # save occ fs profiles in vanilla folder
        print("Save new file")
        transformed_profiles.to_csv(
            f"{self.path_dict['transformed_occ_fs_profiles']}"
            f"transformed//{self.mapper.mapping_name}_k={self.transformer.n_neighbors}_{self.timestamp}.csv"
        )
