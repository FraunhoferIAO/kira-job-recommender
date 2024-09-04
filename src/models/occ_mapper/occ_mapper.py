from src.interfaces.occMapperAbstract import OccMapper
import pandas as pd
from tqdm import tqdm
import pandas as pd
from tqdm import tqdm
import json
from src.data.esco_helper import esco_helper
import src.data.renaming_helper as renaming_helper


class OccFSMapper(OccMapper):
    """
    OccFSMapper class for creating a mapping between occupations and future skills.
    """

    def __init__(
        self,
        agg_by: str = "occupationUri",
        weighted: bool = True,
        only_essential: bool = True,
        exclude_knowledge: bool = True,
    ):
        """
        Initialize the OccFSMapper with specific settings.

        Args:
            agg_by (str): The column name to aggregate by. Default is "occupationUri".
            weighted (bool): Whether to weight the skill counts. Default is True.
            only_essential (bool): Whether to include only essential skills. Default is True.
            exclude_knowledge (bool): Whether to exclude knowledge skills. Default is True.
        """
        self.agg_by = agg_by
        self.weighted = weighted
        self.only_essential = only_essential
        self.exclude_knowledge = exclude_knowledge

    def create_occ_fs_mapping(self, future_skills_dict: dict, esco_path: str) -> pd.DataFrame:
        """
        Create a mapping of occupations to future skills.

        Args:
            future_skills_dict (dict): Dictionary of future skills.
            esco_path (str): Path to the ESCO data.

        Returns:
            pd.DataFrame: DataFrame with occupations and their future skill profiles.
        """
        self.future_skills_dict = future_skills_dict
        # Initialize esco_helper
        self.esco_helper = esco_helper(esco_path)

        # Get occupations, occupation levels, and occupation-skill relations
        self.occupations = self.esco_helper.get_occupations()
        self.occupation_levels = self.esco_helper.get_detailed_ISCO_levels()
        self.occupation_skills_df = self.esco_helper.get_occupationSkillRelations()

        future_skills_occupations = self.__link_fs_occupation()

        if self.exclude_knowledge:
            future_skills_occupations = future_skills_occupations[
                future_skills_occupations["skillType"] != "knowledge"
            ]

        if self.only_essential:
            future_skills_occupations = future_skills_occupations[
                future_skills_occupations["relationType"] == "essential"
            ]

        grouped_df = (
            future_skills_occupations.groupby([self.agg_by, "FS_ID"])["skillUri"]
            .count()
            .reset_index(name="count")
        )

        # Pivot the grouped data frame to get the desired format
        grouped_fs_profile = grouped_df.pivot(
            index=self.agg_by, columns=["FS_ID"], values="count"
        ).reset_index()

        # Fill any missing values (i.e. no associated FS for entire group) with 0
        grouped_fs_profile = grouped_fs_profile.fillna(0)

        # Add total skill count per designated aggregation group
        total_skills_group = (
            future_skills_occupations.groupby([self.agg_by])["skillUri"]
            .nunique()
            .reset_index()
        )
        grouped_fs_profile["total_skills"] = grouped_fs_profile.join(
            total_skills_group.set_index("occupationUri"),
            on="occupationUri",
            how="left",
        )["skillUri"]

        if self.weighted:
            grouped_fs_profile.iloc[:, 1:-1] = grouped_fs_profile.iloc[:, 1:-1].div(
                grouped_fs_profile.iloc[:, -1], axis=0
            )

        occ_fs_profile = grouped_fs_profile.drop("total_skills", axis=1)
        occ_fs_profile = occ_fs_profile.set_index("occupationUri")

        occ_fs_profile_renamed = renaming_helper.rename_columns(occ_fs_profile)

        return occ_fs_profile_renamed

    def __link_fs_occupation(self) -> pd.DataFrame:
        """
        Link future skills to occupations.

        Returns:
            pd.DataFrame: DataFrame of occupations and future skills.
        """
        occupations_levels_skills = self.occupation_skills_df.join(
            self.occupation_levels.set_index("conceptUri"),
            on="occupationUri",
            how="left",
        )

        skills_future_skills = self.__fs_dict_to_df(self.future_skills_dict)
        skills_future_skills = skills_future_skills.drop_duplicates()
        skills_future_skills.rename(columns={"Key": "conceptUri"}, inplace=True)

        future_skills_occupations = occupations_levels_skills.join(
            skills_future_skills.set_index("conceptUri"), on="skillUri", how="left"
        )

        return future_skills_occupations

    def __fs_dict_to_df(self, input_dict: dict) -> pd.DataFrame:
        """
        Convert a future skills dictionary to a DataFrame.

        Args:
            input_dict (dict): The future skills dictionary.

        Returns:
            pd.DataFrame: DataFrame of future skills.
        """
        # Create an empty DataFrame with columns 'Key', 'FS_ID', and 'FutureSkill'
        fs_df = pd.DataFrame(columns=["Key", "FS_ID"])

        # Iterate over the dictionary items
        for key, value_list in tqdm(input_dict.items()):
            # Iterate over the list of dictionaries in the value
            for item in value_list:
                fs_id = item.get("FS_ID", None)
                # future_skill = item.get("FutureSkill", None)
                data_to_append = pd.DataFrame({"Key": [key], "FS_ID": [fs_id]})
                fs_df = pd.concat([fs_df, data_to_append], ignore_index=True)

        return fs_df
