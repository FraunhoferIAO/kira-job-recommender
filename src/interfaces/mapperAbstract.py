from abc import ABC, abstractmethod
import pandas as pd


class Mapper(ABC):
    """
    Abstract base class for a mapping system.

    This class provides a blueprint for a system that maps Skill URIs to FutureSkills. The specific mapping algorithm is defined in subclasses that implement the `create_fs_dict` method.

    Methods
    -------
    create_fs_dict(df: pd.DataFrame) -> dict:
        Abstract method that creates a dictionary mapping URIs to FutureSkills. This method should be implemented in a subclass.

    Input Format
    -------
    URI                                                                    FutureSkill
    ---------------------------------------------------------------------  -------------
    http://data.europa.eu/esco/skill/c46fcb45-5c14-4ffa-abed-5a43f104bb22  FS1
    ...                                                                    ...

    Output Format (create_fs_dict())
    -------
    {
        "http://data.europa.eu/esco/skill/c46fcb45-5c14-4ffa-abed-5a43f104bb22": [
            "FS1",
            ...
        ],
        ...
    }

    """

    @property
    def mapping_path(self):
        pass

    @abstractmethod
    def create_fs_dict(self, file_path: str) -> dict:
        """
        Abstract method that creates a dictionary mapping URIs to FutureSkills.

        Parameters
        ----------
        file_path : str
            A string representing the file path to the ESCO files.

        Returns
        -------
        dict
            A dictionary where the keys are URIs and the values are lists of associated FutureSkills.

        Raises
        ------
        NotImplementedError
            This method should be implemented in a subclass. The implementation should create a dictionary that maps each URI to its associated FutureSkills.
        """
        pass
