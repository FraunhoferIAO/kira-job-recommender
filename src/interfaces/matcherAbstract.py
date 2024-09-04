from abc import ABC, abstractmethod
import pandas as pd


class Matcher(ABC):
    """
    Abstract base class for a matcher system.

    This class provides a blueprint for a system that matches user profiles with occupation profiles based on certain features. The specific matching algorithm is defined in subclasses that implement the `calculate_distances` method.

    Methods
    -------
    calculate_distances(occupation_profiles: pd.DataFrame, user_profile: pd.DataFrame, sorted=True) -> pd.DataFrame:
        Abstract method that calculates the distances between the occupation profiles (or user profiles and the user profile). This method should be implemented in a subclass.

    Input -> DataFrame
    -------
     URI                                                                    FS1  FS2  FS3  FS4  FS5  FS6  FS7  FS8  FS9  FS10
    ---------------------------------------------------------------------  -------------
    http://data.europa.eu/esco/skill/c46fcb45-5c14-4ffa-abed-5a43f104bb22  40   20   60    0    0    0    10    0    0    0
    ...                                                                    ...

    Input -> np.array
    -------
     [10, 20, 30 ,40, 50, 60, 70, 80,90,100]
    ...                                                                    ...

    Output -> DataFrame
    -------
            FS1        FS2        FS3        FS4        FS5        FS6        FS7        FS8        FS9       FS10                                         conceptUri                Distance
    1276  76.268690  77.513603  93.137625  93.915882  93.694920  84.498655  81.616906  83.156078  54.771942  78.949948  http://data.europa.eu/esco/occupation/6afe39e2...     23.367886
    1253  75.510412  76.781759  89.887102  90.493266  93.328876  81.556794  78.777838  71.272188  51.123573  73.571937  http://data.europa.eu/esco/occupation/68dd0dfc...     27.445063
    ...

    
    """

    @abstractmethod
    def calculate_distances(
        self, occupation_profiles: pd.DataFrame, user_profile: pd.DataFrame, sorted=True
    ) -> pd.DataFrame:
        """
        Abstract method that calculates the distances between the occupation profiles and the user profile.

        Parameters
        ----------
        occupation_profiles : pd.DataFrame
            A DataFrame representing the occupation profiles. Each row represents an occupation, and each column represents a feature of the occupation.
        user_profile : pd.DataFrame
            A DataFrame representing the user profile. Each row should represent a user, and each column should represent a feature of the user.

        sorted : bool, optional
            A boolean indicating whether the returned DataFrame should be sorted by distance to the user profile. Default is True.

        Returns
        -------
        pd.DataFrame
            A DataFrame representing the occupation profiles sorted by the distance to the user profile. Each row represents an occupation, and each column represents a feature of the occupation. There is an additional column 'distance' that represents the distance to the user profile.

        Raises
        ------
        NotImplementedError
            This method should be implemented in a subclass. The implementation should calculate the distance between each occupation profile and the user profile, and return a DataFrame that includes these distances.
        """
        pass
