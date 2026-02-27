import jsonFileHandler

data = jsonFileHandler.readJsonFile("files/insulin.json")

if data != "":
    bInsulin = data['molecules']['bInsulin']
    aInsulin = data['molecules']['aInsulin']
    insulin = bInsulin + aInsulin
    molecularWeightInsulinActual = data['molecularWeightInsulinActual']
    
    print('bInsulin: ' + bInsulin)
    print('aInsulin: ' + aInsulin)
    print('molecularWeightInsulinActual: ' + str(molecularWeightInsulinActual))
    
    aaWeights = data['weights']
    aaCountInsulin = ({
    x: float(insulin.upper().count(x)) 
        for x in ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']
    })
    molecularWeightInsulin = sum({
    x: (aaCountInsulin[x] * aaWeights[x]) 
        for x in ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']}.values())
    print("The rough molecular weight of insulin: " + str(molecularWeightInsulin))
    percentError = ((molecularWeightInsulin - molecularWeightInsulinActual) / molecularWeightInsulinActual) * 100
    
    print("Percent error: " + str(percentError))
else:
    print("Error. Exiting program")