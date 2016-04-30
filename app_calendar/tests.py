from django.test import TestCase
#Import necessary models if you need to use data from the database

#This function is going to test that the priority and cluster for the percentile range is accurate
class Test_PrioritizationAndClusteringTestCase(TestCase):
	#List of 3 nested lists to represent the data structure of range percentiles
	overall_data=[[], [], []]
	'''
		Formula:
 		PR% = L + ( 0.5 x S ) / N   Where, L = Number of below rank, S = Number of same rank, N = Total numbers.
	'''
	#Testing the percentile information here
	all_data = [1, 6, 1.5, 9, 10, 5.66, 4.33, 3, 1.5]

	equation_N = len(all_data)
	equation_L = [i for i in all_data if i < 10]

	#Loop through all the pieces of data inside the given data set
	for data_point in all_data:

		#Get L, the number of items below the currently given rank
		equation_L = len([i for i in all_data if i < data_point])
		equation_N = len(all_data)
		equation_S = len([i for i in all_data if i == data_point])
		
		pr_percent = ((equation_L + (0.5*equation_S)) / equation_N)*100
		
		if (pr_percent <= 25):
			overall_data[0].append(("0-25%", "%d%%"%(pr_percent), "Data Point: %s"%(str(data_point))))
		elif (pr_percent > 25 and pr_percent <= 75):
			overall_data[1].append(("25-75%", "%d%%"%(pr_percent), "Data Point: %s"%(str(data_point))))
		elif (pr_percent > 75 and pr_percent <= 100):
			overall_data[1].append(("75-100%", "%d%%"%(pr_percent), "Data Point: %s"%(str(data_point))))


	for data_set in overall_data:
		try:
			print(data_set[0])
			print(data_set[1])
			print(data_set[2])
		except:
			pass

	#Do calculation with the initial case into the 50th percentile range





