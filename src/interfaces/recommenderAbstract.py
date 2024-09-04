from abc import ABC, abstractmethod


class Recommender(ABC):
    """
    Abstract base class for a recommender system.

    This class serves as a template for systems that recommend occupation profiles based on various user-defined features. The specific recommendation algorithm must be defined in subclasses that implement the `recommend` method.

    Methods
    -------
    recommend(user_profile: dict, items: list) -> list:
        Abstract method that retrieves the preferred labels for recommended jobs. This method must be implemented in a subclass.

        
    Input -> List
    -------

    conceptUri                                                             FS1  FS2  FS3  FS4  FS5  FS6  FS7  FS8  FS9  FS10  kldb_keys  Distance 
    ---------------------------------------------------------------------  ------------------------------------------------- 
    http://data.europa.eu/esco/skill/c46fcb45-5c14-4ffa-abed-5a43f104bb22  40   20   60    0    0    0    10    0    0    0   [3 5 9]    30.695244 
    ...                                                                    ...                      
    
    Output -> List
    -------
        ['Fachkraft in der Nitroglycerinherstellung (Neutralisation)',
        'Aufsichtskraft Rückbau',
        'Import-/Exportsachbearbeiter/Import-/Exportsachbearbeiterin',
        'Bauleiter Unterwasserarbeiten/Bauleiterin Unterwasserarbeiten',
        'Ingenieur Arbeitsschutz im Bergbau/Ingenieurin Arbeitsschutz im Bergbau']

    """

    @abstractmethod
    def recommend(self, recommended_jobs):
        """
        Recommends items based on the user profile and specified preferences.

        Parameters
        ----------
        recommended_jobs : pd.DataFrame
            DataFrame containing the concept URIs of jobs recommended to a user.

        Returns
        -------
        list of dict
            A list containing preferred labels for the recommended jobs, which represent the human-readable titles or names of the occupations.

        Raises
        ------
        NotImplementedError
            This method should be implemented in subclasses to provide the specific recommendation logic based on the implemented algorithm.
        """
        pass


