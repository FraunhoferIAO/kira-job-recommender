from abc import ABC, abstractmethod
import pandas as pd


class Transformer(ABC):
    """
    Abstract base class for a transformation system.

    This class provides a blueprint for a system that transforms occupation profiles based on certain features. The specific transformation algorithm is defined in subclasses that implement the `transform` method.

    Methods
    -------
    transform(occupation_profiles: pd.DataFrame) -> pd.DataFrame:
        Abstract method that transforms the occupation profiles. This method should be implemented in a subclass.

    Input -> DataFrame
    -------
     URI                                                                    FS1  FS2  FS3  FS4  FS5  FS6  FS7  FS8  FS9  FS10
    ---------------------------------------------------------------------  -------------
    http://data.europa.eu/esco/skill/c46fcb45-5c14-4ffa-abed-5a43f104bb22  0.4   0.2   0.6    0    0    0    0.1    0    0    0
    ...                                                                    ...

    Output -> DatFrame
    -------
     URI                                                                    FS1  FS2  FS3  FS4  FS5  FS6  FS7  FS8  FS9  FS10
    ---------------------------------------------------------------------  -------------
    http://data.europa.eu/esco/skill/c46fcb45-5c14-4ffa-abed-5a43f104bb22   40   20   60    0    0    0    10    0    0    0
    ...   
    
    """

    @abstractmethod
    def transform(self, occupation_profiles: pd.DataFrame) -> pd.DataFrame:
        """
        Abstract method that transforms the occupation profiles.

        Parameters
        ----------
        occupation_profiles : pd.DataFrame
            A DataFrame representing the occupation profiles. Each row represents an occupation, and each column represents a feature of the occupation.

        Returns
        -------
        pd.DataFrame
            A DataFrame representing the transformed occupation profiles. Each row represents an occupation, and each column represents a transformed feature of the occupation.

        Raises
        ------
        NotImplementedError
            This method should be implemented in a subclass. The implementation should transform the features of each occupation profile, and return a DataFrame that includes these transformed features.
        """
        pass
