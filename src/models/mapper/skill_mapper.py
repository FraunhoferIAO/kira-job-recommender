from src.interfaces.mapperAbstract import Mapper
import pandas as pd
import numpy as np
import json
from tqdm import tqdm
from bigtree import tree_to_dataframe, dict_to_tree
from src.data.esco_helper import esco_helper


# implementation of Mapper class, using src.data.skill_importer and src.data.occ_fs_mapper as the basis
class SkillMapper(Mapper):
    """
    SkillMapper class for mapping future skills to ESCO skills.
    """
    def __init__(self, mapping_path: str):
        """
        Initialize the SkillMapper with a mapping file path.

        Args:
            mapping_path (str): Path to the future skills mapping file.
        """
        self.mapping_path = mapping_path
        self.mapping_name = self.mapping_path.split("/")[-1].split(".")[0]

    @property
    def mapping_path(self) -> str:
        """
        Getter for mapping_path.

        Returns:
            str: The path to the mapping file.
        """
        return self._mapping_path

    @mapping_path.setter
    def mapping_path(self, mapping_path):
        """
        Setter for mapping_path.

        Args:
            mapping_path (str): The path to the mapping file.
        """
        self._mapping_path = mapping_path

    def create_fs_dict(self, esco_path: str) -> dict:
        """
        Create a dictionary of future skills based on ESCO skills.

        Args:
            esco_path (str): Path to the ESCO data.

        Returns:
            dict: A dictionary of future skills.
        """
        self.esco_helper = esco_helper(esco_path)

        # import esco skill data & prepare
        self.skills_all_de, self.broader_dict = self.__import_esco_skills()

        # import future skill to ecsco mapping & prepare
        self.future_skills, self.future_skills_uris = self.__import_future_skills()

        # create future skill dict (made of esco skills)
        self.future_skill_dict = self.__get_or_create_fs_skill_dict()

        return self.future_skill_dict

    def __import_esco_skills(self) -> tuple:
        """
        Import ESCO skills and skill groups.

        Returns:
            tuple: DataFrames of all skills and broader dictionary.
        """
        # read esco skills and groups, they are organized in
        skills_de = self.esco_helper.get_skills()
        skill_groups_de = self.esco_helper.get_skillGroups()
        skills_all_de = pd.concat([skills_de, skill_groups_de])

        broader_dict = self.esco_helper.create_broader_dict()

        return skills_all_de, broader_dict

    def __import_future_skills(self) -> tuple:
        """
        Import future skills from the mapping file.

        Returns:
            tuple: DataFrame of future skills and list of unique URIs.
        """
        # read future skills to esco mapping
        future_skills = pd.read_csv(self.mapping_path)
        future_skills_uris = future_skills["URI"].dropna().unique().tolist()

        return future_skills, future_skills_uris

    def __get_or_create_fs_skill_dict(self) -> dict:
        """
        Create a dictionary of future skills based on ESCO skills.

        Returns:
            dict: A dictionary of future skills.
        """
        future_skill_dict = {}
        skills_uris_only = self.skills_all_de[
            self.skills_all_de["skillType"] != "knowledge"
        ]["conceptUri"].tolist()

        for uri in tqdm(skills_uris_only):
            paths = self.__find_skill_trees(uri)
            tree = dict_to_tree(paths)
            results_list = self.__skill_retriever(tree, tree.root)
            results_list_unqiue = [
                i for n, i in enumerate(results_list) if i not in results_list[n + 1 :]
            ]
            future_skill_dict[uri] = results_list_unqiue

        return future_skill_dict

    def __skill_matcher(self, uri: str) -> list | None:
        """
        Match future skills to ESCO URIs.

        Args:
            uri (str): The URI of the skill.

        Returns:
            list: A list of matched future skills.
        """
        esco_to_fs = []
        if uri in self.future_skills_uris:
            for i in self.future_skills[self.future_skills["URI"] == uri].index:
                esco_to_fs.append(self.future_skills.iloc[[i]].to_dict("records")[0])
            return esco_to_fs
        else:
            return None

    def __skill_retriever(self, tree, node) -> list:
        """
        Recursively retrieve skills from the tree.

        Args:
            tree: The skill tree.
            node: The current node in the tree.

        Returns:
            list: A list of skills.
        """
        results_list = []
        matches = self.__skill_matcher(node.conceptUri)
        if matches is not None:
            for match in matches:
                results_list.append(match)
        else:
            for child in node.children:
                results_list.extend(self.__skill_retriever(tree, child))
        return results_list

    def __return_preferred_label(self, path: str) -> str:
        """
        Return the preferred label for a given concept URI.

        Args:
            path (str): The concept URI.

        Returns:
            str: The preferred label.
        """
        return self.skills_all_de[self.skills_all_de["conceptUri"] == path][
            "preferredLabel"
        ].values[0]

    """
    __find_skill_trees recursively iterates over the broader_dict to find all branches within the skill tree.
    The root of the tree is the skill conceptUri that is passed to the function. 
    branch_counter and depth_counter are used to create a unique path for each branch.
    """

    def __find_skill_trees(
        self,
        root:str,
        tree_path: str="",
        tree_dict: dict=None,
        branch_counter: int = 0,
        depth_counter: int = 0,
    ) -> dict:
        """
        Recursively find all branches within the skill tree.

        Args:
            root (str): The root of the tree.
            tree_path (str): The current path in the tree.
            tree_dict (dict): The dictionary to store tree paths.
            branch_counter (int): Counter for branches.
            depth_counter (int): Counter for depth.

        Returns:
            dict: A dictionary representing the skill tree.
        """
        # In order to not use a mutable default argument, we need to check if the argument is None
        if tree_dict is None:
            tree_dict = {}
        tree_path += "/" + str(branch_counter) + str(depth_counter)
        tree_dict[tree_path] = {
            "preferredLabel": self.__return_preferred_label(root),
            "conceptUri": root,
        }
        if root in self.broader_dict.keys():
            for leaf in self.broader_dict[root]:
                if len(self.broader_dict[root]) > 1:
                    branch_counter += 1
                self.__find_skill_trees(
                    leaf, tree_path, tree_dict, branch_counter, depth_counter + 1
                )
        return tree_dict

    def create_occ_fs_profile(self, esco_path: str) -> pd.DataFrame:
        """
        Create a profile of occupations linked to future skills.

        Args:
            esco_path (str): Path to the ESCO data.

        Returns:
            pd.DataFrame: DataFrame of occupations and future skills.
        """
        self.esco_helper = esco_helper(esco_path)

        # import esco occupation data & prepare
        self.occupations, self.occupation_levels = self.__import_occupations()

        # import future skill mapping and link to occupations
        self.future_skills_occupations = self.__link_fs_occupation()

        return self.future_skills_occupations

    def __import_occupations(self) -> tuple:
        """
        Import ESCO occupations.

        Returns:
            tuple: DataFrames of occupations and occupation levels.
        """
        # read esco skills and groups, they are organized in
        occupations = self.esco_helper.get_occupations()

        occupation_levels = pd.DataFrame()
        occupation_levels["conceptUri"] = occupations["conceptUri"]

        occupation_levels["ISCO Level 4"] = occupations["iscoGroup"].apply(
            lambda x: "http://data.europa.eu/esco/isco/C" + str(x)
        )
        occupation_levels["ISCO Level 3"] = occupation_levels["ISCO Level 4"].str[:-1]
        occupation_levels["ISCO Level 2"] = occupation_levels["ISCO Level 3"].str[:-1]
        occupation_levels["ISCO Level 1"] = occupation_levels["ISCO Level 2"].str[:-1]

        return occupations, occupation_levels

    def __link_fs_occupation(self) -> pd.DataFrame:
        """
        Link future skills to occupations.

        Returns:
            pd.DataFrame: DataFrame of occupations and future skills.
        """
        occupation_skills_df = self.esco_helper.get_occupationSkillRelations()
        occupations_levels_skills = occupation_skills_df.join(
            self.occupation_levels.set_index("conceptUri"),
            on="occupationUri",
            how="left",
        )

        with open(self.mapping_path, "r") as json_file:
            future_skills_dict = json.load(json_file)

        skills_future_skills = self.__fs_dict_to_df(future_skills_dict)
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
        fs_df = pd.DataFrame()
        for key, value in input_dict.items():
            for i in value:
                fs_df = fs_df.append({"Key": key, "Value": i}, ignore_index=True)
        return fs_df
