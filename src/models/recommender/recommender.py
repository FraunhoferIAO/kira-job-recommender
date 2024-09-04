import pandas as pd
import numpy as np
import json
from scipy.spatial.distance import hamming
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from src.interfaces.recommenderAbstract import Recommender
from src.data.esco_helper import esco_helper

class JobRecommender(Recommender):
    def __init__(
        self,
        user_profile: np.array,
    ):
        """
        Initialize the JobRecommender instance with a user profile.

        Args:
            user_profile (np.array): The numpy array representing the user profile.
        """
        self.user_profile = user_profile,


    def get_recommendations(self, matches):
        """
        Get the top 10 job recommendations from the matched profiles.

        Args:
            matches (pd.DataFrame): The DataFrame containing matched job profiles.

        Returns:
            pd.DataFrame: The top 10 recommended jobs.
        """
        recommended_jobs = matches.head(10)
        return recommended_jobs
    
    def recommend(self, recommended_jobs):
        """
        Retrieve the preferred labels for recommended jobs.

        Args:
            recommended_jobs (pd.DataFrame): DataFrame containing the concept URIs of recommended jobs.

        Returns:
            list: List of preferred labels for the recommended jobs.
        """
        print(recommended_jobs)
        rec_list = []

        for concept_uri in recommended_jobs["conceptUri"]:
            recom_label = self.esco_helper.look_up(concept_uri)["preferredLabel"]
            rec_list.append(recom_label)
        return rec_list


    def compare_occupation_similarity(self, job_fs_profile, broader_job_fs_profile):
        """
        Compare the similarity between job profiles using the Euclidean distance.

        Args:
            job_fs_profile (pd.DataFrame): DataFrame representing a specific job profile.
            broader_job_fs_profile (np.array): Numpy array representing a broader job profile.

        Returns:
            bool: True if the Euclidean distance is below the maximum allowed threshold, else False.
        """
        # max allowed euclidean distance
        max_euclidean_distance = 30
        job_fs_profile.drop("conceptUri", axis=1, inplace=True)

        # preparation
        job_fs_profile_arr = np.array(job_fs_profile)
        broader_job_fs_profile_arr = np.array(broader_job_fs_profile)

        # Compute Euclidean distance
        similarities = euclidean_distances(job_fs_profile_arr.reshape(-1, 1), broader_job_fs_profile_arr.reshape(-1, 1))
        
        euclidean_distance = similarities[0][0]

        if euclidean_distance < max_euclidean_distance:
            return True
        else:
            return False
        
    def refine_recommendations(self, recommended_jobs, transformed_profiles_preferred, occ_fs_profile_scaled_df):
        """
        Refines recommendations by evaluating broader job profiles and their closeness to the original jobs.

        Args:
            recommended_jobs (pd.DataFrame): The initial set of job recommendations.
            transformed_profiles_preferred (pd.DataFrame): Transformed profiles for preference matching.
            occ_fs_profile_scaled_df (pd.DataFrame): Scaled job profiles for comparison.

        Returns:
            pd.DataFrame: Final list of refined job recommendations.
        """
        recommended_jobs_columns = recommended_jobs.columns
        recommended_jobs_broader_occ = pd.DataFrame(columns=recommended_jobs_columns)

        for recom_uri in recommended_jobs["conceptUri"]:
            job_fs_profile = recommended_jobs.loc[recommended_jobs["conceptUri"] == recom_uri, recommended_jobs.columns[0:11]]
            recom_broader_uri = self.broader_occupations.loc[self.broader_occupations["conceptUri"] == recom_uri, "broaderUri"].iloc[0]
            
            # check if broader job profile is close enough to original job (only if broader job is no ISCO job)
            try:
                # check if broader occupations is not an isco occupation
                broader_fs_profile = occ_fs_profile_scaled_df.loc[recom_broader_uri]
                # check if broader occupation is close enough to original occupation
                if self.compare_occupation_similarity(job_fs_profile, broader_fs_profile) == True:
                    broader_fs_profile_recom = pd.DataFrame(broader_fs_profile).T
                    # broader occupation uri (new concept uri)
                    broader_fs_profile_recom_concept_uri = broader_fs_profile_recom.iloc[0].name # occupation uri
                    # broader occupation details
                    #broader_fs_profile_recom_concept = job_fs_profiles.loc[job_fs_profiles["conceptUri"] == broader_fs_profile_recom_concept_uri] # beinhaltet alles außer broader uri
                    broader_fs_profile_recom_concept = transformed_profiles_preferred.loc[transformed_profiles_preferred["conceptUri"] == broader_fs_profile_recom_concept_uri]
                    # get the new broader broader uri
                    recom_broader_uri = self.broader_occupations.loc[self.broader_occupations["conceptUri"] == broader_fs_profile_recom_concept_uri, "broaderUri"].iloc[0]
                    # add the new broader broader uri to the data frame
                    broader_fs_profile_recom_concept["broaderUri"] = recom_broader_uri
                    # remove elements where broader_occupation will be recommended
                    recommended_jobs = recommended_jobs[recommended_jobs["conceptUri"] != recom_uri]
                    # add new recommendation to list    
                    recommended_jobs_broader_occ = pd.concat([recommended_jobs_broader_occ, broader_fs_profile_recom_concept], axis=0, ignore_index=False)   
            except:
                continue

        # create final recommendation list
        final_recom = pd.concat([recommended_jobs, recommended_jobs_broader_occ], axis=0, ignore_index=False)
 
        return final_recom

    def get_comfort_zone_recommendation(self, top_jobs, transformed_profiles_preferred, transformed_profiles, esco_path:str):
        """
        Generate recommendations within the user's comfort zone by integrating broader occupation data.

        Args:
            top_jobs (pd.DataFrame): The top jobs already filtered for the user.
            transformed_profiles_preferred (pd.DataFrame): Preferred profiles for detailed matching.
            transformed_profiles (pd.DataFrame): All available transformed profiles.
            esco_path (str): Path to the ESco helper data for accessing broader occupation relations.

        Returns:
            pd.DataFrame: Final recommendations within the comfort zone.
        """
        self.esco_helper = esco_helper(esco_path)
        self.broader_occupations = self.esco_helper.get_broaderRelationsOccPillar()

        recommended_jobs = top_jobs

        # Remove Occupations from the same broader occupation
        recommended_jobs = recommended_jobs.merge(self.broader_occupations[['conceptUri', 'broaderUri']], on='conceptUri', how='left')
        recommended_jobs = recommended_jobs.drop_duplicates(subset=['broaderUri'], keep='first')

        # Check for broader occupation for refined recommendations
        final_recom = self.refine_recommendations(recommended_jobs.head(5), transformed_profiles_preferred,transformed_profiles)
        final_recom.drop("broaderUri", axis=1, inplace=True)

        return final_recom


