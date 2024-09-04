from abc import ABC, abstractmethod
import pandas as pd


class OccMapper(ABC):
    """
    Abstract base class for mapping FS to occupation profiles.

    This class provides a blueprint for a system that maps occupation profiles to FutureSkills. The specific mapping algorithm is defined in subclasses that implement the `create_occ_fs_mapping` method.

    Methods
    -------
    create_occ_fs_mapping(dict) -> pd.DataFrame:
        Abstract method that creates a DataFrame mapping occupations to FutureSkills. This method should be implemented in a subclass.

    Input
    -------
    {
        "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab":
            [
                {"URI": "http://data.europa.eu/esco/skill/869fc2ce-478f-4420-8766-e1f02cec4fb2", "FS_ID": "FS_3"},
                {"URI": "http://data.europa.eu/esco/skill/5c26881e-2759-4a38-b136-5e0f6071b524", "FS_ID": "FS_7"},
                {"URI": "http://data.europa.eu/esco/skill/fe5eabaa-63f6-4c44-b405-fc3ded8d56cb", "FS_ID": "FS_3"}
            ],
        "http://data.europa.eu/esco/skill/00064735-8fad-454b-90c7-ed858cc993f2":  ...

    Output -> DataFrame
    -------
     URI                                                                    FS1  FS2  FS3  FS4  FS5  FS6  FS7  FS8  FS9  FS10
    ---------------------------------------------------------------------  -------------
    http://data.europa.eu/esco/skill/c46fcb45-5c14-4ffa-abed-5a43f104bb22  0.4    0.2    0.6    0    0    0    0.1    0    0    0
    ...                                                                    ...

    """


    @abstractmethod
    def create_occ_fs_mapping(self, dict: dict, esco_path: str) -> pd.DataFrame:
        """
        Abstract method that creates a pd.DataFrame mapping Occupations to FutureSkills.

        Parameters
        ----------
        dict : dict
            A dictionary mapping URIs to FutureSkills
        esco_path : str
            A string representing the file path to the ESCO files.

        Returns
        -------
        pd.DataFrame
            A pd.DataFrame mapping occupations to FutureSkills. The occupations are the index and the FutureSkills are the columns.

        Raises
        ------
        NotImplementedError
            This method should be implemented in a subclass. The implementation should create a dictionary that maps each URI to its associated FutureSkills.
        """
        pass
