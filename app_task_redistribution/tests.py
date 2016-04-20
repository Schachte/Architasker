from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from app_calendar.models import UserEvent
from app_account_management.models import UserExtended
from .views import *

#########################################################################################################
#																										#
# 	MAKE SURE TO COMMENT OUT THE HTTPRESPONSE AT THE END OF THE FREE BLOCK ALGORITHM AND UNCOMMENT		#
# 	THE RETURN STATEMENT OF THE FREE BLOCK LIST BEFORE RUNNING THESE TESTS.								#
#																										#
#	THE EXPECTED LISTS ARE TO HELP UNDERSTAND WHAT THE TEST IS LOOKING FOR								#
#	THE DATES IN THE EXPECTED LISTS ARE INCORRECT, SO YOU WILL HAVE TO JUST LOOK						#
#	AT THE TIMES AND MATCH THEM WITH THE DATES IN THE CURRENT WEEK YOU ARE TESTING. 					#
#																										#
#	ALSO, THE USER EVENT OBJECTS WILL NEED TO BE MANUALLY UPDATED TO REFLECT THE CURRENT WEEK. 			#
#	THIS SHOULD BE AUTOMATED IN THE FUTURE. 															#
#																										#
#	Author: Connor Maddox																				#
#########################################################################################################

class FreeBlocksTestCase(TestCase):
	def setUp(self):
		#test_all_week_free1
		self.factory = RequestFactory()
		self.user1 = User.objects.create(username="user1", password="password")
		UserExtended.objects.create(authenticated_user = self.user1, wakeup_time = "08:00", 
									sleepy_time = "20:00", time_zone = "America/Phoenix", 
									min_task_time="0", travel_time = "0")
		#test_all_week_free2
		self.user2 = User.objects.create(username="user2", password="password")
		UserExtended.objects.create(authenticated_user = self.user2, wakeup_time = "11:00", 
									sleepy_time = "03:00", time_zone = "America/Phoenix",
									min_task_time="0", travel_time = "0")
		#test_overlap_wakeup1
		self.user3 = User.objects.create(username="user3", password="password")
		UserExtended.objects.create(authenticated_user = self.user3, wakeup_time = "08:00", 
									sleepy_time = "20:00", time_zone = "America/Phoenix", 
									min_task_time="0", travel_time = "0")

		#Change start and end time according to current day
		UserEvent.objects.create(authenticated_user = self.user3, start_time = "2016-04-11T07:00:00Z", end_time = "2016-04-11T09:00:00Z")

		#test_overlap_wakeup_cluster1
		self.user4 = User.objects.create(username="user4", password="password")
		UserExtended.objects.create(authenticated_user = self.user4, wakeup_time = "08:00", 
									sleepy_time = "20:00", time_zone = "America/Phoenix", 
									min_task_time="0", travel_time = "0")

		UserEvent.objects.create(authenticated_user = self.user4, start_time = "2016-04-11T07:00:00Z", end_time = "2016-04-11T09:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user4, start_time = "2016-04-11T06:00:00Z", end_time = "2016-04-11T10:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user4, start_time = "2016-04-11T08:00:00Z", end_time = "2016-04-11T11:00:00Z")

		#test_overlap_bedtime1
		self.user5 = User.objects.create(username="user5", password="password")
		UserExtended.objects.create(authenticated_user = self.user5, wakeup_time = "08:00",
									sleepy_time = "20:00", time_zone = "America/Phoenix",
									min_task_time="0", travel_time = "0")

		UserEvent.objects.create(authenticated_user = self.user5, start_time = "2016-04-11T19:00:00Z", end_time = "2016-04-11T21:00:00Z")

		#test_overlap_bedtime_cluster1
		self.user6 = User.objects.create(username="user6", password="password")
		UserExtended.objects.create(authenticated_user = self.user6, wakeup_time = "08:00", 
									sleepy_time = "20:00", time_zone = "America/Phoenix", 
									min_task_time="0", travel_time = "0")

		UserEvent.objects.create(authenticated_user = self.user6, start_time = "2016-04-11T19:00:00Z", end_time = "2016-04-11T21:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user6, start_time = "2016-04-11T18:00:00Z", end_time = "2016-04-11T22:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user6, start_time = "2016-04-11T20:00:00Z", end_time = "2016-04-11T23:00:00Z")

		#test_during_day_cluster1
		self.user7 = User.objects.create(username="user7", password="password")
		UserExtended.objects.create(authenticated_user = self.user7, wakeup_time = "08:00", 
									sleepy_time = "20:00", time_zone = "America/Phoenix", 
									min_task_time="0", travel_time = "0")

		UserEvent.objects.create(authenticated_user = self.user7, start_time = "2016-04-11T10:00:00Z", end_time = "2016-04-11T13:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user7, start_time = "2016-04-11T09:00:00Z", end_time = "2016-04-11T14:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user7, start_time = "2016-04-11T11:00:00Z", end_time = "2016-04-11T15:00:00Z")

		#test_normally distributed1
		self.user8 = User.objects.create(username="user8", password="password")
		UserExtended.objects.create(authenticated_user = self.user8, wakeup_time = "08:00", 
									sleepy_time = "20:00", time_zone = "America/Phoenix", 
									min_task_time="0", travel_time = "0")

		UserEvent.objects.create(authenticated_user = self.user8, start_time = "2016-04-11T10:00:00Z", end_time = "2016-04-11T13:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user8, start_time = "2016-04-12T09:00:00Z", end_time = "2016-04-12T10:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user8, start_time = "2016-04-13T11:00:00Z", end_time = "2016-04-13T15:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user8, start_time = "2016-04-13T09:00:00Z", end_time = "2016-04-13T11:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user8, start_time = "2016-04-14T12:00:00Z", end_time = "2016-04-14T14:00:00Z")
		UserEvent.objects.create(authenticated_user = self.user8, start_time = "2016-04-14T17:00:00Z", end_time = "2016-04-14T20:00:00Z")
		
	def test_all_week_free1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user1

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start = day[0:10] + "T08:00:00Z"
			end = day[0:10] + "T20:00:00Z"
			expected_list.append((start, end))

		# expected_list = [	('2016-02-01T08:00:00Z', '2016-02-01T20:00:00Z'), 
		# 					('2016-02-02T08:00:00Z', '2016-02-02T20:00:00Z'), 
		# 					('2016-02-03T08:00:00Z', '2016-02-03T20:00:00Z'), 
		# 					('2016-02-04T08:00:00Z', '2016-02-04T20:00:00Z'), 
		# 					('2016-02-05T08:00:00Z', '2016-02-05T20:00:00Z'), 
		# 					('2016-02-06T08:00:00Z', '2016-02-06T20:00:00Z'), 
		# 					('2016-02-07T08:00:00Z', '2016-02-07T20:00:00Z')]
		self.assertEqual(expected_list, free_time)

	def test_all_week_free2(self):
		request = self.factory.get('/archicalc')
		request.user = self.user2

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []
		
		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start_day = day[0:10] + "T00:00:00Z"
			end_day = day[0:10] + "T23:59:59Z"
			start = day[0:10] + "T11:00:00Z"
			end = day[0:10] + "T03:00:00Z"
			expected_list.append((start_day, end))
			expected_list.append((start, end_day))

		# expected_list = [	('2016-02-01T00:00:00Z', '2016-02-01T03:00:00Z'),
		# 					('2016-02-01T11:00:00Z', '2016-02-01T23:59:59Z'), 
		# 					('2016-02-02T00:00:00Z', '2016-02-02T03:00:00Z'),
		# 					('2016-02-02T11:00:00Z', '2016-02-02T23:59:59Z'), 
		# 					('2016-02-03T00:00:00Z', '2016-02-03T03:00:00Z'),
		# 					('2016-02-03T11:00:00Z', '2016-02-03T23:59:59Z'), 
		# 					('2016-02-04T00:00:00Z', '2016-02-04T03:00:00Z'),
		# 					('2016-02-04T11:00:00Z', '2016-02-04T23:59:59Z'), 
		# 					('2016-02-05T00:00:00Z', '2016-02-05T03:00:00Z'),
		# 					('2016-02-05T11:00:00Z', '2016-02-05T23:59:59Z'), 
		# 					('2016-02-06T00:00:00Z', '2016-02-06T03:00:00Z'),
		# 					('2016-02-06T11:00:00Z', '2016-02-06T23:59:59Z'), 
		# 					('2016-02-07T00:00:00Z', '2016-02-07T03:00:00Z'),
		# 					('2016-02-07T11:00:00Z', '2016-02-07T23:59:59Z'),]
		self.assertEqual(expected_list, free_time)

	def test_overlap_wakeup1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user3

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start = day[0:10] + "T08:00:00Z"
			end = day[0:10] + "T20:00:00Z"
			expected_list.append((start, end))
		start = days_in_current_week[0][0:10] + "T09:00:00Z"
		end = days_in_current_week[0][0:10] + "T20:00:00Z"
		expected_list[0] = (start, end)

		# expected_list = [	('2016-04-11T09:00:00Z', '2016-04-11T20:00:00Z'), 
		# 					('2016-04-12T08:00:00Z', '2016-04-12T20:00:00Z'), 
		# 					('2016-04-13T08:00:00Z', '2016-04-13T20:00:00Z'), 
		# 					('2016-04-14T08:00:00Z', '2016-04-14T20:00:00Z'), 
		# 					('2016-04-15T08:00:00Z', '2016-04-15T20:00:00Z'), 
		# 					('2016-04-16T08:00:00Z', '2016-04-16T20:00:00Z'), 
		# 					('2016-04-17T08:00:00Z', '2016-04-17T20:00:00Z')]
		# print expected_list
		# print free_time

		self.assertEqual(expected_list, free_time)

	def test_overlap_wakeup_cluster1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user4

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start = day[0:10] + "T08:00:00Z"
			end = day[0:10] + "T20:00:00Z"
			expected_list.append((start, end))
		start = days_in_current_week[0][0:10] + "T11:00:00Z"
		end = days_in_current_week[0][0:10] + "T20:00:00Z"
		expected_list[0] = (start, end)

		# expected_list = [	('2016-04-11T11:00:00Z', '2016-04-11T20:00:00Z'), 
		# 					('2016-04-12T08:00:00Z', '2016-04-12T20:00:00Z'), 
		# 					('2016-04-13T08:00:00Z', '2016-04-13T20:00:00Z'), 
		# 					('2016-04-14T08:00:00Z', '2016-04-14T20:00:00Z'), 
		# 					('2016-04-15T08:00:00Z', '2016-04-15T20:00:00Z'), 
		# 					('2016-04-16T08:00:00Z', '2016-04-16T20:00:00Z'), 
		# 					('2016-04-17T08:00:00Z', '2016-04-17T20:00:00Z')]
		# print expected_list
		# print free_time
		self.assertEqual(expected_list, free_time)

	def test_overlap_bedtime1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user5

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start = day[0:10] + "T08:00:00Z"
			end = day[0:10] + "T20:00:00Z"
			expected_list.append((start, end))
		start = days_in_current_week[0][0:10] + "T08:00:00Z"
		end = days_in_current_week[0][0:10] + "T19:00:00Z"
		expected_list[0] = (start, end)

		# expected_list = [	('2016-04-11T08:00:00Z', '2016-04-11T19:00:00Z'), 
		# 					('2016-04-12T08:00:00Z', '2016-04-12T20:00:00Z'), 
		# 					('2016-04-13T08:00:00Z', '2016-04-13T20:00:00Z'), 
		# 					('2016-04-14T08:00:00Z', '2016-04-14T20:00:00Z'), 
		# 					('2016-04-15T08:00:00Z', '2016-04-15T20:00:00Z'), 
		# 					('2016-04-16T08:00:00Z', '2016-04-16T20:00:00Z'), 
		# 					('2016-04-17T08:00:00Z', '2016-04-17T20:00:00Z')]
		# print expected_list
		# print free_time
		self.assertEqual(expected_list, free_time)

	def test_overlap_bedtime_cluster1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user6

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		for day in days_in_current_week:
			start = day[0:10] + "T08:00:00Z"
			end = day[0:10] + "T20:00:00Z"
			expected_list.append((start, end))
		start = days_in_current_week[0][0:10] + "T08:00:00Z"
		end = days_in_current_week[0][0:10] + "T18:00:00Z"
		expected_list[0] = (start, end)

		# expected_list = [	('2016-04-11T08:00:00Z', '2016-04-11T18:00:00Z'), 
		# 					('2016-04-12T08:00:00Z', '2016-04-12T20:00:00Z'), 
		# 					('2016-04-13T08:00:00Z', '2016-04-13T20:00:00Z'), 
		# 					('2016-04-14T08:00:00Z', '2016-04-14T20:00:00Z'), 
		# 					('2016-04-15T08:00:00Z', '2016-04-15T20:00:00Z'), 
		# 					('2016-04-16T08:00:00Z', '2016-04-16T20:00:00Z'), 
		# 					('2016-04-17T08:00:00Z', '2016-04-17T20:00:00Z')]
		# print expected_list
		# print free_time
		self.assertEqual(expected_list, free_time)

	def test_during_day_cluster1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user7

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		current_day = 0
		for day in days_in_current_week:
			if current_day == 0:
				start = days_in_current_week[0][0:10] + "T08:00:00Z"
				end = days_in_current_week[0][0:10] + "T09:00:00Z"
				expected_list.append((start, end))
				start = days_in_current_week[0][0:10] + "T15:00:00Z"
				end = days_in_current_week[0][0:10] + "T20:00:00Z"
				expected_list.append((start, end))
			else:		
				start = day[0:10] + "T08:00:00Z"
				end = day[0:10] + "T20:00:00Z"
				expected_list.append((start, end))
			current_day += 1
		

		# expected_list = [	('2016-04-11T08:00:00Z', '2016-04-11T09:00:00Z'),
		# 					('2016-04-11T15:00:00Z', '2016-04-11T20:00:00Z'),
		# 					('2016-04-12T08:00:00Z', '2016-04-12T20:00:00Z'), 
		# 					('2016-04-13T08:00:00Z', '2016-04-13T20:00:00Z'), 
		# 					('2016-04-14T08:00:00Z', '2016-04-14T20:00:00Z'), 
		# 					('2016-04-15T08:00:00Z', '2016-04-15T20:00:00Z'), 
		# 					('2016-04-16T08:00:00Z', '2016-04-16T20:00:00Z'), 
		# 					('2016-04-17T08:00:00Z', '2016-04-17T20:00:00Z')]
		# print expected_list
		# print free_time
		self.assertEqual(expected_list, free_time)

	def test_normally_distributed1(self):
		request = self.factory.get('/archicalc')
		request.user = self.user8

		start_week_range = get_current_week_range(request)[0]
		days_in_current_week = []

		for single_date in (parse(start_week_range) + datetime.timedelta(n) for n in range(7)):
			days_in_current_week.append(str(single_date))

		free_time = task_distribution(request)
		expected_list = []
		current_day = 0
		for day in days_in_current_week:
			if current_day == 0:
				start = days_in_current_week[0][0:10] + "T08:00:00Z"
				end = days_in_current_week[0][0:10] + "T10:00:00Z"
				expected_list.append((start, end))
				start = days_in_current_week[0][0:10] + "T13:00:00Z"
				end = days_in_current_week[0][0:10] + "T20:00:00Z"
				expected_list.append((start, end))
			elif current_day == 1:
				start = days_in_current_week[1][0:10] + "T08:00:00Z"
				end = days_in_current_week[1][0:10] + "T09:00:00Z"
				expected_list.append((start, end))
				start = days_in_current_week[1][0:10] + "T10:00:00Z"
				end = days_in_current_week[1][0:10] + "T20:00:00Z"
				expected_list.append((start, end))
			elif current_day == 2:
				start = days_in_current_week[2][0:10] + "T08:00:00Z"
				end = days_in_current_week[2][0:10] + "T09:00:00Z"
				expected_list.append((start, end))
				start = days_in_current_week[2][0:10] + "T15:00:00Z"
				end = days_in_current_week[2][0:10] + "T20:00:00Z"
				expected_list.append((start, end))
			elif current_day == 3:
				start = days_in_current_week[3][0:10] + "T08:00:00Z"
				end = days_in_current_week[3][0:10] + "T12:00:00Z"
				expected_list.append((start, end))
				start = days_in_current_week[3][0:10] + "T14:00:00Z"
				end = days_in_current_week[3][0:10] + "T17:00:00Z"
				expected_list.append((start, end))
			else:		
				start = day[0:10] + "T08:00:00Z"
				end = day[0:10] + "T20:00:00Z"
				expected_list.append((start, end))
			current_day += 1
		

		# expected_list = [	('2016-02-01T08:00:00Z', '2016-02-01T10:00:00Z'), 
		# 					('2016-02-01T13:00:00Z', '2016-02-01T20:00:00Z'), 
		# 					('2016-02-02T08:00:00Z', '2016-02-02T09:00:00Z'), 
		# 					('2016-02-02T10:00:00Z', '2016-02-02T20:00:00Z'), 
		# 					('2016-02-03T08:00:00Z', '2016-02-03T09:00:00Z'), 
		# 					('2016-02-03T15:00:00Z', '2016-02-03T20:00:00Z'), 
		# 					('2016-02-04T08:00:00Z', '2016-02-04T12:00:00Z'),
		#					('2016-02-04T14:00:00Z', '2016-02-04T17:00:00Z'),
		#					('2016-02-05T08:00:00Z', '2016-02-05T20:00:00Z'),
		#					('2016-02-06T08:00:00Z', '2016-02-06T20:00:00Z'),
		#					('2016-02-07T08:00:00Z', '2016-02-07T20:00:00Z'),]
		# print expected_list
		# print free_time
		self.assertEqual(expected_list, free_time)