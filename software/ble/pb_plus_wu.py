import sys
import statistics

powerblade = open(sys.argv[1], 'r')
output = open(sys.argv[2], 'w')

output.write("#Time\tAct P\tWU P\tPB P\tAct PF\tWU PF\tPB PF\n")

timeStart = 0

truePower = []
wuPower = []
pbPower = []

trueFactor = []
wuFactor = []
pbFactor = []

for PBline in powerblade:
	wattsup = open('wattsup.dat','r')
	plm = open('plm1.dat','r')
	if(len(PBline) > 0):
		# print('#####################################')
		# print(PBline)
		PBline = PBline.split('\t')
		pbtime = float(PBline[0])
		pbtrue = float(PBline[1])
		pbpf = float(PBline[2])
		if(timeStart == 0):
			timeStart = pbtime

		# For each powerblade point, find the closest watts up point	
		bestTime = 0
		bestTrue = 0
		bestPF = 0
		for WUline in wattsup:
			# print(WUline)
			WUline = WUline.split('\t')
			wutime = float(WUline[0])
			wutrue = float(WUline[1])
			wupf = float(WUline[3])

			# Determine if this point is closer than others
			# print(pbtime - bestTime)
			# print(pbtime - wutime)
			# print()
			if(abs(pbtime - bestTime) > abs(pbtime - wutime)):
				bestTime = wutime
				bestTrue = wutrue
				bestPF = wupf
		wuPower.append(bestTrue)
		wuFactor.append(bestPF)

		wattsup.close()

		bestPLMTime = 0
		bestPLMTrue = 0
		bestPLMPF = 0
		for PLMline in plm:
			PLMline = PLMline.split('\t')
			plmtime = float(PLMline[0])
			plmtrue = float(PLMline[1])
			plmpf = float(PLMline[3])
		
			# Determine if this point is closer than others
			if(abs(pbtime - bestPLMTime) > abs(pbtime - plmtime)):
				bestPLMTime = plmtime
				bestPLMTrue = plmtrue
				bestPLMPF = plmpf
		truePower.append(bestPLMTrue)
		trueFactor.append(bestPLMPF)

		plm.close()

		# Output values
		pbPower.append(pbtrue)
		pbFactor.append(pbpf)
		outstring = str(round(pbtime-timeStart,2)) + '\t' + str(bestPLMTrue) + '\t' + str(bestTrue) + '\t' + str(pbtrue) + '\t' + str(bestPLMPF) + '\t' + str(bestPF) + '\t' + str(pbpf)
		#print(outstring)
		output.write(outstring + '\n')

mean_trueP = sum(truePower)/len(truePower)
mean_wuP = sum(wuPower)/len(wuPower)
mean_pbP = sum(pbPower)/len(pbPower)
mean_truePF = sum(trueFactor)/len(trueFactor)
mean_wuPF = sum(wuFactor)/len(wuFactor)
mean_pbPF = sum(pbFactor)/len(pbFactor)

print()
print("PLM True Power:\t\t\tPower Factor:")
print("Mean: " + str(round(mean_trueP,2)) + ',\t' + str(round(statistics.variance(truePower),4)),end="")
print("\t\t",end="")
print("Mean: " + str(round(mean_truePF,3)) + ',\t' + str(round(statistics.variance(trueFactor),4)))
print()
print("Watts Up True Power:\t\tPower Factor")
print("Mean: " + str(round(mean_wuP,2)) + ',\t' + str(round(statistics.variance(wuPower),4)),end="")
print("\t\t",end="")
print("Mean: " + str(round(mean_wuPF,3)) + ',\t' + str(round(statistics.variance(wuFactor),4)))
if mean_trueP > 0:
	print("Error: " + str(round(100*abs(mean_trueP-mean_wuP)/mean_trueP,2)))
print()
print("PowerBlade True Power:\t\tPower Factor")
print("Mean: " + str(round(mean_pbP,2)) + ',\t' + str(round(statistics.variance(pbPower),4)),end="")
print("\t\t",end="")
print("Mean: " + str(round(mean_pbPF,3)) + ',\t' + str(round(statistics.variance(pbFactor),4)))
if mean_trueP > 0:
	print("Error: " + str(round(100*abs(mean_trueP-mean_pbP)/mean_trueP,2)))
print()




