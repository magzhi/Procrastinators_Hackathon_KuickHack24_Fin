import cv2
import easyocr
import re
from datetime import datetime

def resize_image(img, width, height):
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)

def correct_gender_in_mrz(mrz_line_2_extracted, expected_gender):
    if mrz_line_2_extracted[20] == '0':
        mrz_line_2_extracted = mrz_line_2_extracted[:20] + expected_gender + mrz_line_2_extracted[21:]
    return mrz_line_2_extracted

def check_expiry(expiry_date_str):
    if not expiry_date_str:
        return "No expiry date provided."
    try:
        clean_date_str = re.sub(r'\s+', '.', expiry_date_str.strip())
        expiry_date = datetime.strptime(clean_date_str, '%d.%m.%Y')
        if expiry_date < datetime.now():
            return "Document has expired."
        else:
            return "Document is valid by expiry date."
    except ValueError:
        return "Invalid expiry date format. Please use DD.MM.YYYY format."

def extract_text(image_path, areas):
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Image not loaded.")
        return {}, None
    image = resize_image(image, 3271, 2250)
    reader = easyocr.Reader(['en'])
    results = {}
    for area in areas:
        y1, x1, y2, x2 = area["coords"]
        crop_img = image[y1:y2, x1:x2]
        result = reader.readtext(crop_img, detail=0)
        extracted_text = ' '.join(result)
        results[area["key"]] = extracted_text.strip()
    return results

def reformat_date(date_str):
    date_str = date_str.replace(' ', '').replace('.', '')
    if len(date_str) == 8:
        day, month, year = date_str[:2], date_str[2:4], date_str[4:]
        return f'{year[-2:]}{month}{day}'
    return "Invalid date format"

def hashing(str1):
    count = 0
    hash_val = 0
    for element in str1:
        if element.isdigit():
            digit = int(element)
        else:
            digit = ord(element.upper()) - 55
        hash_val += digit * [7, 3, 1][count % 3]
        count += 1
    return hash_val % 10

def create_mrz_2(passN, code, birthYYMMDD, gender, endYYMMDD, personN):
    C1 = str(hashing(passN))
    C2 = str(hashing(birthYYMMDD))
    C3 = str(hashing(endYYMMDD))
    C4 = str(hashing(personN))
    C5 = str(hashing(passN + C1 + birthYYMMDD + C2 + endYYMMDD + C3 + personN + "0000000" + C4))

    MRZ2 = passN + C1 + code + birthYYMMDD + C2 + gender + endYYMMDD + C3 + personN
    MRZ2 = MRZ2 + (44-len(MRZ2)-2)*'<' + C4 + C5

    return MRZ2

def main2(file_path):
    common_areas = [{"key": "MRZ Line-1", "coords": [1786, 86, 1949, 3219]}]
    azerbaijan_areas = [
        {"key": "Passport Number", "coords": [252, 2083, 330, 2513]},
        {"key": "Country Code", "coords": [268, 1362, 349, 1561]},
        {"key": "Date of Birth", "coords": [1046, 963, 1135, 1371]},
        {"key": "Personal Number", "coords": [1048, 1572, 1137, 1889]},
        {"key": "Sex", "coords": [1038, 2299, 1115, 2470]},
        {"key": "Date of Expiry", "coords": [1337, 1562, 1421, 1977]},
        {"key": "MRZ Line-1", "coords": [1778, 126, 1902, 3104]},
        {"key": "MRZ Line-2", "coords": [1932, 138, 2056, 3089]}
    ]
    serbia_areas = [
        {"key": "Passport Number", "coords": [302, 2080, 368, 2473]},
        {"key": "Country Code", "coords": [300, 1402, 375, 1589]},
        {"key": "Date of Birth", "coords": [830, 991, 886, 1331]},
        {"key": "Personal Number", "coords": [824, 2073, 890, 2595]},
        {"key": "Sex", "coords": [955, 977, 1036, 1152]},
        {"key": "Date of Expiry", "coords": [1549, 982, 1637, 1351]},
        {"key": "MRZ Line-1", "coords": [1817, 88, 1941, 3196]},
        {"key": "MRZ Line-2", "coords": [1995, 112, 2126, 3190]}
    ]
    data = extract_text(file_path, common_areas)
    mrz_line_1 = data.get("MRZ Line-1", "").strip().replace(' ', '')
    country_code = mrz_line_1[2:5]
    print(f"Country code extracted: {country_code}")

    if country_code == 'AZE':
        areas = azerbaijan_areas
    elif country_code == 'SRB':
        areas = serbia_areas
    else:
        print("Country code not recognized or MRZ lines not properly read.")
        return False,country_code,"Country code not recognized or MRZ lines not properly read."

    data = extract_text(file_path, areas)
    for key, value in data.items():
        print(f"{key}: {value.replace(' ', '')}")

    expiry_date = data.get("Date of Expiry", None)
    if check_expiry(expiry_date) != "Document is valid by expiry date.":
        print(check_expiry(expiry_date))
        return False,country_code,"Document has expired."

    passport_number = data.get("Passport Number", "")
    country_code = data.get("Country Code", "")
    dob = reformat_date(data.get("Date of Birth", ""))
    personal_number = data.get("Personal Number", "")
    sex = data.get("Sex", "").strip()
    sex = 'M' if sex == 'KIM' or sex[0] == 'M' else 'F'
    expiry = reformat_date(data.get("Date of Expiry", ""))
    mrz_line_2_extracted = data.get("MRZ Line-2", "").replace(' ', '')
    mrz_line_2_extracted = correct_gender_in_mrz(mrz_line_2_extracted, sex)

    if country_code == 'AZE':
        mrz_line_2_extracted=mrz_line_2_extracted[:10]+'AZE'+ mrz_line_2_extracted[13:]
    elif country_code == 'SRB':
        mrz_line_2_extracted=mrz_line_2_extracted[:10]+'SRB'+ mrz_line_2_extracted[13:]

    mrz_line_2_calculated = create_mrz_2(passport_number, country_code, dob, sex, expiry, personal_number)

    print(f"Extracted MRZ-2: {mrz_line_2_extracted}")
    print(f"Calculated MRZ-2: {mrz_line_2_calculated}")
    print("Document is valid." if mrz_line_2_extracted == mrz_line_2_calculated else "Document is not valid.")
    return mrz_line_2_extracted == mrz_line_2_calculated,country_code,"Document is not valid by MRZ"