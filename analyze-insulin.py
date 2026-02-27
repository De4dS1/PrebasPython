import re

with open("prepoinsulin-seq.txt", "r") as f:    
    raw_data = f.read()
    
    clean_data = re.sub(r"\bORIGIN\b", "", raw_data, flags = re.IGNORECASE)

    clean_data = clean_data.replace("//", "")    

    clean_data = re.sub(r"[^A-Za-z]", "", clean_data)

    clean_data = clean_data.lower()

with open("prepoinsulin-seq.txt", "w") as f:
    f.write(clean_data)

print("Longitud prepoinsulina = ", len(clean_data))

if len(clean_data) != 110:
    print("Error, la secuencia no tiene 110 caracteres")
    exit()

lsinsulin = clean_data[0:24]

binsulin = clean_data[24:54]

cinsulin = clean_data[54:89]

ainsulin = clean_data[89:110]

with open("lsinsulin-seq-clean.xt", "w") as f:
    f.write(lsinsulin)

with open("lsinsulin-seq-clean.xt", "w") as f:
    f.write(binsulin)

with open("lsinsulin-seq-clean.xt", "w") as f:
    f.write(cinsulin)
with open("lsinsulin-seq-clean.xt", "w") as f:
    f.write(ainsulin)

print("lsinsulin = ", len(lsinsulin))
print("lsinsulin = ", len(binsulin))
print("lsinsulin = ", len(cinsulin))
print("lsinsulin = ", len(ainsulin))

insulin = binsulin + ainsulin
print("Insulina procesada = ", len(insulin))

print("'secuencia de la insulina = ",  insulin)
