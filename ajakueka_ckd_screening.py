import csv
import json
import requests

## read the files
csv_file = requests.get(
    "https://ils.unc.edu/courses/2024_fall/chip490_335/patient_demographics.csv"
)
demographics_r = list(csv.DictReader(csv_file.text.splitlines()))

json_file = requests.get("https://ils.unc.edu/courses/2024_fall/chip490_335/cmp.json")
cmp = json_file.json()

## pre-process
for row in demographics_r:
    row["sex"] = row["sex"]
    row["first_name"] = row["first_name"]
    row["last_name"] = row["last_name"]
    row["mobile_number"] = row["mobile_number"]
    row["age"] = int(row["age"])
    row["patient_id"] = row["patient_id"]


## define the calculation needed for eGFR
def eGFR_calculation(age, sex, scr):
    if sex == "F":
        k = 0.7
        a = -0.241
        f_or_not = 1.012
    else:
        k = 0.9
        a = -0.302
        f_or_not = 1.0

    low = min(scr / k, 1)
    high = max(scr / k, 1)

    patient_eGFR = 142 * (low**a) * (high**-1.200) * (0.9938**age) * f_or_not
    return patient_eGFR


## create a variable that lists cdk_patients
CDK_patients = []
for row in demographics_r:
    patient_name = row["first_name"] + " " + row["last_name"]
    patient_phone = row["mobile_number"]
    patient_id = row["patient_id"]
    ## pull creatinine values from the json file
    if patient_id in cmp:
        patient_measures = cmp[patient_id]
        scr = None
        for measure in patient_measures:
            if measure["measure"] == "Creatinine":
                scr = measure.get("patient_measure")
                break
        ## calculate the eGFR
        if scr is not None:
            age = int(row["age"])
            sex = row["sex"]
            patient_eGFR = eGFR_calculation(age, sex, scr)
            ## identify those with eGFR =< 65
            if patient_eGFR <= 65:
                CDK_patients.append(
                    {
                        "patient_id": patient_id,
                        "patient_name": patient_name,
                        "patient_phone": patient_phone,
                        "patient_eGFR": (patient_eGFR),
                    }
                )

## write results to csv file results.csv
with open("results.csv", "w", newline="") as file:
    fieldnames = ["patient_id", "patient_name", "patient_phone", "patient_eGFR"]
    writer = csv.DictWriter(file, fieldnames)
    writer.writeheader()

    for patient in CDK_patients:
        writer.writerow(patient)
