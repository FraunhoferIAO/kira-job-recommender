import src.models.mapper.skill_mapper as skill_mapper
import src.models.occ_mapper.occ_mapper as occ_mapper
import src.models.transformer.occ_transformer as occ_transformer
import src.pipeline.data_preparation_pipeline as data_pipe

data_path = "kira-webscraping/data/"

path_to_mapping = "kira-webscraping/data/FutureSkillMappings/processed/MappingTable_manual.csv"
path_to_user_profiles = "kira-webscraping/data/UserData/reference_user_profiles_20240528T143048Z.csv"

mapper = skill_mapper.SkillMapper(path_to_mapping)
occ_fs_mapper = occ_mapper.OccFSMapper()
transformer = occ_transformer.OccTransformer(reference_user_profiles=path_to_user_profiles)

# DATA PREPARATION PIPELINE
datapipe = data_pipe.DataPrepPipeline(
    data_path=data_path, mapper=mapper, occ_mapper=occ_fs_mapper, transformer=transformer
)
datapipe.run()
print("Data Preparation Pipeline finished.")
