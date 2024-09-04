import os
import sys

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(1, os.path.join(sys.path[0], ".."))

import src.data.esco_helper as EscoHelper
import src.data.renaming_helper as renaming_helper
import src.models.matcher.matcher as matcher
import src.models.recommender.recommender as recommender
import src.pipeline.recommender_pipeline as recommender_pipe

data_path = "kira-webscraping/data/"
esco_path = "kira-webscraping/data/ESCO/"
path_reference_user_profiles = "kira-webscraping/data/UserData/reference_user_profiles_20240528T143048Z.csv"  # replace path here to newest version of user_profiles
path_transformed_occ_profiles = "kira-webscraping/data/FutureSkills/OccupationFSProfiles/transformed/MappingTable_test_new_k=10_20240528T143048Z.csv"  # replace path here to newest version of transformed profiles

job_matcher = matcher.JobMatcher()
reference_user_profiles = pd.read_csv(path_reference_user_profiles, index_col=0)
reference_user_profiles.iloc[:, 8:18] = renaming_helper.rename_columns(reference_user_profiles.iloc[:, 8:18])

transformed_occ_profiles = pd.read_csv(path_transformed_occ_profiles, index_col=0)
transformed_occ_profiles.rename_axis("conceptUri", inplace=True)
esco_helper = EscoHelper.esco_helper(esco_path)

app = Flask(__name__)
CORS(app)


@app.route("/recommendations", methods=["POST"])
def recommendation_detail():
    """
    Call the recommender pipeline to get job recommendations for a given user profile.

    Returns:
        dict: Returns a dictionary containing the recommended job profile.
    """
    columns = [
        "FS1",
        "FS2",
        "FS3",
        "FS4",
        "FS5",
        "FS6",
        "FS7",
        "FS8",
        "FS9",
        "FS10",
        "last_job",
        "second_last_job",
        "previous_job",
        "job_recommendations",
        "job_ratings",
    ]
    target_profile = pd.DataFrame(columns=columns)

    # Get user data from profile and prepare as df for recommender
    data = request.get_json()

    preferences = data.get("preferenced_sectors", None)

    last_job_data = data.get("last_job")
    last_job: dict[str, bool] | None = (
        {last_job_data["uri"]: last_job_data["liked"]} if last_job_data and isinstance(last_job_data, dict) else None
    )

    second_last_job_data = data.get("second_last_job")
    second_last_job: dict[str, bool] | None = (
        {second_last_job_data["uri"]: second_last_job_data["liked"]}
        if second_last_job_data and isinstance(second_last_job_data, dict)
        else None
    )

    previous_job_data = data.get("previous_job")
    previous_job: dict[str, bool] | None = (
        {previous_job_data["uri"]: previous_job_data["liked"]}
        if previous_job_data and isinstance(previous_job_data, dict)
        else None
    )

    job_recommendations = data.get("job_recommendations", [])
    job_ratings = data.get("job_ratings", [])
    job_history = [job for job in [last_job, second_last_job, previous_job] if job is not None]

    target_profile.loc[0, columns[:10]] = data["profile"]
    target_profile.loc[0, ["last_job", "second_last_job", "previous_job"]] = [last_job, second_last_job, previous_job]
    target_profile.loc[0, "job_recommendations"] = ",".join(job_recommendations) if job_recommendations else "NaN"
    target_profile.loc[0, "job_ratings"] = ",".join(map(str, job_ratings)) if job_ratings else "NaN"

    # Initialize recommender pipeline
    job_recommender = recommender.JobRecommender(target_profile.iloc[0, :10].values)

    recom_pipe = recommender_pipe.RecommenderPipeline(
        data_path=data_path, matcher=job_matcher, recommender=job_recommender
    )

    # Run pipeline
    recommendations = recom_pipe.run(
        target_profile=target_profile,
        preferences=preferences,
        job_history=job_history,
        transformed_profiles=transformed_occ_profiles,
        user_profiles=reference_user_profiles,
    )

    uri = recommendations.iloc[0][
        "conceptUri"
    ]  # in our case, we only want the first recommendation, remove this line if you want all recommendations
    profile = occupation_detail(uri)
    return jsonify(profile)


@app.route("/occupations", methods=["GET"])
def occupation_list():
    """
    Returns the occupation profiles for a list of given URIs.

    Args:
        uri_list (str): A comma-separated list of URIs.

    Returns:
        list of dict: A list of occupation profiles.
    """
    uri_list = request.args.get("uri_list", None)
    rec_list = []
    if uri_list:
        for uri in uri_list.split(","):
            profile = occupation_detail(uri)
            rec_list.append(profile)
        return jsonify(rec_list)
    else:
        return jsonify({"error": "No uris provided."})


def occupation_detail(uri: str):
    """
    Get the occupation profile for a given URI.

    Args:
        uri (str): The URI of the occupation profile.

    Returns:
        dict: Returns a dictionary containing the recommended job profile.
    """
    entry = {}
    profile = transformed_occ_profiles.loc[uri].iloc[:10].to_dict()
    try:
        entry = {
            "label": esco_helper.look_up_label(uri),
            "description": esco_helper.look_up_description(uri),
            "uri": uri,
            "skills": [
                {"label": x}
                for x in [
                    {"label": x}
                    for x in esco_helper.look_up_skills(uri, include_knowledge=False, include_optional=False)[:10]
                    if str(x) != "nan"
                ]
            ],
            "profile": profile,
        }
        return entry
    except:
        print(f"Error: {uri} not found.")
        return None


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
