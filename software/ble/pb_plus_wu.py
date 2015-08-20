import sys
import statistics

powerblade = open(sys.argv[1], 'r')
output = open(sys.argv[2], 'w')

output.write("#Time\tDiff\tAct P\tPB P\tAct PF\tPB PF\n")

timeStart = 0

truePower = []
pbPower = []
trueFactor = []
pbFactor = []

for PBline in powerblade:
	wattsup = open('wattsup.dat','r')
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
		
		wattsup.close()

		# Output values
		truePower.append(bestTrue)
		pbPower.append(pbtrue)
		trueFactor.append(bestPF)
		pbFactor.append(pbpf)
		outstring = str(round(pbtime-timeStart,2)) + '\t' + str(round(pbtime-bestTime,2)) + '\t' + str(bestTrue) + '\t' + str(pbtrue) + '\t' + str(bestPF) + '\t' + str(pbpf)
		#print(outstring)
		output.write(outstring + '\n')

print()
print("Actual True Power:")
print("Mean: " + str(round(sum(truePower)/len(truePower),2)) + ',\t' + str(round(statistics.variance(truePower),4)))
print()
print("PowerBlade True Power:")
print("Mean: " + str(round(sum(pbPower)/len(pbPower),2)) + ',\t' + str(round(statistics.variance(pbPower),4)))
print()
print("Actual Power Factor:")
print("Mean: " + str(round(sum(trueFactor)/len(trueFactor),3)) + ',\t' + str(round(statistics.variance(trueFactor),4)))
print()
print("PowerBlade Power Factor:")
print("Mean: " + str(round(sum(pbFactor)/len(pbFactor),3)) + ',\t' + str(round(statistics.variance(pbFactor),4)))
print()



