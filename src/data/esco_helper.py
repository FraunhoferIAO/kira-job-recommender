import pandas as pd

"""
Helper Class for ESCO to fetch needed views and tables without loading the csv individually
"""


class esco_helper:
    def __init__(self, realtive_path_to_esco, language="de"):
        self.path = realtive_path_to_esco
        self.language = language
        self.look_up_table = self.load_look_up_table()

    def load_look_up_table(self):
        """
        Load Look-up table from ESCO sources
        :return: Dataframe with Skills/SkillGroups/Occupations/ISCOGroups
        """

        occupations = self.get_occupations()
        ISCO_groups = self.get_ISCOGroups()
        skills = self.get_skills()
        skillGroups = self.get_skillGroups()

        look_up_table = pd.concat([occupations, ISCO_groups, skills, skillGroups], axis=0, ignore_index=True)
        look_up_table.set_index("conceptUri", inplace=True)

        return look_up_table

    def load_skill_level_lookup(self):
        esco_hierarchy = self.get_skillsHierarchy()
        esco_broader_skills_pillar = self.get_broaderRelationsSkillPillar()
        esco_skills = self.get_skills()

        # create lookup first part
        cols = [
            "Level 0 URI",
            "Level 0 preferred term",
            "Level 1 URI",
            "Level 1 preferred term",
            "Level 2 URI",
            "Level 2 preferred term",
            "Level 3 URI",
            "Level 3 preferred term",
            "Skill URI",
            "Skill preferred term",
            "Skill group",
            "Level 0 code",
            "Level 1 code",
            "Level 2 code",
            "Level 3 code",
        ]
        lookup_base = pd.DataFrame(columns=cols)

        # fill in values from hierarchy table
        common_cols = set(lookup_base.columns).intersection(esco_hierarchy.columns)
        for col in common_cols:
            lookup_base[col] = esco_hierarchy[col]

        # fill remaining values:
        # 1. find out where the current list ends
        # -> these skills are the broader concepts for which the narrower concepts must be found in the relations skill pillar
        lowest_level = []
        for i in range(0, 4):
            col = f"Level {i} URI"
            unique_urls = lookup_base[col].value_counts()[lookup_base[col].value_counts() == 1].index.tolist()
            lowest_level = lowest_level + unique_urls

        # 2. find narrower concepts in relations skill pillar for lowest level in lookup
        # for each lowest level, get all narrower concepts from skill pillar
        relations = {}

        for url in lowest_level:
            narrower_concepts = esco_broader_skills_pillar.loc[
                esco_broader_skills_pillar["broaderUri"] == url, "conceptUri"
            ].tolist()
            all_narrower_concepts = self.__search_urls_for_narrower_skills(narrower_concepts)

            if bool(all_narrower_concepts):
                narrower_concepts = narrower_concepts + all_narrower_concepts

            relations[url] = narrower_concepts

        # create lists with according data and whitespaces
        # columns of lookup_base as lists
        level_0_uris = lookup_base["Level 0 URI"].tolist()
        level_0_term = lookup_base["Level 0 preferred term"].tolist()
        level_1_uris = lookup_base["Level 1 URI"].tolist()
        level_1_term = lookup_base["Level 1 preferred term"].tolist()
        level_2_uris = lookup_base["Level 2 URI"].tolist()
        level_2_term = lookup_base["Level 2 preferred term"].tolist()
        level_3_uris = lookup_base["Level 3 URI"].tolist()
        level_3_term = lookup_base["Level 3 preferred term"].tolist()
        level_0_code = lookup_base["Level 0 code"].tolist()
        level_1_code = lookup_base["Level 1 code"].tolist()
        level_2_code = lookup_base["Level 2 code"].tolist()
        level_3_code = lookup_base["Level 3 code"].tolist()

        # skill_uris = [item for sublist in relations.values() for item in sublist]
        skill_uris = []
        skill_preferred_terms = []
        skill_groups = []

        lines_to_match = 0
        insert_id = 0
        for i, row in lookup_base.iterrows():
            lines_to_match += 1
            for key, value in relations.items():
                if key in row.values:
                    insert_id += lines_to_match
                    # expand lists accordingly
                    skill_uris.extend([None] * lines_to_match)
                    skill_uris.extend(value)

                    level_0_uris[insert_id:insert_id] = [level_0_uris[insert_id - 1]] * len(value)
                    level_0_term[insert_id:insert_id] = [level_0_term[insert_id - 1]] * len(value)
                    level_1_uris[insert_id:insert_id] = [level_1_uris[insert_id - 1]] * len(value)
                    level_1_term[insert_id:insert_id] = [level_1_term[insert_id - 1]] * len(value)
                    level_2_uris[insert_id:insert_id] = [level_2_uris[insert_id - 1]] * len(value)
                    level_2_term[insert_id:insert_id] = [level_2_term[insert_id - 1]] * len(value)
                    level_3_uris[insert_id:insert_id] = [level_3_uris[insert_id - 1]] * len(value)
                    level_3_term[insert_id:insert_id] = [level_3_term[insert_id - 1]] * len(value)
                    level_0_code[insert_id:insert_id] = [level_0_code[insert_id - 1]] * len(value)
                    level_1_code[insert_id:insert_id] = [level_1_code[insert_id - 1]] * len(value)
                    level_2_code[insert_id:insert_id] = [level_2_code[insert_id - 1]] * len(value)
                    level_3_code[insert_id:insert_id] = [level_3_code[insert_id - 1]] * len(value)
                    insert_id += len(value)
                    lines_to_match = 0

        # fill the rest of the table (skill term and skill group)
        for item in skill_uris:
            if item is None:
                skill_preferred_terms.append(None)
                skill_groups.append(None)

            else:
                # find preferred term and group for skill uri
                skill_preferred_terms.append(
                    esco_skills.loc[esco_skills["conceptUri"] == item, "preferredLabel"].values[0]
                )
                skill_groups.append(esco_skills.loc[esco_skills["conceptUri"] == item, "skillType"].values[0])

        # put it all together
        final_lookup = {
            "Level 0 URI": level_0_uris,
            "Level 0 preferred term": level_0_term,
            "Level 1 URI": level_1_uris,
            "Level 1 preferred term": level_1_term,
            "Level 2 URI": level_2_uris,
            "Level 2 preferred term": level_2_term,
            "Level 3 URI": level_3_uris,
            "Level 3 preferred term": level_3_term,
            "Skill URI": skill_uris,
            "Skill preferred term": skill_preferred_terms,
            "Skill group": skill_groups,
            "Level 0 code": level_0_code,
            "Level 1 code": level_1_code,
            "Level 2 code": level_2_code,
            "Level 3 code": level_3_code,
        }

        lookup = pd.DataFrame(final_lookup)

        return lookup

    def get_occupations(self):
        occupations = pd.read_csv(
            f"{self.path}/ESCO dataset - v1.1.1 - classification - {self.language} - csv/occupations_{self.language}.csv",
            dtype=str,
        )

        return occupations

    def get_ISCOGroups(self):
        ISCOGroups = pd.read_csv(
            f"{self.path}/ESCO dataset - v1.1.1 - classification - {self.language} - csv/ISCOGroups_{self.language}.csv",
            dtype=str,
        )
        return ISCOGroups

    def get_skills(self):
        skills = pd.read_csv(
            f"{self.path}/ESCO dataset - v1.1.1 - classification - {self.language} - csv/skills_{self.language}.csv",
            dtype=str,
        )
        return skills

    def get_skillGroups(self):
        skillGroups = pd.read_csv(
            f"{self.path}/ESCO dataset - v1.1.1 - classification - {self.language} - csv/skillGroups_{self.language}.csv",
            dtype=str,
        )
        return skillGroups

    def get_skillsHierarchy(self):
        skillsHierarchy = pd.read_csv(
            f"{self.path}/ESCO dataset - v1.1.1 - classification - {self.language} - csv/skillsHierarchy_{self.language}.csv",
            dtype=str,
        )
        return skillsHierarchy

    def get_broaderRelationsSkillPillar(self):
        broaderRelationsSkillPillar = pd.read_csv(
            f"{self.path}/ESCO dataset - v1.1.1 - classification -  - csv/broaderRelationsSkillPillar.csv",
            dtype=str,
        )
        return broaderRelationsSkillPillar

    def get_broaderRelationsOccPillar(self):
        broaderTelationsOccPillar = pd.read_csv(
            f"{self.path}/ESCO dataset - v1.1.1 - classification -  - csv/broaderRelationsOccPillar.csv",
            dtype=str,
        )
        return broaderTelationsOccPillar

    def get_occupationSkillRelations(self):
        occupationSkillRelations = pd.read_csv(
            f"{self.path}/ESCO dataset - v1.1.1 - classification -  - csv/occupationSkillRelations.csv",
            dtype=str,
        )
        return occupationSkillRelations

    def look_up(self, uris):
        """
        Look up the Details of the URI in the ESCO Skills Dataframe
        :param uri: URI of the Skill
        :return: Skill Name
        """
        return self.look_up_table.loc[uris]

    def look_up_label(self, uris):
        return self.look_up(uris)["preferredLabel"]

    def look_up_IscoGroup(self, uris):
        return self.look_up(uris)["iscoGroup"]

    def look_up_code(self, uris):
        return self.look_up(uris)["code"]

    def look_up_description(self, uris):
        return self.look_up(uris)["description"]

    def look_up_skills(self, uris, include_knowledge, include_optional):
        occupationSkillRelations = self.get_occupationSkillRelations()

        if not include_knowledge:
            occupationSkillRelations = occupationSkillRelations[occupationSkillRelations["skillType"] != "knowledge"]
        if not include_optional:
            occupationSkillRelations = occupationSkillRelations[occupationSkillRelations["relationType"] != "optional"]

        occupationSkillRelations = occupationSkillRelations[occupationSkillRelations["occupationUri"] == uris]

        skills = occupationSkillRelations["skillUri"].tolist()
        skills = list(map(self.look_up_label, skills))
        return skills

    def get_detailed_ISCO_levels(self):
        """
        Get the detailed ISCO levels
        :return: Dataframe with detailed ISCO levels
        """
        occupations = self.get_occupations()
        occupation_levels = pd.DataFrame()
        occupation_levels["conceptUri"] = occupations["conceptUri"]

        occupation_levels["ISCO Level 4"] = occupations["iscoGroup"].apply(
            lambda x: "http://data.europa.eu/esco/isco/C" + str(x)
        )
        occupation_levels["ISCO Level 3"] = occupation_levels["ISCO Level 4"].str[:-1]
        occupation_levels["ISCO Level 2"] = occupation_levels["ISCO Level 3"].str[:-1]
        occupation_levels["ISCO Level 1"] = occupation_levels["ISCO Level 2"].str[:-1]

        return occupation_levels

    def create_broader_dict(self, type="Skill"):
        """
        Get a dictionary of broader relations
        :return: Dictionary of broader relations
        """
        if type == "Skill":
            broaderRelations = self.get_broaderRelationsSkillPillar()

        elif type == "Occupation":
            broaderRelations = self.get_broaderRelationsOccPillar()
        else:
            raise ValueError("Type must be 'Skill' or 'Occupation'")

        broader_dict = {}
        for index, row in broaderRelations.iterrows():
            if row["conceptUri"] in broader_dict:
                broader_dict[row["conceptUri"]].append(row["broaderUri"])
            else:
                broader_dict[row["conceptUri"]] = [row["broaderUri"]]
        return broader_dict

    def get_narrower_occupations(self, uri):
        """
        Get all narrower Occupations of a Occupation
        :param uri: URI of the Occupation
        :return: List of narrower Occupations URIs
        """
        occupations = self.get_occupations()
        code = self.look_up_code(uri)
        return occupations[
            occupations["code"].astype("string").str.startswith(str(code))
            & (occupations["code"].astype("string").str.len() > len(str(code)))
        ][["conceptUri"]].values

    def get_broader(self, uri):
        """
        Get all broader Skills/Occupations of a Skill/Occupation
        :param uri: URI of the Skill/Occupation
        :return: List of broader Skills/Occupations
        """
        return None

    def __search_urls_for_narrower_skills(self, urls):
        # get necessary tables
        esco_broader_skills_pillar = self.get_broaderRelationsSkillPillar()

        relations = []
        for url in urls:
            if url in esco_broader_skills_pillar["broaderUri"].values:
                narrower_concepts = esco_broader_skills_pillar.loc[
                    esco_broader_skills_pillar["broaderUri"] == url, "conceptUri"
                ].tolist()
                relations = relations + narrower_concepts

                narrower_relations = self.__search_urls_for_narrower_skills(narrower_concepts)
                if bool(narrower_relations):
                    relations = relations + narrower_relations

        return relations
