from src.interfaces.transformerAbstract import Transformer

import pandas as pd
import numpy as np
import sys
from datetime import datetime, timezone
from sklearn.preprocessing import MinMaxScaler, PowerTransformer
from sklearn.impute import KNNImputer
import src.data.renaming_helper as renaming_helper


class OccTransformer(Transformer):
    """
    OccTransformer class for transforming occupation future skills profiles.
    """
    def __init__(
            self,
            reference_user_profiles: str=None,
            impute: bool = True,
            n_neighbors: int = 10
    ):
        """
        Initialize the OccTransformer with specific settings.

        Args:
            reference_user_profiles (str): Path to the reference user profiles CSV file.
            impute (bool): Whether to impute missing values. Default is True.
            n_neighbors (int): Number of neighbors to use for KNN imputation. Default is 10.
        """
        self.reference_user_profiles = self.check_user_profiles(reference_user_profiles)
        self.reference_timestamp = reference_user_profiles
        self.impute = impute
        self.n_neighbors = n_neighbors

    def check_user_profiles(self, reference_user_profiles):
        """
        Check and load reference user profiles from a CSV file.

        Args:
            reference_user_profiles (str): Path to the reference user profiles CSV file.

        Returns:
            pd.DataFrame: DataFrame of reference user profiles.

        Raises:
            SystemExit: If the reference user profiles file is not found.
        """
        if reference_user_profiles is not None:
            try:
                user_profiles = pd.read_csv(reference_user_profiles, index_col=0)
                return renaming_helper.rename_columns(user_profiles.iloc[:, 8:18])
            except:
                print("Reference user profiles not found. Aborting.")
                sys.exit()
                
        return None

    def transform(self, occ_fs_profiles: pd.DataFrame) -> pd.DataFrame:
        """
        Transform occupation future skills profiles.

        Args:
            occ_fs_profiles (pd.DataFrame): DataFrame of occupation future skills profiles.

        Returns:
            pd.DataFrame: Transformed DataFrame of occupation future skills profiles.

        Raises:
            SystemExit: If columns of the input DataFrame do not match the reference user profiles.
        """

        try:
            occ_fs_profiles = occ_fs_profiles[self.reference_user_profiles.columns]
        except:
            print("Columns not matching. Aborting.")
            sys.exit()

        # impute nan with knn
        if self.impute:
            # set zero to nan
            occ_fs_profiles_df_nan = self.set_zero_to_nan(occ_fs_profiles)

            occ_fs_profiles = self.knn_impute(
                occ_fs_profiles_df_nan, n_neighbors=self.n_neighbors
            )

        #transform job profiles
        occ_fs_profile_transformed_df = self.transform_job_profiles(
            occ_fs_profiles, self.reference_user_profiles
        )

        occ_fs_profile_transformed_df[occ_fs_profile_transformed_df < 0] = 0

        return occ_fs_profile_transformed_df

    def set_zero_to_nan(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Set zero values to NaN in the DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame.

        Returns:
            pd.DataFrame: DataFrame with zero values set to NaN.
        """
        df[df == 0] = np.nan
        return df

    def knn_impute(self, df: pd.DataFrame, n_neighbors: int) -> pd.DataFrame:
        """
        Impute missing values using KNN imputer.

        Args:
            df (pd.DataFrame): Input DataFrame with NaN values.
            n_neighbors (int): Number of neighbors to use for KNN imputation.

        Returns:
            pd.DataFrame: DataFrame with imputed values.
        """
        imputer = KNNImputer(n_neighbors=n_neighbors)
        df_imputed = imputer.fit_transform(df)
        df_imputed = pd.DataFrame(df_imputed, columns=df.columns, index=df.index)
        return df_imputed

    def power_transform(self, df: pd.DataFrame, power_transformer: PowerTransformer=None) -> pd.DataFrame:
        """
        Apply power transformation to the DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame.
            power_transformer (PowerTransformer, optional): Pre-fitted power transformer. Default is None.

        Returns:
            pd.DataFrame: Transformed DataFrame.
        """
        if power_transformer is None:
            power_transformer = PowerTransformer(method="yeo-johnson", standardize=True)
            power_transformer.fit(df)
        array = power_transformer.transform(df)
        df = pd.DataFrame(array, columns=df.columns, index=df.index)
        return df

    def min_max_scale(self, df: pd.DataFrame, min_max_scaler: MinMaxScaler=None) -> pd.DataFrame:
        """
        Apply min-max scaling to the DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame.
            min_max_scaler (MinMaxScaler, optional): Pre-fitted min-max scaler. Default is None.

        Returns:
            pd.DataFrame: Scaled DataFrame.
        """
        if min_max_scaler is None:
            min_max_scaler = MinMaxScaler()
            min_max_scaler.fit(df)
        array = min_max_scaler.transform(df)
        df = pd.DataFrame(array, columns=df.columns, index=df.index)
        return df

    def inverse_power_transform(self,
        df: pd.DataFrame, power_transformer: PowerTransformer
    ) -> pd.DataFrame:
        """
        Apply inverse power transformation to the DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame.
            power_transformer (PowerTransformer): Pre-fitted power transformer.

        Returns:
            pd.DataFrame: Inversely transformed DataFrame.
        """
        array = power_transformer.inverse_transform(df)
        df = pd.DataFrame(array, columns=df.columns, index=df.index)
        return df

    def inverse_min_max_scale(self,
        df: pd.DataFrame, min_max_scaler: MinMaxScaler
    ) -> pd.DataFrame:
        """
        Apply inverse min-max scaling to the DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame.
            min_max_scaler (MinMaxScaler): Pre-fitted min-max scaler.

        Returns:
            pd.DataFrame: Inversely scaled DataFrame.
        """
        array = min_max_scaler.inverse_transform(df)
        df = pd.DataFrame(array, columns=df.columns, index=df.index)
        return df

    def get_fitted_power_transformer(self, df: pd.DataFrame) -> PowerTransformer:
        """
        Fit a power transformer to the DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame.

        Returns:
            PowerTransformer: Fitted power transformer.
        """
        power_transformer = PowerTransformer(method="yeo-johnson", standardize=True)
        power_transformer.fit(df)
        return power_transformer

    def get_fitted_min_max_scaler(self, df: pd.DataFrame) -> MinMaxScaler:
        """
        Fit a min-max scaler to the DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame.

        Returns:
            MinMaxScaler: Fitted min-max scaler.
        """
        min_max_scaler = MinMaxScaler()
        min_max_scaler.fit(df)
        return min_max_scaler

    def transform_job_profiles(
        self, df_jobs: pd.DataFrame, df_users: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Transform job profiles to match the distribution of user profiles.

        Args:
            df_jobs (pd.DataFrame): DataFrame of job profiles.
            df_users (pd.DataFrame): DataFrame of user profiles.

        Returns:
            pd.DataFrame: Transformed DataFrame of job profiles.
        """
        df_jobs = self.power_transform(df_jobs)
        df_jobs = self.min_max_scale(df_jobs)

        user_power_transformer = self.get_fitted_power_transformer(df_users)
        df_users_transformed = self.power_transform(df_users, user_power_transformer)
        user_min_max_scaler = self.get_fitted_min_max_scaler(df_users_transformed)

        df_jobs = self.inverse_min_max_scale(df_jobs, user_min_max_scaler)
        df_jobs = self.inverse_power_transform(df_jobs, user_power_transformer)

        return df_jobs
