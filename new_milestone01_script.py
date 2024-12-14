import csv
import json
import requests
import pandas as pd

## read the files using requests
csv_file = requests.get(
    "https://ils.unc.edu/courses/2024_fall/chip490_335/patient_demographics.csv"
)
demographics_r = list(csv.DictReader(csv_file.text.splitlines()))

json_file = requests.get("https://ils.unc.edu/courses/2024_fall/chip490_335/cmp.json")
cmp = json_file.json()


## set calculations for eGFR
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
patients = []
for row in demographics_r:
    patient_id = row["patient_id"]
    if patient_id in cmp:
        patient_measures = cmp[patient_id]
        scr = None
        for measure in patient_measures:
            if measure["measure"] == "Creatinine":
                scr = measure.get("patient_measure")
                break
        ## calculate the eGFR
        if scr is not None:
            height = int(row["height_inches"])
            weight = int(row["weight_lbs"])
            age = int(row["age"])
            sex = row["sex"]
            bmi = (weight * 703) / height**2
            patient_eGFR = eGFR_calculation(age, sex, scr)
            ## identify those with eGFR =< 65
            if patient_eGFR <= 65:
                patients.append(
                    {
                        "patient_age": age,
                        "patient_height": height,
                        "patient_weight": weight,
                        "patient_bmi": bmi,
                        "patient_sex": sex,
                        "patient_eGFR": patient_eGFR,
                    }
                )

## convert output to a pandas dataframe
df = pd.DataFrame(patients)

df.to_csv("final_output.csv")
