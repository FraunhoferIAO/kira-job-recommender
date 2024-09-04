
def find_best_match(df, renaming_dict):
    matched_columns = {}
    
    for col in df.columns:
        best_match = None
        highest_score = 0
        
        for key in renaming_dict.keys():
            score = 0
            if col == key:
                best_match = key
                break  # Exact match found
            elif key in col or col in key:
                score = len(set(col).intersection(set(key)))
                
            if score > highest_score:
                best_match = key
                highest_score = score
        
        if best_match is None:
            raise ValueError(f"No suitable match found for column: {col}")
        
        if best_match in matched_columns:
            raise ValueError(
                f"Duplicate match found for columns: {col} and {matched_columns[best_match]}"
            )
        
        matched_columns[best_match] = col
    
    return matched_columns


def rename_columns(df):
    """
    Rename columns of df based on the best fuzzy match in renaming_dict as preparation for using FutureSkills enums

    Parameters:
    - df: DataFrame with columns to be renamed.

    Returns:
    - DataFrame with renamed columns.
    """
    renaming_dict = {
        'self_initiative': 'FS1',
        'flexibility': 'FS2',
        'leadership': 'FS3',
        'communication': 'FS4',
        'creativity': 'FS5',
        'customer_orientation': 'FS6',
        'organization': 'FS7',
        'problem_solving': 'FS8',
        'resilience': 'FS9',
        'goal_orientation': 'FS10',
        "FS_1_Eigeninitiative": "FS1",
        "FS_1": "FS1",
        "Eigeninitiative": "FS1",
        "FS_2_Flexibilität": "FS2",
        "FS_2": "FS2",
        "Flexibilität": "FS2",
        "FS_3_Führungsfähigkeiten": "FS3",
        "FS_3": "FS3",
        "Führung": "FS3",
        "FS_4_Kommunikation / Überzeugungsvermögen": "FS4",
        "FS_4": "FS4",
        "Kommunikation / Überzeugungsvermögen": "FS4",
        "Überzeugungsvermögen": "FS4",
        "Kommunikation": "FS4",
        "FS_5_Kreativität": "FS5",
        "FS_5": "FS5",
        "Kreativität": "FS5",
        "FS_6_Kundenorientierung": "FS6",
        "FS_6": "FS6",
        "Kund:Innenorientierung": "FS6",
        "Kundenorientierung": "FS6",
        "FS_7_Organisationsfähigkeit": "FS7",
        "FS_7": "FS7",
        "Organisationsfähigkeit": "FS7",
        "FS_8_Problemlösungsfähigkeit": "FS8",
        "FS_8": "FS8",
        "Problemlösungsfähigkeit": "FS8",
        "FS_9_Resilienz": "FS9",
        "FS_9": "FS9",
        "Resilienz": "FS9",
        "FS_10_Zielorientierung": "FS10",
        "FS_10": "FS10",
        "Zielorientierung": "FS10",
    }

    # check that all columns are not already renamed
    if set(df.columns).issubset(renaming_dict.values()):
        return df

    # Find the best match for each column in df
    matched_columns = {}
    matched_columns = find_best_match(df, renaming_dict)

    # Rename columns based on the best matches
    inverse_matched_columns = {v: renaming_dict[k] for k, v in matched_columns.items()}
    df = df.rename(columns=inverse_matched_columns)

    # Check that all columns are uniquely assigned
    if len(set(df.columns)) != 10:
        print(f'problem erkannt: {len(set(df.columns))} != 10')
        print(df.columns)
        raise ValueError

    return df
