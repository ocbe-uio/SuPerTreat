from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from flask_cors import CORS

app = Flask(__name__)

app.config['SWAGGER'] = {
     'title': 'SuPerTreat API',
     'uiversion': 2
 }
CORS(app)
api = Swagger(app)

def select_model(clinical_scenario: str, outcome: str, gene_signature_type: str, censoring_time: int) -> str:
    """
    Selects the appropriate model name based on the given parameters.

    Args:
        clinical_scenario (str): The clinical scenario code.
        outcome (str): The desired outcome.
        gene_signature_type (str): The type of gene signature.
        censoring_time (int): The censoring time in minutes.

    Returns:
        str: The model name based on the given parameters.

    Raises:
        KeyError: If the provided clinical scenario or gene signature type is not valid.

    Examples:
        >>> select_model("3", "dfs", "score", 24)
        'gs2_score_interaction_dfs_24m'

        >>> select_model("1", "os", "none", 60)
        'clinical_base_os_60m'
    """
    clinical_scenarios = {
        "1": "clinical_base",
        "2": "gs1",
        "3": "gs2",
        "4": "gs3",
        "5": "gs4",
        "6": "gs5"
    }

    gene_signature_types = {
        "none": "",
        "class": "class_interaction_",
        "score": "score_interaction_"
    }

    if clinical_scenario == "1":
        gene_signature_type = "none"

    try:
        model_name = (
            clinical_scenarios[clinical_scenario]
            + "_"
            + gene_signature_types[gene_signature_type]
            + outcome
            + "_"
            + str(censoring_time)
            + "m"
        )
    except KeyError as e:
        raise KeyError("Invalid clinical scenario or gene signature type.") from e

    return model_name



from typing import Dict, Iterable, Union

def get_patient_trajectory(single_patient: Iterable[Dict[str, Union[float, int]]]) -> Dict[str, Iterable[Union[float, int]]]:
    """
    Extracts the patient trajectory from an iterable of time points.

    Args:
        single_patient (Iterable[Dict[str, Union[float, int]]]): The iterable of time points for a single patient.
            Each time point is represented as a dictionary with keys 'survival_probability', 'time', 'ci_lower', and 'ci_upper'.

    Returns:
        Dict[str, Iterable[Union[float, int]]]: A dictionary containing the patient trajectory information.
            The keys are 'survival_probability', 'time', 'ci_lower', and 'ci_upper',
            and the corresponding values are iterables of floats or integers.

    Examples:
        >>> patient_data = [
        ...     {"survival_probability": 0.9, "time": 12, "ci_lower": 0.8, "ci_upper": 0.95},
        ...     {"survival_probability": 0.85, "time": 24, "ci_lower": 0.75, "ci_upper": 0.91},
        ...     {"survival_probability": 0.8, "time": 36, "ci_lower": 0.71, "ci_upper": 0.88}
        ... ]
        >>> get_patient_trajectory(patient_data)
        {'survival_probability': [0.9, 0.85, 0.8],
         'time': [12, 24, 36],
         'ci_lower': [0.8, 0.75, 0.71],
         'ci_upper': [0.95, 0.91, 0.88]}
    """
    survival_probability = []
    time = []
    ci_lower = []
    ci_upper = []

    for timepoint in single_patient:
        survival_probability.append(timepoint["survival_probability"])
        time.append(timepoint["time"])
        ci_lower.append(timepoint["ci_lower"])
        ci_upper.append(timepoint["ci_upper"])

    result = {
        "survival_probability": survival_probability,
        "time": time,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper
    }

    return result


def check_tumor_region(request) -> str:
    """
    Checks the tumor region and returns the corresponding HPV status.

    Args:
        tumor_region (str): The tumor region.

    Returns:
        str: The HPV status. Returns 'unknown' if the tumor region is not 'oropharynx'.

    Examples:
        >>> check_tumor_region("oropharynx")
        'negative'

        >>> check_tumor_region("hypopharynx")
        'unknown'

        >>> check_tumor_region("oral cavity")
        'unknown'

        >>> check_tumor_region("larynx")
        'unknown'

        >>> check_tumor_region("oropharynx")
        'positive'
    """
    if request.get('tumor_region') != "oropharynx":
        hpv_status = "unknown"
    else:
        hpv_status = request.get('hpv_status')  

    return hpv_status


@app.route('/base_model', methods=['POST'])
@swag_from('models.yml')
def base_model():
    """
    Endpoint for retrieving patient trajectory data based on specified query parameters.

    Returns:
        flask.Response: A JSON response containing the patient trajectory data.

    Raises:
        None

    Example:


    """
    
    #
    try:
        request_data = request.json
        
        # Retrieve query parameters
        outcome = request_data.get('outcome') 
        censoring_time = request_data.get('censoring_time')

        #[clinical_scenario, outcome, gene_signature_type, censoring_time, request_data.get("clinical_sex")]
        model_name = select_model("1", 
                                outcome, 
                                "none", 
                                censoring_time)
        
        collection = db[model_name]

        query = {"model": model_name,
                    "clinical_sex": request_data.get('clinical_sex'),
                    "clinical_age_at_diagnosis": int(request_data.get('clinical_age_at_diagnosis')),
                    "ctn_disease_extension_diagnosis": request_data.get('ctn_disease_extension_diagnosis'),
                    "surge_undergone_cancer_surgery": request_data.get('surge_undergone_cancer_surgery'),
                    "radio_radiotherapy_treatment": request_data.get('radio_radiotherapy_treatment'),
                    "chemo_chemotherapy_treatment": request_data.get('chemo_chemotherapy_treatment'),
                    "smoking_category": request_data.get('smoking_category'),
                    "tumor_region": request_data.get('tumor_region'),
                    "hpv_status": check_tumor_region(request_data)
                    }


        # Query the result
        single_patient_records = collection.find(query)

        result = get_patient_trajectory(single_patient_records)

        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/hpv_negative', methods=['POST'])
@swag_from('models.yml')
def hpv_negative():
    """
    Endpoint for model scenario 2.

    Retrieves query parameters from the request and performs a query based on the provided parameters.
    The result is returned as a JSON response.

    Returns:
        JSON response containing the patient trajectory.

    Raises:
        ValueError: If the gene_signature_type is not "class" or "score".
        Exception: If any error occurs during the execution.
    """
    try:
        request_data = request.json

        # Retrieve query parameters
        outcome = request_data.get('outcome') 
        gene_signature_type = request_data.get('gene_signature_type') 
        censoring_time = request_data.get('censoring_time')

        #[clinical_scenario, outcome, gene_signature_type, censoring_time, request_data.get("clinical_sex")]
        model_name = select_model("2", 
                                outcome, 
                                gene_signature_type, 
                                censoring_time)
        
        collection = db[model_name]

    

        gs1_os_dict = {
                    "-2": -0.2931846, 
                    "-1": 0.4036082, 
                    "0": 1.100401, 
                    "1": 1.7971937, 
                    "2": 2.4939865}
        
        gs1_dfs_dict = {
                        "-2": -0.2431567, 
                        "-1": 0.4148494, 
                        "0":  1.0728555, 
                        "1":  1.7308616, 
                        "2":  2.3888677
                        }

        query = {"model": model_name,
                    "clinical_sex": request_data.get('clinical_sex'),
                    "clinical_age_at_diagnosis": int(request_data.get('clinical_age_at_diagnosis')),
                    "ctn_disease_extension_diagnosis": request_data.get('ctn_disease_extension_diagnosis'),
                    "surge_undergone_cancer_surgery": request_data.get('surge_undergone_cancer_surgery'),
                    "radio_radiotherapy_treatment": request_data.get('radio_radiotherapy_treatment'),
                    "chemo_chemotherapy_treatment": request_data.get('chemo_chemotherapy_treatment'),
                    "smoking_category": request_data.get('smoking_category'),
                    "tumor_region": request_data.get('tumor_region'),
                    "hpv_status": "negative"
                    }

        if request_data.get("gene_signature_type") == "class":
            query["gs1_class"] = request_data.get('gs_class')
        elif request_data.get("gene_signature_type") == "score":
            if outcome == "os":
                query["gs1_score"] = gs1_os_dict[request_data.get('gs_score')]
            elif outcome == "dfs":
                query["gs1_score"] = gs1_dfs_dict[request_data.get('gs_score')]
        else:
            return "Bad request: Score or class required.", 400

        # Query the result
        single_patient_records = collection.find(query)

        result = get_patient_trajectory(single_patient_records)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/hpv_positive', methods=['POST'])
@swag_from('models.yml')
def hpv_positive():
    """
    Endpoint for Clinical Scenario 3: Gene signature model for HPV-Positive.
    
    Retrieves the query parameters from the request and uses them to query the database
    and obtain the patient trajectory based on the selected model and input parameters.
    
    Returns the patient trajectory as a JSON response.
    """
    request_data = request.json

    # Retrieve query parameters
    outcome = request_data.get('outcome') 
    gene_signature_type = request_data.get('gene_signature_type') 
    censoring_time = "24"

    #[clinical_scenario, outcome, gene_signature_type, censoring_time, request_data.get("clinical_sex")]
    model_name = select_model("3", 
                              outcome, 
                              "score", 
                              censoring_time)
    
    collection = db[model_name]

 

    gs2_os_dict = {
        "-2": -43.54348,
        "-1": -40.06991,
        "0": -36.59634,
        "1": -33.12277, 
        "2": -29.6492
    }

    gs2_dfs_dict = {
        "-2": -43.34192,
        "-1": -39.94582,
        "0": -36.54972,
        "1": -33.15362,
        "2": -29.75752
    }

    query = {"model": model_name,
                "clinical_sex": request_data.get('clinical_sex'),
                "clinical_age_at_diagnosis": int(request_data.get('clinical_age_at_diagnosis')),
                "ctn_disease_extension_diagnosis": request_data.get('ctn_disease_extension_diagnosis'),
                "surge_undergone_cancer_surgery": request_data.get('surge_undergone_cancer_surgery'),
                "radio_radiotherapy_treatment": request_data.get('radio_radiotherapy_treatment'),
                "chemo_chemotherapy_treatment": request_data.get('chemo_chemotherapy_treatment'),
                "smoking_category": request_data.get('smoking_category'),
                "tumor_region": request_data.get('tumor_region'),
                "hpv_status": "positive"
                }

    if request_data.get("gene_signature_type") == "score":
        if outcome == "os":
            query["gs2_score"] = gs2_os_dict[request_data.get('gs_score')]
        elif outcome == "dfs":
            query["gs2_score"] = gs2_dfs_dict[request_data.get('gs_score')]
    else:
        return "Bad request: only score is accepted.", 400

  
    # Query the result
    single_patient_records = collection.find(query)

    result = get_patient_trajectory(single_patient_records)

    return jsonify(result)


@app.route('/radiosensitivity', methods=['POST'])
@swag_from('models.yml')
def radiosensitivity():
    """
    Endpoint for Clinical Scenario 4: Gene signature model for radiosensitivity
    
    Retrieves the query parameters from the request and uses them to query the database
    and obtain the patient trajectory based on the selected model and input parameters.
    
    Returns the patient trajectory as a JSON response.
    """
    
    request_data = request.json

    # Retrieve query parameters
    outcome = request_data.get('outcome') 
    gene_signature_type = request_data.get('gene_signature_type') 
    censoring_time = request_data.get('censoring_time')

  
    model_name = select_model("4", 
                              outcome, 
                              gene_signature_type, 
                              censoring_time)
    
    collection = db[model_name]


    gs3_os_dict = {
        '-2': -0.26048004,
        '-1': -0.08093769,
        '0': 0.09860467,
        '1': 0.27814702,
        '2': 0.45768938
    }

    
    gs3_dfs_dict = {
        '-2': -0.26653957,
        '-1': -0.08628749,
        '0': 0.0939646,
        '1': 0.27421669,
        '2': 0.45446877
    }


    query = {"model": model_name,
                "clinical_sex": request_data.get('clinical_sex'),
                "clinical_age_at_diagnosis": int(request_data.get('clinical_age_at_diagnosis')),
                "ctn_disease_extension_diagnosis": request_data.get('ctn_disease_extension_diagnosis'),
                "surge_undergone_cancer_surgery": request_data.get('surge_undergone_cancer_surgery'),
                "radio_radiotherapy_treatment": request_data.get('radio_radiotherapy_treatment'),
                "chemo_chemotherapy_treatment": request_data.get('chemo_chemotherapy_treatment'),
                "smoking_category": request_data.get('smoking_category'),
                "tumor_region": request_data.get('tumor_region'),
                "hpv_status":  check_tumor_region(request_data)
                }

    if request_data.get("gene_signature_type") == "class":
        query["gs3_class"] = request_data.get('gs_class')
    elif request_data.get("gene_signature_type") == "score":
        if outcome == "os":
            query["gs3_score"] = gs3_os_dict[request_data.get('gs_score')]
        elif outcome == "dfs":
            query["gs3_score"] = gs3_dfs_dict[request_data.get('gs_score')]
    else:
        return "Bad request: Score or class required.", 400


    # Query the result
    single_patient_records = collection.find(query)

    result = get_patient_trajectory(single_patient_records)

    return jsonify(result)


@app.route('/chemosensitivity_platinum', methods=['POST'])
@swag_from('models.yml')
def chemosensitivity_platinum():

    request_data = request.json

    # Retrieve query parameters
    outcome = request_data.get('outcome') 
    gene_signature_type = "score"
    censoring_time = "24"


    model_name = select_model("5", 
                              outcome, 
                              gene_signature_type, 
                              censoring_time)
    
    collection = db[model_name]


    gs4_os_dict = {
        "-2": -1.6086046,
        "-1": -1.109999,
        "0": -0.6113933,
        "1": -0.1127877,
        "2": 0.3858179
    }
    
    gs4_dfs_dict =  {
        "-2": -1.5821354,
        "-1": -1.1019201,
        "0": -0.6217047,
        "1": -0.1414894,
        "2": 0.338726
    }


    query = {
        "model": model_name,
        "clinical_sex": request_data.get("clinical_sex"),
        "clinical_age_at_diagnosis": int(request_data.get("clinical_age_at_diagnosis")),
        "ctn_stage_7ed_modified": request_data.get("ctn_stage_7ed_modified"),
        "chemo_platin_agent": request_data.get("chemo_platin_agent"),
        "smoking_category": request_data.get("smoking_category"),
        "tumor_region": request_data.get("tumor_region"),
        "hpv_status": check_tumor_region(request_data)
    }


    if request_data.get("gene_signature_type") == "score":
        if outcome == "os":
            query["gs4_score"] = gs4_os_dict[request_data.get('gs_score')]
        elif outcome == "dfs":
            query["gs4_score"] = gs4_dfs_dict[request_data.get('gs_score')]
    else:
        return "Bad request: only score available for this gene signature.", 400

    
    # Query the result
    single_patient_records = collection.find(query)

    result = get_patient_trajectory(single_patient_records)

    return jsonify(result)


@app.route('/chemosensitivity_cetuximab', methods=['POST'])
@swag_from('models.yml')
def chemosensitivity_cetuximab():

    request_data = request.json
    
    # Retrieve query parameters
    outcome = request_data.get('outcome') 
    gene_signature_type = "score"
    censoring_time = "24"


    model_name = select_model("6", 
                              outcome, 
                              gene_signature_type, 
                              censoring_time)
    
    collection = db[model_name]


    gs5_os_dict = {
        "-2": -2.144831,
        "-1": 1.39765,
        "0": 4.940131,
        "1": 8.482613,
        "2": 12.025094
    }

    
    gs5_dfs_dict = {
        '-2': -1.836707,
        '-1': 1.598949,
        '0': 5.034605,
        '1': 8.470261,
        '2': 11.905917
    }

    request_data = request.json
    
    query = {
        "model": model_name,
        "clinical_sex": request_data.get("clinical_sex"),
        "clinical_age_at_diagnosis": int(request_data.get("clinical_age_at_diagnosis")),
        "ctn_stage_7ed_modified": request_data.get("ctn_stage_7ed_modified"),
        "chemo_cetuximab_agent": request_data.get("chemo_cetuximab_agent"),
        "smoking_category": request_data.get("smoking_category"),
        "tumor_region": request_data.get("tumor_region"),
        "hpv_status": check_tumor_region(request_data)
    }


    if request_data.get("gene_signature_type") == "score":
        if outcome == "os":
            query["gs5_score"] = gs5_os_dict[request_data.get('gs_score')]
        elif outcome == "dfs":
            query["gs5_score"] = gs5_dfs_dict[request_data.get('gs_score')]
    else:
        return "Bad request: only score available for this gene signature.", 400

    # Query the result
    single_patient_records = collection.find(query)

    result = get_patient_trajectory(single_patient_records)

    return jsonify(result)


from flask import request

@app.route('/hazard_ratios', methods=['POST'])
@swag_from('models.yml')
def hazard_ratios():
    """
    Endpoint for retrieving hazard ratios for the gene signature models.
    
    Retrieves the request body parameters and calculates the hazard ratios
    based on the selected outcome, gene signature type, and censoring time.
    
    Returns the hazard ratios along with confidence intervals, p-value, and comparison as a JSON response.
    """
    
    # Retrieve request body parameters
    request_data = request.json
    outcome = request_data.get('outcome')
    gene_signature_type = request_data.get('gene_signature_type')
    censoring_time = request_data.get('censoring_time')
    clinical_scenario = request_data.get('clinical_scenario')

    model_name = select_model(clinical_scenario, outcome, gene_signature_type, censoring_time)
   
    collection = db["hazard_ratios"]
    # Construct the query for retrieving the hazard ratios from MongoDB
    query = {
        "model": {
            "$regex": model_name
        }
    }
    
    # Query the MongoDB collection to retrieve the hazard ratios
    hazard_ratio_data = collection.find(query)

    #if hazard_ratio_data.count() == 0:
    #    return "Invalid input parameters", 400

    # Extract the relevant data from the retrieved documents
    hazard_ratio = []
    hr_upper_ci = []
    hr_lower_ci = []
    p_value = []
    comparison = []
    for row in hazard_ratio_data:  
        hazard_ratio.append(row["HR"])
        hr_upper_ci.append(row["HR_upper95"])
        hr_lower_ci.append(row["HR_lower95"])
        p_value.append(row["P_value"])
        comparison.append(row["comparison"]) 

    # Construct the response payload
    response = {
        "hazard_ratio": hazard_ratio,
        "hr_upper_ci": hr_upper_ci,
        "hr_lower_ci": hr_lower_ci,
        "p_value": p_value,
        "comparison": comparison
    }

    return jsonify(response)


@app.route('/restricted_mean', methods=['POST'])
@swag_from('models.yml')
def restricted_mean():
    return

if __name__ == '__main__':
    from pymongo import MongoClient

    client = MongoClient('mongodb://localhost:27017/')  
    db = client['supertreat'] 
    
    app.run(port=8001, debug=True)


