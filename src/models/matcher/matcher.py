import numpy as np
import pandas as pd
from scipy.spatial.distance import hamming
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

from src.data.esco_helper import esco_helper
from src.interfaces.matcherAbstract import Matcher


class JobMatcher(Matcher):
    def __init__(
        self,
        method="euclidean",
    ):
        """
        Initializes the JobMatcher instance with a specified distance calculation method.

        Args:
            method (str): Specifies the method for distance calculation, either "euclidean" or "cosine".
        """
        self.method = method

    def filter_by_preferences(self, job_fs_profiles, esco2kldb, preferences=None):
        """
        Filters job profiles based on user-defined preferences and merges them with kldb keys.

        Args:
            job_fs_profiles (pd.DataFrame): DataFrame containing job profiles.
            esco2kldb (pd.DataFrame): DataFrame mapping occupation URIs to concept URIs.
            preferences (list, optional): List of user preferences to apply as a filter.

        Returns:
            pd.DataFrame: A DataFrame with filtered job profiles including future skills, concept URIs, and kldb keys.
        """

        print("not enough compatible user profiles, filtering by preferences only")

        job_fs_profiles = job_fs_profiles.merge(
            esco2kldb,
            left_on="conceptUri",
            right_on="conceptUri",
        )

        if preferences is not None:
            count_occupations = len(job_fs_profiles)
            filter = "|".join(map(str, preferences))

            print(f"Filter for preferences kldb_keys: { filter }")
            job_fs_profiles = job_fs_profiles[job_fs_profiles["kldb_keys"].str.contains(filter, regex=True)]
            print(
                f"Removed {count_occupations - len(job_fs_profiles)} from {count_occupations} occupations based on preferences"
            )
        else:
            print("No preferences given")
        return job_fs_profiles, job_fs_profiles  # dirty fix to return two dataframes

    def extract_user_rating(self, user_profile):
        """
        Extracts user job ratings and recommendations from a user profile.

        Args:
            user_profile (pd.Series or pd.DataFrame): User profile data containing job ratings and recommendations.

        Returns:
            tuple: A tuple containing lists of user ratings and recommended concept URIs.
        """
        if isinstance(user_profile, pd.Series):
            user_profile_rating_list = (
                user_profile["job_ratings"].split(",") if pd.notna(user_profile["job_ratings"]) else np.nan
            )
            rated_conceptUri_list = (
                user_profile["job_recommendations"].split(",")
                if pd.notna(user_profile["job_recommendations"])
                else np.nan
            )
        else:
            user_profile_rating_list = (
                user_profile["job_ratings"].apply(lambda x: x.split(",") if pd.notna(x) else np.nan).tolist()[0]
            )
            rated_conceptUri_list = (
                user_profile["job_recommendations"]
                .apply(lambda x: x.split(",") if pd.notna(x) else np.nan)
                .tolist()[0]
            )

        return user_profile_rating_list, rated_conceptUri_list

    def expand_rows(self, df):
        """
        Expands a DataFrame where each user profile contains lists of recommendations and ratings into multiple rows, one for each recommendation.

        Args:
            df (pd.DataFrame): DataFrame containing user profiles with job recommendations and ratings.

        Returns:
            pd.DataFrame: An expanded DataFrame with each row containing a single job recommendation and its corresponding rating.
        """
        expanded_data = []
        for index, row in df.iterrows():
            for rec, rating in zip(row["job_recommendations"], row["job_ratings"]):
                new_row = row.to_dict()
                new_row["conceptUri"] = rec
                new_row["single_job_rating"] = rating
                new_row["ID"] = index
                expanded_data.append(new_row)
        return pd.DataFrame(expanded_data)

    def expand_user_profiles(self, df_user_profiles):
        """
        Prepares user profiles by splitting string entries into lists and expanding them into multiple rows based on recommendations and ratings.

        Args:
            df_user_profiles (pd.DataFrame): DataFrame containing user profiles with job recommendations and ratings.

        Returns:
            pd.DataFrame: Expanded DataFrame of user profiles.
        """

        def process_column_data(item):
            if isinstance(item, list):
                return item  # Return the list as is if it's already a list
            elif pd.isna(item):
                return []  # Convert NaNs to empty lists if that's preferred
            elif isinstance(item, str):
                return item.split(",")  # This case seems unexpected; included for completeness
            else:
                return []  # Handle other unexpected data types by returning an empty list

        # Apply the processing function to both columns
        df_user_profiles["job_recommendations"] = df_user_profiles["job_recommendations"].apply(process_column_data)
        df_user_profiles["job_ratings"] = df_user_profiles["job_ratings"].apply(process_column_data)

        # drop rows with missing values in job_recommendations and job_ratings (since we cant evaluate them)
        df_cleaned = df_user_profiles.dropna(subset=["job_recommendations", "job_ratings"])

        df_user_profiles_expanded = self.expand_rows(df_cleaned)
        return df_user_profiles_expanded

    def mapSectorsToNumbers(self, sectorsList):
        """
        Maps sector descriptions to their respective numbers as per the KldB categorization.

        Args:
            sectorsList (list): List of sector descriptions.

        Returns:
            list: List of corresponding sector numbers.
        """
        sectors_kldb = {
            1: "Land-, Forst- und Tierwirtschaft und Gartenbau",
            2: "Rohstoffgewinnung, Produktion und Fertigung",
            3: "Bau, Architektur, Vermessung und Gebäudetechnik",
            4: "Naturwissenschaft, Geografie und Informatik",
            5: "Verkehr, Logistik, Schutz und Sicherheit",
            6: "Kaufmännische Dienstleistungen, Warenhandel, Vertrieb, Hotel und Tourismus",
            7: "Unternehmensorganisation, Buchhaltung, Recht und Verwaltung",
            8: "Gesundheit, Soziales, Lehre und Erziehung",
            9: "Sprach-, Geistes-, Gesellschafts- und Wirtschaftswissenschaften, Medien, Kunst und Kultur",
            0: "Militär",
        }
        return [key for key, value in sectors_kldb.items() if value in sectorsList]

    def filter_by_rating(
        self,
        transformed_profiles,
        user_profiles,
        esco_kldb,
        esco_path,
        preferences=None,
        job_history=None,
        rated_conceptUri_list=None,
        user_profile_rating_list=None,
    ):
        """
        Filters user profiles based on their previous ratings and optionally additional preferences. Returns profiles that rated the same job positively or negatively.

        Args:
            transformed_profiles (pd.DataFrame): All available job profiles.
            user_profiles (pd.DataFrame): DataFrame containing user profiles.
            esco_kldb (pd.DataFrame): DataFrame linking ESCO occupations to user profiles.
            preferences (list, optional): List of preferences for filtering.
            job_history (list): List of dictionaries containing job URIs and ratings from the user's job history.
            rated_conceptUri_list (list, optional): List of job URIs previously recommended to the user.
            user_profile_rating_list (list, optional): List of ratings for the jobs previously recommended.

        Returns:
            tuple: Two DataFrames, one filtered by shared preferences and the other without shared preferences.
        """
        # Initialize ESCO helper
        self.esco_helper = esco_helper(esco_path)

        # extract most recent rating and corresponding concept uri
        df_user_profiles_expanded = self.expand_user_profiles(user_profiles)

        def is_nan_or_empty(value):
            if isinstance(value, float) and np.isnan(value):
                return True
            if isinstance(value, list) and len(value) == 0:
                return True
            return False

        # If last job wasn't rated
        if is_nan_or_empty(rated_conceptUri_list) or is_nan_or_empty(user_profile_rating_list):
            user_profiles_by_job_history = self.filter_by_job_history(transformed_profiles, job_history=job_history)
            user_profiles_by_preference_and_history = self.filter_by_preferences(
                user_profiles_by_job_history, esco_kldb, preferences
            )
            return user_profiles_by_preference_and_history
        else:
            rated_conceptUri = rated_conceptUri_list[-1]
            user_profile_last_rating = user_profile_rating_list[-1]

        # If last job was rated
        if user_profile_last_rating == "-1":
            # get profiles that rated same job negative as well
            matching_profiles = df_user_profiles_expanded[
                (df_user_profiles_expanded["conceptUri"] == rated_conceptUri)
                & (df_user_profiles_expanded["single_job_rating"] == "-1")
            ]

        elif user_profile_last_rating == "1":
            # get profiles that rated same job positive as well
            matching_profiles = df_user_profiles_expanded[
                (df_user_profiles_expanded["conceptUri"] == rated_conceptUri)
                & (df_user_profiles_expanded["single_job_rating"] == "1")
            ]

        else:
            # if no rating is given (skipped, value = 0), filter by preferences only (use transformed_profiles (all jobs), not user profiles)
            transformed_profiles_filtered = transformed_profiles[
                ~transformed_profiles.index.isin(rated_conceptUri_list)
            ]
            user_profiles_by_job_history = self.filter_by_job_history(
                transformed_profiles_filtered, job_history=job_history
            )
            user_profiles_by_preference_and_history = self.filter_by_preferences(
                user_profiles_by_job_history, esco_kldb, preferences
            )
            return user_profiles_by_preference_and_history

        # extract ids of matching profiles
        relevant_ids = matching_profiles["user_id"].values

        # filter for jobs that where liked by the matching profiles
        user_profiles_prefiltered = df_user_profiles_expanded[
            df_user_profiles_expanded["user_id"].isin(relevant_ids)
            & (df_user_profiles_expanded["single_job_rating"] == "1")
        ]

        # exclude already suggested occupations
        user_profiles_filtered = user_profiles_prefiltered[
            ~user_profiles_prefiltered["conceptUri"].isin(rated_conceptUri_list)
        ]

        # check if there is at least one matching row, if not filter all jobs by preferences only and return
        if user_profiles_filtered.empty:
            # transformed_profiles_filtered = transformed_profiles[~transformed_profiles['conceptUri'].isin(rated_conceptUri_list)]
            transformed_profiles_filtered = transformed_profiles[
                ~transformed_profiles.index.isin(rated_conceptUri_list)
            ]
            user_profiles_by_job_history = self.filter_by_job_history(
                transformed_profiles_filtered, job_history=job_history
            )
            user_profiles_by_preference_and_history = self.filter_by_preferences(
                user_profiles_by_job_history, esco_kldb, preferences
            )
            return user_profiles_by_preference_and_history

        user_profiles_filtered["num_preferences"] = user_profiles_filtered["professional_interests"].apply(
            lambda x: self.mapSectorsToNumbers(x) if pd.notnull(x) else []
        )

        # get user profiles that rated job the same but dont share preferences
        def is_preference_not_matched(num_prefs):
            return all(pref not in num_prefs for pref in preferences)

        not_filtered_user_profiles = user_profiles_filtered[
            user_profiles_filtered["num_preferences"].apply(is_preference_not_matched)
        ]

        # get user porfiles that rated job the same and share preferences
        def is_preference_matched(num_prefs):
            return any(pref in num_prefs for pref in preferences)

        filtered_user_profiles = user_profiles_filtered[
            user_profiles_filtered["num_preferences"].apply(is_preference_matched)
        ]
        print(f"found {len(filtered_user_profiles)} user profiles that rated the job the same and share preferences")
        print(
            f"found {len(not_filtered_user_profiles)} user profiles that rated the job the same but dont share preferences"
        )
        return filtered_user_profiles, not_filtered_user_profiles

    def calculate_distances(self, query_vector, job_fs_profiles, sorted=True):
        """
        Calculates the distances between a query vector and job profiles using the specified method.

        Args:
            query_vector (pd.Series or pd.DataFrame): The query vector of the user's job preferences.
            job_fs_profiles (pd.DataFrame): DataFrame containing job profiles.
            sorted (bool): If True, sorts the DataFrame by distance.

        Returns:
            pd.DataFrame: A DataFrame of job profiles with an additional column for the calculated distances.
        """

        # dirty bugfix
        column_map = {
            "self_initiative": "FS1",
            "flexibility": "FS2",
            "leadership": "FS3",
            "communication": "FS4",
            "creativity": "FS5",
            "customer_orientation": "FS6",
            "organization": "FS7",
            "problem_solving": "FS8",
            "resilience": "FS9",
            "goal_orientation": "FS10",
        }

        if "self_initiative" in job_fs_profiles.columns:
            job_fs_profiles.rename(columns=column_map, inplace=True)

        future_skill_col_names = ["FS1", "FS2", "FS3", "FS4", "FS5", "FS6", "FS7", "FS8", "FS9", "FS10"]

        # Convert query_vector to NumPy array and reshape
        query_vector_np = query_vector[future_skill_col_names].values.reshape(1, -1)

        if self.method == "euclidean":
            similarities = euclidean_distances(query_vector_np, job_fs_profiles[future_skill_col_names].values)
            top_indices = np.argsort(similarities.flatten())
        elif self.method == "cosine":
            similarities = cosine_similarity(query_vector_np, job_fs_profiles[future_skill_col_names].values)
            top_indices = np.argsort(similarities.flatten())[::-1]

        sorted_df = job_fs_profiles.iloc[top_indices]
        sorted_df["Distance"] = similarities.flatten()[top_indices]

        return sorted_df

    def zone_calculator(self, job_fs_profiles, user_fs_profile, learning_factor=0.3, panic_tolerance=0.1):
        """
        Calculates learning and panic zones based on Hamming distance between user FS profiles and job FS profiles.

        Args:
            job_fs_profiles (pd.DataFrame): DataFrame containing job FS profiles.
            user_fs_profile (array): Array representing the user's FS profile.
            learning_factor (float): Factor defining the learning zone threshold.
            panic_tolerance (float): Tolerance level for defining the panic zone.

        Returns:
            tuple: Lists of calculated Hamming distances and the adjusted FS profiles.
        """
        output_arrays = []
        output_hamming = []
        base_length = len(user_fs_profile)
        for arr in job_fs_profiles.iloc[:, :-2].values:
            # Ensure each array in arrays_list has length 10 and valid values
            # if len(arr) != 10 or any(val not in [0, 1, 2] for val in arr):
            if len(arr) != base_length:
                raise ValueError("Each array in arrays_list must have the same lnegth as the inital_array")

            for i in range(base_length):
                if arr[i] <= user_fs_profile[i]:
                    arr[i] = user_fs_profile[i]
                elif user_fs_profile[i] < 0.2 and arr[i] > user_fs_profile[i] + panic_tolerance:
                    arr = [-1] * base_length
                    break
                elif arr[i] >= user_fs_profile[i] + learning_factor:
                    arr[i] = 2
                else:
                    arr[i] = user_fs_profile[i]

            hamming_dist = hamming(user_fs_profile, arr) * base_length
            output_arrays.append(arr)
            output_hamming.append(hamming_dist)

        return output_hamming, output_arrays

    def filter_by_job_history(self, job_fs_profiles, job_history):
        """
        Remove all occupations that the user did not like in the past, similar jobs and narrower jobs.

        Args:
            job_fs_profiles (pd.DataFrame): DataFrame containing job profiles.
            job_history (list): List of dictionaries containing job URIs and ratings from the user's job history.

        Returns:
            df: DataFrame containing filtered job profiles.
        """

        # Get jobs that the user disliked
        print("Filter by job history")
        jobs_disliked = [key for job_dict in job_history for key, value in job_dict.items() if not value]
        print("Disliked jobs: ", jobs_disliked)

        profiles_to_remove = pd.Index([])
        narrower_jobs_to_remove = pd.Index([])
        max_euclidean_distance = 30

        if len(jobs_disliked) > 0:
            for job in jobs_disliked:

                profiles_to_remove = profiles_to_remove.union(pd.Index([job]))

                # Collect profiles that are to be removed due to their similarity
                similarities = euclidean_distances(
                    job_fs_profiles.loc[job].values.reshape(1, -1),
                    job_fs_profiles,
                )

                flattened_similarities = similarities.flatten()
                mask = flattened_similarities < max_euclidean_distance

                removed_profiles = job_fs_profiles[mask].index
                profiles_to_remove = profiles_to_remove.union(removed_profiles)

                # job_fs_profiles_df = job_fs_profiles[mask]
                # job_fs_profiles_df["Distance"] = flattened_similarities[mask]
                print(f"Remove {len(removed_profiles)} jobs based on similarity with job {job}")
                # print(job_fs_profiles_df[["Distance"]])

                # Collect narrower occupations to be removed
                narrower_occupations = self.esco_helper.get_narrower_occupations(job)
                print(f"Remove {len(narrower_occupations)} narrower jobs for {job}")
                narrower_jobs_to_remove = narrower_jobs_to_remove.union(pd.Index(narrower_occupations))

            # Remove simliar and narrower jobs
            all_jobs_to_remove = profiles_to_remove.union(narrower_jobs_to_remove)
            job_fs_profiles = job_fs_profiles[~job_fs_profiles.index.isin(all_jobs_to_remove)]
            print(f"Removed {len(all_jobs_to_remove)} jobs based on job history.")
            return job_fs_profiles
        else:
            print("No disliked jobs. Skip filtering by job history.")
            return job_fs_profiles
