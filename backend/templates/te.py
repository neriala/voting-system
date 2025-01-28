import random

def is_valid_national_id(id_number):
    if len(id_number) != 9 or not id_number.isdigit():
        return False

    counter = 0
    for i in range(9):
        digit = int(id_number[i]) * ((i % 2) + 1)  
        if digit > 9:
            digit -= 9
        counter += digit

    return counter % 10 == 0

def generate_valid_national_id():
    while True:
        id_number = ''.join(str(random.randint(0, 9)) for _ in range(9))  
        if is_valid_national_id(id_number):
            return id_number

def calculate_center_id(national_id):
    return (int(national_id[-1]) % 3) + 1

voters = {1: [], 2: [], 3: []}  # To store voters for each center_id

while any(len(voters[center_id]) < 15 for center_id in voters):
    national_id = generate_valid_national_id()
    center_id = calculate_center_id(national_id)

    if len(voters[center_id]) < 15 and national_id not in voters[1] + voters[2] + voters[3]:
        voters[center_id].append(national_id)

for center_id, ids in voters.items():
    for national_id in ids:
        print(f"add_voter(\"{national_id}\", {center_id})")