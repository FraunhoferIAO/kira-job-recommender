"""
This class implements the recommender pipeline for the KIRA project.
It consists of the following steps:
1. Matcher: Match a given user profile with the Occupation_FS_Profiles
2. Recommender: Recommend the most suitable occupation to the user based on the match and the personal preferences
"""

import sys
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.interfaces.matcherAbstract import Matcher
from src.interfaces.recommenderAbstract import Recommender


class RecommenderPipeline:
    """
    Recommender Pipeline for the KIRA project.

    Attributes:
        matcher (Matcher): Matcher object for profile matching.
        recommender (Recommender): Recommender object for occupation recommendation.
        data_path (str): Base path for data storage.
        path_dict (dict): Dictionary of paths used in the pipeline.
    """

    def __init__(
        self, matcher: Optional[Matcher] = None, recommender: Optional[Recommender] = None, data_path: str = "data/"
    ):
        self.data_path = data_path
        self.matcher = matcher
        self.recommender = recommender

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

    def run(
        self,
        target_profile: pd.DataFrame,
        preferences: Dict[str, Any],
        job_history: List[Optional[Dict[str, bool]]],
        transformed_profiles: pd.DataFrame,
        user_profiles: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Run the full recommender pipeline.

        Args:
            user_profile_fs (pd.DataFrame): DataFrame containing the user profile.
            preferences (dict): Dictionary of user preferences.
            job_history (list): List of dictionaries containing job URIs and ratings from the user's job history.
            transformed_profiles (pd.DataFrame): DataFrame of transformed occupation profiles.

        Returns:
            pd.DataFrame: DataFrame of recommended occupations.
        """

        try:
            # 1. Matcher
            matches, transformed_profiles_preferred = self.match_user_profile(
                target_profile, transformed_profiles, user_profiles, preferences=preferences, job_history=job_history
            )

            # 2. Recommender
            recommendations = self.recommend_occupation(
                matches, transformed_profiles_preferred, transformed_profiles, comfort_zone=True
            )
        except Exception as e:
            print(f"Oops something went wrong: {e}")
            sys.exit()

        return recommendations

    """
    Matcher Block
    """

    def match_user_profile(
        self,
        target_profile: pd.DataFrame,
        transformed_profiles: pd.DataFrame,
        user_profiles: pd.DataFrame,
        preferences: Optional[Dict[str, Any]] = None,
        job_history: List[Optional[Dict[str, bool]]] = [],
        learning_zone: bool = False,
    ) -> tuple:
        """
        Match the user profile with the transformed occupation profiles.

        Args:
            user_profile_fs (pd.DataFrame): DataFrame containing the user profile.
            transformed_profiles (pd.DataFrame): DataFrame of transformed occupation profiles.
            preferences (dict, optional): Dictionary of user preferences.
            learning_zone (bool, optional): Whether to calculate the learning zone.

        Returns:
            tuple: Tuple containing the matchings and the filtered transformed profiles.
        """
        esco_kldb = pd.read_csv(self.path_dict["ESCO2kldb"])

        # extract ratings and corresponding concept uris
        user_profile_rating_list, rated_conceptUri_list = self.matcher.extract_user_rating(target_profile)

        # transformed profiles holds two dataframes, first df is the one with the preferences filter, the second one is the one without the preferences filter
        filtered_profiles = self.matcher.filter_by_rating(
            transformed_profiles,
            user_profiles,
            esco_kldb,
            esco_path=self.path_dict["ESCO_path"],
            preferences=preferences,
            job_history=job_history,
            rated_conceptUri_list=rated_conceptUri_list,
            user_profile_rating_list=user_profile_rating_list,
        )

        # check number of recommendations, recommendations 1-4 get filtered by preferences result, the last one not
        # if no filtered recommendations found, use the unfiltered recommendations
        def is_nan_or_empty(value):
            if isinstance(value, float) and np.isnan(value):
                return True
            if isinstance(value, list) and len(value) == 0:
                return True
            return False

        if is_nan_or_empty(user_profile_rating_list):
            filtered_profiles = filtered_profiles[0]
            if filtered_profiles.empty:
                filtered_profiles = filtered_profiles[1]
        elif filtered_profiles[0].empty or len(user_profile_rating_list) == 0:
            filtered_profiles = filtered_profiles[1]
        else:
            filtered_profiles = filtered_profiles[0]

        matchings = self.matcher.calculate_distances(target_profile, filtered_profiles)

        if learning_zone:
            matchings = self.matcher.zone_calculator()

        print("========================================")
        return matchings, transformed_profiles

    """
    Recommender Block
    """

    def recommend_occupation(
        self,
        matches: pd.DataFrame,
        transformed_profiles_preferred: pd.DataFrame,
        transformed_profiles: pd.DataFrame,
        comfort_zone: bool = True,
    ) -> pd.DataFrame:
        """
        Recommend the most suitable occupation to the user.

        Args:
            matches (pd.DataFrame): DataFrame of matched profiles.
            transformed_profiles_preferred (pd.DataFrame): DataFrame of filtered transformed profiles.
            transformed_profiles (pd.DataFrame): DataFrame of transformed occupation profiles.
            comfort_zone (bool, optional): Whether to use the comfort zone for recommendations.

        Returns:
            pd.DataFrame: DataFrame of recommended occupations.
        """
        if comfort_zone:
            rec_jobs = self.recommender.get_comfort_zone_recommendation(
                matches, transformed_profiles_preferred, transformed_profiles, self.path_dict["ESCO_path"]
            )
        else:
            rec_jobs = self.recommender.get_recommendations(matches)

        return rec_jobs
